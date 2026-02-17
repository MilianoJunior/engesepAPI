```markdown
# ⚡ ENGESEP API - Monitoramento de Geração

API desenvolvida em **FastAPI** e **Pandas** para monitoramento e cálculo de produção de energia em usinas hidrelétricas. 

A arquitetura utiliza uma camada de abstração via JSON (`config/usinas.json`) para normalizar nomes de colunas e tabelas, permitindo que o código seja agnóstico à estrutura do banco de dados legado.

---

## 📂 Estrutura do Projeto

O projeto segue uma arquitetura modular, separando configuração, lógica de negócio e acesso a dados.

```text
/
├── config/
│   └── usinas.json       # Mapeamento de tabelas, colunas e aliases (Fonte de Verdade)
├── libs/
│   ├── db.py             # Conexão com MySQL e consultas dinâmicas baseadas no JSON
│   ├── calculos.py       # Lógica de negócio (Pandas: Agregações, Filtros, Diff)
│   ├── utils.py          # Utilitários de data e formatação
│   └── usina_model.py    # Modelos Pydantic (Request/Response Schemas)
├── main.py               # Entrypoint da aplicação (Rotas FastAPI)
├── railway.json          # Configuração de deploy (Railway)
└── requirements.txt      # Dependências do projeto

```

---

## ⚙️ Configuração (JSON Abstraction)

A API não possui nomes de colunas *hardcoded*. Toda a tradução do banco de dados para a API é feita no arquivo `config/usinas.json`.

**Exemplo de configuração para Energia:**

```json
"CGH-APARECIDA": {
    "tabelas": ["cgh_aparecida"],
    "energia": {
        "cgh_aparecida": ["acumulador_energia as 'UG-01 Energia Ativa Acumulada'"]
    }
}

```

---

## 🧠 Lógica de Cálculo de Produção (`libs/calculos.py`)

O cálculo de produção **não é uma leitura direta**. Ele deriva a produção a partir de acumuladores brutos, aplicando limpeza de ruído e diferenciação temporal.

### 1. Pipeline de Pré-Processamento

Antes de qualquer cálculo, os dados brutos passam por este tratamento rigoroso:

1. **Merge de Tabelas:** Para usinas com tabelas separadas por Unidade Geradora (ex: PCH Pedras), os dados são unificados usando o `data_hora` como chave.
2. **Filtro de Ruído Baixo:** Registros com acumulador `< 10` são descartados (indica erro de leitura/reset).
3. **Offset (Regra de Negócio):**
* **Apenas CGH Aparecida:** É somado o valor fixo de `9971.39` ao acumulador bruto antes do processamento.


4. **Filtro de Erro de Sensor:** Registros com valor exato de `103.00` são removidos **antes** do agrupamento.

### 2. Algoritmo de Agregação

A produção é calculada pela diferença (`.diff()`) entre o último valor de um período e o último do anterior.

| Período | Lógica de Agrupamento | Método de Seleção |
| --- | --- | --- |
| **Horário ('H')** | `data_hora` arredondada (`floor('h')`) | `.last()` (Último registro da hora) |
| **Diário ('D')** | `data_hora` convertida p/ data (`dt.date`) | `.last()` (Último registro do dia) |
| **Mensal ('M')** | Chave `YYYY-MM` | `.last()` (Último registro do mês) |

> **Nota:** Utilizamos `.last()` porque o acumulador é sempre crescente. O último valor do período representa o total acumulado até aquele momento.

---

## 🚀 Como Rodar Localmente

### Pré-requisitos

* Python 3.10+
* MySQL Database

### 1. Instalação

```bash
# Clone o repositório
git clone <url-do-repo>

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

```

### 2. Variáveis de Ambiente (.env)

Crie um arquivo `.env` na raiz:

```env
MYSQLHOST=localhost
MYSQLUSER=root
MYSQLPASSWORD=sua_senha
MYSQLDATABASE=nome_do_banco
MYSQLPORT=3306
API_TOKEN=seu_token_seguro

```

### 3. Execução

```bash
uvicorn main:app --reload

```

---

## 📡 Endpoints

### `POST /producao-acumulada`

Calcula a geração de energia por período.

**Body:**

```json
{
  "usina": "CGH-APARECIDA",
  "data_inicio": "2025-08-01 00:00",
  "data_fim": "2025-08-02 23:59",
  "periodo": "D"  // Opções: "H" (Hora), "D" (Dia), "M" (Mês)
}

```

**Response:**

```json
{
  "usina": "CGH-APARECIDA",
  "periodo": "D",
  "resultado": [
    {
      "data": "2025-08-01",
      "prod_UG-01 Energia Ativa Acumulada": 12.5
    },
    {
      "data": "2025-08-02",
      "prod_UG-01 Energia Ativa Acumulada": 11.8
    }
  ]
}

```

---

## 🛠 Stack Tecnológico

* **FastAPI**: Framework web de alta performance.
* **Pandas**: Manipulação de séries temporais e DataFrames.
* **MySQL Connector/SQLAlchemy**: Conexão com banco de dados.
* **Pydantic**: Validação de dados e serialização.

```

```