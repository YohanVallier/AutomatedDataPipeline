"""Application configuration for the sales and stock consolidation pipeline.

This module centralizes all runtime configuration. Values are read from
environment variables (optionally loaded from a ``.env`` file via
``python-dotenv``) and exposed through an immutable :class:`Settings`
dataclass. Sensible defaults are applied when a variable is unset.

The public entry point is :func:`load_settings`, which returns a fully
populated :class:`Settings` instance. The module also exposes a module-level
``settings`` object for convenience in scripts and tests.

Example:
    >>> from config.settings import load_settings
    >>> settings = load_settings()
    >>> settings.input_dir
    'input_data'
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Optional

try:  # pragma: no cover - optional dependency guard
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_INPUT_DIR: Final[str] = "input_data"
DEFAULT_OUTPUT_DIR: Final[str] = "output_data"
DEFAULT_OUTPUT_FILENAME: Final[str] = "consolidated_report.xlsx"
DEFAULT_LOG_DIR: Final[str] = "logs"
DEFAULT_LOG_FILENAME: Final[str] = "execution.log"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_NULL_NUMERIC_FILL_VALUE: Final[float] = 0.0
DEFAULT_NULL_TEXT_FILL_VALUE: Final[str] = "UNKNOWN"
DEFAULT_DROP_CRITICAL_NULLS: Final[bool] = True
DEFAULT_CRITICAL_STOCK_THRESHOLD: Final[float] = 10.0
DEFAULT_SHEET_CONSOLIDATED: Final[str] = "Consolidated"
DEFAULT_SHEET_SALES_BY_BRANCH: Final[str] = "SalesByBranch"
DEFAULT_SHEET_CRITICAL_STOCK: Final[str] = "CriticalStock"
DEFAULT_CONTINUE_ON_ERROR: Final[bool] = True
DEFAULT_ENVIRONMENT: Final[str] = "development"

# Truthy string tokens accepted for boolean environment variables.
_TRUE_TOKENS: Final[frozenset[str]] = frozenset({"1", "true", "yes", "y", "on", "sim"})
_FALSE_TOKENS: Final[frozenset[str]] = frozenset({"0", "false", "no", "n", "off", "nao", "não"})


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable, returning ``default`` when unset/blank.

    Args:
        name: Environment variable name.
        default: Fallback value when the variable is missing or empty.

    Returns:
        The stripped value, or ``default``.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped if stripped else default


def _parse_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable.

    Args:
        name: Environment variable name.
        default: Fallback value when the variable is missing or unrecognized.

    Returns:
        The parsed boolean value.
    """
    raw = _get_env(name)
    if raw is None:
        return default
    token = raw.lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    logger.warning(
        "Valor booleano inválido para %s: %r. Usando padrão %s.", name, raw, default
    )
    return default


def _parse_float(name: str, default: float) -> float:
    """Parse a float environment variable.

    Args:
        name: Environment variable name.
        default: Fallback value when the variable is missing or invalid.

    Returns:
        The parsed float value.
    """
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        logger.warning(
            "Valor numérico inválido para %s: %r. Usando padrão %s.", name, raw, default
        )
        return default


def _parse_str(name: str, default: str) -> str:
    """Parse a string environment variable.

    Args:
        name: Environment variable name.
        default: Fallback value when the variable is missing.

    Returns:
        The parsed string value.
    """
    return _get_env(name, default) or default


