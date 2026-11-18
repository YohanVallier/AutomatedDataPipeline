# My Project — Pipeline de Consolidação de Vendas e Estoque

Pipeline de automação local (CLI) que varre um diretório de entrada em busca de arquivos
Excel (`.xlsx`) e CSV (`.csv`) de diferentes filiais, normaliza colunas e tipos de dados,
trata valores nulos, consolida tudo em um único DataFrame e gera um relatório Excel
formatado com múltiplas abas — registrando toda a operação em um arquivo de log para
auditoria.

> **Objetivo de negócio:** eliminar as ~8 horas semanais gastas na consolidação manual
> de arquivos com formatações inconsistentes, valores nulos, colunas divergentes e
> tipagens incorretas (datas como texto, moedas com símbolos, etc.).

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Formato dos arquivos de entrada](#formato-dos-arquivos-de-entrada)
- [Saída gerada](#saída-gerada)
- [Logs e auditoria](#logs-e-auditoria)
- [Testes](#testes)
- [Qualidade de código](#qualidade-de-código)
- [CI/CD](#cicd)
- [Solução de problemas](#solução-de-problemas)
- [Licença](#licença)

---

## Visão geral

O pipeline executa as seguintes etapas, em ordem:

1. **Varredura** do diretório de entrada (`input_data/`) em busca de arquivos `.xlsx` e `.csv`.
2. **Normalização** dos nomes das colunas (minúsculas, sem acentos, `snake_case`) e dos
   tipos de dados (datas padronizadas, valores numéricos limpos de símbolos de moeda).
3. **Tratamento de nulos** (preenchimento com `0` para numéricos, `UNKNOWN` para texto,
   e descarte de linhas com nulos em colunas críticas).
4. **Consolidação** de todos os dados em um único `DataFrame` unificado.
5. **Geração de tabelas resumo** (Total de Vendas por Filial, Produtos com Estoque Crítico).
6. **Exportação** para `output_data/` como um arquivo Excel formatado com múltiplas abas.
7. **Registro** de toda a operação em `logs/execution.log`.

O processamento é **tolerante a falhas**: se um arquivo falhar (erro de leitura, parsing,
etc.), o erro é registrado no log e o pipeline continua para o próximo arquivo.

---

## Funcionalidades

- ✅ Leitura de arquivos `.xlsx` e `.csv` com detecção automática de separador.
- ✅ Normalização de nomes de colunas (acentos, espaços, maiúsculas/minúsculas).
- ✅ Conversão robusta de datas (texto → `datetime`) e valores monetários (texto → `float`).
- ✅ Tratamento configurável de valores nulos.
- ✅ Consolidação vetorizada (sem `iterrows()`).
- ✅ Tabelas resumo: vendas por filial e estoque crítico.
- ✅ Exportação Excel com múltiplas abas via `openpyxl`.
- ✅ Logging estruturado em arquivo e console.
- ✅ Configuração via variáveis de ambiente (`.env`).
- ✅ Testes unitários com `pytest`.
- ✅ CI/CD com GitHub Actions.

---

## Estrutura do projeto

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

---

## Requisitos

- **Python** `>= 3.10`
- Dependências de runtime:
  - `pandas >= 2.0.0`
  - `openpyxl >= 3.1.0`
  - `python-dotenv >= 1.0.0`
- Dependências de desenvolvimento:
  - `pytest >= 7.4.0`
  - `pytest-cov >= 4.1.0`

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd my-project
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

Instalação em modo editável (recomendado para desenvolvimento):

```bash
pip install -e ".[dev]"
```

Ou, alternativamente, via `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` conforme necessário (veja [Configuração](#configuração)).

---

## Configuração

Todas as configurações são lidas de variáveis de ambiente (com suporte a `.env` via
`python-dotenv`). Os valores padrão estão definidos em `config/settings.py`.

| Variável | Padrão | Descrição |
|---|---|---|
| `INPUT_DIR` | `input_data` | Diretório varrido em busca de arquivos `.xlsx`/`.csv`. |
| `OUTPUT_DIR` | `output_data` | Diretório onde o relatório consolidado é gravado. |
| `OUTPUT_FILENAME` | `consolidated_report.xlsx` | Nome do arquivo Excel gerado. |
| `LOG_DIR` | `logs` | Diretório do arquivo de log. |
| `LOG_FILENAME` | `execution.log` | Nome do arquivo de log. |
| `LOG_LEVEL` | `INFO` | Nível de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `NULL_NUMERIC_FILL_VALUE` | `0` | Valor de preenchimento para nulos numéricos. |
| `NULL_TEXT_FILL_VALUE` | `UNKNOWN` | Valor de preenchimento para nulos textuais. |
| `DROP_CRITICAL_NULLS` | `true` | Descarta linhas com nulos em colunas críticas. |
| `CRITICAL_STOCK_THRESHOLD` | `10` | Limite abaixo do qual o estoque é considerado crítico. |
| `SHEET_CONSOLIDATED` | `Consolidated` | Nome da aba com os dados consolidados. |
| `SHEET_SALES_BY_BRANCH` | `SalesByBranch` | Nome da aba com vendas por filial. |
| `SHEET_CRITICAL_STOCK` | `CriticalStock` | Nome da aba com estoque crítico. |
| `CONTINUE_ON_ERROR` | `true` | Continua o processamento quando um arquivo falha. |
| `ENVIRONMENT` | `development` | Nome do ambiente (`development`, `staging`, `production`). |

> ⚠️ **Nunca** faça commit do arquivo `.env` real. Use apenas o `.env.example` como
> referência.

---

## Uso

### 1. Coloque os arquivos de entrada

Copie os arquivos `.xlsx` e `.csv` das filiais para o diretório `input_data/`:

```bash
mkdir -p input_data
cp /caminho/para/filiais/*.xlsx input_data/
cp /caminho/para/filiais/*.csv  input_data/
```

### 2. Execute o pipeline

Via entry point instalado:

```bash
my-project
```

Ou diretamente pelo módulo:

```bash
python -m my_project.main
```

Ou ainda executando o script:

```bash
python src/my_project/main.py
```

### 3. Verifique os resultados

- **Relatório Excel:** `output_data/consolidated_report.xlsx`
- **Log de execução:** `logs/execution.log`

---

## Formato dos arquivos de entrada

Os arquivos podem ter nomes de colunas divergentes entre filiais. O pipeline normaliza
os nomes automaticamente. Exemplos de colunas reconhecidas:

| Conceito | Exemplos de nomes aceitos |
|---|---|
| Data | `Data`, `DATA`, `data_venda`, `Data Venda` |
| Filial | `Filial`, `FILIAL`, `Loja`, `Unidade` |
| Produto | `Produto`, `PRODUTO`, `Descrição`, `Item` |
| Quantidade | `Quantidade`, `Qtd`, `QTDE` |
| Valor | `Valor`, `Preço`, `Total`, `R$` |
| Estoque | `Estoque`, `Estoque Atual`, `Saldo` |

**Tipos de dados tolerados:**

- Datas como texto (`"01/02/2024"`, `"2024-02-01"`) → convertidas para `datetime`.
- Valores monetários com símbolos (`"R$ 1.234,56"`) → convertidos para `float`.
- Valores nulos (`""`, `"N/A"`, `"null"`) → tratados conforme configuração.

---

## Saída gerada

O arquivo `output_data/consolidated_report.xlsx` contém as seguintes abas:

| Aba | Conteúdo |
|---|---|
| `Consolidated` | Todos os dados unificados e normalizados de todas as filiais. |
| `SalesByBranch` | Total de vendas agregado por filial. |
| `CriticalStock` | Produtos com estoque abaixo do limite configurado. |

---

## Logs e auditoria

Toda a execução é registrada em `logs/execution.log`, incluindo:

- Início e fim do pipeline (com timestamp).
- Arquivos encontrados e processados.
- Erros de leitura/parsing por arquivo (sem interromper o pipeline).
- Contagem de linhas consolidadas.
- Caminho do relatório gerado.

Exemplo de entrada de log:

```
2024-02-01 10:15:32,123 - my_project - INFO - Iniciando pipeline de consolidação.
2024-02-01 10:15:32,456 - my_project - INFO - Arquivo processado: filial_sp.xlsx (1200 linhas).
2024-02-01 10:15:33,789 - my_project - ERROR - Falha ao processar filial_rj.csv: ...
2024-02-01 10:15:34,012 - my_project - INFO - Relatório gerado em output_data/consolidated_report.xlsx
```

---

## Testes

Execute a suíte de testes:

```bash
pytest
```

Com relatório de cobertura:

```bash
pytest --cov=src/my_project --cov-report=term-missing
```

Os testes ficam em `tests/` e utilizam fixtures definidas em `tests/conftest.py`.

---

## Qualidade de código

O projeto adota:

- **Type hints** em todas as funções.
- **Docstrings** no estilo Google.
- **Tratamento de erros** robusto (arquivos ausentes, falhas de parsing).
- **Vetorização** com pandas (sem `iterrows()`).
- **Linting** com `ruff` e **tipagem estática** com `mypy` (configurados em `pyproject.toml`).

Para executar as verificações:

```bash
ruff check src tests
mypy src/my_project
```

---

## CI/CD

O workflow `.github/workflows/tests.yml` executa automaticamente, a cada `push` e
`pull_request`:

1. Instalação das dependências.
2. Execução do `ruff` (lint).
3. Execução do `mypy` (tipagem).
4. Execução do `pytest` com cobertura.

---

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `FileNotFoundError` no diretório de entrada | `input_data/` não existe ou está vazio. | Crie o diretório e adicione arquivos. |
| Nenhum arquivo processado | Extensões não suportadas. | Use apenas `.xlsx` ou `.csv`. |
| Datas não convertidas | Formato não reconhecido. | Verifique o formato no arquivo de origem. |
| Valores monetários como texto | Símbolos não mapeados. | Ajuste a normalização em `data_processing.py`. |
| Log não gerado | Permissão de escrita em `logs/`. | Verifique permissões do diretório. |

---

## Licença

Este projeto está licenciado sob a **MIT License**. Consulte o arquivo [LICENSE](LICENSE)
para mais detalhes.

---

## Contribuição

1. Faça um fork do projeto.
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`).
3. Faça commit das alterações (`git commit -m 'feat: adiciona nova funcionalidade'`).
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`).
5. Abra um Pull Request.

Consulte o [CHANGELOG.md](CHANGELOG.md) para o histórico de versões.