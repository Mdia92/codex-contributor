from __future__ import annotations

from pathlib import Path


def load_local_environment() -> None:
    """Load the ignored workspace .env without overriding explicit process vars."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env", override=False)

