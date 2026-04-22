from __future__ import annotations

from pathlib import Path

from statnarrator.models import (
    AnovaGroup,
    Coefficient,
    EffectMagnitude,
    SignificanceLevel,
    StatInput,
    StatType,
)
from statnarrator.narrator import narrate
from statnarrator.parser import load_stat_input

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------

def test_narrate_regression_basic():
    stat = load_stat_input(FIXTURES / "regression.json")
    output = narrate(stat)
    assert output.stat_type == StatType.REGRESSION
    assert output.significance == SignificanceLevel.HIGHLY_SIGNIFICANT
    assert output.effect_magnitude == EffectMagnitude.LARGE
    assert "Satisfaction" in output.headline
    assert output.plain_summary
    assert output.practitioner_takeaway
    assert not output.llm_enhanced
    assert output.llm_narrative is None


def test_narrate_regression_segments():
    stat = load_stat_input(FIXTURES / "regression.json")
    output = narrate(stat)
    labels = [s.label for s in output.segments]
    assert "Model overview" in labels
    assert "Model fit" in labels
    assert "Predictors" in labels


def test_narrate_regression_no_sig_preds():
    stat = StatInput(
        stat_type=StatType.REGRESSION,
        n=100,
        outcome="Satisfaction",
        r_squared=0.05,
        p_value=0.31,
        coefficients=[
            Coefficient(name="Price", b=0.04, p=0.62),
            Coefficient(name="Speed", b=0.03, p=0.71),
        ],
    )
    output = narrate(stat)
    assert "No significant predictors" in output.headline


# ---------------------------------------------------------------------------
# t-test
# ---------------------------------------------------------------------------

def test_narrate_ttest():
    stat = load_stat_input(FIXTURES / "ttest.json")
    output = narrate(stat)
    assert output.stat_type == StatType.TTEST
    assert output.significance == SignificanceLevel.HIGHLY_SIGNIFICANT
    assert output.effect_magnitude == EffectMagnitude.MEDIUM
    assert "higher" in output.headline.lower() or "lower" in output.headline.lower()


def test_narrate_ttest_not_significant():
    stat = StatInput(
        stat_type=StatType.TTEST,
        n=60,
        group1_label="Treatment",
        group2_label="Control",
        mean_group1=3.2,
        mean_group2=3.1,
        t_statistic=0.45,
        t_df=58,
        p_value=0.65,
        cohens_d=0.09,
    )
    output = narrate(stat)
    assert output.significance == SignificanceLevel.NOT_SIGNIFICANT
    assert "No significant difference" in output.headline


# ---------------------------------------------------------------------------
# ANOVA
# ---------------------------------------------------------------------------

def test_narrate_anova():
    stat = load_stat_input(FIXTURES / "anova.json")
    output = narrate(stat)
    assert output.stat_type == StatType.ANOVA
    assert output.significance == SignificanceLevel.HIGHLY_SIGNIFICANT
    assert output.effect_magnitude == EffectMagnitude.MEDIUM
    # Group means segment should be present
    labels = [s.label for s in output.segments]
    assert "Group means" in labels


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def test_narrate_correlation():
    stat = load_stat_input(FIXTURES / "correlation.json")
    output = narrate(stat)
    assert output.stat_type == StatType.CORRELATION
    assert output.significance == SignificanceLevel.HIGHLY_SIGNIFICANT
    assert output.effect_magnitude == EffectMagnitude.LARGE
    assert "positive" in output.headline.lower()


def test_narrate_negative_correlation():
    stat = StatInput(
        stat_type=StatType.CORRELATION,
        n=100,
        var1="Ease of use",
        var2="Support tickets",
        r=-0.45,
        p_value=0.0001,
    )
    output = narrate(stat)
    assert "negative" in output.headline.lower()


# ---------------------------------------------------------------------------
# Chi-square
# ---------------------------------------------------------------------------

def test_narrate_chi_square():
    stat = load_stat_input(FIXTURES / "chi_square.json")
    output = narrate(stat)
    assert output.stat_type == StatType.CHI_SQUARE
    assert output.significance == SignificanceLevel.HIGHLY_SIGNIFICANT
    assert output.effect_magnitude == EffectMagnitude.SMALL


# ---------------------------------------------------------------------------
# Unknown stat type
# ---------------------------------------------------------------------------

def test_narrate_unknown_type():
    stat = StatInput(stat_type=StatType.UNKNOWN, n=50, p_value=0.04)
    output = narrate(stat)
    assert output.stat_type == StatType.UNKNOWN
    assert any("Unrecognised" in w for w in output.warnings)


# ---------------------------------------------------------------------------
# to_dict round-trip
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    stat = load_stat_input(FIXTURES / "ttest.json")
    output = narrate(stat)
    d = output.to_dict()
    assert d["stat_type"] == "ttest"
    assert d["llm_enhanced"] is False
    assert d["llm_narrative"] is None
    assert isinstance(d["segments"], list)
    assert isinstance(d["warnings"], list)
