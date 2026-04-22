"""
stat-narrator — basic usage examples.

Run with:
    python examples/basic_usage.py
"""
from statnarrator import narrate
from statnarrator.models import Coefficient, StatInput, StatType

# ── Example 1: Regression ──────────────────────────────────────────────────
regression = StatInput(
    stat_type=StatType.REGRESSION,
    n=245,
    outcome="Willingness to Pay",
    r_squared=0.43,
    adjusted_r_squared=0.42,
    f_statistic=60.8,
    f_df1=3,
    f_df2=241,
    p_value=0.0003,
    coefficients=[
        Coefficient(name="Satisfaction", b=0.52, se=0.08, t=6.5, p=0.0002, beta=0.41),
        Coefficient(name="Trust",        b=0.31, se=0.09, t=3.4, p=0.0008, beta=0.28),
        Coefficient(name="Ease",         b=0.08, se=0.07, t=1.1, p=0.255,  beta=0.06),
    ],
    context="Post-purchase survey, SaaS B2B product",
)

result = narrate(regression)
print("=== REGRESSION ===")
print("Headline:", result.headline)
print("Significance:", result.significance.value)
print("Effect:", result.effect_magnitude.value)
print("Takeaway:", result.practitioner_takeaway)
if result.warnings:
    print("Warnings:", result.warnings)

# ── Example 2: t-test ──────────────────────────────────────────────────────
ttest = StatInput(
    stat_type=StatType.TTEST,
    n=120,
    group1_label="New onboarding",
    group2_label="Legacy onboarding",
    mean_group1=4.31,
    mean_group2=3.74,
    sd_group1=0.82,
    sd_group2=0.91,
    t_statistic=3.87,
    t_df=118,
    p_value=0.0002,
    cohens_d=0.66,
)

result = narrate(ttest)
print("\n=== T-TEST ===")
print("Headline:", result.headline)
print("Plain summary:", result.plain_summary)

# ── Example 3: JSON output ─────────────────────────────────────────────────
import json

result = narrate(regression)
print("\n=== JSON OUTPUT (first 400 chars) ===")
print(json.dumps(result.to_dict(), indent=2)[:400], "...")

# ── Example 4: LLM enrichment (requires API key) ───────────────────────────
# Uncomment and set OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
#
# from statnarrator.llm import enrich
# result = narrate(regression)
# result = enrich(regression, result, backend="anthropic")
# print(result.llm_narrative)
