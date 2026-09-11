from __future__ import annotations

import argparse
import asyncio
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import structlog
import uvicorn

if TYPE_CHECKING:
    import sqlite3
    from contextlib import AbstractContextManager

    from fastapi import FastAPI

from .config import settings
from .config.settings import (
    DEFAULT_DB_PATH,
    SCHEDULER_AVAILABLE,
    SEMANTIC_SEARCH_AVAILABLE,
    SERVER_HOST,
    SERVER_PORT,
    SERVER_VERSION,
)
from .core.rate_limiter import rate_limiter
from .services.cli_output import (
    _print_doctor,
    _print_maintenance,
    _print_payload,
    _print_status,
)
from .services.cli_parser import _compatibility_parser, _product_parser
from .utils.dependency_check import check_dependencies
from .utils.security import generate_api_key

logger = structlog.get_logger()


def _write_generated_api_key() -> None:
    """Write a newly generated key directly to the requesting terminal."""
    sys.stdout.write(f"{generate_api_key()}\n")
    sys.stdout.write(
        "\nSet this as your MARM_API_KEY environment variable.\n"
        "Keep it secret - this is the only time it will be shown.\n"
    )


async def run_server_with_shutdown() -> None:
    """Run the HTTP server with MARM's shared graceful-shutdown path."""
    from .core.shutdown_manager import shutdown_manager
    from .server import app

    shutdown_manager.shutdown_event = asyncio.Event()
    shutdown_manager.shutdown_initiated = False
    shutdown_manager._cleanup_complete = False
    await shutdown_manager.setup_signal_handlers()
    server = uvicorn.Server(
        uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")
    )
    server_task = asyncio.create_task(server.serve())
    shutdown_task = asyncio.create_task(shutdown_manager.wait_for_shutdown())
    done, _pending = await asyncio.wait(
        [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
    )
    graceful_shutdown_signaled = shutdown_task in done
    if graceful_shutdown_signaled:
        logger.info("Shutdown signal received, closing server")
        server.should_exit = True
        await server_task
    for task in (shutdown_task,):
        if task.done():
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    if server_task in done and not graceful_shutdown_signaled:
        await server_task
    if graceful_shutdown_signaled:
        logger.info("Server shutdown complete")


def create_server() -> "FastAPI":
    """Return the FastAPI app instance for external use."""
    from .server import app

    return app


def apply_runtime_preset(
    *,
    swarm: bool = False,
    swarm_max: bool = False,
    trusted: bool = False,
    rate_limit_rpm: Optional[int] = None,
) -> dict:
    """Apply CLI rate-limit/write-queue presets to imported runtime modules."""
    from .core import memory as memory_module

    if rate_limit_rpm is not None and rate_limit_rpm < 0:
        raise ValueError("--rate-limit-rpm must be 0 or greater")
    rpm = settings.MARM_RATE_LIMIT_RPM_DEFAULT
    mode = "default"
    write_queue_enabled = settings.WRITE_QUEUE_ENABLED
    if swarm:
        rpm, mode, write_queue_enabled = 200, "swarm", True
    if swarm_max:
        rpm, mode, write_queue_enabled = 600, "swarm-max", True
    if rate_limit_rpm is not None:
        rpm, mode = rate_limit_rpm, "custom"
    if trusted:
        rpm, mode, write_queue_enabled = 0, "trusted", True
    if "COMPACTION_TRIGGER_COUNT" in os.environ:
        compaction_trigger_count = settings.COMPACTION_TRIGGER_COUNT
    else:
        compaction_trigger_count = 5 if mode == "default" else 20
    settings.MARM_RATE_LIMIT_RPM = rpm
    settings.WRITE_QUEUE_ENABLED = write_queue_enabled
    settings.COMPACTION_TRIGGER_COUNT = compaction_trigger_count
    memory_module.WRITE_QUEUE_ENABLED = write_queue_enabled
    memory_module.COMPACTION_TRIGGER_COUNT = compaction_trigger_count
    rate_limiter.configure(
        requests=rpm,
        window=settings.RATE_LIMIT_WINDOW_SECONDS,
        block_duration=settings.RATE_LIMIT_BLOCK_SECONDS,
    )
    return {
        "mode": mode,
        "rate_limit_rpm": rpm,
        "write_queue_enabled": write_queue_enabled,
    }


def _profile_flags(profile: str) -> dict[str, bool]:
    return {
        "swarm": profile == "swarm",
        "swarm_max": profile == "swarm-max",
        "trusted": profile == "trusted",
    }


def reconcile_profile_and_rpm(
    profile: str, rate_limit_rpm: int | None
) -> tuple[str, int | None]:
    """apply_runtime_preset lets trusted overwrite an explicit rpm, so never pair the two."""
    if rate_limit_rpm is not None and profile == "trusted":
        return "standard", rate_limit_rpm
    return profile, rate_limit_rpm


def resolve_runtime_preset(
    profile: str | None, rate_limit_rpm: int | None
) -> tuple[str, int | None]:
    """An explicit CLI flag wins; otherwise a Console-saved preset survives the restart."""
    if profile is not None:
        return reconcile_profile_and_rpm(profile, rate_limit_rpm)
    from .core import runtime_flags

    try:
        saved_profile, saved_rpm = runtime_flags.saved_runtime_preset()
    except Exception:
        logger.warning("Could not read the saved runtime preset", exc_info=True)
        return "standard", rate_limit_rpm
    resolved = saved_profile or "standard"
    effective_rpm = rate_limit_rpm if rate_limit_rpm is not None else saved_rpm
    if rate_limit_rpm is None:
        return resolved, effective_rpm
    return reconcile_profile_and_rpm(resolved, effective_rpm)


def resolve_restart_preset(state: dict) -> tuple[str, int | None]:
    """A saved Console change is newer than the metadata written at the last start."""
    from .core import runtime_flags

    try:
        saved_profile, saved_rpm = runtime_flags.saved_runtime_preset()
    except Exception:
        logger.warning("Could not read the saved runtime preset", exc_info=True)
        saved_profile, saved_rpm = None, None
    if saved_profile:
        return reconcile_profile_and_rpm(saved_profile, saved_rpm)
    return state.get("profile", "standard"), state.get("rate_limit_rpm")


def _run_foreground(
    *, profile: str | None, rate_limit_rpm: int | None, runtime_id: str | None = None
) -> None:
    from .core.runtime_manager import (
        clear_state,
        log_path,
        make_state,
        start_log_maintenance,
        write_state,
    )

    identity = runtime_id or str(uuid.uuid4())
    profile, rate_limit_rpm = resolve_runtime_preset(profile, rate_limit_rpm)
    os.environ["MARM_RUNTIME_ID"] = identity
    os.environ["MARM_RUNTIME_PROFILE"] = profile
    runtime_config = apply_runtime_preset(
        **_profile_flags(profile), rate_limit_rpm=rate_limit_rpm
    )
    write_state(
        make_state(
            runtime_id=identity,
            profile=profile,
            rate_limit_rpm=rate_limit_rpm,
        )
    )
    start_log_maintenance(log_path())
    try:
        _log_startup(runtime_config)
        asyncio.run(run_server_with_shutdown())
    finally:
        clear_state(identity)


def _log_startup(runtime_config: dict) -> None:
    base_url = f"http://{SERVER_HOST}:{SERVER_PORT}"
    logger.info(
        "Starting MARM MCP Server",
        version=SERVER_VERSION,
        mcp_endpoint=f"{base_url}/mcp",
        docs=f"{base_url}/docs",
        database=DEFAULT_DB_PATH,
        rate_limit_mode=runtime_config["mode"],
        rate_limit_rpm=runtime_config["rate_limit_rpm"],
        write_queue_enabled=runtime_config["write_queue_enabled"],
    )
    logger.info(
        "Feature status",
        semantic_search="ENABLED" if SEMANTIC_SEARCH_AVAILABLE else "DISABLED",
        scheduler="ENABLED" if SCHEDULER_AVAILABLE else "DISABLED",
    )


def _ensure_runtime() -> dict[str, Any]:
    from .core.runtime_manager import inspect_runtime, start_background

    current = inspect_runtime()
    return current if current["state"] == "ready" else start_background()


def _fast_start_http(args: argparse.Namespace) -> int:
    """Delegate the reusable local HTTP workflow to its service owner."""
    from .services.product_workflows import fast_start_http

    return fast_start_http(args)


def _runtime_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    from .core.runtime_manager import request_runtime_strict

    _ensure_runtime()
    return request_runtime_strict(path, method="POST", payload=payload, timeout=300.0)


def _migrate_embeddings() -> int:
    print("Stop every MARM HTTP and STDIO process before migrating embeddings.")
    print("STDIO processes cannot be detected reliably and must be stopped manually.")
    if _http_server_is_running():
        print(
            "Migration refused: a MARM HTTP server is still running.", file=sys.stderr
        )
        return 1
    if not Path(DEFAULT_DB_PATH).exists():
        print("No MARM memory database exists; nothing needs migration.")
        return 0
    from .utils.embedding_migration import migrate_embeddings

    try:
        result = migrate_embeddings(DEFAULT_DB_PATH)
    except Exception as exc:
        logger.error("Embedding migration failed", error=str(exc))
        print("Embedding migration failed.", file=sys.stderr)
        return 1
    print(f"Embedding migration complete: {result['rows_migrated']} vector(s) updated.")
    return 0


class _ReadOnlyMemory:
    """Minimal get_connection() shim so a dry-run scan never opens MARMMemory,
    whose constructor runs schema DDL (DROP/CREATE INDEX) on every call."""

    def __init__(self, db_path: str) -> None:
        self._uri = f"{Path(db_path).resolve().as_uri()}?mode=ro"

    def get_connection(self) -> AbstractContextManager[sqlite3.Connection]:
        import sqlite3
        from contextlib import closing

        return closing(sqlite3.connect(self._uri, uri=True))


def _compaction_dry_run(session_name: str, as_json: bool) -> int:
    if not Path(DEFAULT_DB_PATH).exists():
        if as_json:
            _print_payload({"candidates": [], "report_path": None}, as_json=True)
        else:
            print("No MARM memory database exists; nothing to scan.")
        return 0
    from .core.compaction import run_compaction_dry_run

    result = run_compaction_dry_run(_ReadOnlyMemory(DEFAULT_DB_PATH), session_name)
    if as_json:
        _print_payload(result, as_json=True)
        return 0
    candidates = result["candidates"]
    if not candidates:
        print(f"No compaction candidates found for session '{session_name}'.")
        return 0
    print(f"{len(candidates)} compaction candidate(s) for session '{session_name}':")
    for candidate in candidates:
        print(
            f"  {len(candidate['source_memory_ids'])} memories, "
            f"avg similarity {candidate['avg_similarity']}"
        )
    if result["report_path"]:
        print(f"Report written to {result['report_path']}")
    else:
        print("Report could not be written; see error above.", file=sys.stderr)
    return 0


def _rechunk() -> int:
    print("Stop every MARM HTTP and STDIO process before re-chunking.")
    print("STDIO processes cannot be detected reliably and must be stopped manually.")
    if _http_server_is_running():
        print("Re-chunk refused: a MARM HTTP server is still running.", file=sys.stderr)
        return 1
    if not Path(DEFAULT_DB_PATH).exists():
        print("No MARM memory database exists; nothing needs re-chunking.")
        return 0
    from .utils.chunk_backfill import RechunkRefused, rechunk_memories

    try:
        result = rechunk_memories(DEFAULT_DB_PATH)
    except RechunkRefused as exc:
        print(f"Re-chunk refused: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.error("Re-chunk failed", error=str(exc))
        print("Re-chunk failed.", file=sys.stderr)
        return 1
    if not result["memories_rechunked"]:
        return 0
    print(
        f"Re-chunked {result['memories_rechunked']} memories."
        f" {result['chunks_before']} chunk rows -> {result['chunks_after']}."
    )
    return 0


def _upgrade(args: argparse.Namespace) -> int:
    """Delegate package update policy to the lifecycle service."""
    from .services.product_workflows import upgrade

    return upgrade(args, print_payload=_print_payload)


def _uninstall(args: argparse.Namespace) -> int:
    """Delegate package removal policy to the lifecycle service."""
    from .services.product_workflows import uninstall

    return uninstall(args)


def _init_skill(args: argparse.Namespace) -> int:
    """Delegate skill installation to its focused service."""
    from .services.skill_install import install_skill

    return install_skill(args)


def _dispatch_product(args: argparse.Namespace) -> int:
    from .core import runtime_manager
    from .services.runtime_status import (
        doctor_status,
        full_status,
        knowledge_status,
        maintenance_status,
    )

    if args.command == "fast-start-http":
        return _fast_start_http(args)
    if args.command in {"start", "http"}:
        if args.foreground:
            _run_foreground(
                profile=args.profile,
                rate_limit_rpm=args.rate_limit_rpm,
                runtime_id=args.runtime_id,
            )
            return 0
        background_profile, background_rpm = resolve_runtime_preset(
            args.profile, args.rate_limit_rpm
        )
        result = runtime_manager.start_background(
            profile=background_profile, rate_limit_rpm=background_rpm
        )
        state = result.get("metadata", {})
        print(
            f"MARM runtime ready: http://127.0.0.1:{state.get('port', SERVER_PORT)}/mcp"
        )
        print("Console: run `marm-memory console` when you want the web app.")
        return 0
    if args.command == "stdio":
        from . import server_stdio

        server_stdio.main()
        return 0
    if args.command == "stop":
        print(
            "MARM runtime stopped."
            if runtime_manager.stop_runtime(force=args.force)
            else "MARM runtime is not running."
        )
        return 0
    if args.command == "restart":
        current = runtime_manager.read_state() or {}
        profile, rpm = resolve_restart_preset(current)
        runtime_manager.stop_runtime(force=args.force, stop_console_process=False)
        runtime_manager.start_background(profile=profile, rate_limit_rpm=rpm)
        print("MARM runtime restarted. A running Console was left available.")
        return 0
    if args.command == "status":
        payload = full_status()
        (
            _print_payload(payload, as_json=True)
            if args.as_json
            else _print_status(payload)
        )
        return 0
    if args.command == "doctor":
        payload = doctor_status()
        (
            _print_payload(payload, as_json=True)
            if args.as_json
            else _print_doctor(payload)
        )
        return 0 if payload["ok"] else 1
    if args.command == "logs":
        return _show_logs(args.lines, args.follow)
    if args.command == "console":
        _ensure_runtime()
        from .console.cli import run_console

        return run_console(
            open_browser=args.open_browser,
            foreground=args.foreground,
            import_key=args.import_key,
        )
    if args.command == "knowledge":
        if args.knowledge_command == "status":
            _print_payload(knowledge_status())
            return 0
        if args.knowledge_command == "auto":
            return _dispatch_auto(args.state, "concept")
        payload = {
            "search_all": args.search_all,
            "session_name": args.session,
            "project": args.project,
        }
        _print_payload(_runtime_post("/marm_concept_build", payload))
        return 0
    if args.command == "projects":
        if args.projects_command == "auto":
            return _dispatch_auto(args.state, "graph")
        return _dispatch_projects(args)
    if args.command == "maintenance":
        if args.maintenance_command == "status":
            payload = maintenance_status()
            (
                _print_payload(payload, as_json=True)
                if args.as_json
                else _print_maintenance(payload)
            )
            return 0
        if args.maintenance_command == "chunks":
            return _rechunk()
        if args.maintenance_command == "compaction":
            return _compaction_dry_run(args.session, args.as_json)
        return _migrate_embeddings()
    if args.command == "key":
        if args.key_command == "generate":
            _write_generated_api_key()
            return 0
        from .services import key_management

        if args.key_command == "init":
            if args.remove_plaintext and not args.keychain:
                print(
                    "--remove-plaintext only applies together with --keychain: the key "
                    "has to be stored somewhere before the file can go.",
                    file=sys.stderr,
                )
                return 2
            path, created = key_management.initialize_managed_key()
            state = "Created" if created else "Using existing"
            print(f"{state} MARM API key file: {path}")
            if not args.keychain:
                return 0
            try:
                _key, removed = key_management.migrate_managed_key_to_keychain(
                    path, remove_plaintext=args.remove_plaintext
                )
            except key_management.KeychainUnavailable as exc:
                print(
                    f"Could not store the key in the OS keychain: {exc}",
                    file=sys.stderr,
                )
                return 1
            print(
                "Stored the MARM API key in the OS keychain "
                f"({key_management.KEYRING_SERVICE}/{key_management.KEYRING_USERNAME})."
            )
            if removed:
                print(f"Removed the plaintext key file: {path}")
            else:
                print(f"Kept {path} as the backward-compatible fallback.")
            return 0
        if args.key_command == "path":
            print(key_management.managed_key_path())
            return 0
        key = key_management.read_managed_key()
        if not key:
            print(
                "No managed MARM API key exists. Run `marm-memory key init` first.",
                file=sys.stderr,
            )
            return 1
        print(
            "Warning: terminal capture and shell history may retain this key.",
            file=sys.stderr,
        )
        print(key)
        return 0
    if args.command == "docker":
        return _dispatch_docker(args)
    if args.command in {"upgrade", "update"}:
        return _upgrade(args)
    if args.command == "uninstall":
        return _uninstall(args)
    if args.command == "init":
        return _init_skill(args)
    if args.command == "version":
        print(SERVER_VERSION)
        return 0
    return 2


def _dispatch_docker(args: argparse.Namespace) -> int:
    """Delegate Docker behavior to the shared Docker CLI service."""
    from .services.docker_cli import dispatch_docker

    return dispatch_docker(args, print_payload=_print_payload)


def _dispatch_auto(state: str, scope: str) -> int:
    """Turn automatic indexing on or off for one of the two indexers."""
    from .services.graph_auto_cli import dispatch_auto

    return dispatch_auto(state=state, scope=scope, print_payload=_print_payload)


def _dispatch_projects(args: argparse.Namespace) -> int:
    """Delegate code-index operations to the focused project CLI service."""
    from .services.projects_cli import dispatch_projects

    return dispatch_projects(
        args,
        ensure_runtime=_ensure_runtime,
        runtime_post=_runtime_post,
        print_payload=_print_payload,
    )


def _show_logs(lines: int, follow: bool) -> int:
    """Delegate managed-log display to the focused log service."""
    from .core.runtime_manager import log_path
    from .services.product_logs import show_logs

    return show_logs(lines, follow, path=log_path())


def _dispatch_compatibility(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> int:
    if args.generate_key:
        _write_generated_api_key()
        return 0
    if args.check_deps:
        return 0 if check_dependencies() else 1
    if args.migrate_embeddings:
        return _migrate_embeddings()
    if args.rechunk:
        return _rechunk()
    try:
        runtime_config = apply_runtime_preset(
            swarm=args.swarm,
            swarm_max=args.swarm_max,
            trusted=args.trusted,
            rate_limit_rpm=args.rate_limit_rpm,
        )
    except ValueError as exc:
        parser.error(str(exc))
    _log_startup(runtime_config)
    try:
        asyncio.run(run_server_with_shutdown())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as exc:
        logger.error("Server error", error=str(exc))
        return 1
    return 0


def main() -> None:
    """Dispatch the product CLI or preserve the legacy server command."""
    executable = Path(sys.argv[0]).name.lower()
    product_mode = executable.startswith("marm-memory") or (
        len(sys.argv) > 1
        and sys.argv[1]
        in {
            "start",
            "fast-start-http",
            "http",
            "stdio",
            "stop",
            "restart",
            "status",
            "console",
            "logs",
            "doctor",
            "knowledge",
            "projects",
            "maintenance",
            "key",
            "docker",
            "upgrade",
            "update",
            "uninstall",
            "init",
            "version",
        }
    )
    parser = _product_parser() if product_mode else _compatibility_parser()
    arguments = sys.argv[1:]
    if product_mode and arguments[:1] == ["help"]:
        if len(arguments) == 1:
            parser.print_help()
            raise SystemExit(0)
        arguments = [arguments[1], "--help", *arguments[2:]]
    args = parser.parse_args(arguments)
    if product_mode:
        try:
            code = _dispatch_product(args)
        except KeyboardInterrupt:
            print("Operation cancelled.", file=sys.stderr)
            code = 130
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            code = 1
    else:
        code = _dispatch_compatibility(args, parser)
    raise SystemExit(code)


def _http_server_is_running() -> bool:
    probe_host = SERVER_HOST
    if probe_host in {"0.0.0.0", "::", "[::]"}:
        probe_host = "127.0.0.1"
    request = urllib.request.Request(f"http://{probe_host}:{SERVER_PORT}/health")
    try:
        with urllib.request.urlopen(request, timeout=0.75):
            return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
