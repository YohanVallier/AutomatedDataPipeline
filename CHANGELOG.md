# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Suporte a arquivos `.xls` (formato legado do Excel).
- Detecção automática de encoding para arquivos CSV.
- Geração de gráficos resumo no relatório Excel.
- Empacotamento em executável standalone (PyInstaller).

## [0.1.0] - 2024-02-01

### Added
- Estrutura inicial do projeto modular seguindo padrões modernos de Python
  (`src/my_project/`, `tests/`, `docs/`, `scripts/`, `data/`, `logs/`, `config/`,
  `.github/workflows/`).
- Pipeline de automação local (CLI) para consolidação de arquivos Excel de vendas e
  estoque de múltiplas filiais.
- Varredura automática do diretório de entrada (`input_data/`) em busca de arquivos
  `.xlsx` e `.csv`.
- Normalização de nomes de colunas (minúsculas, sem acentos, `snake_case`) e de tipos
  de dados (datas padronizadas, valores monetários limpos de símbolos).
- Tratamento configurável de valores nulos (preenchimento com `0` para numéricos,
  `UNKNOWN` para texto, e descarte de linhas com nulos em colunas críticas).
- Consolidação vetorizada de todos os dados em um único `DataFrame` unificado
  (sem uso de `iterrows()`).
- Geração de tabelas resumo:
  - Total de Vendas por Filial.
  - Produtos com Estoque Crítico.
- Exportação do relatório consolidado para `output_data/` como arquivo Excel formatado
  com múltiplas abas (`Consolidated`, `SalesByBranch`, `CriticalStock`) via `openpyxl`.
- Logging estruturado em arquivo (`logs/execution.log`) e console para auditoria.
- Tratamento de erros tolerante a falhas: se um arquivo falhar (leitura, parsing, etc.),
  o erro é registrado no log e o pipeline continua para o próximo arquivo.
- Configuração via variáveis de ambiente com suporte a `.env` (`python-dotenv`).
- Arquivos de boilerplate essenciais:
  - `.gitignore`
  - `.env.example`
  - `pyproject.toml`
  - `requirements.txt`
  - `README.md`
  - `LICENSE` (MIT)
  - `CHANGELOG.md`
- Arquivos `__init__.py` em todos os pacotes Python.
- Testes unitários com `pytest` em `tests/test_main.py` e fixtures em
  `tests/conftest.py`.
- Workflow de CI/CD em `.github/workflows/tests.yml` executando lint (`ruff`),
  tipagem estática (`mypy`) e testes (`pytest` com cobertura).
- Tipagem estática (Type Hints) em todas as funções e Docstrings no estilo Google.
- Arquivos `.gitkeep` para preservar diretórios vazios (`logs/`, `docs/`, `scripts/`,
  `data/raw/`, `data/processed/`).

### Configuration
- Variáveis de ambiente suportadas (com valores padrão definidos em
  `config/settings.py`):
  - `INPUT_DIR`, `OUTPUT_DIR`, `OUTPUT_FILENAME`
  - `LOG_DIR`, `LOG_FILENAME`, `LOG_LEVEL`
  - `NULL_NUMERIC_FILL_VALUE`, `NULL_TEXT_FILL_VALUE`, `DROP_CRITICAL_NULLS`
  - `CRITICAL_STOCK_THRESHOLD`
  - `SHEET_CONSOLIDATED`, `SHEET_SALES_BY_BRANCH`, `SHEET_CRITICAL_STOCK`
  - `CONTINUE_ON_ERROR`, `ENVIRONMENT`

### Dependencies
- Runtime: `pandas>=2.0.0`, `openpyxl>=3.1.0`, `python-dotenv>=1.0.0`.
- Development: `pytest>=7.4.0`, `pytest-cov>=4.1.0`.

[Unreleased]: https://github.com/example/my-project/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/example/my-project/releases/tag/v0.1.0