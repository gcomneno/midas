from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from math import sqrt
from typing import Sequence

from .microscope import cumulative_products, MicroscopeConfig


@dataclass(frozen=True)
class ModularAnomaly:
    k: int
    p: int
    M: int
    residue: int
    count: int
    expected_mean: float
    z: float
    amplification: float


def bucket_counts(values: Sequence[int], M: int) -> Counter[int]:
    return Counter(v % M for v in values)


def scan_modular_anomalies(
    values: Sequence[int],
    config: MicroscopeConfig,
    *,
    z_threshold: float = 3.0,
    min_expected_mean: float = 5.0,
    top_n: int = 10,
) -> list[ModularAnomaly]:
    anomalies: list[ModularAnomaly] = []
    Ms = cumulative_products(config.primes)
    N = len(values)

    for k, (p, M) in enumerate(zip(config.primes, Ms), start=1):
        expected_mean = N / M if M > 0 else 0.0
        if expected_mean < min_expected_mean:
            continue

        p_uniform = 1.0 / M if M > 0 else 0.0
        sigma = sqrt(N * p_uniform * (1 - p_uniform)) if p_uniform > 0 else 0.0
        if sigma <= 0:
            continue

        counts = bucket_counts(values, M)
        for residue, count in counts.items():
            z = (count - expected_mean) / sigma
            if z < z_threshold:
                continue
            amplification = (count / expected_mean) if expected_mean > 0 else 0.0
            anomalies.append(
                ModularAnomaly(
                    k=k,
                    p=p,
                    M=M,
                    residue=residue,
                    count=count,
                    expected_mean=expected_mean,
                    z=z,
                    amplification=amplification,
                )
            )

    anomalies.sort(key=lambda a: (-a.z, -a.amplification, a.k, a.residue))
    return anomalies[:top_n]


def anomalies_to_dict(anomalies: list[ModularAnomaly]) -> list[dict[str, object]]:
    return [asdict(a) for a in anomalies]
