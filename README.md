# ⚡ ENGESEP API - Monitoramento de Geração

API desenvolvida em **FastAPI** e **Pandas** para monitoramento e cálculo de produção de energia em usinas hidrelétricas.

A arquitetura utiliza uma camada de abstração via JSON (`config/usinas.json`) para normalizar nomes de colunas e tabelas, permitindo que o código seja agnóstico à estrutura do banco de dados legado.

---

## 📂 Estrutura do Projeto

```text
/
├── config/
│   └── usinas.json                # Mapeamento de tabelas, colunas e aliases
├── libs/
│   ├── db.py                      # Conexão MySQL e queries dinâmicas
│   ├── usina_model.py             # UsinaModel (consulta energia) + USINAS_CONFIG
│   ├── telemetria_model.py        # TelemetriaModel (consulta sensor/grupo bruto)
│   ├── processador_telemetria.py  # Filtro outliers (IQR) + resolução automática
│   ├── calculos.py                # Cálculo de produção de energia
│   ├── cache_store.py             # Cache em memória com TTL
│   └── utils.py                   # Utilitários de data e formatação
├── teste/
│   ├── test_telemetria_model.py   # Fase 1: testes do TelemetriaModel
│   ├── test_telemetria_fase2.py   # Fase 2: testes outliers + resolução
│   ├── test_api_fase3.py          # Fase 3: testes das rotas HTTP
│   ├── visualizar_sensores.py     # Streamlit: visualização Fase 1
│   └── visualizar_fase2.py        # Streamlit: visualização Fase 2 (Plotly)
├── main.py                        # Entrypoint (rotas FastAPI)
├── railway.json                   # Deploy Railway
└── requirements.txt               # Dependências
```

---

## 🏗️ Arquitetura

```
┌────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│   main.py      │     │  TelemetriaModel      │     │  ProcessadorTelemetria  │
│  (Rotas API)   │────▶│  (Consulta bruta)     │────▶│  (Outliers + Resample) │
└────────────────┘     └──────────────────────┘     └────────────────────────┘
        │                                                        │
        │              ┌──────────────────────┐                  │
        │              │  UsinaModel          │                  │
        └─────────────▶│  (Energia acumulada) │──▶ Calculos.py   │
                       └──────────────────────┘                  │
                                                                 ▼
                                                          DataFrame final
```

- **Model** → só consulta SQL, retorna DataFrame bruto
- **Processador** → filtra outliers + calcula resolução + resample
- **Calculos** → lógica de negócio (produção de energia)

---

## ⚙️ Processamento de Telemetria (`libs/processador_telemetria.py`)

### Filtro de Outliers (IQR)

- Calcula Q1, Q3 e IQR por coluna
- Valores fora de `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` são **substituídos** pelo último valor válido (`ffill`)
- **Não perde registros** — mantém a janela temporal intacta
- Grupos do tipo `status` não são filtrados

### Resolução Automática

O cliente envia apenas `data_inicio` e `data_fim`. A API decide a resolução:

| Intervalo Solicitado | Resolução (Resample) |
| :------------------- | :------------------- |
| ≤ 1 hora             | 1min (dados brutos)  |
| ≤ 1 dia              | 15min                |
| > 1 dia              | 30min                |

---

## 📡 Endpoints

### `GET /health`

Health check do banco de dados.

```json
{ "status": "operacional", "database": "conectado" }
```

---

### `GET /usinas`

Lista todas as usinas configuradas.

---

### `GET /grupos/{usina}`

Lista grupos e variáveis disponíveis para a usina.

**Exemplo:** `GET /grupos/CGH-APARECIDA`

```json
{
  "potencia": ["UG-01 Potência Ativa"],
  "temperaturas": ["UG-01 Temp. Óleo UHLM", "UG-01 Temp. Mancal Guia"],
  "energia": ["UG-01 Energia Acumulada"]
}
```

---

### `POST /sensor-usina`

Consulta **sensor individual** com filtro de outliers e resolução automática.

**Body:**

```json
{
  "usina": "CGH-APARECIDA",
  "variavel": "UG-01 Potência Ativa",
  "data_inicio": "15/01/2026 00:00",
  "data_fim": "16/01/2026 00:00",
  "token": "seu_token"
}
```

**Response:**

```json
{
  "usina": "CGH-APARECIDA",
  "variavel": "UG-01 Potência Ativa",
  "registros": 96,
  "dados": [
    { "data_hora": "2026-01-15T00:00:00", "UG-01 Potência Ativa": 120.5 },
    { "data_hora": "2026-01-15T00:15:00", "UG-01 Potência Ativa": 118.3 }
  ]
}
```

---

### `POST /grupo-usina`

Consulta **grupo de variáveis** (ex: todas as temperaturas) com filtro e resolução.

**Body:**

```json
{
  "usina": "CGH-APARECIDA",
  "grupo": "temperaturas",
  "data_inicio": "15/01/2026 00:00",
  "data_fim": "16/01/2026 00:00",
  "token": "seu_token"
}
```

**Response:**

```json
{
  "usina": "CGH-APARECIDA",
  "grupo": "temperaturas",
  "registros": 96,
  "dados": [
    {
      "data_hora": "2026-01-15T00:00:00",
      "UG-01 Temp. Óleo UHLM": 35.1,
      "UG-01 Temp. Mancal Guia": 42.0
    }
  ]
}
```

---

### `POST /tabela-usina`

Retorna **todas as colunas** de todas as tabelas da usina, filtrado apenas por data. Sem filtro de outliers nem resample.

**Body:**

```json
{
  "usina": "CGH-APARECIDA",
  "data_inicio": "15/01/2026 08:00",
  "data_fim": "15/01/2026 09:00",
  "token": "seu_token"
}
```

**Response:**

```json
{
  "usina": "CGH-APARECIDA",
  "registros": 60,
  "tabelas": ["cgh_aparecida"],
  "dados": [
    {
      "data_hora": "2026-01-15T08:00:00",
      "coluna1": 1.0,
      "coluna2": 2.0,
      "_tabela": "cgh_aparecida"
    }
  ]
}
```

---

### `POST /producao-acumulada`

Calcula a geração de energia por período.

**Body:**

```json
{
  "usina": "CGH-APARECIDA",
  "data_inicio": "01/08/2025 00:00",
  "data_fim": "02/08/2025 23:59",
  "periodo": "D",
  "token": "seu_token"
}
```

> **Formato obrigatório das datas:** `DD/MM/YYYY HH:mm`.
>
> **Opções de período:** `"H"` (Hora), `"D"` (Dia), `"M"` (Mês).

---

## 🧪 Como Testar

```bash
# Fase 1: Model (consulta bruta)
python -m teste.test_telemetria_model

# Fase 2: Processador (outliers + resolução)
python -m teste.test_telemetria_fase2

# Fase 3: Rotas da API (requer uvicorn rodando)
uvicorn main:app --reload  # terminal 1
python -m teste.test_api_fase3  # terminal 2

# Visualização (Streamlit)
streamlit run teste/visualizar_fase2.py
```

---

## 🚀 Como Rodar Localmente

### Pré-requisitos

- Python 3.10+
- MySQL Database

### 1. Instalação

```bash
git clone <url-do-repo>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente (.env)

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

## 🛠 Stack Tecnológico

- **FastAPI** — Framework web de alta performance
- **Pandas** — Manipulação de séries temporais
- **Plotly** — Visualização (Streamlit)
- **MySQL Connector** — Conexão com banco
- **Pydantic** — Validação de dados
- **Streamlit** — Dashboards de teste
