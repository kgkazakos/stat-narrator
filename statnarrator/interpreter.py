from __future__ import annotations

import math
from typing import Optional

from .models import EffectMagnitude, SignificanceLevel, StatInput, StatType

SIG_LABELS = {
    SignificanceLevel.HIGHLY_SIGNIFICANT: "p < .001",
    SignificanceLevel.SIGNIFICANT: "p < .01",
    SignificanceLevel.MARGINAL: "p < .05",
    SignificanceLevel.NOT_SIGNIFICANT: "non-significant",
}


def classify_significance(p: Optional[float]) -> SignificanceLevel:
    if p is None:
        return SignificanceLevel.NOT_SIGNIFICANT
    if p < 0.001:
        return SignificanceLevel.HIGHLY_SIGNIFICANT
    elif p < 0.01:
        return SignificanceLevel.SIGNIFICANT
    elif p < 0.05:
        return SignificanceLevel.MARGINAL
    else:
        return SignificanceLevel.NOT_SIGNIFICANT


def classify_r_squared(r2: float) -> EffectMagnitude:
    """Cohen (1988) benchmarks for R²."""
    if r2 < 0.02:
        return EffectMagnitude.NEGLIGIBLE
    elif r2 < 0.13:
        return EffectMagnitude.SMALL
    elif r2 < 0.26:
        return EffectMagnitude.MEDIUM
    else:
        return EffectMagnitude.LARGE


def classify_cohens_d(d: float) -> EffectMagnitude:
    """Cohen (1988) benchmarks for d."""
    d = abs(d)
    if d < 0.2:
        return EffectMagnitude.NEGLIGIBLE
    elif d < 0.5:
        return EffectMagnitude.SMALL
    elif d < 0.8:
        return EffectMagnitude.MEDIUM
    else:
        return EffectMagnitude.LARGE


def classify_correlation(r: float) -> EffectMagnitude:
    """Cohen (1988) benchmarks for r."""
    r = abs(r)
    if r < 0.10:
        return EffectMagnitude.NEGLIGIBLE
    elif r < 0.30:
        return EffectMagnitude.SMALL
    elif r < 0.50:
        return EffectMagnitude.MEDIUM
    else:
        return EffectMagnitude.LARGE


def classify_eta_squared(eta2: float) -> EffectMagnitude:
    """Cohen (1988) benchmarks for η²."""
    if eta2 < 0.01:
        return EffectMagnitude.NEGLIGIBLE
    elif eta2 < 0.06:
        return EffectMagnitude.SMALL
    elif eta2 < 0.14:
        return EffectMagnitude.MEDIUM
    else:
        return EffectMagnitude.LARGE


def classify_cramers_v(v: float) -> EffectMagnitude:
    v = abs(v)
    if v < 0.10:
        return EffectMagnitude.NEGLIGIBLE
    elif v < 0.30:
        return EffectMagnitude.SMALL
    elif v < 0.50:
        return EffectMagnitude.MEDIUM
    else:
        return EffectMagnitude.LARGE


def derive_effect_magnitude(stat: StatInput) -> EffectMagnitude:
    """Select the canonical effect size measure for the given stat type."""
    if stat.stat_type == StatType.REGRESSION:
        if stat.r_squared is not None:
            return classify_r_squared(stat.r_squared)
    elif stat.stat_type == StatType.TTEST:
        if stat.cohens_d is not None:
            return classify_cohens_d(stat.cohens_d)
        if stat.t_statistic is not None and stat.t_df is not None and stat.t_df > 0:
            d_est = 2 * stat.t_statistic / math.sqrt(stat.t_df)
            return classify_cohens_d(d_est)
    elif stat.stat_type == StatType.ANOVA:
        if stat.eta_squared is not None:
            return classify_eta_squared(stat.eta_squared)
    elif stat.stat_type == StatType.CORRELATION:
        if stat.r is not None:
            return classify_correlation(stat.r)
    elif stat.stat_type == StatType.CHI_SQUARE:
        if stat.cramers_v is not None:
            return classify_cramers_v(stat.cramers_v)
    elif stat.stat_type == StatType.FACTOR:
        if stat.total_variance_explained is not None:
            pct = stat.total_variance_explained
            if pct < 40:
                return EffectMagnitude.SMALL
            elif pct < 60:
                return EffectMagnitude.MEDIUM
            else:
                return EffectMagnitude.LARGE
    return EffectMagnitude.SMALL  # conservative default


def collect_warnings(stat: StatInput) -> list[str]:
    warnings: list[str] = []
    if stat.n < 30:
        warnings.append(
            f"Small sample size (n = {stat.n}). Interpret estimates with caution; "
            "results may not generalise."
        )
    if stat.stat_type == StatType.REGRESSION and stat.r_squared is None:
        warnings.append("R² not provided; model fit cannot be assessed.")
    if stat.p_value is not None and 0.04 <= stat.p_value <= 0.06:
        warnings.append(
            f"p-value ({stat.p_value:.3f}) is close to the .05 threshold. "
            "Report the exact value; avoid binary significant/non-significant framing."
        )
    if stat.stat_type == StatType.TTEST and stat.cohens_d is None:
        warnings.append(
            "Cohen's d not provided. Effect size is a required complement to p-values."
        )
    if stat.stat_type == StatType.ANOVA and stat.eta_squared is None:
        warnings.append("η² not provided. Report effect size alongside the F-statistic.")
    if stat.stat_type == StatType.CHI_SQUARE and stat.cramers_v is None:
        warnings.append("Cramér's V not provided. Report effect size for χ² tests.")
    return warnings
