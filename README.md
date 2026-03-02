# MIDAS — Modular Integer Dataset Analysis System
![CI](../../actions/workflows/ci.yml/badge.svg)

Deterministic, explainable, minimal analysis of **integer datasets** to detect **non-random modular structure**.
- Not ML
- Not prediction
- Discrete multi-level modular analysis

## Install (dev)
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Usage

Analyze a synthetic dataset:
midas analyze --synth weak_id --N 976 --seed 123456 --baseline-random

Analyze an input file (one integer per line):
midas analyze --input data.txt --baseline-random

## Notes
Output is intentionally stable and tested with golden tests.

Baseline uses deterministic seeds derived from --seed.
