# MIDAS — Modular Integer Dataset Analysis System
![CI](../../actions/workflows/ci.yml/badge.svg)

A deterministic modular **microscope for integer datasets**.

MIDAS analyzes integer sequences to detect **non‑random modular structure** using a fully deterministic,
explainable method based on modular arithmetic.

MIDAS deliberately avoids:
- Machine Learning
- Prediction models
- Continuous statistical fitting

Instead, it performs **multi‑level modular analysis** on integer datasets.

---

# Concept

MIDAS applies a sequence of "modular lenses" using small primes:

primes = [3, 5, 7, 11, 13, 17]

For each level `k`:

M_k = product(primes[:k])

The dataset is bucketed modulo `M_k` and MIDAS measures:
- bucket coverage
- largest bucket
- expected mean occupancy
- amplification factor
- z‑score (when statistically valid)

This produces a **modular fingerprint** describing the structure of the dataset.

---

# Structural Fingerprint

MIDAS samples random pairs of values and computes:

k* = first level where two values diverge modulo M_k

The resulting distribution forms a **fingerprint of structural depth**.

The fingerprint is compared against a deterministic Monte‑Carlo baseline,
producing:
- anomaly score (L1 distance)
- noise floor
- signal‑to‑noise ratio (SNR)

---

# Verdict

Datasets are classified using SNR:

snr < 2        → random_like
2 ≤ snr < 5    → weak_structure
snr ≥ 5        → structured

Additional notes may appear:

note: borderline_signal

This occurs when: 2 ≤ snr < 3
indicating the signal is **near the decision boundary**.

Strong biases may also trigger:
note: strong_modular_bias_detected
note: extreme_modular_bias_detected

---

# Modular Anomaly Scanner

MIDAS can localize **where the modular bias occurs**.

Enable it with:
midas analyze --scan-anomalies ...

Example:
midas analyze --synth weak_id --N 976 --baseline-random --scan-anomalies

Example output:
-- MODULAR ANOMALY SCANNER --
k= 2  p= 5  M=15        residue=0       count=255     expected=65.07
k= 2  p= 5  M=15        residue=5       count=255     expected=65.07
k= 2  p= 5  M=15        residue=10      count=236     expected=65.07

Meaning:
The dataset concentrates around residues {0,5,10} modulo 15.

Scanner output includes:
- level k
- prime p
- modulus M
- anomalous residue
- observed vs expected counts
- z‑score
- amplification

This helps explain **why MIDAS detected structure**.

---

# Installation (dev)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Requirements:
- Python ≥ 3.10

---

# Try it in 60 seconds

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
midas analyze --synth weak_id --N 976 --seed 123456 --baseline-random
```

Expected:
- prints a modular fingerprint
- returns a verdict: `random_like` / `weak_structure` / `structured`

---

# Usage

Analyze a synthetic dataset:
```bash
midas analyze --synth weak_id --N 976 --seed 123456 --baseline-random
```

Analyze integers from a file:
```bash
midas analyze --input data.txt --baseline-random
```

Run anomaly scanner:
```bash
midas analyze --input data.txt --baseline-random --scan-anomalies
```

---

# Testing

MIDAS uses **golden tests** to guarantee deterministic CLI output.

Run tests with:
```bash
pytest
```

Golden tests ensure:
- stable output
- reproducible diagnostics
- regression protection

---

# Design Philosophy

MIDAS follows strict principles:
- deterministic
- minimal
- explainable
- stable before feature growth

The goal is **structural diagnostics**, not prediction.

---

# Notes
Performance pass completed.
Safe micro-optimizations retained.
Experimental residue-cache approach rejected after regression.
Current pure-Python design considered near practical plateau.

---

# License
MIT
