from __future__ import annotations

import os
import stat
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..utils.security import generate_api_key, restrict_windows_file_to_current_user

# Where the optional `keychain` extra stores MARM's key. One service/username
# pair, so a `keyring` CLI user finds it under the same names MARM reports.
KEYRING_SERVICE = "marm-mcp"
KEYRING_USERNAME = "api-key"


class KeychainUnavailable(RuntimeError):
    """Raised when an explicit keychain command cannot reach a usable backend.

    Only the opt-in commands raise this. Read paths downgrade to the plaintext
    file instead, because a server that refuses to start on a headless box is
    worse than one that falls back to the storage the issue already accepts.
    """


def managed_key_path() -> Path:
    """Return the managed local env file without creating it."""
    return Path.home() / ".marm" / ".env"


def read_managed_key_from_file(path: Path | None = None) -> str:
    """Read MARM_API_KEY from the managed .env file only.

    Never consults the keychain: Docker and the explicit-`path` callers need the
    key that is actually in the file they named, not one from the user's keychain.
    """
    try:
        for raw_line in (
            (path or managed_key_path()).read_text(encoding="utf-8").splitlines()
        ):
            line = raw_line.strip()
            if not line or line.startswith("#") or not line.startswith("MARM_API_KEY="):
                continue
            value = line.split("=", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                return value[1:-1]
            return value.split("#", 1)[0].strip()
    except OSError:
        pass
    return ""


def read_managed_key(path: Path | None = None) -> str:
    """Read the managed key: the OS keychain first, then the .env file.

    The server's bootstrap and the CLI, Console and Docker callers all resolve
    through here, so a key stored in the keychain can no longer be invisible to
    `marm-memory key reveal` or to the Console's client.

    An explicit ``path`` pins the lookup to that file. That is deliberate: the
    Docker paths pass an env file they are about to hand to a container, and
    substituting the host keychain for it would misrepresent what the container
    is actually going to receive.
    """
    if path is not None:
        return read_managed_key_from_file(path)
    return read_keychain_key() or read_managed_key_from_file()


def _protect_key_file(path: Path) -> bool:
    """Apply and verify owner-only access before treating a key as usable."""
    if sys.platform != "win32":
        try:
            path.chmod(0o600)
            return stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
        except OSError:
            return False
    try:
        return restrict_windows_file_to_current_user(path)
    except OSError:
        return False


def initialize_managed_key(path: Path | None = None) -> tuple[Path, bool]:
    """Create the managed key file once, preserving an existing credential."""
    destination = path or managed_key_path()
    if read_managed_key_from_file(destination):
        if not _protect_key_file(destination):
            raise RuntimeError(f"Could not secure managed key file: {destination}")
        return destination, False
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(
            f"Managed key file exists but does not contain MARM_API_KEY: {destination}"
        ) from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
            key_file.write(f"MARM_API_KEY={generate_api_key()}\n")
    except OSError:
        destination.unlink(missing_ok=True)
        raise
    if not _protect_key_file(destination):
        raise RuntimeError(f"Could not secure managed key file: {destination}")
    return destination, True


# --- Optional OS keychain backend ---------------------------------------------
#
# `keyring` is an optional extra, not a dependency: containers and headless VPS
# boxes have no Secret Service, and on Linux the package drags in dbus/jeepney
# for a backend that cannot exist there. Everything below therefore tolerates
# the package being absent and degrades to the .env file.


def _load_keyring() -> Any | None:
    """Import keyring lazily, or return None when the extra is not installed."""
    try:
        import keyring
    except Exception:
        return None
    return keyring


@lru_cache(maxsize=1)
def keychain_status() -> tuple[bool, str]:
    """Return ``(usable, reason)`` for the OS keychain, cached for the process.

    Cached because every import of ``config.settings`` reaches this through
    ``resolve_marm_api_key``, and on Linux resolving a backend is a DBus round
    trip that can block or raise an unlock prompt. Caching keeps repeated
    imports, including CLI commands that never need a key, off that path.

    ``keyring`` substitutes a failing backend when none is available rather than
    raising at import, so the resolved backend object is what gets inspected
    instead of the import result.
    """
    keyring = _load_keyring()
    if keyring is None:
        return False, "the optional 'keychain' extra (keyring) is not installed"
    try:
        from keyring.backends import fail, null
    except Exception:
        # An older or vendored keyring without those modules: trust the probe.
        return True, ""
    try:
        backend = keyring.get_keyring()
    except Exception as exc:
        return False, f"the keyring backend could not be resolved ({exc})"
    if isinstance(backend, (fail.Keyring, null.Keyring)):
        return False, "no OS keychain backend is available"
    return True, ""


def reset_keychain_cache() -> None:
    """Drop the cached backend probe so a swapped backend is re-examined."""
    keychain_status.cache_clear()


def keychain_installed() -> bool:
    """Whether the optional keyring extra is importable at all."""
    return _load_keyring() is not None


def keychain_available() -> bool:
    """Whether keyring resolved a real keychain backend on this machine."""
    return keychain_status()[0]


def keychain_lookup() -> tuple[str, str]:
    """Return ``(key, problem)`` for the key stored in the OS keychain.

    ``problem`` is empty when a key was found, and also when the keychain is
    merely not installed -- the optional extra being absent is a supported
    configuration, not a fault, and must not become startup noise for the many
    installs that never opted in.

    A keychain that *is* installed but broken (no backend, locked collection, a
    read that raises) does come back with a reason, so a silent fall through to
    the plaintext file is never the only clue the user gets.
    """
    usable, reason = keychain_status()
    if not usable:
        return "", "" if not keychain_installed() else reason
    keyring = _load_keyring()
    if keyring is None:
        return "", ""
    try:
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or "", ""
    except Exception as exc:
        return "", f"the OS keychain could not be read ({type(exc).__name__}: {exc})"


def read_keychain_key() -> str:
    """Return the key stored in the OS keychain, or "" when there is none."""
    return keychain_lookup()[0]


def _write_keychain_key(key: str) -> tuple[bool, str]:
    """Store ``key`` in the OS keychain. Returns ``(ok, reason)``."""
    usable, reason = keychain_status()
    if not usable:
        return False, reason
    keyring = _load_keyring()
    if keyring is None:
        return False, "the optional 'keychain' extra (keyring) is not installed"
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
    except Exception as exc:
        return (
            False,
            f"the OS keychain rejected the write ({type(exc).__name__}: {exc})",
        )
    return True, ""


def write_keychain_key(key: str) -> None:
    """Store ``key`` in the OS keychain, raising when no backend accepts it."""
    ok, reason = _write_keychain_key(key)
    if not ok:
        raise KeychainUnavailable(reason)


def migrate_managed_key_to_keychain(
    path: Path | None = None, *, remove_plaintext: bool = False
) -> tuple[str, bool]:
    """Copy the managed .env key into the OS keychain.

    Returns ``(key, plaintext_removed)``. This is the only path that writes to
    the keychain and it is reachable only from an explicit CLI command: startup
    never does it, because on Linux ``set_password`` can raise an unlock prompt
    and block the import that calls it.

    The plaintext file is kept unless ``remove_plaintext`` is set. The issue
    asks for `.env` to stay as the backward-compatible fallback, and a legacy
    credential is never deleted automatically -- keeping the file is also what
    stops a keychain that later becomes unreachable from silently rotating the
    key out from under every already-configured client.
    """
    source = path or managed_key_path()
    key = read_managed_key_from_file(source)
    if not key:
        raise KeychainUnavailable(f"{source} does not contain MARM_API_KEY")
    write_keychain_key(key)
    # Read back before reporting success: a backend that accepts the write and
    # silently drops it would otherwise look like a completed migration while
    # the file the user was told not to rely on is the only remaining copy.
    if read_keychain_key() != key:
        raise KeychainUnavailable(
            "the OS keychain did not return the key that was just written"
        )
    if not remove_plaintext:
        return key, False
    try:
        source.unlink(missing_ok=True)
    except OSError as exc:
        raise KeychainUnavailable(
            f"the key is in the keychain but {source} could not be removed: {exc}"
        ) from exc
    return key, True
