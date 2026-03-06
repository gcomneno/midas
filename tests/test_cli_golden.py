import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_cli(args):
    cmd = [sys.executable, "-m", "midas", *args]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout

def test_analyze_weak_id_golden():
    expected = (ROOT / "tests/data/expected/analyze_weak_id.txt").read_text(encoding="utf-8")
    out = run_cli([
        "analyze",
        "--synth", "weak_id",
        "--N", "976",
        "--seed", "123456",
        "--baseline-random",
    ])
    assert out == expected

def test_analyze_uniform_golden():
    expected = (ROOT / "tests/data/expected/analyze_uniform.txt").read_text(encoding="utf-8")
    out = run_cli([
        "analyze",
        "--synth", "uniform",
        "--N", "976",
        "--seed", "123456",
        "--baseline-random",
    ])
    assert out == expected

def test_analyze_weak_id_scan_golden():
    expected = (ROOT / "tests/data/expected/analyze_weak_id_scan.txt").read_text(encoding="utf-8")
    out = run_cli([
        "analyze",
        "--synth", "weak_id",
        "--N", "976",
        "--seed", "123456",
        "--baseline-random",
        "--scan-anomalies",
    ])
    assert out == expected
