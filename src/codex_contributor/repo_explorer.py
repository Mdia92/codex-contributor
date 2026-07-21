from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from .models import RepositoryMap


IGNORED = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
EXTENSIONS = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust", ".java": "Java"}


def detect_test_command(root: Path) -> list[str] | None:
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or (root / "tests").is_dir():
        return ["python", "-m", "pytest"]
    if (root / "package.json").exists():
        return ["npm", "test", "--", "--runInBand"]
    if (root / "go.mod").exists():
        return ["go", "test", "./..."]
    if (root / "Cargo.toml").exists():
        return ["cargo", "test"]
    return None


def _python_symbols(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, OSError):
        return []
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def map_repository(root: Path, max_files: int = 5000) -> RepositoryMap:
    root = root.resolve()
    files: list[str] = []
    languages: Counter[str] = Counter()
    symbols: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if len(files) >= max_files:
            break
        if not path.is_file() or any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix()
        files.append(relative)
        language = EXTENSIONS.get(path.suffix.lower())
        if language:
            languages[language] += 1
        if path.suffix.lower() == ".py":
            found = _python_symbols(path)
            if found:
                symbols[relative] = found
    return RepositoryMap(
        root=str(root), files=sorted(files), languages=dict(languages),
        test_command=detect_test_command(root), symbols=symbols,
    )

