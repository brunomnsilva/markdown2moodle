"""Exit-code tests for md2moodle: usage and conversion failures must exit nonzero."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "md2moodle.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_too_many_args_exits_nonzero():
    proc = run_cli("a", "b", "c", "d")
    assert proc.returncode == 2
    assert "Usage" in proc.stdout


def test_no_args_exits_nonzero_with_usage():
    proc = run_cli()
    assert proc.returncode == 2
    assert "Usage" in proc.stdout
    assert "Traceback" not in (proc.stdout + proc.stderr)


def test_missing_input_file_exits_nonzero():
    proc = run_cli("does-not-exist.md")
    assert proc.returncode == 1
    assert "does-not-exist.md" in (proc.stdout + proc.stderr)
    assert "Traceback" not in (proc.stdout + proc.stderr)
