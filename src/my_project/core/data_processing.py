"""Data processing operations for the sales and stock consolidation pipeline.

This module implements the core ETL transformations:

- Column name normalization (lowercase, accent-free, ``snake_case``).
- Data type normalization (dates, numeric/currency values).
- Null handling (numeric fill, text fill, critical-row dropping).
- Consolidation of multiple frames into a single unified ``DataFrame``.
- Summary table builders (sales by branch, critical stock).

All operations are vectorized with pandas; ``iterrows()`` is never used.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Any, Iterable, Optional

import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - typing only
    from config.settings import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

# Canonical column names used across the pipeline.
COL_DATE = "data"
COL_BRANCH = "filial"
COL_PRODUCT = "produto"
COL_QUANTITY = "quantidade"
COL_VALUE = "valor"
COL_STOCK = "estoque"

# Aliases (already normalized) mapped to canonical names.
_COLUMN_ALIASES: dict[str, str] = {
    # date
    "data": COL_DATE,
    "data_venda": COL_DATE,
    "data_da_venda": COL_DATE,
    "dt": COL_DATE,
    "date": COL_DATE,
    # branch
    "filial": COL_BRANCH,
    "loja": COL_BRANCH,
    "unidade": COL_BRANCH,
    "branch": COL_BRANCH,
    "store": COL_BRANCH,
    # product
    "produto": COL_PRODUCT,
    "descricao": COL_PRODUCT,
    "descricao_produto": COL_PRODUCT,
    "item": COL_PRODUCT,
    "product": COL_PRODUCT,
    # quantity
    "quantidade": COL_QUANTITY,
    "qtd": COL_QUANTITY,
    "qtde": COL_QUANTITY,
    "qty": COL_QUANTITY,
    "quantity": COL_QUANTITY,
    # value
    "valor": COL_VALUE,
    "preco": COL_VALUE,
    "preco_unitario": COL_VALUE,
    "total": COL_VALUE,
    "valor_total": COL_VALUE,
    "value": COL_VALUE,
    "price": COL_VALUE,
    # stock
    "estoque": COL_STOCK,
    "estoque_atual": COL_STOCK,
    "saldo": COL_STOCK,
    "stock": COL_STOCK,
}

# Columns that must not be null; rows with nulls here are dropped when enabled.
_CRITICAL_COLUMNS: tuple[str, ...] = (COL_DATE, COL_BRANCH)

# Columns treated as numeric.
_NUMERIC_COLUMNS: tuple[str, ...] = (COL_QUANTITY, COL_VALUE, COL_STOCK)

# Columns treated as text.
_TEXT_COLUMNS: tuple[str, ...] = (COL_BRANCH, COL_PRODUCT)

# Currency / thousands separators stripped from numeric strings.
_CURRENCY_PATTERN = re.compile(r"[R$\s\u00a0]")
_NULL_TOKENS = {"", "n/a", "na", "null", "none", "nan", "-", "--"}


def _strip_accents(value: str) -> str:
    """Remove diacritics from a string.

    Args:
        value: Input string.

    Returns:
        The string with combining marks removed.
    """
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_column_name(name: Any) -> str:
    """Normalize a single column name to ``snake_case`` without accents.

    Args:
        name: Raw column name (any type; coerced to ``str``).

    Returns:
        A lowercase, accent-free, underscore-separated column name.
    """
    text = _strip_accents(str(name)).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all column names and map known aliases to canonical names.

    Args:
        df: Input ``DataFrame``.

    Returns:
        A new ``DataFrame`` with normalized column names.
    """
    renamed = {col: normalize_column_name(col) for col in df.columns}
    result = df.rename(columns=renamed)
    result = result.rename(columns={k: v for k, v in _COLUMN_ALIASES.items() if k in result.columns})
    # Collapse duplicate columns produced by alias mapping (keep first).
    if result.columns.duplicated().any():
        result = result.loc[:, ~result.columns.duplicated()]
    return result


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    """Convert a series of possibly-formatted numeric strings to floats.

    Handles currency symbols, thousands separators and both ``1.234,56`` and
    ``1,234.56`` conventions. Validates and handles unexpected characters.

    Args:
        series: Input series (object or numeric dtype).

    Returns:
        A float series with unparseable values coerced to ``NaN``.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype("float64")

    text = series.astype("string").str.strip()
    # Strip all currency symbols and whitespace
    text = text.str.replace(_CURRENCY_PATTERN, "", regex=True)
    text = text.mask(text.str.lower().isin(_NULL_TOKENS))

    # Remove any remaining non-numeric characters except separators
    text = text.str.replace(r"[^0-9.,]", "", regex=True)

    # Decide decimal separator per value: if both present, the last one wins.
    has_comma = text.str.contains(",", regex=False, na=False)
    has_dot = text.str.contains(".", regex=False, na=False)

    both = has_comma & has_dot
    comma_last = both & (text.str.rfind(",") > text.str.rfind("."))
    dot_last = both & ~comma_last

    # Both separators: drop the thousands separator, keep the decimal one.
    text = text.where(~comma_last, text.str.replace(".", "", regex=False))
    text = text.where(~dot_last, text.str.replace(",", "", regex=False))
    text = text.where(~comma_last, text.str.replace(",", ".", regex=False))

    # Only comma present: treat as decimal separator.
    only_comma = has_comma & ~has_dot
    text = text.where(~only_comma, text.str.replace(",", ".", regex=False))

    return pd.to_numeric(text, errors="coerce").astype("float64")


def _clean_date_series(series: pd.Series) -> pd.Series:
    """Convert a series of possibly-textual dates to ``datetime64``.

    Args:
        series: Input series.

    Returns:
        A ``datetime64[ns]`` series with unparseable values coerced to ``NaT``.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    text = series.astype("string").str.strip()
    text = text.mask(text.str.lower().isin(_NULL_TOKENS))

    # Try day-first (Brazilian) parsing first, then fall back to default.
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True, format="mixed")
    fallback = pd.to_datetime(text, errors="coerce", format="mixed")
    return parsed.fillna(fallback)


def normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize data types for known canonical columns.

    Args:
        df: Input ``DataFrame`` with normalized column names.

    Returns:
        A new ``DataFrame`` with dates as ``datetime64`` and numeric columns as
        ``float64``.
    """
    result = df.copy()

    if COL_DATE in result.columns:
        result[COL_DATE] = _clean_date_series(result[COL_DATE])

    for column in _NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = _clean_numeric_series(result[column])

    for column in _TEXT_COLUMNS:
        if column in result.columns:
            result[column] = result[column].astype("string").str.strip()

    return result


# ---------------------------------------------------------------------------
# Null handling
# ---------------------------------------------------------------------------


def handle_nulls(df: pd.DataFrame, settings: "Settings") -> pd.DataFrame:
    """Apply null-handling rules configured in ``settings``.

    Args:
        df: Input ``DataFrame`` with normalized columns and dtypes.
        settings: Application settings providing fill values and flags.

    Returns:
        A new ``DataFrame`` with nulls handled.
    """
    result = df.copy()

    if getattr(settings, "drop_critical_nulls", True):
        critical = [col for col in _CRITICAL_COLUMNS if col in result.columns]
        if critical:
            before = len(result)
            result = result.dropna(subset=critical)
            dropped = before - len(result)
            if dropped:
                logger.info("Descartadas %d linha(s) com nulos em colunas críticas.", dropped)

    numeric_fill = getattr(settings, "null_numeric_fill_value", 0)
    text_fill = getattr(settings, "null_text_fill_value", "UNKNOWN")

    for column in _NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = result[column].fillna(numeric_fill)

    for column in _TEXT_COLUMNS:
        if column in result.columns:
            result[column] = result[column].fillna(text_fill)

    return result


# ---------------------------------------------------------------------------
# Public normalization entry point
# ---------------------------------------------------------------------------


def normalize_dataframe(df: pd.DataFrame, settings: "Settings") -> pd.DataFrame:
    """Normalize a raw input frame end-to-end.

    Applies column-name normalization, dtype normalization and null handling.

    Args:
        df: Raw ``DataFrame`` read from an input file.
        settings: Application settings controlling null handling.

    Returns:
        A normalized ``DataFrame``. Returns an empty ``DataFrame`` with no
        columns if the input is empty or has no columns (logged as warning).

    Raises:
        ValueError: If the input frame is None.
    """
    if df is None:
        raise ValueError("DataFrame de entrada é None.")

    if df.empty or len(df.columns) == 0:
        logger.warning("DataFrame de entrada vazio ou sem colunas; retornando vazio.")
        return pd.DataFrame()

    result = normalize_columns(df)
    result = normalize_dtypes(result)
    result = handle_nulls(result, settings)
    return result.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------


def consolidate_frames(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate multiple normalized frames into a single ``DataFrame``.

    Args:
        frames: Iterable of normalized ``DataFrame`` objects.

    Returns:
        A unified ``DataFrame`` with a reset index.

    Raises:
        ValueError: If no non-empty frames are provided.
    """
    valid = [frame for frame in frames if frame is not None and not frame.empty]
    if not valid:
        raise ValueError("Nenhum DataFrame válido para consolidar.")

    consolidated = pd.concat(valid, ignore_index=True, sort=False)
    return consolidated.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------


