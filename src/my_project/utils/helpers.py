"""Helper functions used across the sales and stock consolidation pipeline.

This module provides small, dependency-light utilities shared by the core,
services and orchestration layers:

- :func:`ensure_directory` — create a directory (and parents) if missing.
- :func:`slugify` — normalize arbitrary text into a filesystem-safe slug.
- :func:`safe_divide` — division that returns a default on zero denominator.
- :func:`format_currency` — format a numeric value as a Brazilian currency string.
- :func:`chunked` — split an iterable into fixed-size chunks.

All functions are typed, documented in Google style and raise explicit
exceptions where appropriate.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator, Sequence, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Pattern used to collapse non-alphanumeric runs into a single separator.
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it (and parents) when missing.

    Args:
        path: Directory path to create or validate.

    Returns:
        The resolved directory path.

    Raises:
        OSError: If the directory cannot be created.
        NotADirectoryError: If the path exists but is not a directory.
    """
    directory = Path(path)
    if directory.exists():
        if not directory.is_dir():
            raise NotADirectoryError(f"O caminho existe mas não é um diretório: {directory}")
        return directory

    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Não foi possível criar o diretório {directory}: {exc}") from exc

    logger.debug("Diretório criado: %s", directory)
    return directory


def _strip_accents(value: str) -> str:
    """Remove diacritics from a string.

    Args:
        value: Input string.

    Returns:
        The string with combining marks removed.
    """
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify(value: str, *, separator: str = "_") -> str:
    """Convert arbitrary text into a lowercase, filesystem-safe slug.

    Accents are removed, non-alphanumeric characters are collapsed into the
    given separator, and leading/trailing separators are trimmed.

    Args:
        value: Input text to slugify.
        separator: Character used to join words. Defaults to ``"_"``.

    Returns:
        A normalized slug. Returns an empty string when the input contains no
        alphanumeric characters.
    """
    if not isinstance(value, str):
        value = str(value)

    text = _strip_accents(value).strip().lower()
    text = _SLUG_PATTERN.sub(separator, text)
    return text.strip(separator)


def safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """Divide two numbers, returning ``default`` when the denominator is zero.

    Args:
        numerator: The dividend.
        denominator: The divisor.
        default: Value returned when ``denominator`` is zero or non-finite.

    Returns:
        The quotient, or ``default`` when division is not possible.
    """
    try:
        if denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def format_currency(value: float, *, symbol: str = "R$") -> str:
    """Format a numeric value as a Brazilian currency string.

    Args:
        value: Numeric value to format.
        symbol: Currency symbol prefix. Defaults to ``"R$"``.

    Returns:
        A string such as ``"R$ 1.234,56"``. Non-numeric inputs yield
        ``"R$ 0,00"``.
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0

    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")
    return f"{symbol} {formatted}"


def chunked(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """Split a sequence into consecutive chunks of at most ``size`` items.

    Args:
        items: The sequence to split.
        size: Maximum number of items per chunk. Must be positive.

    Yields:
        Slices of ``items`` with length ``<= size``.

    Raises:
        ValueError: If ``size`` is not a positive integer.
    """
    if size <= 0:
        raise ValueError(f"O tamanho do chunk deve ser positivo, recebido: {size}")

    for start in range(0, len(items), size):
        yield items[start : start + size]


def flatten(nested: Iterable[Iterable[T]]) -> list[T]:
    """Flatten one level of nesting from an iterable of iterables.

    Args:
        nested: An iterable whose elements are themselves iterables.

    Returns:
        A flat list containing all inner elements in order.
    """
    return [item for group in nested for item in group]
</｜｜DSML｜｜>