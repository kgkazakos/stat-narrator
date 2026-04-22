from __future__ import annotations

import json
from pathlib import Path

import pytest

from statnarrator.models import StatType
from statnarrator.parser import load_stat_input, parse_stat_input

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_regression():
    stat = load_stat_input(FIXTURES / "regression.json")
    assert stat.stat_type == StatType.REGRESSION
    assert stat.n == 245
    assert stat.r_squared == pytest.approx(0.43)
    assert len(stat.coefficients) == 3
    assert stat.coefficients[0].name == "Satisfaction"
    assert stat.coefficients[0].beta == pytest.approx(0.41)


def test_parse_ttest():
    stat = load_stat_input(FIXTURES / "ttest.json")
    assert stat.stat_type == StatType.TTEST
    assert stat.n == 120
    assert stat.cohens_d == pytest.approx(0.66)
    assert stat.group1_label == "New onboarding"


def test_parse_anova():
    stat = load_stat_input(FIXTURES / "anova.json")
    assert stat.stat_type == StatType.ANOVA
    assert stat.n == 180
    assert len(stat.groups) == 3
    assert stat.groups[0].name == "Power users"
    assert stat.groups[0].mean == pytest.approx(4.7)


def test_parse_correlation():
    stat = load_stat_input(FIXTURES / "correlation.json")
    assert stat.stat_type == StatType.CORRELATION
    assert stat.r == pytest.approx(0.62)
    assert stat.var1 == "Task completion time"


def test_parse_chi_square():
    stat = load_stat_input(FIXTURES / "chi_square.json")
    assert stat.stat_type == StatType.CHI_SQUARE
    assert stat.chi_square == pytest.approx(18.7)
    assert stat.cramers_v == pytest.approx(0.21)


def test_parse_unknown_stat_type():
    raw = {"stat_type": "bayesian_nightmare", "n": 50}
    stat = parse_stat_input(raw)
    assert stat.stat_type == StatType.UNKNOWN
    assert stat.n == 50


def test_parse_from_json_string():
    raw = json.dumps({"stat_type": "correlation", "n": 80, "r": 0.34, "p_value": 0.002})
    stat = parse_stat_input(json.loads(raw))
    assert stat.stat_type == StatType.CORRELATION
    assert stat.r == pytest.approx(0.34)
