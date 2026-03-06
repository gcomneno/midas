from __future__ import annotations

import argparse
import json
from pathlib import Path
from random import Random
from typing import Any

from midas.microscope import MicroscopeConfig, report_to_dict, run_microscope
from midas.scanner import scan_modular_anomalies, anomalies_to_dict


def _get_dict_list(d: dict[str, Any], key: str) -> list[dict[str, Any]]:
    x = d.get(key)
    if x is None:
        return []
    if isinstance(x, list):
        return [e for e in x if isinstance(e, dict)]
    return []


def _get_str_list(d: dict[str, Any], key: str) -> list[str]:
    x = d.get(key)
    if x is None:
        return []
    if isinstance(x, list):
        return [s for s in x if isinstance(s, str)]
    return []


def parse_lens(s: str) -> list[int]:
    parts = [p.strip() for p in s.split(",") if p.strip()]
    primes = [int(x) for x in parts]
    if not primes:
        raise ValueError("empty lens")
    if any(p <= 1 for p in primes):
        raise ValueError("lens must contain integers > 1")
    if len(set(primes)) != len(primes):
        raise ValueError("lens must not contain duplicates")
    return primes


def first_primes(n: int) -> list[int]:
    """Genera i primi n numeri primi (semplice). OK per n=10000."""
    primes: list[int] = []
    x = 2
    while len(primes) < n:
        is_prime = True
        d = 2
        while d * d <= x:
            if x % d == 0:
                is_prime = False
                break
            d += 1 if d == 2 else 2
        if is_prime:
            primes.append(x)
        x += 1 if x == 2 else 2
    return primes


def format_fp(fp: dict[str, float], K: int) -> str:
    return "[" + ", ".join(f"{k}:{fp.get(str(k), 0.0):.3f}" for k in range(0, K + 1)) + "]"


def read_int_lines(path: Path) -> list[int]:
    values: list[int] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        try:
            values.append(int(line))
        except ValueError as e:
            raise ValueError(f"{path}:{lineno}: not an int: {raw!r}") from e
    return values


def read_jsonl_field(path: Path, field: str) -> list[int]:
    values: list[int] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{lineno}: invalid json: {e}") from e
        if field not in obj:
            raise ValueError(f"{path}:{lineno}: missing field {field!r}")
        try:
            values.append(int(obj[field]))
        except (TypeError, ValueError) as e:
            raise ValueError(f"{path}:{lineno}: field {field!r} not int-like: {obj[field]!r}") from e
    return values


