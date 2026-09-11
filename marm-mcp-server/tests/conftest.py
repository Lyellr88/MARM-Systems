"""Test helpers for isolated MARM server imports."""

import importlib
import os
import shutil
import sys
import tempfile
import time
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _resolve_cbm_binary() -> str | None:
    env = os.environ.get("CBM_BINARY_PATH")
    if env and os.path.exists(env):
        return env
    try:
        from codebase_memory_mcp import _cli

        binary_path = _cli._bin_path(_cli._version())
        if binary_path.exists():
            return str(binary_path)
    except Exception:
        pass
    return None


_CBM_BINARY = _resolve_cbm_binary()
if _CBM_BINARY:
    os.environ.setdefault("CBM_BINARY_PATH", _CBM_BINARY)

requires_binary = pytest.mark.skipif(
    _CBM_BINARY is None,
    reason="codebase-memory-mcp binary not available (offline / not downloaded)",
)


def pytest_collection_modifyitems(items):
    opt_in_markers = {
        "smoke_docker": "MARM_SMOKE_DOCKER",
        "smoke_destructive": "MARM_SMOKE_DESTRUCTIVE",
    }
    for item in items:
        for marker, environment_name in opt_in_markers.items():
            if (
                item.get_closest_marker(marker)
                and os.environ.get(environment_name) != "1"
            ):
                item.add_marker(
                    pytest.mark.skip(reason=f"{marker} requires {environment_name}=1")
                )


def _cbm_sandbox(tmp_path_factory) -> Path:
    """A directory engine 0.10.5 will accept as its home.

    From 0.10.5 the binary refuses to start when any component of its resolved
    cache path grants write access to an account it does not trust, reporting
    "exact executable identity could not be verified". Windows temp roots often
    carry exactly such an entry, which makes pytest's own temp tree unusable as
    the engine's home. LOCALAPPDATA is the same place the engine keeps its real
    cache, so it is permissioned the way the engine expects.
    """
    if os.name != "nt":
        return tmp_path_factory.mktemp("cbm-home")
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("USERPROFILE")
    if not base:
        base = str(Path.home())
    root = Path(base) / "marm-tests"
    root.mkdir(parents=True, exist_ok=True)
    _sweep_stale_sandboxes(root)
    return Path(tempfile.mkdtemp(prefix="cbm-home-", dir=root))


_STALE_SANDBOX_AGE_SECONDS = 6 * 60 * 60


def _sandbox_last_active(path: Path) -> float:
    """Newest mtime anywhere inside the sandbox, not the directory's own.

    A running session writes into `<sandbox>/.cache/codebase-memory-mcp`, and a
    write that deep does not update the sandbox directory's mtime. Judging by the
    directory alone reports "untouched since creation" for the entire run, so a
    session outliving the cutoff would have its home deleted underneath it.
    """
    newest = path.stat().st_mtime
    for child in path.rglob("*"):
        try:
            newest = max(newest, child.stat().st_mtime)
        except OSError:
            continue
    return newest


def _sweep_stale_sandboxes(root: Path) -> None:
    """Drop sandboxes left behind by earlier runs.

    Teardown cannot be relied on for this: the engine child holds lock files
    under its home, so a session that is killed, or that ends before the child
    releases them, leaves the directory on disk. Gated on the sandbox's most
    recent internal activity so a concurrent or long-running session keeps its
    own. Not proof against a live session that has been completely idle for the
    whole cutoff window, which no test run is.
    """
    cutoff = time.time() - _STALE_SANDBOX_AGE_SECONDS
    for path in root.glob("cbm-home-*"):
        try:
            if path.is_dir() and _sandbox_last_active(path) < cutoff:
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass


@pytest.fixture(autouse=True, scope="session")
def isolated_cbm_store(tmp_path_factory):
    """Keep test indexes out of the developer's real code graph.

    The binary stores each project in ~/.cache/codebase-memory-mcp regardless
    of MARM_GRAPH_STORE_DIR, so any test that reaches index_repository used to
    add a permanent entry to the machine's real project list. It resolves that
    directory from HOME (POSIX) or USERPROFILE (Windows), both verified to
    redirect it, so pointing them at a session temp directory isolates the
    store without changing how the child is invoked.
    """
    sandbox = _cbm_sandbox(tmp_path_factory)
    previous = {name: os.environ.get(name) for name in ("HOME", "USERPROFILE")}
    for name in previous:
        os.environ[name] = str(sandbox)
    yield sandbox
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    if sandbox.parent.name == "marm-tests":
        shutil.rmtree(sandbox, ignore_errors=True)


_KEY_MANAGEMENT_MODULE = "marm_mcp_server.services.key_management"