def build_sales_by_branch_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total sales value and quantity per branch.

    Args:
        df: Consolidated ``DataFrame``.

    Returns:
        A ``DataFrame`` with columns ``filial``, ``total_vendas`` and
        ``total_quantidade``, sorted by ``total_vendas`` descending.

    Raises:
        KeyError: If the ``filial`` column is missing.
    """
    if COL_BRANCH not in df.columns:
        raise KeyError(f"Coluna obrigatória ausente: {COL_BRANCH}")

    aggregations: dict[str, str] = {}
    if COL_VALUE in df.columns:
        aggregations[COL_VALUE] = "sum"
    if COL_QUANTITY in df.columns:
        aggregations[COL_QUANTITY] = "sum"

    if not aggregations:
        raise KeyError("Nenhuma coluna de valor ou quantidade disponível para resumo.")

    summary = df.groupby(COL_BRANCH, dropna=False).agg(aggregations).reset_index()
    summary = summary.rename(
        columns={
            COL_VALUE: "total_vendas",
            COL_QUANTITY: "total_quantidade",
        }
    )

    if "total_vendas" in summary.columns:
        summary = summary.sort_values("total_vendas", ascending=False, kind="stable")

    return summary.reset_index(drop=True)


def build_critical_stock_summary(df: pd.DataFrame, settings: "Settings") -> pd.DataFrame:
    """Identify products whose stock is below the configured threshold.

    Args:
        df: Consolidated ``DataFrame``.
        settings: Application settings providing ``critical_stock_threshold``.

    Returns:
        A ``DataFrame`` of products with critical stock, sorted ascending by
        stock level.

    Raises:
        KeyError: If the ``estoque`` column is missing.
    """
    if COL_STOCK not in df.columns:
        raise KeyError(f"Coluna obrigatória ausente: {COL_STOCK}")

    threshold = getattr(settings, "critical_stock_threshold", 10)

    columns = [col for col in (COL_BRANCH, COL_PRODUCT, COL_STOCK) if col in df.columns]
    critical = df.loc[df[COL_STOCK] < threshold, columns].copy()

    if COL_PRODUCT in critical.columns:
        critical = critical.sort_values(COL_STOCK, ascending=True, kind="stable")

    return critical.reset_index(drop=True)