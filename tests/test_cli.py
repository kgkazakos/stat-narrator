from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from statnarrator.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"


def test_narrate_command_rich():
    runner = CliRunner()
    result = runner.invoke(cli, ["narrate", str(FIXTURES / "regression.json")])
    assert result.exit_code == 0
    assert "REGRESSION NARRATIVE" in result.output


def test_narrate_command_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["narrate", str(FIXTURES / "regression.json"), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stat_type"] == "regression"
    assert "headline" in data
    assert "segments" in data
    assert "practitioner_takeaway" in data


def test_narrate_ttest_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["narrate", str(FIXTURES / "ttest.json"), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stat_type"] == "ttest"
    assert data["significance"] == "highly_significant"


def test_narrate_correlation_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["narrate", str(FIXTURES / "correlation.json"), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stat_type"] == "correlation"


def test_narrate_anova_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["narrate", str(FIXTURES / "anova.json"), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stat_type"] == "anova"


def test_narrate_chi_square_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["narrate", str(FIXTURES / "chi_square.json"), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stat_type"] == "chi_square"


def test_batch_command_json():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["batch", str(FIXTURES), "--json-output"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 3


def test_batch_empty_dir(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["batch", str(tmp_path)])
    assert result.exit_code == 0
    assert "No JSON files" in result.output


def test_batch_out_dir(tmp_path):
    out_dir = tmp_path / "narrated"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["batch", str(FIXTURES), "--json-output", "--out-dir", str(out_dir)],
    )
    assert result.exit_code == 0
    assert out_dir.exists()
    files = list(out_dir.glob("*.json"))
    assert len(files) >= 3


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
