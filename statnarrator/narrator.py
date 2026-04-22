from __future__ import annotations

from .interpreter import (
    classify_significance,
    collect_warnings,
    derive_effect_magnitude,
)
from .models import (
    EffectMagnitude,
    NarrativeOutput,
    NarrativeSegment,
    SignificanceLevel,
    StatInput,
    StatType,
)

_EFFECT_WORDS = {
    EffectMagnitude.NEGLIGIBLE: "negligible",
    EffectMagnitude.SMALL: "small",
    EffectMagnitude.MEDIUM: "moderate",
    EffectMagnitude.LARGE: "large",
}

_SIG_WORDS = {
    SignificanceLevel.HIGHLY_SIGNIFICANT: "highly significant",
    SignificanceLevel.SIGNIFICANT: "significant",
    SignificanceLevel.MARGINAL: "marginally significant",
    SignificanceLevel.NOT_SIGNIFICANT: "not significant",
}


def _fmt_p(p: float | None) -> str:
    if p is None:
        return "p = N/A"
    if p < 0.001:
        return "p < .001"
    return f"p = {p:.3f}"


def _fmt_ci(lo: float | None, hi: float | None) -> str:
    if lo is None or hi is None:
        return ""
    return f"95% CI [{lo:.2f}, {hi:.2f}]"


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------

