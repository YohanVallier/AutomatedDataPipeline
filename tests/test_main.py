"""Unit tests for the main orchestration module.

These tests exercise :func:`my_project.main.run_pipeline` and the internal
``_process_single_file`` helper using temporary directories and synthetic
input files. They verify the happy path, fault tolerance, and error handling
of the end-to-end pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest

from my_project.main import _process_single_file, main, run_pipeline
from config.settings import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Build a ``Settings`` instance pointing at temporary directories.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        A ``Settings`` instance with isolated input/output/log directories.
    """
    input_dir = tmp_path / "input_data"
    output_dir = tmp_path / "output_data"
    log_dir = tmp_path / "logs"
    input_dir.mkdir()
    output_dir.mkdir()
    log_dir.mkdir()

    return Settings(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        output_filename="consolidated_report.xlsx",
        log_dir=str(log_dir),
        log_filename="execution.log",
        log_level="DEBUG",
        null_numeric_fill_value=0.0,
        null_text_fill_value="UNKNOWN",
        drop_critical_nulls=True,
        critical_stock_threshold=10.0,
        sheet_consolidated="Consolidated",
        sheet_sales_by_branch="SalesByBranch",
        sheet_critical_stock="CriticalStock",
        continue_on_error=True,
        environment="test",
    )


@pytest.fixture()
def sample_csv(settings: Settings) -> Path:
    """Create a valid CSV input file inside the settings input directory.

    Args:
        settings: The active test settings.

    Returns:
        Path to the created CSV file.
    """
    path = Path(settings.input_dir) / "filial_sp.csv"
    frame = pd.DataFrame(
        {
            "Data": ["01/02/2024", "02/02/2024"],
            "Filial": ["SP", "SP"],
            "Produto": ["Caneta", "Lápis"],
            "Quantidade": ["10", "5"],
            "Valor": ["R$ 1.234,56", "R$ 50,00"],
            "Estoque": ["3", "20"],
        }
    )
    frame.to_csv(path, index=False, encoding="utf-8")
    return path


@pytest.fixture()
def sample_xlsx(settings: Settings) -> Path:
    """Create a valid Excel input file inside the settings input directory.

    Args:
        settings: The active test settings.

    Returns:
        Path to the created ``.xlsx`` file.
    """
    path = Path(settings.input_dir) / "filial_rj.xlsx"
    frame = pd.DataFrame(
        {
            "DATA": ["2024-02-01", "2024-02-03"],
            "FILIAL": ["RJ", "RJ"],
            "PRODUTO": ["Borracha", "Régua"],
            "QTD": ["7", "2"],
            "TOTAL": ["100,00", "200,50"],
            "ESTOQUE": ["5", "15"],
        }
    )
    frame.to_excel(path, index=False, engine="openpyxl")
    return path


@pytest.fixture()
def corrupt_csv(settings: Settings) -> Path:
    """Create a CSV file that cannot be parsed (binary garbage).

    Args:
        settings: The active test settings.

    Returns:
        Path to the corrupt file.
    """
    path = Path(settings.input_dir) / "corrupt.csv"
    path.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
    return path


