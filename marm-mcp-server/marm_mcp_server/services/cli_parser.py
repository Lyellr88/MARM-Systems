from __future__ import annotations

import argparse
from pathlib import Path

from ..config.settings import SERVER_VERSION


def _add_profile_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        choices=("standard", "swarm", "swarm-max", "trusted"),
        default=None,
        help="Rate-limit preset. Omitted means a Console-saved profile, else standard.",
    )
    parser.add_argument(
        "--rate-limit-rpm",
        type=int,
        help="Override HTTP rate limit RPM; 0 disables rate limiting",
    )


def _add_docker_run_arguments(parser: argparse.ArgumentParser) -> None:
    _add_profile_arguments(parser)
    # A container is configured at run time and must not inherit a host-saved preset.
    parser.set_defaults(profile="standard")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--data-dir", type=Path, default=Path.home() / ".marm")
    parser.add_argument("--name", default="marm-mcp-server")
    parser.add_argument("--tag", default="latest")
    parser.add_argument("--repo", type=Path, action="append", default=[])
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--expose-network", action="store_true")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--memory")
    parser.add_argument("--cpus")


def _product_help() -> str:
    """Return the stable, human-oriented root help for the product CLI."""
    from .product_help import render_product_help

    return render_product_help(SERVER_VERSION)


class _ProductArgumentParser(argparse.ArgumentParser):
    """Keep root help stable while retaining argparse for all subcommands."""

    def format_help(self) -> str:
        return _product_help()