def _narrate_regression(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    outcome = stat.outcome or stat.model_name or "the outcome variable"

    seg_context = NarrativeSegment(
        label="Model overview",
        text=(
            f"A multiple linear regression was conducted predicting {outcome} "
            f"(n = {stat.n})."
            + (f" Model specification: {stat.model_name}." if stat.model_name and stat.outcome else "")
        ),
    )

    fit_parts: list[str] = []
    if stat.r_squared is not None:
        r2_pct = stat.r_squared * 100
        adj_note = (
            f" (adjusted R² = {stat.adjusted_r_squared:.2f})"
            if stat.adjusted_r_squared is not None
            else ""
        )
        fit_parts.append(
            f"The model explained {r2_pct:.1f}% of variance in {outcome} "
            f"(R² = {stat.r_squared:.2f}{adj_note}), "
            f"a {_EFFECT_WORDS[effect]} effect size."
        )
    if stat.f_statistic is not None:
        df_note = (
            f"({stat.f_df1}, {stat.f_df2})"
            if stat.f_df1 is not None and stat.f_df2 is not None
            else ""
        )
        fit_parts.append(
            f"The overall model was {_SIG_WORDS[sig]} "
            f"(F{df_note} = {stat.f_statistic:.2f}, {_fmt_p(stat.p_value)})."
        )

    seg_fit = NarrativeSegment(
        label="Model fit",
        text=" ".join(fit_parts) if fit_parts else "Model fit statistics were not provided.",
    )

    sig_preds: list[str] = []
    ns_preds: list[str] = []
    pred_sentences: list[str] = []
    for coef in stat.coefficients:
        coef_sig = classify_significance(coef.p)
        ci_str = _fmt_ci(coef.ci_lower, coef.ci_upper)
        ci_part = f", {ci_str}" if ci_str else ""
        beta_part = f", β = {coef.beta:.2f}" if coef.beta is not None else ""
        pred_sentences.append(
            f"{coef.name} was a {_SIG_WORDS[coef_sig]} predictor of {outcome} "
            f"(b = {coef.b:.2f}{beta_part}{ci_part}, {_fmt_p(coef.p)})."
        )
        if coef_sig != SignificanceLevel.NOT_SIGNIFICANT:
            sig_preds.append(coef.name)
        else:
            ns_preds.append(coef.name)

    seg_preds = NarrativeSegment(
        label="Predictors",
        text=" ".join(pred_sentences) if pred_sentences else "No predictor coefficients were provided.",
    )

    if sig_preds:
        r2_clause = f" (R² = {stat.r_squared:.2f})" if stat.r_squared is not None else ""
        headline = (
            f"{' and '.join(sig_preds[:2])} significantly predicted {outcome}{r2_clause}."
        )
    else:
        headline = f"No significant predictors of {outcome} were identified."

    plain_parts: list[str] = []
    if stat.r_squared is not None:
        plain_parts.append(
            f"The regression model accounted for {stat.r_squared * 100:.1f}% "
            f"of the variance in {outcome}."
        )
    if sig_preds:
        conj = " and ".join(sig_preds)
        verb = "were" if len(sig_preds) > 1 else "was"
        noun = "predictors" if len(sig_preds) > 1 else "predictor"
        plain_parts.append(f"{conj} {verb} the strongest {noun}.")
    if ns_preds:
        plain_parts.append(f"{' and '.join(ns_preds)} did not reach significance.")
    plain_summary = " ".join(plain_parts)

    if sig_preds:
        second = f" and {sig_preds[1]}" if len(sig_preds) > 1 else ""
        takeaway = (
            f"Focus product or design interventions on {sig_preds[0]}{second} — "
            f"these variables have the strongest evidence-based relationship to {outcome}."
        )
    else:
        takeaway = (
            f"The tested variables did not reliably predict {outcome}. "
            "Consider expanding the variable set or revisiting the conceptual model."
        )

    return NarrativeOutput(
        stat_type=StatType.REGRESSION,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=[seg_context, seg_fit, seg_preds],
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# t-test
# ---------------------------------------------------------------------------

def _narrate_ttest(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    g1 = stat.group1_label or "Group 1"
    g2 = stat.group2_label or "Group 2"

    direction = ""
    if stat.mean_group1 is not None and stat.mean_group2 is not None:
        direction = "higher" if stat.mean_group1 > stat.mean_group2 else "lower"

    mean_text = ""
    if stat.mean_group1 is not None and stat.mean_group2 is not None:
        sd1 = f" (SD = {stat.sd_group1:.2f})" if stat.sd_group1 is not None else ""
        sd2 = f" (SD = {stat.sd_group2:.2f})" if stat.sd_group2 is not None else ""
        mean_text = (
            f"{g1} (M = {stat.mean_group1:.2f}{sd1}) scored {direction} "
            f"than {g2} (M = {stat.mean_group2:.2f}{sd2})."
        )

    df_str = f"({stat.t_df:.0f})" if stat.t_df is not None else ""
    t_str = f"t{df_str} = {stat.t_statistic:.2f}" if stat.t_statistic is not None else ""
    d_str = f"d = {stat.cohens_d:.2f}" if stat.cohens_d is not None else ""
    stats_parts = [x for x in [t_str, _fmt_p(stat.p_value), d_str] if x]
    stats_text = f"({', '.join(stats_parts)})" if stats_parts else ""

    seg_result = NarrativeSegment(
        label="Test result",
        text=(
            f"An independent-samples t-test was conducted (n = {stat.n}). "
            f"{mean_text} The difference was {_SIG_WORDS[sig]} {stats_text}."
        ),
    )

    seg_effect = NarrativeSegment(
        label="Effect size",
        text=(
            f"Cohen's d = {stat.cohens_d:.2f} indicates a {_EFFECT_WORDS[effect]} effect size."
            if stat.cohens_d is not None
            else "Effect size (Cohen's d) was not provided — report this alongside the t-statistic."
        ),
    )

    if sig != SignificanceLevel.NOT_SIGNIFICANT and direction:
        headline = (
            f"{g1} scored {direction} than {g2} — "
            f"{_EFFECT_WORDS[effect]} effect ({_SIG_WORDS[sig]})."
        )
    else:
        headline = f"No significant difference detected between {g1} and {g2}."

    plain_summary = (
        f"{'A statistically significant' if sig != SignificanceLevel.NOT_SIGNIFICANT else 'No significant'} "
        f"difference was found between {g1} and {g2} {stats_text}."
        + (f" The effect is {_EFFECT_WORDS[effect]}." if stat.cohens_d is not None else "")
    )

    if sig != SignificanceLevel.NOT_SIGNIFICANT:
        takeaway = (
            f"The difference between {g1} and {g2} is statistically real and "
            f"{_EFFECT_WORDS[effect]} in magnitude. "
            "This finding is sufficient to warrant further investigation or targeted design intervention."
        )
    else:
        takeaway = (
            f"No reliable difference was detected between {g1} and {g2}. "
            "If a difference is theoretically expected, consider whether the study was adequately powered."
        )

    return NarrativeOutput(
        stat_type=StatType.TTEST,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=[seg_result, seg_effect],
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# ANOVA
# ---------------------------------------------------------------------------

def _narrate_anova(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    f_val = stat.f_value if stat.f_value is not None else stat.f_statistic
    group_names = [g.name for g in stat.groups] if stat.groups else []
    groups_str = ", ".join(group_names) if group_names else "multiple groups"

    result_text = (
        f"A one-way ANOVA was conducted across {groups_str} (n = {stat.n})."
        + (f" F = {f_val:.2f}, {_fmt_p(stat.p_value)}." if f_val is not None else "")
        + f" The result was {_SIG_WORDS[sig]}."
    )
    seg_result = NarrativeSegment(label="ANOVA result", text=result_text)

    seg_effect = NarrativeSegment(
        label="Effect size",
        text=(
            f"η² = {stat.eta_squared:.3f} indicates a {_EFFECT_WORDS[effect]} effect — "
            f"group membership accounts for approximately {stat.eta_squared * 100:.1f}% of variance."
            if stat.eta_squared is not None
            else "η² not reported; effect size is required alongside the F-statistic."
        ),
    )

    segments = [seg_result, seg_effect]
    if stat.groups:
        means_parts = [
            f"{g.name} (M = {g.mean:.2f})" if g.mean is not None else g.name
            for g in stat.groups
        ]
        seg_means = NarrativeSegment(
            label="Group means", text="Group means: " + ", ".join(means_parts) + "."
        )
        segments.append(seg_means)

    headline = (
        f"Significant differences across {groups_str} — {_EFFECT_WORDS[effect]} effect size."
        if sig != SignificanceLevel.NOT_SIGNIFICANT
        else f"No significant differences detected across {groups_str}."
    )

    f_clause = f"F = {f_val:.2f}, " if f_val is not None else ""
    plain_summary = (
        f"{'Significant' if sig != SignificanceLevel.NOT_SIGNIFICANT else 'No significant'} "
        f"differences were detected across {groups_str} "
        f"({f_clause}{_fmt_p(stat.p_value)})."
        + (f" η² = {stat.eta_squared:.2f} ({_EFFECT_WORDS[effect]} effect)." if stat.eta_squared is not None else "")
    )

    takeaway = (
        "Group differences are statistically real. "
        "Follow up with post-hoc comparisons to identify which specific groups differ."
        if sig != SignificanceLevel.NOT_SIGNIFICANT
        else "No reliable group differences detected. "
        "Consider whether the study was adequately powered to detect the expected effect."
    )

    return NarrativeOutput(
        stat_type=StatType.ANOVA,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=segments,
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def _narrate_correlation(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    v1 = stat.var1 or "Variable 1"
    v2 = stat.var2 or "Variable 2"
    r = stat.r if stat.r is not None else 0.0
    direction_word = "positive" if r >= 0 else "negative"

    seg_result = NarrativeSegment(
        label="Correlation",
        text=(
            f"A Pearson correlation was computed between {v1} and {v2} (n = {stat.n}). "
            f"r = {r:.2f}, {_fmt_p(stat.p_value)}. "
            f"The association was {_SIG_WORDS[sig]} and {direction_word} in direction."
        ),
    )

    seg_effect = NarrativeSegment(
        label="Effect size",
        text=(
            f"r = {r:.2f} represents a {_EFFECT_WORDS[effect]} effect "
            "by conventional benchmarks (Cohen, 1988)."
        ),
    )

    headline = (
        f"{'Significant' if sig != SignificanceLevel.NOT_SIGNIFICANT else 'Non-significant'} "
        f"{direction_word} correlation between {v1} and {v2} (r = {r:.2f})."
    )
    plain_summary = (
        f"{v1} and {v2} showed a {_EFFECT_WORDS[effect]}, {direction_word} correlation "
        f"(r = {r:.2f}, {_fmt_p(stat.p_value)}, n = {stat.n})."
    )
    takeaway = (
        (
            f"The relationship between {v1} and {v2} is reliable and warrants further investigation."
            if sig != SignificanceLevel.NOT_SIGNIFICANT
            else f"No reliable linear relationship was detected between {v1} and {v2}."
        )
        + " Note that correlation does not establish causation."
    )

    return NarrativeOutput(
        stat_type=StatType.CORRELATION,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=[seg_result, seg_effect],
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# Chi-square
# ---------------------------------------------------------------------------

def _narrate_chi_square(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    chi_val = stat.chi_square if stat.chi_square is not None else 0.0
    df_note = f", df = {stat.chi_df}" if stat.chi_df is not None else ""

    seg_result = NarrativeSegment(
        label="Chi-square test",
        text=(
            f"A chi-square test of independence was conducted "
            f"(n = {stat.n}{df_note}). "
            f"χ² = {chi_val:.2f}, {_fmt_p(stat.p_value)}. "
            f"The result was {_SIG_WORDS[sig]}."
        ),
    )

    seg_effect = NarrativeSegment(
        label="Effect size",
        text=(
            f"Cramér's V = {stat.cramers_v:.2f} indicates a {_EFFECT_WORDS[effect]} association."
            if stat.cramers_v is not None
            else "Cramér's V not provided; report effect size alongside χ²."
        ),
    )

    headline = (
        f"{'Significant' if sig != SignificanceLevel.NOT_SIGNIFICANT else 'No significant'} "
        f"association detected (χ² = {chi_val:.2f})."
    )
    sig_word = (
        "found a statistically significant"
        if sig != SignificanceLevel.NOT_SIGNIFICANT
        else "did not find a significant"
    )
    cramers_clause = (
        f" Cramér's V = {stat.cramers_v:.2f} ({_EFFECT_WORDS[effect]} effect)."
        if stat.cramers_v is not None
        else ""
    )
    plain_summary = (
        f"The chi-square test {sig_word} association "
        f"(χ² = {chi_val:.2f}, {_fmt_p(stat.p_value)}, n = {stat.n}).{cramers_clause}"
    )
    takeaway = (
        "The categorical variables are meaningfully associated. "
        "Examine the contingency table to understand the direction of the relationship."
        if sig != SignificanceLevel.NOT_SIGNIFICANT
        else "No reliable association found. "
        "Consider whether sample size was adequate to detect an effect."
    )

    return NarrativeOutput(
        stat_type=StatType.CHI_SQUARE,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=[seg_result, seg_effect],
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# Factor analysis
# ---------------------------------------------------------------------------

def _narrate_factor(
    stat: StatInput, sig: SignificanceLevel, effect: EffectMagnitude
) -> NarrativeOutput:
    n_factors = stat.n_factors if stat.n_factors is not None else len(stat.factors)
    var_pct = stat.total_variance_explained

    seg_result = NarrativeSegment(
        label="Factor structure",
        text=(
            f"Factor analysis extracted {n_factors} "
            f"{'factor' if n_factors == 1 else 'factors'} from {stat.n} observations."
            + (f" Together they explain {var_pct:.1f}% of total variance." if var_pct is not None else "")
        ),
    )

    factor_texts: list[str] = []
    for fac in stat.factors:
        top = sorted(fac.loadings, key=lambda x: abs(x.loading), reverse=True)[:3]
        loading_str = ", ".join(f"{lo.variable} ({lo.loading:.2f})" for lo in top)
        line = f"{fac.name}: top loadings — {loading_str}."
        if fac.eigenvalue is not None and fac.variance_explained is not None:
            line += (
                f" Eigenvalue = {fac.eigenvalue:.2f}, "
                f"variance explained = {fac.variance_explained:.1f}%."
            )
        factor_texts.append(line)

    seg_factors = NarrativeSegment(
        label="Factor details",
        text=" ".join(factor_texts) if factor_texts else "No factor details provided.",
    )

    headline = (
        f"{n_factors} {'factor' if n_factors == 1 else 'factors'} extracted"
        + (f", explaining {var_pct:.1f}% of variance." if var_pct is not None else ".")
    )
    plain_summary = (
        f"Factor analysis identified {n_factors} underlying "
        f"{'dimension' if n_factors == 1 else 'dimensions'}"
        + (f", collectively accounting for {var_pct:.1f}% of total variance" if var_pct is not None else "")
        + "."
    )
    takeaway = (
        "Use the extracted factors as composites in further analyses or as a basis for scale development. "
        "Examine factor loadings critically and consider cross-validation on a holdout sample."
    )

    return NarrativeOutput(
        stat_type=StatType.FACTOR,
        significance=sig,
        effect_magnitude=effect,
        headline=headline,
        segments=[seg_result, seg_factors],
        plain_summary=plain_summary,
        practitioner_takeaway=takeaway,
        warnings=collect_warnings(stat),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_DISPATCH = {
    StatType.REGRESSION: _narrate_regression,
    StatType.TTEST: _narrate_ttest,
    StatType.ANOVA: _narrate_anova,
    StatType.CORRELATION: _narrate_correlation,
    StatType.CHI_SQUARE: _narrate_chi_square,
    StatType.FACTOR: _narrate_factor,
}


def narrate(stat: StatInput) -> NarrativeOutput:
    """Produce a plain-language narrative from a StatInput.

    Rules are applied entirely offline — no API calls. Pass the result to
    ``statnarrator.llm.enrich`` for optional LLM enrichment.
    """
    sig = classify_significance(stat.p_value)
    effect = derive_effect_magnitude(stat)
    fn = _DISPATCH.get(stat.stat_type)
    if fn is None:
        return NarrativeOutput(
            stat_type=stat.stat_type,
            significance=sig,
            effect_magnitude=effect,
            headline="Statistical results processed.",
            segments=[
                NarrativeSegment(
                    label="Result",
                    text=f"n = {stat.n}, {_fmt_p(stat.p_value)}.",
                )
            ],
            plain_summary=f"Statistical analysis conducted on n = {stat.n} observations.",
            practitioner_takeaway="Consult a statistician for interpretation of this output type.",
            warnings=collect_warnings(stat)
            + ["Unrecognised stat type — narrative may be incomplete."],
        )
    return fn(stat, sig, effect)