@pytest.fixture()
def empty_csv(settings: Settings) -> Path:
    """Create an empty CSV file.

    Args:
        settings: The active test settings.

    Returns:
        Path to the empty CSV file.
    """
    path = Path(settings.input_dir) / "empty.csv"
    path.write_text("", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _process_single_file
# ---------------------------------------------------------------------------


def test_process_single_file_returns_normalized_frame(
    sample_csv: Path, settings: Settings
) -> None:
    """A valid CSV file is read and normalized into a DataFrame."""
    result = _process_single_file(sample_csv, settings)

    assert result is not None
    assert not result.empty
    assert "filial" in result.columns
    assert "data" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(result["data"])
    assert pd.api.types.is_numeric_dtype(result["valor"])


def test_process_single_file_missing_file_returns_none(
    settings: Settings, tmp_path: Path
) -> None:
    """A missing file is logged and yields ``None``."""
    missing = tmp_path / "does_not_exist.csv"
    assert _process_single_file(missing, settings) is None


def test_process_single_file_corrupt_returns_none(
    corrupt_csv: Path, settings: Settings
) -> None:
    """A corrupt file is logged and yields ``None`` without raising."""
    assert _process_single_file(corrupt_csv, settings) is None


def test_process_single_file_empty_returns_none(
    empty_csv: Path, settings: Settings
) -> None:
    """An empty file is logged and yields ``None``."""
    assert _process_single_file(empty_csv, settings) is None


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------


def test_run_pipeline_success(
    settings: Settings, sample_csv: Path, sample_xlsx: Path
) -> None:
    """The pipeline consolidates valid files and writes the Excel report."""
    exit_code = run_pipeline(settings)

    assert exit_code == 0
    report = Path(settings.output_dir) / settings.output_filename
    assert report.exists()

    sheets = pd.read_excel(report, sheet_name=None, engine="openpyxl")
    assert settings.sheet_consolidated in sheets
    assert settings.sheet_sales_by_branch in sheets
    assert settings.sheet_critical_stock in sheets
    assert len(sheets[settings.sheet_consolidated]) == 4


def test_run_pipeline_missing_input_dir_returns_two(tmp_path: Path) -> None:
    """A missing input directory yields exit code ``2``."""
    settings = Settings(
        input_dir=str(tmp_path / "nope"),
        output_dir=str(tmp_path / "out"),
        log_dir=str(tmp_path / "logs"),
        log_level="DEBUG",
    )
    assert run_pipeline(settings) == 2


def test_run_pipeline_empty_input_dir_returns_one(settings: Settings) -> None:
    """An empty input directory yields exit code ``1``."""
    assert run_pipeline(settings) == 1


def test_run_pipeline_continues_on_error(
    settings: Settings, sample_csv: Path, corrupt_csv: Path
) -> None:
    """A corrupt file does not abort the pipeline when continue_on_error is set."""
    exit_code = run_pipeline(settings)

    assert exit_code == 0
    report = Path(settings.output_dir) / settings.output_filename
    assert report.exists()


def test_run_pipeline_aborts_on_error_when_configured(
    settings: Settings, corrupt_csv: Path
) -> None:
    """When continue_on_error is False, a failure aborts with exit code ``2``."""
    strict = Settings(
        input_dir=settings.input_dir,
        output_dir=settings.output_dir,
        output_filename=settings.output_filename,
        log_dir=settings.log_dir,
        log_filename=settings.log_filename,
        log_level=settings.log_level,
        continue_on_error=False,
    )
    assert run_pipeline(strict) == 2


def test_run_pipeline_writes_log(
    settings: Settings, sample_csv: Path
) -> None:
    """The pipeline writes an execution log file."""
    run_pipeline(settings)
    log_file = Path(settings.log_dir) / settings.log_filename
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Iniciando pipeline" in content


def test_run_pipeline_with_only_empty_files(
    settings: Settings, empty_csv: Path
) -> None:
    """When all files are empty, the pipeline returns exit code ``1`` and logs the event."""
    exit_code = run_pipeline(settings)
    assert exit_code == 1
    
    log_file = Path(settings.log_dir) / settings.log_filename
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Nenhum arquivo pôde ser processado com sucesso" in content


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_returns_int(monkeypatch: pytest.MonkeyPatch) -> None:
    """``main`` returns an integer exit code."""
    monkeypatch.setattr(
        "my_project.main.run_pipeline",
        lambda settings=None: 0,
    )
    assert main() == 0


def test_main_handles_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """``main`` converts ``KeyboardInterrupt`` into exit code ``130``."""

    def _raise(settings: object = None) -> int:
        raise KeyboardInterrupt

    monkeypatch.setattr("my_project.main.run_pipeline", _raise)
    assert main() == 130


def test_main_handles_unexpected_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """``main`` converts unexpected exceptions into exit code ``2``."""

    def _raise(settings: object = None) -> int:
        raise RuntimeError("boom")

    monkeypatch.setattr("my_project.main.run_pipeline", _raise)
    assert main() == 2