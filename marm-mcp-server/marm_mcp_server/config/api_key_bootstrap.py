import os
import sys
from pathlib import Path

from ..services import key_management
from ..services.key_management import _protect_key_file
from ..utils.security import generate_api_key

_MARM_ENV_PATH = Path.home() / ".marm" / ".env"


def _file_link(path: Path) -> str:
    try:
        uri = path.as_uri()
        return f"\033]8;;{uri}\033\\{path}\033]8;;\033\\"
    except Exception:
        return str(path)


def _load_key_from_file() -> str:
    """Read MARM_API_KEY from ~/.marm/.env if present.

    Delegates to `key_management` so the server and the CLI cannot drift apart on
    how the file is parsed; that duplication was the reason a keychain-stored key
    was invisible to `marm-memory key reveal`.
    """
    return key_management.read_managed_key_from_file(_MARM_ENV_PATH)


def _load_key_from_keychain() -> str:
    """Read MARM_API_KEY from the OS keychain, if the user put one there.

    Reads only. Writing happens through the explicit `marm-memory key init
    --keychain` command instead, because on Linux a `set_password` can raise an
    unlock prompt and block the module import that reaches this line.

    A keychain that is installed but broken reports why on stderr, so falling
    through to the plaintext file is never silent. A keychain that was never
    installed stays quiet: that is a supported configuration, not a fault.
    """
    key, problem = key_management.keychain_lookup()
    if problem:
        print(
            f"MARM: cannot use the OS keychain ({problem}); "
            f"falling back to {_MARM_ENV_PATH}.",
            file=sys.stderr,
        )
    return key


def resolve_marm_api_key(server_host: str) -> str:
    """Resolve MARM_API_KEY: env var, then OS keychain, then ~/.marm/.env, then
    auto-generate and persist one when server_host is 0.0.0.0 and no key was
    found anywhere.

    The whole chain stays behind the 0.0.0.0 gate. The default bind is
    127.0.0.1, where no credential store is consulted and no key is generated.
    """
    marm_api_key = os.environ.get("MARM_API_KEY", "")

    if server_host == "0.0.0.0" and not marm_api_key:
        marm_api_key = _load_key_from_keychain() or _load_key_from_file()

    is_generate_key_cmd = "--generate-key" in sys.argv or sys.argv[1:3] == [
        "key",
        "generate",
    ]

    if server_host == "0.0.0.0" and not marm_api_key and not is_generate_key_cmd:
        marm_api_key = generate_api_key()
        key_persisted = False
        try:
            _MARM_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
            _MARM_ENV_PATH.write_text(f"MARM_API_KEY={marm_api_key}\n")
            try:
                key_protected = _protect_key_file(_MARM_ENV_PATH)
            except Exception:
                key_protected = False
            if key_protected:
                key_persisted = True
            else:
                try:
                    _MARM_ENV_PATH.unlink(missing_ok=True)
                except OSError as e:
                    print(
                        "WARNING: API key file protection failed and the insecure "
                        f"file could not be removed: {_MARM_ENV_PATH}: {e}. Remove "
                        "it immediately. The generated API key remains active in "
                        "memory for this process only; do not rely on the insecure "
                        "file surviving a restart. Set MARM_API_KEY explicitly in "
                        "the environment.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "WARNING: API key file protection failed. The API key is being "
                        "kept in memory only and will not survive a restart. Set "
                        "MARM_API_KEY explicitly in the environment.",
                        file=sys.stderr,
                    )
        except Exception as e:
            print(f"WARNING: Could not save API key to {_MARM_ENV_PATH}: {e}")

        print()
        print(
            "MARM: SERVER_HOST=0.0.0.0 detected — API key auto-generated (first start)."
        )
        if key_persisted:
            print(f"Saved to: {_file_link(_MARM_ENV_PATH)}")
            print()
            print(
                "Add this to your MCP client (replace YOUR_KEY with the key from the file above):"
            )
            print(
                '  claude mcp add --transport http marm-memory http://localhost:8001/mcp --header "Authorization: Bearer YOUR_KEY"'
            )
            print()
            print("On subsequent starts the key loads silently from the file above.")
            if key_management.keychain_installed():
                print()
                print(
                    "To keep the key out of a plaintext file, move it into your OS "
                    "keychain with: marm-memory key init --keychain"
                )
        else:
            print("Set MARM_API_KEY explicitly and restart to connect.")
        print()

    return marm_api_key
