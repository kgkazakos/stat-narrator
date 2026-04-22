from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from .models import EffectMagnitude, NarrativeOutput, SignificanceLevel
from .narrator import narrate
from .parser import load_stat_input

console = Console()

_SIG_COLOURS = {
    SignificanceLevel.HIGHLY_SIGNIFICANT: "bold green",
    SignificanceLevel.SIGNIFICANT: "green",
    SignificanceLevel.MARGINAL: "yellow",
    SignificanceLevel.NOT_SIGNIFICANT: "red",
}

_EFFECT_COLOURS = {
    EffectMagnitude.NEGLIGIBLE: "dim",
    EffectMagnitude.SMALL: "cyan",
    EffectMagnitude.MEDIUM: "blue",
    EffectMagnitude.LARGE: "bold magenta",
}


def _render(output: NarrativeOutput, json_out: bool) -> None:
    if json_out:
        click.echo(json.dumps(output.to_dict(), indent=2))
        return

    console.print(Rule(f"[bold]{output.stat_type.value.upper()} NARRATIVE[/bold]"))
    console.print(Panel(f"[bold]{output.headline}[/bold]", expand=False))

    sig_col = _SIG_COLOURS[output.significance]
    eff_col = _EFFECT_COLOURS[output.effect_magnitude]

    meta = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    meta.add_column("Label", style="dim", width=16)
    meta.add_column("Value")
    meta.add_row("Significance", f"[{sig_col}]{output.significance.value}[/{sig_col}]")
    meta.add_row("Effect size", f"[{eff_col}]{output.effect_magnitude.value}[/{eff_col}]")
    console.print(meta)

    for seg in output.segments:
        console.print(f"\n[bold dim]{seg.label}[/bold dim]")
        console.print(seg.text)

    console.print(Rule("Plain summary"))
    console.print(output.plain_summary)

    console.print(Rule("Practitioner takeaway"))
    console.print(f"[bold]{output.practitioner_takeaway}[/bold]")

    if output.llm_narrative:
        console.print(Rule("LLM-enhanced narrative"))
        console.print(output.llm_narrative)

    if output.warnings:
        console.print(Rule("[yellow]Warnings[/yellow]"))
        for w in output.warnings:
            console.print(f"  [yellow]⚠[/yellow]  {w}")


@click.group()
@click.version_option("0.1.0")
def cli() -> None:
    """stat-narrator — translate statistical output into plain-language research narratives."""


@cli.command(name="narrate")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--llm-backend",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default=None,
    help="Optional LLM backend for narrative enrichment.",
)
@click.option("--json-output", is_flag=True, help="Emit JSON instead of rich terminal output.")
def narrate_cmd(input_file: Path, llm_backend: "str | None", json_output: bool) -> None:
    """Narrate a single statistical result from INPUT_FILE (JSON)."""
    try:
        stat = load_stat_input(input_file)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        console.print(f"[red]Failed to parse input:[/red] {exc}")
        sys.exit(1)

    output = narrate(stat)

    if llm_backend:
        from .llm import enrich

        output = enrich(stat, output, llm_backend)

    _render(output, json_output)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--llm-backend",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default=None,
)
@click.option("--json-output", is_flag=True)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Write per-file JSON narratives to this directory.",
)
def batch(
    input_dir: Path,
    llm_backend: "str | None",
    json_output: bool,
    out_dir: "Path | None",
) -> None:
    """Narrate all JSON files found in INPUT_DIR."""
    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        console.print("[yellow]No JSON files found in the specified directory.[/yellow]")
        return

    results: list[tuple[str, NarrativeOutput]] = []
    for fp in json_files:
        try:
            stat = load_stat_input(fp)
            output = narrate(stat)
            if llm_backend:
                from .llm import enrich

                output = enrich(stat, output, llm_backend)
            results.append((fp.name, output))
            if not json_output:
                console.print(f"\n[dim]{fp.name}[/dim]")
                _render(output, json_out=False)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{fp.name}:[/red] {exc}")

    if json_output:
        click.echo(
            json.dumps(
                [{"file": name, **out.to_dict()} for name, out in results], indent=2
            )
        )

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, output in results:
            (out_dir / name).write_text(json.dumps(output.to_dict(), indent=2))
        console.print(
            f"\n[green]✓ Saved {len(results)} narrative(s) to {out_dir}[/green]"
        )