# ---------------------------------------------------------------------------
# Settings dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    """Immutable application configuration.

    Attributes:
        input_dir: Directory scanned for incoming ``.xlsx``/``.csv`` files.
        output_dir: Directory where the consolidated Excel report is written.
        output_filename: Name of the generated Excel workbook.
        log_dir: Directory where the log file is written.
        log_filename: Name of the log file.
        log_level: Logging level name (e.g. ``"INFO"``).
        null_numeric_fill_value: Fill value for numeric nulls.
        null_text_fill_value: Fill value for textual nulls.
        drop_critical_nulls: Whether to drop rows with nulls in critical columns.
        critical_stock_threshold: Stock level below which stock is critical.
        sheet_consolidated: Sheet name for the consolidated data.
        sheet_sales_by_branch: Sheet name for the sales-by-branch summary.
        sheet_critical_stock: Sheet name for the critical-stock summary.
        continue_on_error: Whether to continue when a single file fails.
        environment: Environment name (``development``, ``staging``, ``production``).
    """

    input_dir: str = DEFAULT_INPUT_DIR
    output_dir: str = DEFAULT_OUTPUT_DIR
    output_filename: str = DEFAULT_OUTPUT_FILENAME
    log_dir: str = DEFAULT_LOG_DIR
    log_filename: str = DEFAULT_LOG_FILENAME
    log_level: str = DEFAULT_LOG_LEVEL
    null_numeric_fill_value: float = DEFAULT_NULL_NUMERIC_FILL_VALUE
    null_text_fill_value: str = DEFAULT_NULL_TEXT_FILL_VALUE
    drop_critical_nulls: bool = DEFAULT_DROP_CRITICAL_NULLS
    critical_stock_threshold: float = DEFAULT_CRITICAL_STOCK_THRESHOLD
    sheet_consolidated: str = DEFAULT_SHEET_CONSOLIDATED
    sheet_sales_by_branch: str = DEFAULT_SHEET_SALES_BY_BRANCH
    sheet_critical_stock: str = DEFAULT_SHEET_CRITICAL_STOCK
    continue_on_error: bool = DEFAULT_CONTINUE_ON_ERROR
    environment: str = DEFAULT_ENVIRONMENT

    @property
    def input_path(self) -> Path:
        """Return the input directory as a :class:`pathlib.Path`."""
        return Path(self.input_dir)

    @property
    def output_path(self) -> Path:
        """Return the output directory as a :class:`pathlib.Path`."""
        return Path(self.output_dir)

    @property
    def log_path(self) -> Path:
        """Return the log directory as a :class:`pathlib.Path`."""
        return Path(self.log_dir)

    @property
    def output_file(self) -> Path:
        """Return the full path of the generated Excel report."""
        return self.output_path / self.output_filename

    @property
    def log_file(self) -> Path:
        """Return the full path of the log file."""
        return self.log_path / self.log_filename


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """Load environment variables from a ``.env`` file when available.

    Args:
        dotenv_path: Optional explicit path to the ``.env`` file. When ``None``,
            ``python-dotenv`` searches the current working directory upward.
    """
    if load_dotenv is None:  # pragma: no cover - dependency missing
        logger.debug("python-dotenv não instalado; usando apenas variáveis de ambiente.")
        return

    try:
        if dotenv_path is not None:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        else:
            load_dotenv(override=False)
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("Falha ao carregar arquivo .env: %s", exc)


def load_settings(dotenv_path: Optional[Path] = None) -> Settings:
    """Build a :class:`Settings` instance from environment variables.

    Args:
        dotenv_path: Optional explicit path to a ``.env`` file. When ``None``,
            ``python-dotenv`` performs its default discovery.

    Returns:
        A fully populated, immutable :class:`Settings` instance.
    """
    _load_dotenv(dotenv_path)

    settings = Settings(
        input_dir=_parse_str("INPUT_DIR", DEFAULT_INPUT_DIR),
        output_dir=_parse_str("OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
        output_filename=_parse_str("OUTPUT_FILENAME", DEFAULT_OUTPUT_FILENAME),
        log_dir=_parse_str("LOG_DIR", DEFAULT_LOG_DIR),
        log_filename=_parse_str("LOG_FILENAME", DEFAULT_LOG_FILENAME),
        log_level=_parse_str("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
        null_numeric_fill_value=_parse_float(
            "NULL_NUMERIC_FILL_VALUE", DEFAULT_NULL_NUMERIC_FILL_VALUE
        ),
        null_text_fill_value=_parse_str("NULL_TEXT_FILL_VALUE", DEFAULT_NULL_TEXT_FILL_VALUE),
        drop_critical_nulls=_parse_bool("DROP_CRITICAL_NULLS", DEFAULT_DROP_CRITICAL_NULLS),
        critical_stock_threshold=_parse_float(
            "CRITICAL_STOCK_THRESHOLD", DEFAULT_CRITICAL_STOCK_THRESHOLD
        ),
        sheet_consolidated=_parse_str("SHEET_CONSOLIDATED", DEFAULT_SHEET_CONSOLIDATED),
        sheet_sales_by_branch=_parse_str(
            "SHEET_SALES_BY_BRANCH", DEFAULT_SHEET_SALES_BY_BRANCH
        ),
        sheet_critical_stock=_parse_str("SHEET_CRITICAL_STOCK", DEFAULT_SHEET_CRITICAL_STOCK),
        continue_on_error=_parse_bool("CONTINUE_ON_ERROR", DEFAULT_CONTINUE_ON_ERROR),
        environment=_parse_str("ENVIRONMENT", DEFAULT_ENVIRONMENT),
    )

    logger.debug("Configurações carregadas: ambiente=%s", settings.environment)
    return settings


# Module-level convenience instance (lazily evaluated at import time).
settings: Settings = load_settings()

__all__: list[str] = [
    "Settings",
    "load_settings",
    "settings",
]