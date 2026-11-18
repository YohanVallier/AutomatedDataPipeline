"""Main entry point for orchestrating the sales and stock consolidation pipeline.

This module wires together the file service, logging service, data processing
core and configuration settings to execute the end-to-end ETL workflow:

1. Scan the input directory for ``.xlsx`` and ``.csv`` files.
2. Read and normalize each file (columns, dtypes, nulls).
3. Consolidate all frames into a single unified ``DataFrame``.
4. Build summary tables (sales by branch, critical stock).
5. Export a multi-sheet Excel report to the output directory.
6. Log every step to ``execution.log`` for auditing.

The pipeline is fault-tolerant: a failure on a single file is logged and the
run continues with the remaining files (configurable via ``CONTINUE_ON_ERROR``).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pandas as pd

from my_project.core.data_processing import (
    build_critical_stock_summary,
    build_sales_by_branch_summary,
    consolidate_frames,
    normalize_dataframe,
)
from my_project.services.file_service import (
    export_report,
    find_input_files,
    read_data_file,
)
from my_project.services.logging_service import setup_logging

if TYPE_CHECKING:  # pragma: no cover - typing only
    from config.settings import Settings

logger = logging.getLogger(__name__)


def _process_single_file(
    file_path: Path,
    settings: "Settings",
) -> Optional[pd.DataFrame]:
    """Read and normalize a single input file.

    Args:
        file_path: Path to the ``.xlsx`` or ``.csv`` file to process.
        settings: Application settings controlling normalization behaviour.

    Returns:
        A normalized ``DataFrame`` on success, or ``None`` if the file could
        not be read or parsed.
    """
    try:
        raw_frame = read_data_file(file_path)
    except FileNotFoundError:
        logger.error("Arquivo não encontrado: %s", file_path)
        return None
    except PermissionError:
        logger.error("Permissão negada ao acessar arquivo: %s", file_path)
        return None
    except (ValueError, OSError) as exc:
        logger.error("Falha ao ler arquivo %s: %s", file_path, exc)
        return None
    except MemoryError:
        logger.error("Memória insuficiente ao processar arquivo: %s", file_path)
        return None
    except Exception as exc:  # noqa: BLE001 - defensive: never crash the pipeline
        logger.exception("Erro inesperado ao ler %s: %s", file_path, exc)
        return None

    if raw_frame is None or raw_frame.empty:
        logger.warning("Arquivo vazio ou sem dados: %s", file_path)
        return None

    try:
        normalized = normalize_dataframe(raw_frame, settings)
    except ValueError as exc:
        logger.warning("Arquivo %s não pôde ser normalizado (vazio ou sem colunas): %s", file_path, exc)
        return None
    except (KeyError, TypeError) as exc:
        logger.error("Falha ao normalizar %s: %s", file_path, exc)
        return None
    except Exception as exc:  # noqa: BLE001 - defensive
        logger.exception("Erro inesperado ao normalizar %s: %s", file_path, exc)
        return None

    logger.info(
        "Arquivo processado: %s (%d linhas).",
        file_path.name,
        len(normalized),
    )
    return normalized


def run_pipeline(settings: Optional["Settings"] = None) -> int:
    """Execute the full consolidation pipeline.

    Args:
        settings: Optional pre-built settings object. When ``None``, settings
            are loaded from environment variables / ``.env``.

    Returns:
        Process exit code: ``0`` on success, ``1`` when no data could be
        consolidated, ``2`` on an unrecoverable error.
    """
    if settings is None:
        from config.settings import load_settings
        settings = load_settings()

    setup_logging(settings)
    logger.info("Iniciando pipeline de consolidação.")

    input_dir = Path(settings.input_dir)
    if not input_dir.exists():
        logger.error("Diretório de entrada não encontrado: %s", input_dir)
        return 2

    try:
        files = find_input_files(input_dir)
    except OSError as exc:
        logger.error("Falha ao varrer diretório %s: %s", input_dir, exc)
        return 2
    except PermissionError as exc:
        logger.error("Permissão negada ao acessar diretório %s: %s", input_dir, exc)
        return 2

    if not files:
        logger.warning("Nenhum arquivo .xlsx ou .csv encontrado em %s.", input_dir)
        return 1

    logger.info("Encontrados %d arquivo(s) para processar.", len(files))

    frames: list[pd.DataFrame] = []
    failures = 0
    for file_path in files:
        frame = _process_single_file(file_path, settings)
        if frame is None:
            failures += 1
            if not settings.continue_on_error:
                logger.error(
                    "Abortando pipeline: falha em %s e CONTINUE_ON_ERROR=false.",
                    file_path.name,
                )
                return 2
            continue
        frames.append(frame)

    if not frames:
        logger.error("Nenhum arquivo pôde ser processado com sucesso.")
        return 1

    try:
        consolidated = consolidate_frames(frames)
    except (ValueError, TypeError) as exc:
        logger.error("Falha ao consolidar dados: %s", exc)
        return 2

    logger.info("Dados consolidados: %d linha(s).", len(consolidated))

    try:
        sales_by_branch = build_sales_by_branch_summary(consolidated)
        critical_stock = build_critical_stock_summary(consolidated, settings)
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Falha ao gerar tabelas resumo: %s", exc)
        return 2

    output_dir = Path(settings.output_dir)
    output_path = output_dir / settings.output_filename

    try:
        export_report(
            output_path=output_path,
            consolidated=consolidated,
            sales_by_branch=sales_by_branch,
            critical_stock=critical_stock,
            settings=settings,
        )
    except OSError as exc:
        logger.error("Falha ao exportar relatório %s: %s", output_path, exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - defensive
        logger.exception("Erro inesperado ao exportar relatório: %s", exc)
        return 2

    logger.info("Relatório gerado em %s", output_path)
    if failures:
        logger.warning(
            "Pipeline concluído com %d arquivo(s) com falha (de %d).",
            failures,
            len(files),
        )
    else:
        logger.info("Pipeline concluído com sucesso.")
    return 0


def main() -> int:
    """CLI entry point for the consolidation pipeline.

    Returns:
        Process exit code (see :func:`run_pipeline`).
    """
    try:
        return run_pipeline()
    except KeyboardInterrupt:
        logger.warning("Execução interrompida pelo usuário.")
        return 130
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        logger.exception("Erro fatal no pipeline: %s", exc)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())