from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AnovaGroup, Coefficient, Factor, FactorLoading, StatInput, StatType


def _load_raw(source: "str | Path") -> dict[str, Any]:
    """Accept a file path or a raw JSON string and return a dict."""
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text())
    # Fall back to treating source as a JSON string
    return json.loads(str(source))


def parse_stat_input(raw: dict[str, Any]) -> StatInput:
    """Parse a raw dict into a :class:`StatInput`."""
    stat_type_str = str(raw.get("stat_type", "unknown")).lower()
    try:
        stat_type = StatType(stat_type_str)
    except ValueError:
        stat_type = StatType.UNKNOWN

    coefficients = [
        Coefficient(
            name=str(c["name"]),
            b=float(c["b"]),
            se=c.get("se"),
            t=c.get("t"),
            p=c.get("p"),
            ci_lower=c.get("ci_lower"),
            ci_upper=c.get("ci_upper"),
            beta=c.get("beta"),
        )
        for c in raw.get("coefficients", [])
    ]

    groups = [
        AnovaGroup(
            name=str(g["name"]),
            mean=g.get("mean"),
            sd=g.get("sd"),
            n=g.get("n"),
        )
        for g in raw.get("groups", [])
    ]

    factors = [
        Factor(
            name=str(f["name"]),
            eigenvalue=f.get("eigenvalue"),
            variance_explained=f.get("variance_explained"),
            loadings=[
                FactorLoading(
                    variable=str(lo["variable"]),
                    loading=float(lo["loading"]),
                    communality=lo.get("communality"),
                )
                for lo in f.get("loadings", [])
            ],
        )
        for f in raw.get("factors", [])
    ]

    return StatInput(
        stat_type=stat_type,
        n=int(raw["n"]),
        p_value=raw.get("p_value"),
        model_name=raw.get("model_name"),
        outcome=raw.get("outcome"),
        r_squared=raw.get("r_squared"),
        adjusted_r_squared=raw.get("adjusted_r_squared"),
        f_statistic=raw.get("f_statistic"),
        f_df1=raw.get("f_df1"),
        f_df2=raw.get("f_df2"),
        coefficients=coefficients,
        t_statistic=raw.get("t_statistic"),
        t_df=raw.get("t_df"),
        cohens_d=raw.get("cohens_d"),
        mean_group1=raw.get("mean_group1"),
        mean_group2=raw.get("mean_group2"),
        sd_group1=raw.get("sd_group1"),
        sd_group2=raw.get("sd_group2"),
        group1_label=raw.get("group1_label", "Group 1"),
        group2_label=raw.get("group2_label", "Group 2"),
        f_value=raw.get("f_value"),
        eta_squared=raw.get("eta_squared"),
        groups=groups,
        r=raw.get("r"),
        var1=raw.get("var1"),
        var2=raw.get("var2"),
        chi_square=raw.get("chi_square"),
        chi_df=raw.get("chi_df"),
        cramers_v=raw.get("cramers_v"),
        n_factors=raw.get("n_factors"),
        total_variance_explained=raw.get("total_variance_explained"),
        factors=factors,
        context=raw.get("context"),
    )


def load_stat_input(source: "str | Path") -> StatInput:
    """Load and parse a StatInput from a file path or JSON string."""
    raw = _load_raw(source)
    return parse_stat_input(raw)