class MemoryKeychain:
    """In-process stand-in for the OS keychain.

    A test run must never reach the developer's real credential store. On Windows
    and macOS a single `keyring.set_password` leaves a permanent `marm-mcp`
    entry behind, and the round-trip assertions then read back a value the
    developer never stored. Everything lives in a dict that dies with the test.
    """

    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.values.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.values[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        del self.values[(service, username)]

    def get_keyring(self) -> "MemoryKeychain":
        """Stand in for a resolved backend: not a fail/null stub, so "usable"."""
        return self


class _FailKeyring:
    """Mirrors keyring.backends.fail.Keyring, which keyring falls back to."""


class _NullKeyring:
    """Mirrors keyring.backends.null.Keyring."""


def _reset_loaded_keychain_cache() -> None:
    """Clear the cached backend probe, without importing the package ourselves.

    Deliberately lazy: the probe is per-module-instance, so a module that is
    imported during the test already starts uncached, and importing MARM here
    for every test in the suite would be a lot of work for a cache reset.
    """
    module = sys.modules.get(_KEY_MANAGEMENT_MODULE)
    if module is not None:
        module.reset_keychain_cache()


def install_memory_keychain(monkeypatch) -> MemoryKeychain:
    """Make `import keyring` resolve to an in-memory backend for this test."""
    chain = MemoryKeychain()
    module = types.ModuleType("keyring")
    # Reached through the instance on every call, not bound once at install
    # time: a test that monkeypatches `memory_keychain.set_password` to observe
    # or drop a write has to actually intercept it.
    module.get_password = lambda service, username: chain.get_password(
        service, username
    )
    module.set_password = lambda service, username, password: chain.set_password(
        service, username, password
    )
    module.delete_password = lambda service, username: chain.delete_password(
        service, username
    )
    module.get_keyring = lambda: chain.get_keyring()

    backends = types.ModuleType("keyring.backends")
    fail_module = types.ModuleType("keyring.backends.fail")
    fail_module.Keyring = _FailKeyring
    null_module = types.ModuleType("keyring.backends.null")
    null_module.Keyring = _NullKeyring
    backends.fail = fail_module
    backends.null = null_module
    module.backends = backends

    for name, value in (
        ("keyring", module),
        ("keyring.backends", backends),
        ("keyring.backends.fail", fail_module),
        ("keyring.backends.null", null_module),
    ):
        monkeypatch.setitem(sys.modules, name, value)

    _reset_loaded_keychain_cache()
    return chain


def uninstall_keychain(monkeypatch) -> None:
    """Make `import keyring` fail, standing in for a machine without the extra.

    A None entry in sys.modules is what CPython uses to mean "this import
    failed"; `import keyring` then raises ImportError, which is the branch the
    optional extra takes on a plain `pip install marm-mcp-server`.
    """
    monkeypatch.setitem(sys.modules, "keyring", None)
    _reset_loaded_keychain_cache()


@pytest.fixture(autouse=True)
def memory_keychain(monkeypatch) -> MemoryKeychain:
    """Hand every test an empty in-memory keychain instead of the real one.

    Empty on purpose: tests written before the keychain existed assert that a
    missing key makes resolution fall through to `.env`, and that has to stay
    true. Tests that need a stored key seed this fixture.
    """
    return install_memory_keychain(monkeypatch)


def load_isolated_server(monkeypatch, tmp_path, api_key="", write_queue_enabled=False):
    """Import the server after pointing global state at a temporary database.

    Modules are dropped via monkeypatch.delitem, not a bare del, so the original
    module objects are restored at teardown. Otherwise the isolated re-import
    below leaves a new module generation in sys.modules for the rest of the
    session, and later tests that bound symbols (e.g. MARMMemory) at import time
    would silently reference the stale generation.
    """
    for name in list(sys.modules):
        if name == "marm_mcp_server" or name.startswith("marm_mcp_server."):
            monkeypatch.delitem(sys.modules, name)

    monkeypatch.setenv("MARM_DB_PATH", str(tmp_path / "marm_memory.db"))
    monkeypatch.setenv("MARM_ANALYTICS_DB_PATH", str(tmp_path / "analytics.db"))
    monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
    monkeypatch.setenv("WRITE_QUEUE_ENABLED", "1" if write_queue_enabled else "0")
    if api_key:
        monkeypatch.setenv("MARM_API_KEY", api_key)
    else:
        monkeypatch.delenv("MARM_API_KEY", raising=False)

    server = importlib.import_module("marm_mcp_server.server")

    memory_module = importlib.import_module("marm_mcp_server.core.memory")
    monkeypatch.setattr(memory_module.memory, "_encoder_failed", True)
    monkeypatch.setattr(memory_module.memory, "active_notebook_entries_by_session", {})
    monkeypatch.setattr(memory_module.memory, "active_log_session", "main")

    rate_limiter_module = importlib.import_module("marm_mcp_server.core.rate_limiter")
    rate_limiter_module.rate_limiter.request_buckets.clear()
    rate_limiter_module.rate_limiter.blocked_ips.clear()

    return server


def local_client(app):
    return TestClient(app, client=("127.0.0.1", 50000))


def remote_client(app):
    return TestClient(app, client=("10.0.0.25", 50000))


@pytest.fixture(scope="session")
def binary() -> str:
    if _CBM_BINARY is None:
        pytest.skip("binary unavailable")
    return _CBM_BINARY


@pytest.fixture(scope="session")
def graph_client(binary):
    from marm_graph.config import settings as graph_settings
    from marm_graph.core.cbm_client import CbmClient

    graph_settings.STORE_DIR.mkdir(parents=True, exist_ok=True)
    client = CbmClient(
        command=[binary],
        cwd=graph_settings.CBM_CWD,
        startup_timeout=90,
        call_timeout=180,
    )
    client.start()
    yield client
    client.close()


@pytest.fixture(scope="session")
def graph_project(graph_client) -> str:
    """Index the packaged marm_graph source and return the derived project name."""
    package_root = Path(__file__).resolve().parents[1] / "marm_graph"
    result = graph_client.call_tool(
        "index_repository", {"repo_path": str(package_root), "mode": "moderate"}
    )
    name = result.get("project")
    assert name, f"index_repository returned no project name: {result}"
    return name


@pytest.fixture(scope="session")
def client(graph_client):
    """Compatibility alias for tests moved from the standalone marm-graph suite."""
    return graph_client


@pytest.fixture(scope="session")
def project(graph_project):
    """Compatibility alias for tests moved from the standalone marm-graph suite."""
    return graph_project
