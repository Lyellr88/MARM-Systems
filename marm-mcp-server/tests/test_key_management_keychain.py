"""Keychain storage in `services/key_management` (issue #37).

The autouse `memory_keychain` fixture in conftest.py swaps `keyring` for an
in-memory backend for the whole session, so nothing here can leave an entry in
the developer's real Credential Manager, Keychain, or Secret Service.
"""

from __future__ import annotations

import pytest
from conftest import uninstall_keychain

from marm_mcp_server.services import key_management


def _managed_env_file(tmp_path, key: str | None = "plaintext-key"):
    path = tmp_path / ".marm" / ".env"
    path.parent.mkdir(parents=True, exist_ok=True)
    if key is not None:
        path.write_text(f"MARM_API_KEY={key}\n")
    return path


def test_migration_stores_the_key_and_keeps_the_file_by_default(
    tmp_path, memory_keychain
):
    """The issue keeps .env as the backward-compatible fallback.

    Leaving it in place is also what stops a keychain that later becomes
    unreachable from rotating the key out from under configured clients.
    """
    path = _managed_env_file(tmp_path)

    key, removed = key_management.migrate_managed_key_to_keychain(path)

    assert key == "plaintext-key"
    assert removed is False
    assert path.exists()
    assert (
        memory_keychain.get_password(
            key_management.KEYRING_SERVICE, key_management.KEYRING_USERNAME
        )
        == "plaintext-key"
    )


def test_migration_removes_the_plaintext_file_when_explicitly_asked(
    tmp_path, memory_keychain
):
    """Removing it is the only way the issue's threat model actually changes.

    It stays opt-in: a legacy credential is never deleted automatically.
    """
    path = _managed_env_file(tmp_path)

    key, removed = key_management.migrate_managed_key_to_keychain(
        path, remove_plaintext=True
    )

    assert key == "plaintext-key"
    assert removed is True
    assert not path.exists()
    assert key_management.read_managed_key_from_file(path) == ""


def test_migration_rejects_a_write_the_keychain_did_not_keep(
    tmp_path, monkeypatch, memory_keychain
):
    """A backend that accepts and drops the write must not look like success.

    Without the read-back, the only remaining copy is the file the user was told
    they could stop relying on.
    """
    path = _managed_env_file(tmp_path)
    monkeypatch.setattr(memory_keychain, "set_password", lambda *args: None)

    with pytest.raises(key_management.KeychainUnavailable, match="did not return"):
        key_management.migrate_managed_key_to_keychain(path)


def test_migration_refuses_when_the_env_file_holds_no_key(tmp_path, memory_keychain):
    path = _managed_env_file(tmp_path, key=None)

    with pytest.raises(key_management.KeychainUnavailable, match="does not contain"):
        key_management.migrate_managed_key_to_keychain(path)


def test_migration_explains_itself_when_no_backend_is_available(
    tmp_path, monkeypatch, memory_keychain
):
    """The explicit command fails loudly rather than writing nothing quietly."""
    uninstall_keychain(monkeypatch)
    path = _managed_env_file(tmp_path)

    with pytest.raises(key_management.KeychainUnavailable, match="keychain"):
        key_management.migrate_managed_key_to_keychain(path)
    assert path.exists()


def test_an_explicit_path_reads_the_file_and_not_the_keychain(
    tmp_path, monkeypatch, memory_keychain
):
    """Docker hands a container a specific env file.

    Resolving that lookup through the host keychain would misreport what the
    container is about to receive.
    """
    path = _managed_env_file(tmp_path, "file-key")
    monkeypatch.setattr(key_management, "managed_key_path", lambda: path)
    memory_keychain.set_password(
        key_management.KEYRING_SERVICE, key_management.KEYRING_USERNAME, "keychain-key"
    )

    assert key_management.read_managed_key(path) == "file-key"
    assert key_management.read_managed_key() == "keychain-key"


def test_lookup_is_quiet_when_the_optional_extra_is_missing(monkeypatch):
    """Not installing the extra is supported, so it produces no problem text.

    Startup prints whatever comes back here, and the default install must not be
    nagged about a configuration it never opted into.
    """
    uninstall_keychain(monkeypatch)

    assert key_management.keychain_lookup() == ("", "")
    assert key_management.keychain_installed() is False
    assert key_management.keychain_available() is False


def test_lookup_reports_a_broken_backend(monkeypatch, memory_keychain):
    def explode(service, username):
        raise RuntimeError("collection is locked")

    monkeypatch.setattr(memory_keychain, "get_password", explode)

    key, problem = key_management.keychain_lookup()

    assert key == ""
    assert "collection is locked" in problem


def test_the_backend_probe_is_cached_until_it_is_reset(monkeypatch, memory_keychain):
    """Cached because every settings import reaches the probe.

    On Linux resolving a backend is a DBus round trip, and it used to run on
    every import, including CLI commands that never need a key.
    """
    probes = []
    monkeypatch.setattr(
        memory_keychain,
        "get_keyring",
        lambda: (probes.append(1), memory_keychain)[1],
    )
    key_management.reset_keychain_cache()

    key_management.keychain_available()
    key_management.keychain_available()
    key_management.read_keychain_key()

    assert len(probes) == 1
