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
# 16. GET  /memoria            → uso de memória RSS, threads e status do GIL
# -------------------------------------------------------------------

"""
API para monitoramento de produção de energia em usinas hidrelétricas.
Autor: Miliano Fernandes de Oliveira
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from typing import Literal
from dotenv import load_dotenv
import uvicorn
import os
import subprocess
import sys
import threading
import psutil
import pandas as pd

from libs.db import Database
from libs.usina_model import UsinaModel, USINAS_CONFIG
from libs.calculos import Calculos
from libs.telemetria_model import TelemetriaModel
from libs.processador_telemetria import processar_sensor, processar_grupo
from libs import producao_cache_model as pcm

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


# ======================== VERSÃO ========================

def _obter_versao() -> str:
    """Retorna versão da API a partir do git (hash curto + data do commit)."""
    try:
        hash_curto = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        data_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ci'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()[:16]
        return f"{hash_curto} ({data_commit})"
    except Exception:
        return 'desconhecida'


API_VERSION = _obter_versao()


# ======================== MONITORAMENTO DE MEMÓRIA ========================

_proc = psutil.Process(os.getpid())


def _mem_log_enabled() -> bool:
    return os.getenv('MEM_LOG_ENABLED', '0').strip().lower() in {'1', 'true', 'yes', 'on'}


def _log_memoria(prefixo: str = '[MEM]'):
    """Imprime RSS, threads ativas e % de memória do sistema."""
    mem = _proc.memory_info()
    sys_mem = psutil.virtual_memory()
    rss_mb = mem.rss / 1024 ** 2
    threads = threading.active_count()
    print(
        f"{prefixo} rss={rss_mb:.1f}MB "
        f"threads={threads} "
        f"sys_usado={sys_mem.percent:.1f}% "
        f"sys_livre={sys_mem.available / 1024 ** 2:.0f}MB"
    )


# ======================== API E ROTAS ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[STARTUP] ENGESEP API versão: {API_VERSION}")
    print(f"[STARTUP] Usinas configuradas: {', '.join(USINAS_CONFIG.keys())}")
    _log_memoria('[MEM][STARTUP]')
    _migrar_banco()
    yield
    _log_memoria('[MEM][SHUTDOWN]')


def _migrar_banco():
    """Cria tabelas necessárias se não existirem. Roda no startup da API."""
    try:
        conn = db._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS producao_historica (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                usina         VARCHAR(64)     NOT NULL,
                mes           CHAR(7)         NOT NULL,
                coluna        VARCHAR(128)    NOT NULL,
                producao_mwh  DECIMAL(12, 3)  NOT NULL,
                calculado_em  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_usina_mes_coluna (usina, mes, coluna)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[MIGRAÇÃO] producao_historica: OK")
    except Exception as e:
        print(f"[MIGRAÇÃO] ERRO ao criar tabela: {e}")



app = FastAPI(title="ENGESEP API", version=API_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.middleware('http')
async def middleware_memoria(request: Request, call_next):
    if _mem_log_enabled():
        _log_memoria(f'[MEM][{request.method} {request.url.path}]')
    return await call_next(request)


db = Database()
usina_model = UsinaModel(db)
telemetria_model = TelemetriaModel(db)
calculos = Calculos()

TOKEN = os.getenv('API_TOKEN', '12345678')


def _validar_token(token: str | None):
    if not token == TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido ou ausente")


# ── Produção de Energia ──

@app.post("/producao-acumulada")
def producao_acumulada(request: ProducaoRequest):
    _validar_token(request.token)
    try:
        periodo = (request.periodo or 'D').upper()[0]

        if periodo != 'M':
            # H e D: fluxo original sem alteração
            df = usina_model.buscar_dados_usina(request.usina, request.data_inicio, request.data_fim, periodo)
            resultado = calculos.calcular_energia_acumulada(df, periodo, request.usina)
            return {'usina': request.usina, 'periodo': periodo, 'resultado': resultado}

        # ── Período M: cache lazy fill para meses fechados + mês atual em tempo real ──
        meses_fechados = pcm._meses_fechados_no_intervalo(request.data_inicio, request.data_fim)

        # Garante que todos os meses fechados estão no cache (calcula e persiste os que faltam)
        pcm.garantir_meses_no_cache(
            db=db,
            calculos=calculos,
            usina=request.usina,
            meses_necessarios=meses_fechados,
            buscar_df_mes_fn=lambda ini, fim: usina_model.buscar_dados_usina(
                request.usina, ini, fim, 'H'
            ),
        )

        # Lê meses fechados do cache
        resultado_historico = pcm.buscar_historico_cache(db, request.usina, meses_fechados)

        # Calcula mês atual em tempo real
        from datetime import datetime
        mes_atual_str = datetime.now().strftime('%Y-%m')
        ini_mes_atual = datetime.now().strftime('%Y-%m-01 00:00:00')
        df_atual = usina_model.buscar_dados_usina(request.usina, ini_mes_atual, request.data_fim, 'H')
        resultado_atual = calculos.calcular_energia_acumulada(df_atual, 'M', request.usina)

        resultado = resultado_historico + resultado_atual
        resultado.sort(key=lambda x: x.get('data', ''))
        return {'usina': request.usina, 'periodo': periodo, 'resultado': resultado}

    except Exception as e:
        import traceback
        print(f"[ERRO] producao_acumulada usina={request.usina}: {e}\n{traceback.format_exc()}")
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
        conn = db._get_conn()
        conn.close()  # devolve ao pool
        return {"status": "operacional", "database": "conectado", "pool_size": db.pool_size}
    except Exception as e:
        return {"status": "com_problemas", "database": "desconectado", "erro": str(e)}


@app.get("/memoria")
def memoria_status():
    """Retorna uso de memória RSS, threads ativas e status do GIL do processo."""
    proc = psutil.Process(os.getpid())
    mem = proc.memory_info()
    mem_virtual = psutil.virtual_memory()

    # GIL: Python 3.13+ suporta free-threaded (sem GIL) via PYTHON_GIL=0
    # Versões anteriores: GIL sempre ativo
    python_version = sys.version_info
    free_threaded = getattr(sys, '_is_gil_enabled', None)
    if free_threaded is None:
        gil_status = "ativo (Python < 3.13, GIL sempre presente)"
    else:
        gil_status = "desativado (free-threaded)" if not free_threaded() else "ativo"

    return {
        "processo": {
            "pid": os.getpid(),
            "memoria_rss_mb": round(mem.rss / 1024 ** 2, 2),
            "memoria_vms_mb": round(mem.vms / 1024 ** 2, 2),
            "threads_ativas": threading.active_count(),
            "cpu_percent": proc.cpu_percent(interval=0.1),
        },
        "sistema": {
            "memoria_total_mb": round(mem_virtual.total / 1024 ** 2, 2),
            "memoria_disponivel_mb": round(mem_virtual.available / 1024 ** 2, 2),
            "memoria_usada_percent": mem_virtual.percent,
        },
        "python": {
            "versao": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "gil": gil_status,
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


