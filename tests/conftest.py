"""Pytest configuration and shared fixtures for the test suite.

This module defines reusable fixtures used across the test suite:

- ``project_root`` — the repository root directory.
- ``settings`` — an isolated :class:`Settings` instance backed by temporary
  directories (input, output and log).
- ``sample_csv`` — a valid CSV input file with Brazilian-formatted values.
- ``sample_xlsx`` — a valid Excel input file with divergent column names.
- ``corrupt_csv`` — a binary file that cannot be parsed as CSV.
- ``sample_frames`` — a list of normalized ``DataFrame`` objects for core tests.
- ``caplog_handler`` — a helper that captures log records for assertions.

Fixtures are intentionally scoped to ``function`` so each test runs in a clean
environment and never leaks state between tests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, List

import pandas as pd
import pytest

from config.settings import Settings

# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_root() -> Path:
    """Return the repository root directory.

    Returns:
        The absolute path to the project root (parent of ``tests/``).
    """
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Settings fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Build an isolated :class:`Settings` instance for a single test.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        A ``Settings`` instance whose input, output and log directories live
        under ``tmp_path`` and are pre-created.
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


# ---------------------------------------------------------------------------
# Input file fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_csv(settings: Settings) -> Path:
    """Create a valid CSV input file with Brazilian-formatted values.

    Args:
        settings: The active test settings.

    Returns:
        Path to the created ``.csv`` file.
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
    """Create a valid Excel input file with divergent column names.

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


# ---------------------------------------------------------------------------
# DataFrame fixtures for core tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_frames() -> List[pd.DataFrame]:
    """Return a list of normalized ``DataFrame`` objects for core tests.

    Returns:
        Two small frames sharing the canonical schema used by the pipeline.
    """
    first = pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-02-01", "2024-02-02"]),
            "filial": ["SP", "SP"],
            "produto": ["Caneta", "Lápis"],
            "quantidade": [10.0, 5.0],
            "valor": [1234.56, 50.0],
            "estoque": [3.0, 20.0],
        }
    )
    second = pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-02-03"]),
            "filial": ["RJ"],
            "produto": ["Borracha"],
            "quantidade": [7.0],
            "valor": [100.0],
            "estoque": [5.0],
        }
    )
    return [first, second]


# ---------------------------------------------------------------------------
# Logging fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def caplog_handler() -> Iterator[logging.Handler]:
    """Attach an in-memory handler to the application logger.

    Yields:
        A :class:`logging.Handler` whose records can be inspected via
        ``handler.records`` (attached dynamically).
    """
    logger = logging.getLogger("my_project")
    handler = logging.Handler()
    records: list[logging.LogRecord] = []
    handler.emit = records.append  # type: ignore[method-assign]
    setattr(handler, "records", records)

    previous_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