def synth_values(kind: str, *, N: int, lo: int, hi: int, seed: int) -> list[int]:
    rng = Random(seed)
    if kind == "uniform":
        return [rng.randrange(lo, hi) for _ in range(N)]
    if kind == "step1000":
        return [i * 1000 for i in range(N)]
    if kind == "powers2":
        return [pow(2, i, hi) for i in range(N)]
    if kind == "timestampish":
        base = 1_700_000_000
        step = 37
        jitter = 2000
        out = []
        t = base
        for _ in range(N):
            t += step
            out.append((t + rng.randrange(-jitter, jitter + 1)) % hi)
        return out
    if kind == "weak_id":
        out = []
        for _ in range(N):
            x = rng.randrange(lo, hi // 1000) * 1000
            tail = 0 if rng.random() < 0.45 else (500 if rng.random() < 0.5 else rng.randrange(1000))
            out.append(x + tail)
        return out
    raise ValueError(f"unknown synth kind: {kind!r}")


def cmd_analyze(args: argparse.Namespace) -> int:
    primes = parse_lens(args.lens)
    K = len(primes)

    seed = args.seed
    N = args.N
    lo, hi = args.lo, args.hi
    rng = Random(seed)

    if args.input is not None:
        if args.input_format == "lines":
            values = read_int_lines(args.input)
        else:
            values = read_jsonl_field(args.input, args.field)

        mode_label = f"file:{args.input.name}"

        if len(values) >= N:
            values = values[:N]
        else:
            N = len(values)
    elif args.synth is not None:
        values = synth_values(args.synth, N=N, lo=lo, hi=hi, seed=seed)
        mode_label = f"synth:{args.synth}"
    else:
        if args.mode == "R":
            values = [rng.randrange(lo, hi) for _ in range(N)]
            mode_label = "random"
        elif args.mode == "A":
            values = [i * 1000 for i in range(N)]
            mode_label = "multiples_of_1000"
        elif args.mode == "B":
            values = [pow(2, i, hi) for i in range(N)]
            mode_label = "powers_of_2_mod_hi"
        elif args.mode == "C":
            values = first_primes(N)
            mode_label = "first_primes"
        else:
            raise ValueError(f"unknown mode={args.mode!r}")

    if N < 100:
        print("WARNING: dataset very small; statistical reliability low")

    config = MicroscopeConfig(
        primes=primes,
        N=N,
        lo=lo,
        hi=hi,
        pairs=args.pairs,
        seed=seed,
    )

    report = run_microscope(values, mode=mode_label, config=config, baseline_random=args.baseline_random)
    anomalies = scan_modular_anomalies(values, config, top_n=args.scan_limit) if args.scan_anomalies else []

    print("\n=== MIDAS Microscope Report ===")
    print(f"mode={report.mode}  seed={seed}  N={N}  range=[{lo},{hi})  K={K}")
    print(f"lens primes={primes}")

    print("\n-- Bucket occupancy by level (mod M_k) --")
    for s in report.levels:
        print(
            f"k={s.k:2d}  p={s.p:2d}  M={s.M:<8d}  "
            f"non_empty={s.non_empty:<6d}  coverage={s.coverage:0.4f}  "
            f"max_bucket={s.max_bucket:<3d}  top3={s.top3}"
        )

    print("\n-- Sampled k* depth distribution (pairs sampled) --")
    print(f"pairs={args.pairs}")
    total = sum(report.kstar_counts.values()) or 1
    for k in range(0, K + 1):
        c = report.kstar_counts.get(str(k), 0)
        print(f"k*={k:2d}  count={c:<6d}  frac={c/total:.4f}")

    print("\n-- Fingerprint (k* fractions) --")
    print(format_fp(report.kstar_fractions, K))

    if report.baseline_random_0 is not None:
        print("\n-- Baseline comparison (vs random) --")
        print(f"baseline_fingerprint={format_fp(report.baseline_random_0, K)}")

        delta_parts = []
        for k in range(0, K + 1):
            d = report.kstar_fractions.get(str(k), 0.0) - report.baseline_random_0.get(str(k), 0.0)
            delta_parts.append(f"{k}:{d:+.3f}")
        print("delta=[" + ", ".join(delta_parts) + "]")

        print(f"anomaly_score_L1={report.anomaly_score_L1:.4f}")
        print(f"noise_floor_L1={report.noise_floor_L1:.4f}")
        print(f"signal_to_noise={report.signal_to_noise:.2f}")

    if report.verdict is not None:
        v = report.verdict
        print("\n-- VERDICT --")
        print(f"verdict={v.get('verdict')}")
        snr = v.get("snr")
        if isinstance(snr, (int, float)):
            print(f"snr={snr:.6f}")
        else:
            print(f"snr={snr}")
        hs = _get_dict_list(v, "hotspots")
        if hs:
            hs_str = ", ".join(
                f"k={h.get('k')} delta={float(h.get('delta', 0.0)):+.3f}"
                for h in hs
            )
            print(f"hotspots={hs_str}")
        for note in _get_str_list(v, "notes"):
            print(f"note: {note}")
        for hyp in _get_str_list(v, "hypothesis"):
            print(f"hypothesis: {hyp}")
        for ev in _get_str_list(v, "evidence"):
            print(f"evidence: {ev}")

    if args.scan_anomalies:
        print("\n-- MODULAR ANOMALY SCANNER --")
        if not anomalies:
            print("no_significant_bucket_anomalies")
        else:
            for a in anomalies:
                print(
                    f"k={a.k:2d}  p={a.p:2d}  M={a.M:<8d}  residue={a.residue:<6d}  "
                    f"count={a.count:<6d}  expected={a.expected_mean:0.2f}  "
                    f"z={a.z:0.2f}  amplification={a.amplification:0.2f}"
                )

    if args.json is not None:
        payload = report_to_dict(report)
        if args.scan_anomalies:
            payload["modular_anomalies"] = anomalies_to_dict(anomalies)
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\n(JSON scritto in: {args.json})")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="midas", description="MIDAS — Modular Integer Dataset Analysis System")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="Analyze a dataset (file or synthetic)")
    a.add_argument("--seed", type=int, default=123456)
    a.add_argument("--N", type=int, default=10_000)
    a.add_argument("--lo", type=int, default=0)
    a.add_argument("--hi", type=int, default=10**9)
    a.add_argument("--pairs", type=int, default=50_000)

    a.add_argument(
        "--mode",
        choices=["R", "A", "B", "C"],
        default="R",
        help="R=random, A=multiples of 1000, B=powers of 2 (mod hi), C=first primes",
    )

    a.add_argument(
        "--lens",
        default="3,5,7,11,13,17",
        help="Comma-separated primes lens, e.g. 3,5,7,11,13,17",
    )
    a.add_argument(
        "--baseline-random",
        action="store_true",
        help="Compute random baselines and show anomaly/noise/SNR",
    )
    a.add_argument(
        "--scan-anomalies",
        action="store_true",
        help="Scan bucket occupancies and report significant modular anomalies",
    )
    a.add_argument(
        "--scan-limit",
        type=int,
        default=10,
        help="Maximum number of modular anomalies to print when --scan-anomalies is enabled",
    )
    a.add_argument("--input", type=Path, default=None, help="Read integers from a file")
    a.add_argument(
        "--input-format",
        choices=["lines", "jsonl"],
        default="lines",
        help="lines: one integer per line; jsonl: read JSON Lines and extract a numeric field",
    )
    a.add_argument(
        "--synth",
        choices=["uniform", "step1000", "powers2", "timestampish", "weak_id"],
        default=None,
        help="Generate a synthetic dataset instead of --mode/--input",
    )
    a.add_argument("--field", default="N", help="JSONL field name to extract when --input-format=jsonl")
    a.add_argument("--json", type=Path, default=None, help="Write JSON report to this file")

    a.set_defaults(func=cmd_analyze)
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return args.func(args)
