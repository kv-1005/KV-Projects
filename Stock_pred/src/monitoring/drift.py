from __future__ import annotations

import numpy as np
import pandas as pd


def population_stability_index(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    # Bin both distributions using expected quantiles
    q = np.linspace(0, 1, bins + 1)
    cuts = expected.quantile(q).values
    cuts[0] = -np.inf
    cuts[-1] = np.inf

    e_counts, _ = np.histogram(expected.values, bins=cuts)
    a_counts, _ = np.histogram(actual.values, bins=cuts)

    e_perc = e_counts / (e_counts.sum() + 1e-12)
    a_perc = a_counts / (a_counts.sum() + 1e-12)

    psi = np.sum((a_perc - e_perc) * np.log((a_perc + 1e-12) / (e_perc + 1e-12)))
    return float(psi)


