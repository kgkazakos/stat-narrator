from __future__ import annotations

import pytest

from statnarrator.interpreter import (
    classify_cohens_d,
    classify_correlation,
    classify_eta_squared,
    classify_r_squared,
    classify_significance,
    collect_warnings,
)
from statnarrator.models import EffectMagnitude, SignificanceLevel, StatInput, StatType


@pytest.mark.parametrize(
    "p, expected",
    [
        (0.0001, SignificanceLevel.HIGHLY_SIGNIFICANT),
        (0.005, SignificanceLevel.SIGNIFICANT),
        (0.03, SignificanceLevel.MARGINAL),
        (0.06, SignificanceLevel.NOT_SIGNIFICANT),
        (None, SignificanceLevel.NOT_SIGNIFICANT),
    ],
)
def test_classify_significance(p, expected):
    assert classify_significance(p) == expected


@pytest.mark.parametrize(
    "r2, expected",
    [
        (0.01, EffectMagnitude.NEGLIGIBLE),
        (0.05, EffectMagnitude.SMALL),
        (0.20, EffectMagnitude.MEDIUM),
        (0.50, EffectMagnitude.LARGE),
    ],
)
def test_classify_r_squared(r2, expected):
    assert classify_r_squared(r2) == expected


@pytest.mark.parametrize(
    "d, expected",
    [
        (0.1, EffectMagnitude.NEGLIGIBLE),
        (0.3, EffectMagnitude.SMALL),
        (0.6, EffectMagnitude.MEDIUM),
        (1.0, EffectMagnitude.LARGE),
        (-0.9, EffectMagnitude.LARGE),  # negative d still large
    ],
)
def test_classify_cohens_d(d, expected):
    assert classify_cohens_d(d) == expected


@pytest.mark.parametrize(
    "r, expected",
    [
        (0.05, EffectMagnitude.NEGLIGIBLE),
        (0.20, EffectMagnitude.SMALL),
        (0.40, EffectMagnitude.MEDIUM),
        (0.70, EffectMagnitude.LARGE),
        (-0.55, EffectMagnitude.LARGE),
    ],
)
def test_classify_correlation(r, expected):
    assert classify_correlation(r) == expected


@pytest.mark.parametrize(
    "eta2, expected",
    [
        (0.005, EffectMagnitude.NEGLIGIBLE),
        (0.03, EffectMagnitude.SMALL),
        (0.10, EffectMagnitude.MEDIUM),
        (0.20, EffectMagnitude.LARGE),
    ],
)
def test_classify_eta_squared(eta2, expected):
    assert classify_eta_squared(eta2) == expected


def test_collect_warnings_small_n():
    stat = StatInput(stat_type=StatType.TTEST, n=20, cohens_d=None)
    warnings = collect_warnings(stat)
    assert any("Small sample" in w for w in warnings)
    assert any("Cohen's d" in w for w in warnings)


def test_collect_warnings_borderline_p():
    stat = StatInput(stat_type=StatType.CORRELATION, n=100, p_value=0.048)
    warnings = collect_warnings(stat)
    assert any("close to the .05" in w for w in warnings)


def test_collect_warnings_clean():
    stat = StatInput(
        stat_type=StatType.REGRESSION,
        n=150,
        p_value=0.001,
        r_squared=0.35,
    )
    warnings = collect_warnings(stat)
    assert not any("Small sample" in w for w in warnings)
    assert not any("R²" in w for w in warnings)
