from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StatType(str, Enum):
    REGRESSION = "regression"
    TTEST = "ttest"
    ANOVA = "anova"
    CORRELATION = "correlation"
    CHI_SQUARE = "chi_square"
    FACTOR = "factor_analysis"
    UNKNOWN = "unknown"


class SignificanceLevel(str, Enum):
    HIGHLY_SIGNIFICANT = "highly_significant"
    SIGNIFICANT = "significant"
    MARGINAL = "marginal"
    NOT_SIGNIFICANT = "not_significant"


class EffectMagnitude(str, Enum):
    NEGLIGIBLE = "negligible"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class Coefficient:
    name: str
    b: float
    se: Optional[float] = None
    t: Optional[float] = None
    p: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    beta: Optional[float] = None  # standardised


@dataclass
class AnovaGroup:
    name: str
    mean: Optional[float] = None
    sd: Optional[float] = None
    n: Optional[int] = None


@dataclass
class FactorLoading:
    variable: str
    loading: float
    communality: Optional[float] = None


@dataclass
class Factor:
    name: str
    eigenvalue: Optional[float] = None
    variance_explained: Optional[float] = None
    loadings: list[FactorLoading] = field(default_factory=list)


@dataclass
class StatInput:
    stat_type: StatType
    n: int
    p_value: Optional[float] = None

    # Regression
    model_name: Optional[str] = None
    outcome: Optional[str] = None
    r_squared: Optional[float] = None
    adjusted_r_squared: Optional[float] = None
    f_statistic: Optional[float] = None
    f_df1: Optional[int] = None
    f_df2: Optional[int] = None
    coefficients: list[Coefficient] = field(default_factory=list)

    # t-test
    t_statistic: Optional[float] = None
    t_df: Optional[float] = None
    cohens_d: Optional[float] = None
    mean_group1: Optional[float] = None
    mean_group2: Optional[float] = None
    sd_group1: Optional[float] = None
    sd_group2: Optional[float] = None
    group1_label: Optional[str] = "Group 1"
    group2_label: Optional[str] = "Group 2"

    # ANOVA
    f_value: Optional[float] = None
    eta_squared: Optional[float] = None
    groups: list[AnovaGroup] = field(default_factory=list)

    # Correlation
    r: Optional[float] = None
    var1: Optional[str] = None
    var2: Optional[str] = None

    # Chi-square
    chi_square: Optional[float] = None
    chi_df: Optional[int] = None
    cramers_v: Optional[float] = None

    # Factor analysis
    n_factors: Optional[int] = None
    total_variance_explained: Optional[float] = None
    factors: list[Factor] = field(default_factory=list)

    # Free-text study context (passed to LLM prompt)
    context: Optional[str] = None


@dataclass
class NarrativeSegment:
    label: str
    text: str


@dataclass
class NarrativeOutput:
    stat_type: StatType
    significance: SignificanceLevel
    effect_magnitude: EffectMagnitude
    headline: str
    segments: list[NarrativeSegment]
    plain_summary: str
    practitioner_takeaway: str
    llm_enhanced: bool = False
    llm_narrative: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "stat_type": self.stat_type.value,
            "significance": self.significance.value,
            "effect_magnitude": self.effect_magnitude.value,
            "headline": self.headline,
            "segments": [{"label": s.label, "text": s.text} for s in self.segments],
            "plain_summary": self.plain_summary,
            "practitioner_takeaway": self.practitioner_takeaway,
            "llm_enhanced": self.llm_enhanced,
            "llm_narrative": self.llm_narrative,
            "warnings": self.warnings,
        }
