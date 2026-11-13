"""
LLM enrichment for stat-narrator.

REFERENCE SCAFFOLDING — excluded from CI.

Trigger via ``--llm-backend openai|anthropic|gemini``. All enrichment is
additive: the rule-based narrative is always produced first and returned
regardless of LLM availability. The LLM receives the rule-based output
as context and writes a polished, report-ready prose narrative.
"""
from __future__ import annotations

from .models import NarrativeOutput, StatInput

_SYSTEM_PROMPT = (
    "You are a senior quantitative UX researcher writing a research report. "
    "Your task is to translate statistical findings into clear, evidence-based "
    "narrative prose suitable for a practitioner audience. "
    "Avoid jargon where plain language suffices. "
    "Do not invent numbers, effect sizes, or p-values. "
    "Ground every claim in the statistics provided."
)


def _build_prompt(stat: StatInput, rule_based: NarrativeOutput) -> str:
    segs = "\n".join(f"  [{s.label}] {s.text}" for s in rule_based.segments)
    return (
        f"Statistical type: {stat.stat_type.value}\n"
        f"n = {stat.n}\n"
        + (f"Study context: {stat.context}\n" if stat.context else "")
        + f"\nRule-based interpretation:\n{segs}\n"
        f"\nHeadline: {rule_based.headline}\n"
        f"Significance: {rule_based.significance.value}\n"
        f"Effect magnitude: {rule_based.effect_magnitude.value}\n"
        f"Practitioner takeaway: {rule_based.practitioner_takeaway}\n"
        "\nWrite a 3-paragraph research narrative (120–180 words) that integrates "
        "these findings into flowing, publication-ready prose. "
        "End with one concrete implication for product or design decisions. "
        "Do not use bullet points."
    )


def enrich_openai(stat: StatInput, result: NarrativeOutput) -> NarrativeOutput:
    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(stat, result)},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        result.llm_narrative = response.choices[0].message.content.strip()
        result.llm_enhanced = True
    except Exception as exc:  # noqa: BLE001
        result.warnings.append(f"OpenAI enrichment failed: {exc}")
    return result


def enrich_anthropic(stat: StatInput, result: NarrativeOutput) -> NarrativeOutput:
    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(stat, result)}],
        )
        result.llm_narrative = response.content[0].text.strip()
        result.llm_enhanced = True
    except Exception as exc:  # noqa: BLE001
        result.warnings.append(f"Anthropic enrichment failed: {exc}")
    return result


def enrich_gemini(stat: StatInput, result: NarrativeOutput) -> NarrativeOutput:
    try:
        from google import genai
        from google.genai import types

        client = genai.Client()
        prompt = _SYSTEM_PROMPT + "\n\n" + _build_prompt(stat, result)
        response = client.models.generate_content(
            model="gemini-4-argon",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=400,
                temperature=0.3,
            ),
        )
        result.llm_narrative = response.text.strip()
        result.llm_enhanced = True
    except Exception as exc:  # noqa: BLE001
        result.warnings.append(f"Gemini enrichment failed: {exc}")
    return result


_BACKENDS = {
    "openai": enrich_openai,
    "anthropic": enrich_anthropic,
    "gemini": enrich_gemini,
}


def enrich(stat: StatInput, result: NarrativeOutput, backend: str) -> NarrativeOutput:
    """Enrich *result* with LLM-generated prose using *backend*."""
    fn = _BACKENDS.get(backend)
    if fn is None:
        result.warnings.append(
            f"Unknown LLM backend '{backend}'. Choose from: openai, anthropic, gemini."
        )
        return result
    return fn(stat, result)
