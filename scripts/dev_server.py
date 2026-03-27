from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import uvicorn


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    load_dotenv()

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8005"))

    # On Windows, uvicorn reload uses subprocess watchers and can be noisy/fragile.
    # Keep reload off by default and enable only when explicitly requested.
    reload_enabled = _env_bool("APP_RELOAD", False)
    if os.name == "nt" and reload_enabled:
        os.environ.setdefault("WATCHFILES_FORCE_POLLING", "true")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        reload_dirs=["app"] if reload_enabled else None,
    )


if __name__ == "__main__":
    main()