def _product_parser() -> argparse.ArgumentParser:
    parser = _ProductArgumentParser(
        prog="marm-memory",
        description="Run and manage marm-memory locally",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Show help")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=SERVER_VERSION,
        help="Show installed version",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=argparse.ArgumentParser
    )

    start = subparsers.add_parser("start", help="Start the local MARM runtime")
    _add_profile_arguments(start)
    start.add_argument("--foreground", action="store_true")
    start.add_argument("--runtime-id", help=argparse.SUPPRESS)

    fast_start = subparsers.add_parser(
        "fast-start-http", help="Start HTTP, Console, and optional client setup"
    )
    _add_profile_arguments(fast_start)
    fast_start.add_argument("--client", help="Configure a supported MCP client")
    fast_start.add_argument("--no-console", action="store_true")
    fast_start.add_argument("--no-browser", action="store_true")

    http = subparsers.add_parser(
        "http", help="Run the HTTP transport in the foreground"
    )
    _add_profile_arguments(http)
    http.add_argument("--runtime-id", help=argparse.SUPPRESS)
    http.set_defaults(foreground=True)

    subparsers.add_parser("stdio", help="Run the MCP STDIO transport")

    stop = subparsers.add_parser("stop", help="Stop the managed MARM runtime")
    stop.add_argument("--force", action="store_true")
    restart = subparsers.add_parser("restart", help="Restart the managed runtime")
    restart.add_argument("--force", action="store_true")
    status = subparsers.add_parser("status", help="Show local MARM status")
    status.add_argument("--json", action="store_true", dest="as_json")
    console = subparsers.add_parser("console", help="Launch MARM Console")
    browser = console.add_mutually_exclusive_group()
    browser.add_argument("--open", action="store_true", dest="open_browser")
    browser.add_argument("--no-open", action="store_false", dest="open_browser")
    console.set_defaults(open_browser=True)
    console.add_argument("--foreground", action="store_true")
    console.add_argument(
        "--import-key",
        action="store_true",
        help="Create a managed authenticated Console browser session",
    )
    logs = subparsers.add_parser("logs", help="Read managed runtime logs")
    logs.add_argument("--follow", action="store_true")
    logs.add_argument("--lines", type=int, default=100)
    doctor = subparsers.add_parser("doctor", help="Diagnose the local install")
    doctor.add_argument("--json", action="store_true", dest="as_json")

    knowledge = subparsers.add_parser("knowledge", help="Manage concept extraction")
    knowledge_sub = knowledge.add_subparsers(dest="knowledge_command", required=True)
    knowledge_sub.add_parser("status")
    build = knowledge_sub.add_parser("build")
    scope = build.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", dest="search_all")
    scope.add_argument("--session")
    scope.add_argument("--project")
    knowledge_auto = knowledge_sub.add_parser(
        "auto", help="Turn automatic concept extraction on or off"
    )
    knowledge_auto.add_argument("state", choices=("on", "off", "status"))

    projects = subparsers.add_parser("projects", help="Manage code indexes")
    projects_sub = projects.add_subparsers(dest="projects_command", required=True)
    projects_sub.add_parser("list")
    index = projects_sub.add_parser("index")
    index.add_argument("path")
    index.add_argument(
        "--mode", choices=("fast", "moderate", "full"), default="moderate"
    )
    project_status = projects_sub.add_parser("status")
    project_status.add_argument("project", nargs="?")
    remove = projects_sub.add_parser("remove")
    remove.add_argument("project")
    remove.add_argument("--confirm", required=True)
    projects_auto = projects_sub.add_parser(
        "auto", help="Turn automatic code re-indexing on or off"
    )
    projects_auto.add_argument("state", choices=("on", "off", "status"))

    maintenance = subparsers.add_parser("maintenance")
    maintenance_sub = maintenance.add_subparsers(
        dest="maintenance_command", required=True
    )
    maintenance_status = maintenance_sub.add_parser("status")
    maintenance_status.add_argument("--json", action="store_true", dest="as_json")
    embeddings = maintenance_sub.add_parser("embeddings")
    embeddings_sub = embeddings.add_subparsers(dest="embeddings_command", required=True)
    embeddings_sub.add_parser("migrate")
    chunks = maintenance_sub.add_parser("chunks")
    chunks_sub = chunks.add_subparsers(dest="chunks_command", required=True)
    chunks_sub.add_parser("rechunk")
    compaction = maintenance_sub.add_parser("compaction")
    compaction_sub = compaction.add_subparsers(dest="compaction_command", required=True)
    compaction_dry_run = compaction_sub.add_parser("dry-run")
    compaction_dry_run.add_argument("--session", required=True)
    compaction_dry_run.add_argument("--json", action="store_true", dest="as_json")

    key = subparsers.add_parser("key", help="Manage local bearer authentication")
    key_sub = key.add_subparsers(dest="key_command", required=True)
    key_sub.add_parser("generate", help="Generate and display an ephemeral key")
    key_init = key_sub.add_parser(
        "init", help="Create or reuse the managed local key file"
    )
    key_init.add_argument(
        "--keychain",
        action="store_true",
        help="Also store the managed key in the OS keychain (needs the keychain extra)",
    )
    key_init.add_argument(
        "--remove-plaintext",
        action="store_true",
        dest="remove_plaintext",
        help="With --keychain, delete the .env file once the keychain has the key",
    )
    key_sub.add_parser("path", help="Print the managed local key-file path")
    key_sub.add_parser("reveal", help="Display the managed local key")

    from .docker_cli import add_docker_commands

    add_docker_commands(subparsers, _add_docker_run_arguments)
    upgrade = subparsers.add_parser(
        "upgrade", aliases=["update"], help="Check for and install a newer MARM release"
    )
    upgrade.add_argument("--check", action="store_true")
    upgrade.add_argument("--version")
    upgrade.add_argument("--yes", action="store_true")
    upgrade.add_argument("--json", action="store_true", dest="as_json")

    uninstall = subparsers.add_parser(
        "uninstall", help="Remove MARM while preserving user data"
    )
    uninstall.add_argument("--yes", action="store_true")

    init = subparsers.add_parser(
        "init", help="Install the MARM skill into detected agents"
    )
    from .skill_install import AGENTS

    for agent in AGENTS:
        init.add_argument(
            f"--g-{agent}",
            action="store_true",
            dest=f"global_{agent}",
            help=f"Install into the home-folder {agent} directory",
        )

    subparsers.add_parser("version", help="Show installed version")
    return parser


def _compatibility_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MARM MCP Server")
    parser.add_argument("--check-deps", action="store_true")
    parser.add_argument("--generate-key", action="store_true")
    parser.add_argument("--swarm", action="store_true")
    parser.add_argument("--swarm-max", action="store_true")
    parser.add_argument("--trusted", action="store_true")
    parser.add_argument("--rate-limit-rpm", type=int)
    parser.add_argument("--migrate-embeddings", action="store_true")
    parser.add_argument("--rechunk", action="store_true")
    return parser
