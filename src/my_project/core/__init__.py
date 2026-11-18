"""Core module for the sales and stock consolidation pipeline.

Exposes the data processing operations used by the orchestration layer:
normalization, consolidation and summary table builders.
"""

from __future__ import annotations

from my_project.core.data_processing import (
    build_critical_stock_summary,
    build_sales_by_branch_summary,
    consolidate_frames,
    normalize_dataframe,
)

__all__: list[str] = [
    "build_critical_stock_summary",
    "build_sales_by_branch_summary",
    "consolidate_frames",
    "normalize_dataframe",
]