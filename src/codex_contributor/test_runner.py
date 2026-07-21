from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .repo_explorer import detect_test_command


@dataclass(frozen=True)
class TestResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def run_tests(root: Path, command: list[str] | None = None, timeout: int = 300) -> TestResult:
    selected = command or detect_test_command(root)
    if not selected:
        raise RuntimeError("No supported test runner detected")
    result = subprocess.run(selected, cwd=root, capture_output=True, text=True, timeout=timeout)
    return TestResult(tuple(selected), result.returncode, result.stdout, result.stderr)

