# stat-narrator

**Translates statistical model outputs into plain-language research narratives.**

Statistical outputs — regression tables, t-test results, ANOVA summaries — are not research narratives. They are numbers. Most research stakeholders cannot read them, and most researchers don't have time to write them up properly for every report. `stat-narrator` closes that gap: feed it a JSON description of your statistical results and it returns a structured, APA-aligned narrative in plain language, ready to drop into a report or stakeholder brief.

---

## The problem it solves

You ran a regression. R² = 0.43, F(3, 241) = 60.8, p < .001. Satisfaction β = 0.41, Trust β = 0.28, Ease ns.

Your PM wants a paragraph. Your director wants a headline. Your research report needs an effect size interpretation. You need all three in the next 10 minutes.

`stat-narrator` generates the paragraph, the headline, the effect size classification, and a practitioner-oriented takeaway — from a JSON file, in seconds, with zero API calls.

---

## Features

- **Six stat types out of the box** — multiple regression, independent t-test, one-way ANOVA, Pearson correlation, chi-square, and factor analysis
- **APA-aligned effect size classification** — Cohen's d, R², η², r, Cramér's V automatically interpreted against established benchmarks (Cohen, 1988)
- **Structured narrative output** — headline, segmented body text, plain summary, practitioner takeaway, warnings
- **Smart warnings** — flags small samples, borderline p-values, missing effect sizes
- **Rule-based core** — zero API calls required; works fully offline
- **Optional LLM enrichment** — pass `--llm-backend openai|anthropic|gemini` for polished report-ready prose
- **Batch mode** — narrate an entire folder of JSON results in one command
- **JSON output flag** — pipe results into downstream tooling

---

## Installation

```bash
pip install stat-narrator
```

With LLM enrichment:

```bash
pip install "stat-narrator[openai]"
pip install "stat-narrator[anthropic]"
pip install "stat-narrator[gemini]"
pip install "stat-narrator[llm]"   # all three
```

---

## Quick start

### CLI

```bash
# Narrate a regression result
stat-narrator narrate my_regression.json

# With LLM enrichment
stat-narrator narrate my_regression.json --llm-backend anthropic

# JSON output
stat-narrator narrate my_regression.json --json-output

# Batch — narrate every JSON file in a directory
stat-narrator batch ./results/

# Batch with output saved to disk
stat-narrator batch ./results/ --out-dir ./narratives/
```

### Python

```python
from statnarrator import narrate
from statnarrator.models import Coefficient, StatInput, StatType

stat = StatInput(
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
        Coefficient(name="Satisfaction", b=0.52, p=0.0002, beta=0.41),
        Coefficient(name="Trust",        b=0.31, p=0.0008, beta=0.28),
        Coefficient(name="Ease",         b=0.08, p=0.255,  beta=0.06),
    ],
)

result = narrate(stat)
print(result.headline)
# → "Satisfaction and Trust significantly predicted Willingness to Pay (R² = 0.43)."

print(result.practitioner_takeaway)
# → "Focus product or design interventions on Satisfaction and Trust..."

print(result.to_dict())  # full structured output as dict
```

---

## Input format

Pass statistical results as a JSON file. The required fields depend on the stat type.

### Regression

```json
{
  "stat_type": "regression",
  "n": 245,
  "outcome": "Willingness to Pay",
  "model_name": "WTP ~ Satisfaction + Trust + Ease",
  "r_squared": 0.43,
  "adjusted_r_squared": 0.42,
  "f_statistic": 60.8,
  "f_df1": 3,
  "f_df2": 241,
  "p_value": 0.0003,
  "coefficients": [
    { "name": "Satisfaction", "b": 0.52, "se": 0.08, "t": 6.5, "p": 0.0002, "ci_lower": 0.36, "ci_upper": 0.68, "beta": 0.41 },
    { "name": "Trust",        "b": 0.31, "se": 0.09, "t": 3.4, "p": 0.0008, "ci_lower": 0.13, "ci_upper": 0.49, "beta": 0.28 },
    { "name": "Ease",         "b": 0.08, "se": 0.07, "t": 1.1, "p": 0.255,  "ci_lower": -0.06, "ci_upper": 0.22, "beta": 0.06 }
  ],
  "context": "Post-purchase survey, SaaS B2B"
}
```

### t-test

