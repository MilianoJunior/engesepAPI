# ENGESEP API

API de monitoramento de produção de energia para usinas hidrelétricas.

Desenvolvida com **FastAPI**, conecta ao banco MySQL para consulta e cálculo de produção acumulada de energia (MWh) por unidade geradora.

---

## Usinas Disponíveis

| Código              | Descrição              | UGs |
|---------------------|------------------------|-----|
| CGH-APARECIDA       | CGH Aparecida          | 1   |
| CGH-FAE             | CGH FAE                | 2   |
| PCH-PEDRAS          | PCH Pedras             | 2   |
| CGH-PICADAS-ALTAS   | CGH Picadas Altas      | 2   |
| CGH-HOPPEN          | CGH Hoppen             | 2   |

---

## Endpoints

### `POST /producao-acumulada`

Calcula a produção de energia acumulada (MWh) por unidade geradora, com agrupamento por período.

**Body (JSON):**

```json
{
  "usina": "CGH-APARECIDA",
  "data_inicio": "01/08/2025 00:00",
  "data_fim": "14/08/2025 17:00",
  "periodo": "D",
  "token": "123456"
}
```

| Campo        | Tipo   | Obrigatório | Descrição                                                  |
|--------------|--------|-------------|------------------------------------------------------------|
| usina        | string | sim         | Código da usina (ver tabela acima)                         |
| data_inicio  | string | sim         | Data/hora início no formato `DD/MM/YYYY HH:mm`            |
| data_fim     | string | sim         | Data/hora fim no formato `DD/MM/YYYY HH:mm`               |
| periodo      | string | não         | `D` (diário), `H` (horário) ou `M` (mensal). Padrão: `D`  |
| token        | string | não         | Token de autenticação                                      |

**Resposta (exemplo):**

```json
{
  "usina": "CGH-APARECIDA",
  "periodo": "D",
  "resultado": {
    "acumulador_energia": [
      { "data": "2025-08-01", "producao_Mwh": 12.45 },
      { "data": "2025-08-02", "producao_Mwh": 11.80 }
    ]
  }
}
```

---

### `GET /usinas`

Lista todas as usinas configuradas com seus códigos, tabelas e colunas de energia.

---

### `GET /health`

Verifica o status da API e a conexão com o banco de dados.

**Resposta:**

```json
{ "status": "operacional", "database": "conectado" }
```

---

## Stack

- **FastAPI** — framework web
- **MySQL** — banco de dados
- **Pandas / NumPy** — processamento de dados
- **Pydantic** — validação de entrada
- **python-dotenv** — variáveis de ambiente

## Variáveis de Ambiente

| Variável        | Descrição                  |
|-----------------|----------------------------|
| MYSQLHOST       | Host do banco MySQL        |
| MYSQLUSER       | Usuário do banco           |
| MYSQLPASSWORD   | Senha do banco             |
| MYSQLDATABASE   | Nome do banco              |
| MYSQLPORT       | Porta do banco (padrão: 3306) |
| API_TOKEN       | Token de autenticação da API  |

