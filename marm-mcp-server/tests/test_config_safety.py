import importlib
import os
import stat
import sys
from unittest import mock

import pytest


def _reload_settings_with_env(env: dict[str, str]):
    """Reload settings under a temporary env patch, then restore the original module."""
    module_name = "marm_mcp_server.config.settings"
    original = sys.modules.pop(module_name, None)

    try:
        with mock.patch.dict(os.environ, env, clear=False):
            settings_mod = importlib.import_module(module_name)
            return importlib.reload(settings_mod)
    finally:
        sys.modules.pop(module_name, None)
        if original is not None:
            sys.modules[module_name] = original


def test_rate_limit_rpm_zero_disables_limiting():
    """MARM_RATE_LIMIT_RPM=0 should be preserved (0 = disable rate limiting)."""
    settings_mod = _reload_settings_with_env({"MARM_RATE_LIMIT_RPM": "0"})
    assert settings_mod.MARM_RATE_LIMIT_RPM == 0


def test_rate_limit_rpm_negative_clamped_to_zero():
    """Negative MARM_RATE_LIMIT_RPM should be clamped to 0 with a warning."""
    settings_mod = _reload_settings_with_env({"MARM_RATE_LIMIT_RPM": "-5"})
    assert settings_mod.MARM_RATE_LIMIT_RPM == 0


def test_malformed_int_env_falls_back_to_default():
    """Malformed int env var should fall back to default, not crash."""
    settings_mod = _reload_settings_with_env({"COMPACTION_TRIGGER_COUNT": "abc"})
    assert settings_mod.COMPACTION_TRIGGER_COUNT == 5


def test_malformed_float_env_falls_back_to_default():
    """Malformed float env var should fall back to default, not crash."""
    settings_mod = _reload_settings_with_env(
        {"CONSOLIDATION_THRESHOLD": "not_a_number"}
    )
    assert settings_mod.CONSOLIDATION_THRESHOLD == 0.92


def test_consolidation_threshold_clamped_to_unit_range():
    """CONSOLIDATION_THRESHOLD > 1.0 should be clamped to [0, 1]."""
    settings_mod = _reload_settings_with_env({"CONSOLIDATION_THRESHOLD": "1.5"})
    assert settings_mod.CONSOLIDATION_THRESHOLD == 1.0


def test_resolve_marm_api_key_persists_a_generated_key_across_starts(
    monkeypatch, tmp_path
):
    """A real generated key must round-trip through resolve_marm_api_key's
    persist-then-reload path exactly: the first 0.0.0.0 start with no key
    anywhere generates and saves one, and every start after that must load
    the same key back rather than generating a new one each time."""
    from marm_mcp_server.config import api_key_bootstrap

    env_path = tmp_path / ".marm" / ".env"
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    first_start = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")
    assert first_start
    assert env_path.read_text() == f"MARM_API_KEY={first_start}\n"
    if os.name != "nt":
        assert stat.S_IMODE(env_path.stat().st_mode) & 0o077 == 0

    second_start = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")
    assert second_start == first_start


def test_resolve_marm_api_key_removes_file_when_protection_fails(
    monkeypatch, tmp_path, capsys
):
    from marm_mcp_server.config import api_key_bootstrap

    env_path = tmp_path / ".marm" / ".env"
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.setattr(api_key_bootstrap, "_protect_key_file", lambda path: False)
    monkeypatch.delenv("MARM_API_KEY", raising=False)
    printed = []
    real_print = print

    def record_print(*args, **kwargs):
        printed.append(args)
        real_print(*args, **kwargs)

    monkeypatch.setattr("builtins.print", record_print)

    generated_key = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")

    assert generated_key
    assert not env_path.exists()
    output = capsys.readouterr()
    warning = output.err
    assert "kept in memory only" in warning
    assert "will not survive a restart" in warning
    assert "Set MARM_API_KEY explicitly in the environment" in warning
    assert ("Set MARM_API_KEY explicitly and restart to connect.",) in printed


def test_resolve_marm_api_key_removes_file_when_protection_raises(
    monkeypatch, tmp_path, capsys
):
    from marm_mcp_server.config import api_key_bootstrap

    env_path = tmp_path / ".marm" / ".env"
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)

    def fail_protection(path):
        raise RuntimeError("ctypes blew up")

    monkeypatch.setattr(api_key_bootstrap, "_protect_key_file", fail_protection)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    generated_key = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")

    assert generated_key
    assert not env_path.exists()
    warning = capsys.readouterr().err
    assert "kept in memory only" in warning
    assert "will not survive a restart" in warning
    assert "Set MARM_API_KEY explicitly in the environment" in warning


def test_resolve_marm_api_key_warns_when_insecure_file_cannot_be_removed(
    monkeypatch, tmp_path, capsys
):
    from marm_mcp_server.config import api_key_bootstrap

    env_path = tmp_path / ".marm" / ".env"
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.setattr(api_key_bootstrap, "_protect_key_file", lambda path: False)

    def fail_unlink(self, missing_ok=False):
        raise OSError("denied")

    monkeypatch.setattr(type(env_path), "unlink", fail_unlink)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    generated_key = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")

    assert generated_key
    assert env_path.exists()
    warning = capsys.readouterr().err
    assert "insecure file could not be removed" in warning
    assert str(env_path) in warning
    assert "memory for this process only" in warning
    assert "Set MARM_API_KEY explicitly in the environment" in warning


# --- OS keychain resolution (issue #37) ---------------------------------------
#
# `memory_keychain` in conftest.py is autouse and hands every test an empty
# in-memory backend, so none of these can reach the developer's real credential
# store. Each assertion below is about the resolution order the issue pins down:
# env -> keychain -> .env -> generated.


