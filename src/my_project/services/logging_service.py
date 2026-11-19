"""Logging configuration for the sales and stock consolidation pipeline.

This module centralizes logging setup for the application. It configures a
root logger that writes to both a rotating file handler (``execution.log``)
and the console, ensuring every pipeline run is auditable.

The public entry point is :func:`setup_logging`, which is idempotent: calling
it multiple times will not duplicate handlers.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Final
import contextlib
from xml.sax import handler


if TYPE_CHECKING:  # pragma: no cover - typing only
    from config.settings import Settings

# Root logger name used across the application.
LOGGER_NAME: Final[str] = "my_project"

# Default log format.
_LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Rotation defaults.
_MAX_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT: Final[int] = 3

# Marker attribute used to detect handlers installed by this module.
_HANDLER_MARKER: Final[str] = "_my_project_handler"


def _resolve_level(level: object) -> int:
    """Resolve a logging level from a string or integer.

    Args:
        level: A level name (e.g. ``"INFO"``) or an integer level.

    Returns:
        The numeric logging level. Falls back to ``logging.INFO`` when the
        value cannot be resolved.
    """
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        resolved = logging.getLevelName(level.strip().upper())
        if isinstance(resolved, int):
            return resolved
    return logging.INFO


def _build_file_handler(log_file: Path, level: int) -> logging.Handler:
    """Create a rotating file handler for the given log file.

    Args:
        log_file: Destination path of the log file.
        level: Numeric logging level for the handler.

    Returns:
        A configured :class:`logging.Handler`.

    Raises:
        OSError: If the log directory cannot be created or the file cannot be
            opened for writing.
        PermissionError: If permission is denied when creating the directory
            or opening the file.
    """
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(
            f"Permissão negada ao criar o diretório de log {log_file.parent}: {exc}"
        ) from exc
    except OSError as exc:
        raise OSError(
            f"Não foi possível criar o diretório de log {log_file.parent}: {exc}"
        ) from exc

    try:
        handler: logging.Handler = RotatingFileHandler(
            log_file,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
    except PermissionError as exc:
        raise PermissionError(
            f"Permissão negada ao abrir o arquivo de log {log_file}: {exc}"
        ) from exc
    except OSError as exc:
        raise OSError(
            f"Não foi possível abrir o arquivo de log {log_file}: {exc}"
        ) from exc

    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    setattr(handler, _HANDLER_MARKER, True)
    return handler


def _build_console_handler(level: int) -> logging.Handler:
    """Create a console (stderr) handler.

    Args:
        level: Numeric logging level for the handler.

    Returns:
        A configured :class:`logging.StreamHandler`.
    """
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    setattr(handler, _HANDLER_MARKER, True)
    return handler


def _clear_managed_handlers(logger: logging.Logger) -> None:
    """Remove handlers previously installed by this module.

    Args:
        logger: The logger whose managed handlers should be removed.
    """
    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
        with contextlib.suppress(Exception):
            handler.close()


def setup_logging(
    settings: Settings | None = None,
    *,
    log_dir: Path | None = None,
    log_filename: str | None = None,
    level: object | None = None,
) -> logging.Logger:
    """Configure application logging for file and console output.

    The function is idempotent: previously installed handlers are removed
    before new ones are attached, so repeated calls do not duplicate output.

    Args:
        settings: Optional application settings providing ``log_dir``,
            ``log_filename`` and ``log_level``. When ``None``, defaults are
            used (``logs/execution.log`` at ``INFO``).
        log_dir: Explicit override for the log directory.
        log_filename: Explicit override for the log file name.
        level: Explicit override for the logging level (name or integer).

    Returns:
        The configured root application logger.

    Raises:
        OSError: If the log directory cannot be created or the log file cannot
            be opened.
        PermissionError: If permission is denied when creating the directory
            or opening the file.
    """
    resolved_dir = Path(
        log_dir if log_dir is not None else getattr(settings, "log_dir", "logs")
    )
    resolved_name = (
        log_filename
        if log_filename is not None
        else getattr(settings, "log_filename", "execution.log")
    )
    resolved_level = _resolve_level(
        level if level is not None else getattr(settings, "log_level", "INFO")
    )

    log_file = resolved_dir / resolved_name

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(resolved_level)
    logger.propagate = False

    _clear_managed_handlers(logger)

    logger.addHandler(_build_file_handler(log_file, resolved_level))
    logger.addHandler(_build_console_handler(resolved_level))

    logger.debug(
        "Logging configurado: arquivo=%s nível=%s",
        log_file,
        logging.getLevelName(resolved_level),
    )
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the application root logger.

    Args:
        name: Optional child logger name. When ``None``, the root application
            logger is returned.

    Returns:
        A :class:`logging.Logger` instance.
    """
    if not name:
        return logging.getLogger(LOGGER_NAME)
    if name.startswith(f"{LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