```json
{
  "stat_type": "ttest",
  "n": 120,
  "group1_label": "New onboarding",
  "group2_label": "Legacy onboarding",
  "mean_group1": 4.31,
  "mean_group2": 3.74,
  "sd_group1": 0.82,
  "sd_group2": 0.91,
  "t_statistic": 3.87,
  "t_df": 118,
  "p_value": 0.0002,
  "cohens_d": 0.66
}
```

### ANOVA

```json
{
  "stat_type": "anova",
  "n": 180,
  "f_value": 12.4,
  "p_value": 0.00001,
  "eta_squared": 0.12,
  "groups": [
    { "name": "Power users",  "mean": 4.7, "sd": 0.6, "n": 60 },
    { "name": "Casual users", "mean": 3.9, "sd": 0.8, "n": 60 },
    { "name": "New users",    "mean": 3.2, "sd": 1.1, "n": 60 }
  ]
}
```

### Correlation

```json
{
  "stat_type": "correlation",
  "n": 310,
  "var1": "Task completion time",
  "var2": "User frustration score",
  "r": 0.62,
  "p_value": 0.00001
}
```

### Chi-square

```json
{
  "stat_type": "chi_square",
  "n": 420,
  "chi_square": 18.7,
  "chi_df": 2,
  "p_value": 0.00009,
  "cramers_v": 0.21
}
```

---

## Output structure

```json
{
  "stat_type": "regression",
  "significance": "highly_significant",
  "effect_magnitude": "large",
  "headline": "Satisfaction and Trust significantly predicted Willingness to Pay (R² = 0.43).",
  "segments": [
    { "label": "Model overview", "text": "..." },
    { "label": "Model fit",      "text": "..." },
    { "label": "Predictors",     "text": "..." }
  ],
  "plain_summary": "The regression model accounted for 43.0% of variance...",
  "practitioner_takeaway": "Focus product interventions on Satisfaction and Trust...",
  "llm_enhanced": false,
  "llm_narrative": null,
  "warnings": []
}
```

---

## Effect size benchmarks

| Statistic | Negligible | Small | Medium | Large |
|-----------|-----------|-------|--------|-------|
| R²        | < .02     | < .13 | < .26  | ≥ .26 |
| Cohen's d | < .20     | < .50 | < .80  | ≥ .80 |
| r         | < .10     | < .30 | < .50  | ≥ .50 |
| η²        | < .01     | < .06 | < .14  | ≥ .14 |
| Cramér's V| < .10     | < .30 | < .50  | ≥ .50 |

Source: Cohen (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.).

---

## Design principles

**Rule-based core is non-negotiable.** Every narrative is generated entirely from deterministic rules — Cohen benchmarks, APA significance conventions, structured templates. No API key required. The tool works on an air-gapped machine.

**LLM enrichment is community scaffolding, not a shipped feature.** `llm.py` is reference code demonstrating how to wrap the rule-based output with a polished prose pass. It is excluded from CI intentionally. Use it when you need report-ready language rather than structured output.

**Warnings are first-class output.** The tool surfaces methodological issues — small samples, missing effect sizes, borderline p-values — as part of every narrative. Good research communication includes knowing what the numbers cannot tell you.

---

## Part of the CPR Ecosystem

`stat-narrator` is Tool 12 in the [CPR Orbital series](https://github.com/kgkazakos) — 40 open-source Python tools for AI-native product research infrastructure, shipping every Friday.

**Related tools in this series:**

| Tool | What it does |
|------|-------------|
| [`survey-cleaner`](https://github.com/kgkazakos/survey-cleaner) | Removes speeders, straight-liners and gibberish before you run stats |
| [`research-rubric`](https://github.com/kgkazakos/research-rubric) | Evaluates qualitative research quality — saturation, bias, evidence |
| [`insight-differ`](https://github.com/kgkazakos/insight-differ) | Surfaces contradictions and gaps between two research reports |
| [`saturation-meter`](https://github.com/kgkazakos/saturation-meter) | Estimates thematic saturation from coded transcript data |

**Computational Product Research (CPR)** is an independent discipline combining rigorous research methods with AI-native tooling. Learn more at [github.com/kgkazakos](https://github.com/kgkazakos).

---

## Development

```bash
git clone https://github.com/kgkazakos/stat-narrator
cd stat-narrator
pip install -e ".[llm]"
pytest tests/ -v
ruff check statnarrator/
```

---

## License

MIT