def _env_file_with_key(tmp_path, key: str):
    env_path = tmp_path / ".marm" / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(f"MARM_API_KEY={key}\n")
    return env_path


def test_env_var_still_overrides_the_keychain(monkeypatch, tmp_path, memory_keychain):
    """An explicit MARM_API_KEY has to win, or Docker env injection breaks."""
    from marm_mcp_server.config import api_key_bootstrap
    from marm_mcp_server.services import key_management

    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.setenv("MARM_API_KEY", "from-the-environment")
    memory_keychain.set_password(
        key_management.KEYRING_SERVICE,
        key_management.KEYRING_USERNAME,
        "from-the-keychain",
    )

    assert api_key_bootstrap.resolve_marm_api_key("0.0.0.0") == "from-the-environment"


def test_keychain_is_preferred_over_the_env_file(
    monkeypatch, tmp_path, memory_keychain
):
    from marm_mcp_server.config import api_key_bootstrap
    from marm_mcp_server.services import key_management

    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)
    memory_keychain.set_password(
        key_management.KEYRING_SERVICE,
        key_management.KEYRING_USERNAME,
        "from-the-keychain",
    )

    assert api_key_bootstrap.resolve_marm_api_key("0.0.0.0") == "from-the-keychain"


def test_an_empty_keychain_falls_through_to_the_env_file(
    monkeypatch, tmp_path, memory_keychain
):
    from marm_mcp_server.config import api_key_bootstrap

    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    assert memory_keychain.values == {}
    assert api_key_bootstrap.resolve_marm_api_key("0.0.0.0") == "from-the-file"


def test_resolve_does_not_touch_the_keychain_for_a_non_public_bind(
    monkeypatch, tmp_path, memory_keychain
):
    """127.0.0.1 is the default, and it must stay inert.

    No credential store, no generated key, no file. Ungating the lookup is the
    one way this change could start minting credentials for every localhost user.
    """
    from marm_mcp_server.config import api_key_bootstrap
    from marm_mcp_server.services import key_management

    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)
    monkeypatch.setattr(
        key_management,
        "keychain_lookup",
        lambda: pytest.fail("a 127.0.0.1 bind must not consult the OS keychain"),
    )

    assert api_key_bootstrap.resolve_marm_api_key("127.0.0.1") == ""


def test_startup_never_writes_a_generated_key_to_the_keychain(
    monkeypatch, tmp_path, memory_keychain
):
    """Startup persists to .env only.

    A keychain write at import time is a DBus `set_password` on Linux that can
    raise an unlock prompt and block the import that calls it, and in tests it
    is what put a real credential in the developer's store. The keychain is
    written by `marm-memory key init --keychain` and nowhere else.
    """
    from marm_mcp_server.config import api_key_bootstrap

    env_path = tmp_path / ".marm" / ".env"
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)
    writes = []
    monkeypatch.setattr(
        memory_keychain,
        "set_password",
        lambda service, username, password: writes.append((service, username)),
    )

    generated = api_key_bootstrap.resolve_marm_api_key("0.0.0.0")

    assert generated
    assert env_path.read_text() == f"MARM_API_KEY={generated}\n"
    assert writes == []


def test_a_broken_keychain_is_reported_rather_than_silently_skipped(
    monkeypatch, tmp_path, capsys, memory_keychain
):
    """A keychain that is installed but unusable must say why it was skipped.

    Falling through to the plaintext file is the right outcome; doing it without
    a word is not, because it degrades exactly the protection the keychain was
    meant to provide.
    """
    from marm_mcp_server.config import api_key_bootstrap

    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    def explode(service, username):
        raise RuntimeError("collection is locked")

    monkeypatch.setattr(memory_keychain, "get_password", explode)

    assert api_key_bootstrap.resolve_marm_api_key("0.0.0.0") == "from-the-file"
    warning = capsys.readouterr().err
    assert "cannot use the OS keychain" in warning
    assert "collection is locked" in warning


def test_an_absent_keychain_extra_stays_quiet(monkeypatch, tmp_path, capsys):
    """Not installing the optional extra is supported, so it must not nag.

    Warning on every start for the default `pip install marm-mcp-server` would
    be noise about a configuration the user never opted into.
    """
    from conftest import uninstall_keychain

    from marm_mcp_server.config import api_key_bootstrap

    uninstall_keychain(monkeypatch)
    env_path = _env_file_with_key(tmp_path, "from-the-file")
    monkeypatch.setattr(api_key_bootstrap, "_MARM_ENV_PATH", env_path)
    monkeypatch.delenv("MARM_API_KEY", raising=False)

    assert api_key_bootstrap.resolve_marm_api_key("0.0.0.0") == "from-the-file"
    captured = capsys.readouterr()
    assert "keychain" not in captured.err
    assert "keychain" not in captured.out


def test_a_keychain_stored_key_matches_what_the_cli_reads(
    monkeypatch, tmp_path, memory_keychain
):
    """The server and the CLI have to agree, which is what one reader buys.

    `key_management.read_managed_key` backs `key reveal`, the Console client and
    the Docker paths. Previously it read `.env` only, so a keychain-stored key
    was invisible to every one of them.
    """
    from marm_mcp_server.services import key_management

    monkeypatch.setattr(
        key_management, "managed_key_path", lambda: tmp_path / ".marm" / ".env"
    )
    memory_keychain.set_password(
        key_management.KEYRING_SERVICE, key_management.KEYRING_USERNAME, "keychain-key"
    )

    assert key_management.read_managed_key() == "keychain-key"
