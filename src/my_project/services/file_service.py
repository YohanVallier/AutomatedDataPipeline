"""File operations for the sales and stock consolidation pipeline.

This module is responsible for all filesystem interactions:

- Scanning the input directory for supported ``.xlsx`` and ``.csv`` files.
- Reading individual data files into ``pandas`` DataFrames with robust
  error handling (missing files, parsing errors, empty files).
- Exporting the consolidated report and summary tables to a formatted,
  multi-sheet Excel workbook via ``openpyxl``.

All functions raise explicit, well-typed exceptions so the orchestration
layer can log failures and continue with the remaining files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - typing only
    from config.settings import Settings

logger = logging.getLogger(__name__)

# Supported input file extensions (lowercase).
SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".xlsx", ".csv")

# CSV encodings attempted in order when reading a file.
_CSV_ENCODINGS: Final[tuple[str, ...]] = ("utf-8", "utf-8-sig", "latin-1")

# Excel engine used for both reading and writing.
_EXCEL_ENGINE: Final[str] = "openpyxl"


def find_input_files(input_dir: Path) -> list[Path]:
    """Scan a directory for supported input files.

    Args:
        input_dir: Directory to scan for ``.xlsx`` and ``.csv`` files.

    Returns:
        A sorted list of file paths with supported extensions.

    Raises:
        FileNotFoundError: If ``input_dir`` does not exist or is not a directory.
        PermissionError: If the directory cannot be read due to permissions.
        OSError: If the directory cannot be read.
    """
    directory = Path(input_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Diretório de entrada não encontrado: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"O caminho não é um diretório: {directory}")

    files: list[Path] = []
    try:
        for entry in directory.iterdir():
            if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(entry)
    except PermissionError as exc:
        raise PermissionError(f"Permissão negada ao acessar {directory}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Erro ao varrer diretório {directory}: {exc}") from exc

    files.sort(key=lambda path: path.name.lower())
    logger.debug("Encontrados %d arquivo(s) em %s.", len(files), directory)
    return files


def _read_csv(file_path: Path) -> pd.DataFrame:
    """Read a CSV file trying multiple encodings and separator detection.

    Args:
        file_path: Path to the ``.csv`` file.

    Returns:
        The parsed ``DataFrame``.

    Raises:
        ValueError: If the file cannot be parsed with any supported encoding.
        MemoryError: If the file is too large to fit in memory.
    """
    last_error: Exception | None = None
    for encoding in _CSV_ENCODINGS:
        try:
            frame = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=None,
                engine="python",
                dtype=str,
                keep_default_na=True,
            )
            # Check if the file has only headers and no data rows
            if frame.empty:
                logger.warning(
                    "Arquivo CSV %s contém apenas cabeçalhos, sem dados.",
                    file_path.name,
                )
                return frame
            return frame
        except MemoryError as exc:
            raise MemoryError(
                f"Memória insuficiente ao ler o arquivo CSV {file_path.name}: {exc}"
            ) from exc
        except UnicodeDecodeError as exc:
            last_error = exc
            logger.debug(
                "Falha de decodificação com encoding %s em %s: %s",
                encoding,
                file_path.name,
                exc,
            )
            continue
        except pd.errors.EmptyDataError as exc:
            raise ValueError(f"Arquivo CSV vazio: {file_path.name}") from exc
        except pd.errors.ParserError as exc:
            raise ValueError(f"Erro de parsing no CSV {file_path.name}: {exc}") from exc

    raise ValueError(
        f"Não foi possível decodificar o CSV {file_path.name}: {last_error}"
    )


def _read_excel(file_path: Path) -> pd.DataFrame:
    """Read an Excel (``.xlsx``) file.

    Args:
        file_path: Path to the ``.xlsx`` file.

    Returns:
        The parsed ``DataFrame``.

    Raises:
        ValueError: If the file cannot be parsed.
        MemoryError: If the file is too large to fit in memory.
        OSError: If the file cannot be read from disk.
    """
    try:
        return pd.read_excel(file_path, engine=_EXCEL_ENGINE, dtype=str)
    except MemoryError as exc:
        raise MemoryError(
            f"Memória insuficiente ao ler o arquivo Excel {file_path.name}: {exc}"
        ) from exc
    except ValueError as exc:
        raise ValueError(f"Erro de parsing no Excel {file_path.name}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Erro de I/O ao ler {file_path.name}: {exc}") from exc


def read_data_file(file_path: Path) -> pd.DataFrame:
    """Read a single supported data file into a ``DataFrame``.

    Dispatches to the appropriate reader based on the file extension.

    Args:
        file_path: Path to a ``.xlsx`` or ``.csv`` file.

    Returns:
        The parsed ``DataFrame`` (all columns as ``str`` for downstream
        normalization).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the extension is unsupported or parsing fails.
        MemoryError: If the file is too large to fit in memory.
        OSError: If the file cannot be read from disk.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    if not path.is_file():
        raise ValueError(f"O caminho não é um arquivo: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".xlsx":
        return _read_excel(path)

    raise ValueError(
        f"Extensão não suportada: '{suffix}' (esperado: {', '.join(SUPPORTED_EXTENSIONS)})."
    )


def _autofit_columns(writer: pd.ExcelWriter, sheet_name: str, frame: pd.DataFrame) -> None:
    """Adjust column widths of a worksheet to fit its content.

    Args:
        writer: Active ``pandas`` Excel writer.
        sheet_name: Name of the worksheet to adjust.
        frame: ``DataFrame`` written to the worksheet.
    """
    try:
        worksheet = writer.sheets[sheet_name]
    except KeyError:  # pragma: no cover - defensive
        return

    for index, column in enumerate(frame.columns, start=1):
        header_length = len(str(column))
        if frame.empty:
            content_length = 0
        else:
            content_length = int(frame[column].astype(str).str.len().max() or 0)
        width = max(header_length, content_length) + 2
        letter = worksheet.cell(row=1, column=index).column_letter
        worksheet.column_dimensions[letter].width = min(width, 60)


def export_report(
    output_path: Path,
    consolidated: pd.DataFrame,
    sales_by_branch: pd.DataFrame,
    critical_stock: pd.DataFrame,
    settings: "Settings",
) -> Path:
    """Export the consolidated data and summaries to a multi-sheet Excel file.

    Args:
        output_path: Destination path for the ``.xlsx`` report.
        consolidated: Unified ``DataFrame`` with all normalized records.
        sales_by_branch: Summary of total sales per branch.
        critical_stock: Summary of products with critical stock.
        settings: Application settings providing sheet names.

    Returns:
        The path of the written report.

    Raises:
        OSError: If the output directory cannot be created or the file cannot
            be written.
        ValueError: If the report cannot be serialized.
    """
    destination = Path(output_path)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"Não foi possível criar o diretório de saída {destination.parent}: {exc}"
        ) from exc

    sheet_consolidated = getattr(settings, "sheet_consolidated", "Consolidated")
    sheet_sales = getattr(settings, "sheet_sales_by_branch", "SalesByBranch")
    sheet_stock = getattr(settings, "sheet_critical_stock", "CriticalStock")

    sheets: list[tuple[str, pd.DataFrame]] = [
        (sheet_consolidated, consolidated),
        (sheet_sales, sales_by_branch),
        (sheet_stock, critical_stock),
    ]

    try:
        with pd.ExcelWriter(destination, engine=_EXCEL_ENGINE) as writer:
            for sheet_name, frame in sheets:
                try:
                    frame.to_excel(writer, sheet_name=sheet_name, index=False)
                    _autofit_columns(writer, sheet_name, frame)
                except (OSError, ValueError, TypeError) as exc:
                    logger.error(
                        "Falha ao escrever a aba %s no relatório %s: %s",
                        sheet_name,
                        destination,
                        exc,
                    )
                    raise
    except OSError as exc:
        raise OSError(f"Falha ao escrever o relatório {destination}: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Falha ao serializar o relatório {destination}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - defensive
        raise OSError(
            f"Erro inesperado ao exportar o relatório {destination}: {exc}"
        ) from exc

    logger.info("Relatório Excel exportado para %s.", destination)
    return destination