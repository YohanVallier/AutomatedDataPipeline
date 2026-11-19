🌐 **Language / Idioma:** [🇺🇸 English]() | [🇧🇷 Português]()

# Sales and Inventory Consolidation Pipeline

A local CLI automation pipeline that scans an input directory for Excel (`.xlsx`) and CSV (`.csv`) files from different branches, normalizes columns and data types, handles missing values, consolidates everything into a single DataFrame, and generates a formatted Excel report with multiple worksheets — while logging the entire operation to an audit log.

> **Business objective:** eliminate the approximately 8 hours per week spent manually consolidating files with inconsistent formatting, missing values, mismatched columns, and incorrect data types (dates stored as text, currencies containing symbols, etc.).

## Table of Contents

* [Overview](#overview)

* [Features](#features)

* [Project Structure](#project-structure)

* [Requirements](#requirements)

* [Installation](#installation)

* [Configuration](#configuration)

* [Usage](#usage)

* [Input File Format](#input-file-format)

* [Generated Output](#generated-output)

* [Logging and Auditing](#logging-and-auditing)

* [Tests](#tests)

* [Code Quality](#code-quality)

* [CI/CD](#cicd)

* [Troubleshooting](#troubleshooting)

* [License](#license)

* [Contributing](#contributing)

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

## Features

* ✅ Reads `.xlsx` and `.csv` files with automatic delimiter detection.

* ✅ Normalizes column names (accents, spaces, uppercase/lowercase).

* ✅ Robustly converts dates (text → `datetime`) and currency values (text → `float`).

* ✅ Configurable handling of missing values.

* ✅ Vectorized data consolidation (without `iterrows()`).

* ✅ Summary tables: sales by branch and critical stock levels.

* ✅ Multi-worksheet Excel export using `openpyxl`.

* ✅ Structured logging to both file and console.

* ✅ Configuration through environment variables (`.env`).

* ✅ Unit tests with `pytest`.

* ✅ CI/CD with GitHub Actions.

## Project Structure

```
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

## Requirements

* **Python** `>= 3.10`

* Runtime dependencies:

  * `pandas >= 2.0.0`

  * `openpyxl >= 3.1.0`

  * `python-dotenv >= 1.0.0`

* Development dependencies:

  * `pytest >= 7.4.0`

  * `pytest-cov >= 4.1.0`

## Installation

### 1. Clone the repository

```
git clone <repository-url>
cd my-project

```

### 2. Create and activate a virtual environment

```
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

```

### 3. Install the dependencies

Editable installation (recommended for development):

```
pip install -e ".[dev]"

```

Alternatively, install dependencies using `requirements.txt`:

```
pip install -r requirements.txt

```

### 4. Configure environment variables

```
cp .env.example .env

```

Edit the `.env` file as needed (see [Configuration](#configuration)).

## Configuration

All settings are read from environment variables (with `.env` support provided by `python-dotenv`). Default values are defined in `config/settings.py`.

| Variable | Default | Description | 
| ----- | ----- | ----- | 
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

## Usage

### 1. Add the input files

Copy the branches' `.xlsx` and `.csv` files into the `input_data/` directory:

```
mkdir -p input_data
cp /path/to/branches/*.xlsx input_data/
cp /path/to/branches/*.csv input_data/

```

### 2. Run the pipeline

Using the installed entry point:

```
my-project

```

Or directly through the module:

```
python -m my_project.main

```

Alternatively, run the script directly:

```
python src/my_project/main.py

```

### 3. Check the results

* **Excel report:** `output_data/consolidated_report.xlsx`

* **Execution log:** `logs/execution.log`

## Input File Format

Column names may differ between branches. The pipeline automatically normalizes them. Examples of recognized column names:

| Concept | Accepted column name examples | 
| ----- | ----- | 
| Date | `Date`, `DATE`, `sale_date`, `Sale Date` | 
| Branch | `Branch`, `BRANCH`, `Store`, `Unit` | 
| Product | `Product`, `PRODUCT`, `Description`, `Item` | 
| Quantity | `Quantity`, `Qty`, `QTY` | 
| Amount | `Amount`, `Price`, `Total`, `Currency` | 
| Stock | `Stock`, `Current Stock`, `Balance` | 

**Supported data formats:**

* Dates stored as text (`"01/02/2024"`, `"2024-02-01"`) → converted to `datetime`.

* Currency values containing symbols (`"R$ 1.234,56"`) → converted to `float`.

* Missing values (`""`, `"N/A"`, `"null"`) → handled according to the configuration.

## Generated Output

The `output_data/consolidated_report.xlsx` file contains the following worksheets:

| Worksheet | Contents | 
| ----- | ----- | 
| `Consolidated` | All unified and normalized data from every branch. | 
| `SalesByBranch` | Total sales aggregated by branch. | 
| `CriticalStock` | Products with stock levels below the configured threshold. | 

## Logging and Auditing

Every execution is recorded in `logs/execution.log`, including:

* Pipeline start and completion (with timestamps).

* Files found and processed.

* File-level read/parsing errors (without stopping the pipeline).

* Number of consolidated rows.

* Path to the generated report.

Example log entries:

```
2024-02-01 10:15:32,123 - my_project - INFO - Starting consolidation pipeline.
2024-02-01 10:15:32,456 - my_project - INFO - File processed: branch_sp.xlsx (1200 rows).
2024-02-01 10:15:33,789 - my_project - ERROR - Failed to process branch_rj.csv: ...
2024-02-01 10:15:34,012 - my_project - INFO - Report generated at output_data/consolidated_report.xlsx

```

## Tests

Run the test suite:

```
pytest

```

To generate a coverage report:

```
pytest --cov=src/my_project --cov-report=term-missing

```

Tests are located in `tests/` and use fixtures defined in `tests/conftest.py`.

## Code Quality

The project follows these practices:

* **Type hints** for all functions.

* **Google-style docstrings**.

* **Robust error handling** (missing files, parsing failures).

* **Pandas vectorization** (without `iterrows()`).

* **Linting** with `ruff` and **static type checking** with `mypy` (configured in `pyproject.toml`).

Run the quality checks:

```
ruff check src tests
mypy src/my_project

```

## CI/CD

The `.github/workflows/tests.yml` workflow runs automatically on every `push` and `pull_request`:

1. Dependency installation.

2. `ruff` execution (linting).

3. `mypy` execution (type checking).

4. `pytest` execution with coverage.

## Troubleshooting

| Symptom | Likely cause | Solution | 
| ----- | ----- | ----- | 
| `FileNotFoundError` for the input directory | `input_data/` does not exist or is empty. | Create the directory and add input files. | 
| No files processed | Unsupported file extensions. | Use only `.xlsx` or `.csv` files. | 
| Dates not converted | Unrecognized date format. | Check the format used in the source file. | 
| Currency values remain as text | Unmapped symbols. | Adjust the normalization logic in `data_processing.py`. | 
| Log file not generated | No write permission for `logs/`. | Check the directory permissions. | 

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.

## Contributing

1. Fork the repository.

2. Create a branch for your feature (`git checkout -b feature/new-feature`).

3. Commit your changes (`git commit -m 'feat: add new feature'`).

4. Push the branch (`git push origin feature/new-feature`).

5. Open a Pull Request.

See [CHANGELOG.md](CHANGELOG.md) for the version history.

# Pipeline de Consolidação de Vendas e Estoque

Um pipeline local de automação via CLI que varre um diretório de entrada em busca de arquivos Excel (`.xlsx`) e CSV (`.csv`) de diferentes filiais, normaliza colunas e tipos de dados, trata valores ausentes, consolida tudo em um único DataFrame e gera um relatório Excel formatado com múltiplas abas — registrando toda a operação em um log de auditoria.

> **Objetivo de negócio:** eliminar as aproximadamente 8 horas semanais gastas consolidando manualmente arquivos com formatação inconsistente, valores ausentes, colunas divergentes e tipos de dados incorretos (datas armazenadas como texto, moedas contendo símbolos, etc.).

## Índice

* [Visão Geral](#visão-geral)

* [Funcionalidades](#funcionalidades)

* [Estrutura do Projeto](#estrutura-do-projeto)

* [Requisitos](#requisitos)

* [Instalação](#instalação)

* [Configuração](#configuração)

* [Uso](#uso)

* [Formato dos Arquivos de Entrada](#formato-dos-arquivos-de-entrada)

* [Saída Gerada](#saída-gerada)

* [Logs e Auditoria](#logs-e-auditoria)

* [Testes](#testes)

* [Qualidade de Código](#qualidade-de-código)

* [Integração e Entrega Contínua (CI/CD)](#integração-e-entrega-contínua-cicd)

* [Solução de Problemas](#solução-de-problemas)

* [Licença](#licença)

* [Contribuição](#contribuição)

## Visão Geral

O pipeline executa as seguintes etapas, em ordem:

1. **Varredura** do diretório de entrada (`input_data/`) em busca de arquivos `.xlsx` e `.csv`.

2. **Normalização** dos nomes das colunas (letras minúsculas, sem acentos, `snake_case`) e dos tipos de dados (datas padronizadas, valores numéricos limpos de símbolos monetários).

3. **Tratamento de valores ausentes** (preenchimento de valores numéricos com `0`, valores de texto com `UNKNOWN` e remoção de linhas com valores ausentes em colunas críticas).

4. **Consolidação** de todos os dados em um único `DataFrame` unificado.

5. **Geração de tabelas resumo** (Total de Vendas por Filial, Produtos com Níveis Críticos de Estoque).

6. **Exportação** dos resultados para `output_data/` como uma pasta de trabalho Excel formatada com múltiplas abas.

7. **Registro (logging)** de toda a operação em `logs/execution.log`.

O pipeline é **tolerante a falhas**: se o processamento de um arquivo falhar (devido a erro de leitura, erro de parsing, etc.), o erro é registrado no log e o pipeline continua processando o próximo arquivo.

## Funcionalidades

* ✅ Lê arquivos `.xlsx` e `.csv` com detecção automática de delimitador.

* ✅ Normaliza nomes de colunas (acentos, espaços, maiúsculas/minúsculas).

* ✅ Converte datas (texto → `datetime`) e valores monetários (texto → `float`) de forma robusta.

* ✅ Tratamento configurável de valores ausentes.

* ✅ Consolidação vetorizada de dados (sem uso de `iterrows()`).

* ✅ Tabelas resumo: vendas por filial e níveis críticos de estoque.

* ✅ Exportação para Excel com múltiplas abas usando `openpyxl`.

* ✅ Logging estruturado tanto em arquivo quanto no console.

* ✅ Configuração por meio de variáveis de ambiente (`.env`).

* ✅ Testes unitários com `pytest`.

* ✅ CI/CD com GitHub Actions.

## Estrutura do Projeto

```
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

## Requisitos

* **Python** `>= 3.10`

* Dependências de execução:

  * `pandas >= 2.0.0`

  * `openpyxl >= 3.1.0`

  * `python-dotenv >= 1.0.0`

* Dependências de desenvolvimento:

  * `pytest >= 7.4.0`

  * `pytest-cov >= 4.1.0`

## Instalação

### 1. Clonar o repositório

```
git clone <repository-url>
cd my-project

```

### 2. Criar e ativar um ambiente virtual

```
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

```

### 3. Instalar as dependências

Instalação editável (recomendada para desenvolvimento):

```
pip install -e ".[dev]"

```

Alternativamente, instale as dependências usando `requirements.txt`:

```
pip install -r requirements.txt

```

### 4. Configurar variáveis de ambiente

```
cp .env.example .env

```

Edite o arquivo `.env` conforme necessário (veja [Configuração](#configuração)).

## Configuração

Todas as configurações são lidas a partir de variáveis de ambiente (com suporte a `.env` fornecido pelo `python-dotenv`). Os valores padrão são definidos em `config/settings.py`.

| Variável | Padrão | Descrição | 
| ----- | ----- | ----- | 
| `INPUT_DIR` | `input_data` | Diretório varrido em busca de arquivos `.xlsx` e `.csv`. | 
| `OUTPUT_DIR` | `output_data` | Diretório onde o relatório consolidado é salvo. | 
| `OUTPUT_FILENAME` | `consolidated_report.xlsx` | Nome do arquivo Excel gerado. | 
| `LOG_DIR` | `logs` | Diretório onde o arquivo de log é armazenado. | 
| `LOG_FILENAME` | `execution.log` | Nome do arquivo de log. | 
| `LOG_LEVEL` | `INFO` | Nível de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). | 
| `NULL_NUMERIC_FILL_VALUE` | `0` | Valor de preenchimento para dados numéricos ausentes. | 
| `NULL_TEXT_FILL_VALUE` | `UNKNOWN` | Valor de preenchimento para dados de texto ausentes. | 
| `DROP_CRITICAL_NULLS` | `true` | Remove linhas contendo valores ausentes em colunas críticas. | 
| `CRITICAL_STOCK_THRESHOLD` | `10` | Limite abaixo do qual o estoque é considerado crítico. | 
| `SHEET_CONSOLIDATED` | `Consolidated` | Nome da aba contendo os dados consolidados. | 
| `SHEET_SALES_BY_BRANCH` | `SalesByBranch` | Nome da aba contendo as vendas por filial. | 
| `SHEET_CRITICAL_STOCK` | `CriticalStock` | Nome da aba contendo os itens com estoque crítico. | 
| `CONTINUE_ON_ERROR` | `true` | Continua o processamento quando um arquivo falha. | 
| `ENVIRONMENT` | `development` | Nome do ambiente (`development`, `staging`, `production`). | 

> ⚠️ **Nunca** faça commit do seu arquivo `.env` real. Use o `.env.example` apenas como referência.

## Uso

### 1. Adicionar os arquivos de entrada

Copie os arquivos `.xlsx` e `.csv` das filiais para o diretório `input_data/`:

```
mkdir -p input_data
cp /path/to/branches/*.xlsx input_data/
cp /path/to/branches/*.csv input_data/

```

### 2. Executar o pipeline

Usando o ponto de entrada instalado:

```
my-project

```

Ou diretamente através do módulo:

```
python -m my_project.main

```

Alternativamente, execute o script diretamente:

```
python src/my_project/main.py

```

### 3. Verificar os resultados

* **Relatório Excel:** `output_data/consolidated_report.xlsx`

* **Log de execução:** `logs/execution.log`

## Formato dos Arquivos de Entrada

Os nomes das colunas podem variar entre as filiais. O pipeline os normaliza automaticamente. Exemplos de nomes de colunas reconhecidos:

| Conceito | Exemplos de nomes de colunas aceitos | 
| ----- | ----- | 
| Data | `Date`, `DATE`, `sale_date`, `Sale Date` | 
| Filial | `Branch`, `BRANCH`, `Store`, `Unit` | 
| Produto | `Product`, `PRODUCT`, `Description`, `Item` | 
| Quantidade | `Quantity`, `Qty`, `QTY` | 
| Valor | `Amount`, `Price`, `Total`, `Currency` | 
| Estoque | `Stock`, `Current Stock`, `Balance` | 

**Formatos de dados suportados:**

* Datas armazenadas como texto (`"01/02/2024"`, `"2024-02-01"`) → convertidas para `datetime`.

* Valores monetários contendo símbolos (`"R$ 1.234,56"`) → convertidos para `float`.

* Valores ausentes (`""`, `"N/A"`, `"null"`) → tratados de acordo com a configuração.

## Saída Gerada

O arquivo `output_data/consolidated_report.xlsx` contém as seguintes abas:

| Aba | Conteúdo | 
| ----- | ----- | 
| `Consolidated` | Todos os dados unificados e normalizados de cada filial. | 
| `SalesByBranch` | Total de vendas agregado por filial. | 
| `CriticalStock` | Produtos com níveis de estoque abaixo do limite configurado. | 

## Logs e Auditoria

Cada execução é registrada em `logs/execution.log`, incluindo:

* Início e conclusão do pipeline (com timestamps).

* Arquivos encontrados e processados.

* Erros de leitura/parsing em nível de arquivo (sem interromper o pipeline).

* Número de linhas consolidadas.

* Caminho para o relatório gerado.

Exemplo de entradas de log:

```
2024-02-01 10:15:32,123 - my_project - INFO - Starting consolidation pipeline.
2024-02-01 10:15:32,456 - my_project - INFO - File processed: branch_sp.xlsx (1200 rows).
2024-02-01 10:15:33,789 - my_project - ERROR - Failed to process branch_rj.csv: ...
2024-02-01 10:15:34,012 - my_project - INFO - Report generated at output_data/consolidated_report.xlsx

```

## Testes

Execute a suíte de testes:

```
pytest

```

Para gerar um relatório de cobertura:

```
pytest --cov=src/my_project --cov-report=term-missing

```

Os testes estão localizados em `tests/` e utilizam fixtures definidas em `tests/conftest.py`.

## Qualidade de Código

O projeto segue estas práticas:

* **Type hints** para todas as funções.

* **Docstrings no estilo Google**.

* **Tratamento robusto de erros** (arquivos ausentes, falhas de parsing).

* **Vetorização com Pandas** (sem `iterrows()`).

* **Linting** com `ruff` e **verificação estática de tipos** com `mypy` (configurados em `pyproject.toml`).

Execute as verificações de qualidade:

```
ruff check src tests
mypy src/my_project

```

## Integração e Entrega Contínua (CI/CD)

O workflow `.github/workflows/tests.yml` é executado automaticamente a cada `push` e `pull_request`:

1. Instalação de dependências.

2. Execução do `ruff` (linting).

3. Execução do `mypy` (verificação de tipos).

4. Execução do `pytest` com cobertura.

## Solução de Problemas

| Sintoma | Causa provável | Solução | 
| ----- | ----- | ----- | 
| `FileNotFoundError` para o diretório de entrada | `input_data/` não existe ou está vazio. | Crie o diretório e adicione os arquivos de entrada. | 
| Nenhum arquivo processado | Extensões de arquivo não suportadas. | Utilize apenas arquivos `.xlsx` ou `.csv`. | 
| Datas não convertidas | Formato de data não reconhecido. | Verifique o formato utilizado no arquivo de origem. | 
| Valores monetários permanecem como texto | Símbolos não mapeados. | Ajuste a lógica de normalização em `data_processing.py`. | 
| Arquivo de log não gerado | Sem permissão de escrita em `logs/`. | Verifique as permissões do diretório. | 

## Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE) file para mais detalhes.

## Contribuição

1. Faça um fork do repositório.

2. Crie uma branch para sua funcionalidade (`git checkout -b feature/new-feature`).

3. Faça commit das suas alterações (`git commit -m 'feat: add new feature'`).

4. Envie a branch para o repositório remoto (`git push origin feature/new-feature`).

5. Abra um Pull Request.

Veja o [CHANGELOG.md](CHANGELOG.md) para o histórico de versões.