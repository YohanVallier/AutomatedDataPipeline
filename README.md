# Sales and Inventory Consolidation Pipeline

A local CLI automation pipeline that scans an input directory for Excel (`.xlsx`) and CSV (`.csv`) files from different branches, normalizes columns and data types, handles missing values, consolidates everything into a single DataFrame, and generates a formatted Excel report with multiple worksheets — while logging the entire operation to an audit log.

> **Business objective:** eliminate the approximately 8 hours per week spent manually consolidating files with inconsistent formatting, missing values, mismatched columns, and incorrect data types (dates stored as text, currencies containing symbols, etc.).

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Input File Format](#input-file-format)
- [Generated Output](#generated-output)
- [Logging and Auditing](#logging-and-auditing)
- [Tests](#tests)
- [Code Quality](#code-quality)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)

---

## Overview

The pipeline performs the following steps, in order:

1. **Scanning** the input directory (`input_data/`) for `.xlsx` and `.csv` files.
2. **Normalization** of column names (lowercase, no accents, `snake_case`) and data types (standardized dates, numeric values cleaned of currency symbols).
3. **Missing-value handling** (filling numeric values with `0`, text values with `UNKNOWN`, and dropping rows with missing values in critical columns).
4. **Consolidation** of all data into a single unified `DataFrame`.
5. **Summary table generation** (Total Sales by Branch, Products with Critical Stock Levels).
6. **Exporting** the results to `output_data/` as a formatted Excel workbook with multiple worksheets.
7. **Logging** the entire operation to `logs/execution.log`.

The pipeline is **fault-tolerant**: if a file fails to process (due to a read error, parsing error, etc.), the error is recorded in the log and the pipeline continues processing the next file.

---

## Features

- ✅ Reads `.xlsx` and `.csv` files with automatic delimiter detection.
- ✅ Normalizes column names (accents, spaces, uppercase/lowercase).
- ✅ Robustly converts dates (text → `datetime`) and currency values (text → `float`).
- ✅ Configurable handling of missing values.
- ✅ Vectorized data consolidation (without `iterrows()`).
- ✅ Summary tables: sales by branch and critical stock levels.
- ✅ Multi-worksheet Excel export using `openpyxl`.
- ✅ Structured logging to both file and console.
- ✅ Configuration through environment variables (`.env`).
- ✅ Unit tests with `pytest`.
- ✅ CI/CD with GitHub Actions.

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── tests.yml
├── config/
│   └── settings.py
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
├── docs/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── data_processing.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── file_service.py
│       │   └── logging_service.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_main.py
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## Requirements

- **Python** `>= 3.10`
- Runtime dependencies:
  - `pandas >= 2.0.0`
  - `openpyxl >= 3.1.0`
  - `python-dotenv >= 1.0.0`
- Development dependencies:
  - `pytest >= 7.4.0`
  - `pytest-cov >= 4.1.0`

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd my-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

Editable installation (recommended for development):

```bash
pip install -e ".[dev]"
```

Alternatively, install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit the `.env` file as needed (see [Configuration](#configuration)).

---

## Configuration

All settings are read from environment variables (with `.env` support provided by `python-dotenv`). Default values are defined in `config/settings.py`.

| Variable | Default | Description |
|---|---|---|
| `INPUT_DIR` | `input_data` | Directory scanned for `.xlsx` and `.csv` files. |
| `OUTPUT_DIR` | `output_data` | Directory where the consolidated report is saved. |
| `OUTPUT_FILENAME` | `consolidated_report.xlsx` | Name of the generated Excel file. |
| `LOG_DIR` | `logs` | Directory where the log file is stored. |
| `LOG_FILENAME` | `execution.log` | Name of the log file. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `NULL_NUMERIC_FILL_VALUE` | `0` | Fill value for missing numeric data. |
| `NULL_TEXT_FILL_VALUE` | `UNKNOWN` | Fill value for missing text data. |
| `DROP_CRITICAL_NULLS` | `true` | Drops rows containing missing values in critical columns. |
| `CRITICAL_STOCK_THRESHOLD` | `10` | Threshold below which inventory is considered critical. |
| `SHEET_CONSOLIDATED` | `Consolidated` | Name of the worksheet containing consolidated data. |
| `SHEET_SALES_BY_BRANCH` | `SalesByBranch` | Name of the worksheet containing sales by branch. |
| `SHEET_CRITICAL_STOCK` | `CriticalStock` | Name of the worksheet containing critical stock items. |
| `CONTINUE_ON_ERROR` | `true` | Continues processing when a file fails. |
| `ENVIRONMENT` | `development` | Environment name (`development`, `staging`, `production`). |

> ⚠️ **Never** commit your actual `.env` file. Use `.env.example` as a reference only.

---

## Usage

### 1. Add the input files

Copy the branches' `.xlsx` and `.csv` files into the `input_data/` directory:

```bash
mkdir -p input_data
cp /path/to/branches/*.xlsx input_data/
cp /path/to/branches/*.csv input_data/
```

### 2. Run the pipeline

Using the installed entry point:

```bash
my-project
```

Or directly through the module:

```bash
python -m my_project.main
```

Alternatively, run the script directly:

```bash
python src/my_project/main.py
```

### 3. Check the results

- **Excel report:** `output_data/consolidated_report.xlsx`
- **Execution log:** `logs/execution.log`

---

## Input File Format

Column names may differ between branches. The pipeline automatically normalizes them. Examples of recognized column names:

| Concept | Accepted column name examples |
|---|---|
| Date | `Date`, `DATE`, `sale_date`, `Sale Date` |
| Branch | `Branch`, `BRANCH`, `Store`, `Unit` |
| Product | `Product`, `PRODUCT`, `Description`, `Item` |
| Quantity | `Quantity`, `Qty`, `QTY` |
| Amount | `Amount`, `Price`, `Total`, `Currency` |
| Stock | `Stock`, `Current Stock`, `Balance` |

**Supported data formats:**

- Dates stored as text (`"01/02/2024"`, `"2024-02-01"`) → converted to `datetime`.
- Currency values containing symbols (`"R$ 1.234,56"`) → converted to `float`.
- Missing values (`""`, `"N/A"`, `"null"`) → handled according to the configuration.

---

## Generated Output

The `output_data/consolidated_report.xlsx` file contains the following worksheets:

| Worksheet | Contents |
|---|---|
| `Consolidated` | All unified and normalized data from every branch. |
| `SalesByBranch` | Total sales aggregated by branch. |
| `CriticalStock` | Products with stock levels below the configured threshold. |

---

## Logging and Auditing

Every execution is recorded in `logs/execution.log`, including:

- Pipeline start and completion (with timestamps).
- Files found and processed.
- File-level read/parsing errors (without stopping the pipeline).
- Number of consolidated rows.
- Path to the generated report.

Example log entries:

```text
2024-02-01 10:15:32,123 - my_project - INFO - Starting consolidation pipeline.
2024-02-01 10:15:32,456 - my_project - INFO - File processed: branch_sp.xlsx (1200 rows).
2024-02-01 10:15:33,789 - my_project - ERROR - Failed to process branch_rj.csv: ...
2024-02-01 10:15:34,012 - my_project - INFO - Report generated at output_data/consolidated_report.xlsx
```

---

## Tests

Run the test suite:

```bash
pytest
```

To generate a coverage report:

```bash
pytest --cov=src/my_project --cov-report=term-missing
```

Tests are located in `tests/` and use fixtures defined in `tests/conftest.py`.

---

## Code Quality

The project follows these practices:

- **Type hints** for all functions.
- **Google-style docstrings**.
- **Robust error handling** (missing files, parsing failures).
- **Pandas vectorization** (without `iterrows()`).
- **Linting** with `ruff` and **static type checking** with `mypy` (configured in `pyproject.toml`).

Run the quality checks:

```bash
ruff check src tests
mypy src/my_project
```

---

## CI/CD

The `.github/workflows/tests.yml` workflow runs automatically on every `push` and `pull_request`:

1. Dependency installation.
2. `ruff` execution (linting).
3. `mypy` execution (type checking).
4. `pytest` execution with coverage.

---

## Troubleshooting

| Symptom | Likely cause | Solution |
|---|---|---|
| `FileNotFoundError` for the input directory | `input_data/` does not exist or is empty. | Create the directory and add input files. |
| No files processed | Unsupported file extensions. | Use only `.xlsx` or `.csv` files. |
| Dates not converted | Unrecognized date format. | Check the format used in the source file. |
| Currency values remain as text | Unmapped symbols. | Adjust the normalization logic in `data_processing.py`. |
| Log file not generated | No write permission for `logs/`. | Check the directory permissions. |

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.

---

## Contributing

1. Fork the repository.
2. Create a branch for your feature (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m 'feat: add new feature'`).
4. Push the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

See [CHANGELOG.md](CHANGELOG.md) for the version history.
