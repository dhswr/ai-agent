"""测试执行器 —— 通过子进程运行 pytest 并解析结果."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestResult:
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    summary: list[str] = field(default_factory=list)


def run_pytest(test_file: Path | str) -> TestResult:
    """运行单个测试文件并解析结果."""
    test_file = Path(test_file)
    if not test_file.exists():
        return TestResult(exit_code=-1, stderr=f"File not found: {test_file}")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=test_file.parent,
        timeout=120,
    )
    return _parse_pytest_output(result)


def run_pytest_dir(test_dir: Path | str) -> TestResult:
    """运行目录下所有测试."""
    test_dir = Path(test_dir)
    if not test_dir.exists():
        return TestResult(exit_code=-1, stderr=f"Directory not found: {test_dir}")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return _parse_pytest_output(result)


def _parse_pytest_output(result: subprocess.CompletedProcess[str]) -> TestResult:
    tr = TestResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    # 解析 pytest 摘要行
    for line in result.stdout.splitlines():
        if "passed" in line or "failed" in line or "error" in line:
            tr.summary.append(line)
            import re

            passed_m = re.search(r"(\d+)\s+passed", line)
            failed_m = re.search(r"(\d+)\s+failed", line)
            errors_m = re.search(r"(\d+)\s+errors?", line)

            if passed_m:
                tr.passed = int(passed_m.group(1))
            if failed_m:
                tr.failed = int(failed_m.group(1))
            if errors_m:
                tr.errors = int(errors_m.group(1))

    return tr
