from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from ..models import RepositoryMap


def commit_sha(repository: RepositoryMap) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository.root, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def cache_path(repository: RepositoryMap, identity: str, cache_dir: Path) -> Path:
    key = f"{commit_sha(repository)}:{identity}"
    return cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"


def cached_call(
    repository: RepositoryMap,
    identity: str,
    cache_dir: Path,
    call: Callable[[], Any],
) -> tuple[Any, bool, Path]:
    path = cache_path(repository, identity, cache_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), True, path
    value = call()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return value, False, path

