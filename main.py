# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. ProducaoRequest           → valida entrada (usina, datas, período, token)
# 2. SensorRequest             → valida entrada para consulta de sensor individual
# 3. GrupoRequest              → valida entrada para consulta de grupo
# 4. TabelaRequest             → valida entrada para dump de tabela completa
# 5. UsinaModel                → busca dados no banco via Database (libs/db.py)
# 6. TelemetriaModel           → consulta telemetria (sensor/grupo) bruto
# 7. ProcessadorTelemetria     → filtra outliers + resample automático
# 8. Calculos                  → cálculo de produção de energia
# 9. POST /producao-acumulada  → busca + cálculos de energia
# 10. POST /sensor-usina       → consulta sensor individual processado
# 11. POST /grupo-usina        → consulta grupo de variáveis processado
# 12. POST /tabela-usina       → dump de tabela completa (todas as colunas)
# 13. GET  /grupos/{usina}     → lista grupos e variáveis disponíveis
# 14. GET  /usinas             → lista usinas configuradas
# 15. GET  /health             → health check do banco
# -------------------------------------------------------------------

"""
API para monitoramento de produção de energia em usinas hidrelétricas.
Autor: Miliano Fernandes de Oliveira
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from typing import Literal
from dotenv import load_dotenv
import uvicorn
import os
import pandas as pd

from libs.db import Database
from libs.usina_model import UsinaModel, USINAS_CONFIG
from libs.calculos import Calculos
from libs.telemetria_model import TelemetriaModel
from libs.processador_telemetria import processar_sensor, processar_grupo

load_dotenv()

# ======================== VALIDADORES BASE ========================

def _validar_usina(v: str) -> str:
    usina_upper = v.upper()
    if usina_upper not in USINAS_CONFIG:
        raise ValueError(f'Usina inválida. Disponíveis: {", ".join(USINAS_CONFIG.keys())}')
    return usina_upper


def _formatar_data(v: str) -> str:
    try:
        dt_obj = datetime.strptime(v, '%d/%m/%Y %H:%M')
        return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValueError("Formato inválido. Use 'DD/MM/YYYY HH:mm'.")


# ======================== MODELOS PYDANTIC ========================

class ProducaoRequest(BaseModel):
    usina: str
    data_inicio: str = Field(..., description="DD/MM/YYYY HH:mm")
    data_fim: str = Field(..., description="DD/MM/YYYY HH:mm")
    periodo: Literal['D', 'M', 'H', 'DIARIO', 'MENSAL', 'HORARIO'] = 'D'
    token: str | None = None

    _v_usina = field_validator('usina')(lambda cls, v: _validar_usina(v))
    _v_datas = field_validator('data_inicio', 'data_fim')(lambda cls, v: _formatar_data(v))

    @field_validator('periodo')
    def normalizar_periodo(cls, v):
        return v.upper()[0]


class SensorRequest(BaseModel):
    usina: str
    variavel: str
    data_inicio: str = Field(..., description="DD/MM/YYYY HH:mm")
    data_fim: str = Field(..., description="DD/MM/YYYY HH:mm")
    token: str | None = None

    _v_usina = field_validator('usina')(lambda cls, v: _validar_usina(v))
    _v_datas = field_validator('data_inicio', 'data_fim')(lambda cls, v: _formatar_data(v))


class GrupoRequest(BaseModel):
    usina: str
    grupo: str
    data_inicio: str = Field(..., description="DD/MM/YYYY HH:mm")
    data_fim: str = Field(..., description="DD/MM/YYYY HH:mm")
    token: str | None = None

    _v_usina = field_validator('usina')(lambda cls, v: _validar_usina(v))
    _v_datas = field_validator('data_inicio', 'data_fim')(lambda cls, v: _formatar_data(v))


class TabelaRequest(BaseModel):
    usina: str
    data_inicio: str = Field(..., description="DD/MM/YYYY HH:mm")
    data_fim: str = Field(..., description="DD/MM/YYYY HH:mm")
    token: str | None = None

    _v_usina = field_validator('usina')(lambda cls, v: _validar_usina(v))
    _v_datas = field_validator('data_inicio', 'data_fim')(lambda cls, v: _formatar_data(v))


# ======================== SERIALIZAÇÃO ========================

def _df_to_json(df: pd.DataFrame) -> list[dict]:
    """Converte DataFrame para list[dict] com data_hora ISO."""
    if df.empty:
        return []
    resultado = []
    for _, row in df.iterrows():
        item = {}
        for col, val in row.items():
            if col == 'data_hora':
                item[col] = val.isoformat() if hasattr(val, 'isoformat') else str(val)
            elif pd.notna(val):
                item[col] = round(float(val), 3) if isinstance(val, (int, float)) else val
            else:
                item[col] = None
        resultado.append(item)
    return resultado


# ======================== API E ROTAS ========================

app = FastAPI(title="ENGESEP API v1", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

db = Database()
usina_model = UsinaModel(db)
telemetria_model = TelemetriaModel(db)
calculos = Calculos()

TOKEN = os.getenv('API_TOKEN', '123456')


def _validar_token(token: str | None):
    if token and token != TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


# ── Produção de Energia ──

@app.post("/producao-acumulada")
def producao_acumulada(request: ProducaoRequest):
    _validar_token(request.token)
    try:
        df = usina_model.buscar_dados_usina(request.usina, request.data_inicio, request.data_fim, request.periodo)
        resultado = calculos.calcular_energia_acumulada(df, request.periodo, request.usina)
        return {'usina': request.usina, 'periodo': request.periodo, 'resultado': resultado}
    except Exception as e:
        print(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar usina {request.usina}.")


# ── Telemetria: Sensor Individual ──

@app.post("/sensor-usina")
def sensor_usina(request: SensorRequest):
    """Consulta sensor individual com filtro de outliers e resolução automática."""
    _validar_token(request.token)
    try:
        df_bruto = telemetria_model.buscar_sensor(
            request.usina, request.variavel, request.data_inicio, request.data_fim
        )
        df_final = processar_sensor(df_bruto, request.data_inicio, request.data_fim)
        return {
            'usina': request.usina,
            'variavel': request.variavel,
            'registros': len(df_final),
            'dados': _df_to_json(df_final),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erro sensor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar sensor {request.variavel}.")


# ── Telemetria: Grupo ──

@app.post("/grupo-usina")
def grupo_usina(request: GrupoRequest):
    """Consulta grupo de variáveis com filtro e resolução automática."""
    _validar_token(request.token)
    try:
        df_bruto = telemetria_model.buscar_grupo(
            request.usina, request.grupo, request.data_inicio, request.data_fim
        )
        df_final = processar_grupo(df_bruto, request.data_inicio, request.data_fim, request.grupo)
        return {
            'usina': request.usina,
            'grupo': request.grupo,
            'registros': len(df_final),
            'dados': _df_to_json(df_final),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erro grupo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar grupo {request.grupo}.")


# ── Telemetria: Tabela Completa ──

@app.post("/tabela-usina")
def tabela_usina(request: TabelaRequest):
    """Retorna todas as colunas de todas as tabelas da usina, filtrado por data."""
    _validar_token(request.token)
    try:
        cfg = USINAS_CONFIG[request.usina]
        tabelas = cfg['tabelas']
        dfs = []

        for tabela in tabelas:
            query = (
                f'SELECT * FROM {tabela} '
                f'WHERE data_hora >= "{request.data_inicio}" '
                f'AND data_hora <= "{request.data_fim}" '
                f'ORDER BY data_hora'
            )
            telemetria_model._garantir_conexao()
            df = telemetria_model.db.fetch_dataframe(query)
            if not df.empty:
                df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce')
                df['_tabela'] = tabela
                dfs.append(df)

        if not dfs:
            return {'usina': request.usina, 'registros': 0, 'tabelas': tabelas, 'dados': []}

        resultado = pd.concat(dfs, ignore_index=True).sort_values('data_hora')
        return {
            'usina': request.usina,
            'registros': len(resultado),
            'tabelas': tabelas,
            'dados': _df_to_json(resultado),
        }
    except Exception as e:
        print(f"Erro tabela: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar tabelas de {request.usina}.")


# ── Listagem ──

@app.get("/grupos/{usina}")
def listar_grupos_usina(usina: str):
    """Lista grupos e variáveis disponíveis para uma usina."""
    usina_upper = usina.upper()
    if usina_upper not in USINAS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Usina '{usina}' não encontrada.")
    return telemetria_model.listar_grupos(usina_upper)


@app.get("/usinas")
def listar_usinas():
    return {
        "usinas_disponiveis": [
            {"codigo": codigo, **config} for codigo, config in USINAS_CONFIG.items()
        ]
    }


@app.get("/health")
def health_check():
    try:
        db.connect()
        db.close()
        return {"status": "operacional", "database": "conectado"}
    except Exception as e:
        return {"status": "com_problemas", "database": "desconectado", "erro": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


