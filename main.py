# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. ProducaoRequest           → valida entrada (usina, datas, período, token)
# 2. UsinaModel                → busca dados no banco via Database (libs/db.py)
# 3. calcular_producao_A       → cálculo A: delta first/last por janela (libs/calculosA.py)
# 4. calcular_producao_B       → cálculo B: .diff() sobre último agrupado (libs/calculosB.py)
# 5. POST /producao-acumulada  → orquestra busca + ambos cálculos para comparação
# 6. GET  /usinas              → lista usinas configuradas
# 7. GET  /health              → health check do banco
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

from libs.db import Database
from libs.usina_model import UsinaModel, USINAS_CONFIG
from libs.calculos import Calculos

load_dotenv()

# ======================== MODELOS ========================

class ProducaoRequest(BaseModel):
    usina: str
    data_inicio: str = Field(..., description="Data e hora no formato DD/MM/YYYY HH:mm, ex: 12/08/2025 17:00")
    data_fim: str = Field(..., description="Data e hora no formato DD/MM/YYYY HH:mm, ex: 13/08/2025 18:30")
    periodo: Literal['D', 'M', 'H', 'DIARIO', 'MENSAL', 'HORARIO'] = 'D'
    token: str | None = None

    @field_validator('usina')
    def validar_usina(cls, v):
        usina_upper = v.upper()
        if usina_upper not in USINAS_CONFIG:
            raise ValueError(f'Usina inválida. Disponíveis: {", ".join(USINAS_CONFIG.keys())}')
        return usina_upper

    @field_validator('data_inicio', 'data_fim')
    def formatar_data_hora(cls, v: str):
        try:
            dt_obj = datetime.strptime(v, '%d/%m/%Y %H:%M')
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Formato de data e hora inválido. Use 'DD/MM/YYYY HH:mm'.")

    @field_validator('periodo')
    def normalizar_periodo(cls, v):
        return v.upper()[0]

# ======================== API E ROTAS ========================

app = FastAPI(title="ENGESEP API v1 - OTIMIZADA", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

db = Database()
usina_model = UsinaModel(db)
calculos = Calculos()

@app.post("/producao-acumulada")
def producao_acumulada(request: ProducaoRequest):
    if request.token and request.token != os.getenv('API_TOKEN', '123456'):
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        df = usina_model.buscar_dados_usina(request.usina, request.data_inicio, request.data_fim, request.periodo)

        resultado = calculos.calcular_energia_acumulada(df, request.periodo, request.usina)

        print(
            f"[RESULTADO] usina={request.usina} periodo={request.periodo} "
            f"itens={len(resultado)}"
        )


        return {'usina': request.usina, 'periodo': request.periodo, 'resultado': resultado}
    except Exception as e:
        print(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar dados da usina {request.usina}.")

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
