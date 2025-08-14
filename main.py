# main_new.py

"""
API simplificada para monitoramento de produção de energia em usinas.
Autor: Miliano Fernandes de Oliveira
Data de criação: 2025-08-12
Última modificação: 2025-08-12
VERSÃO OTIMIZADA - DatabaseService e ProducaoService com melhorias de performance
"""
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from typing import List, Dict, Literal
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
import uvicorn
import os
from functools import reduce

load_dotenv()

# ======================== CONFIGURAÇÃO ========================

USINAS_CONFIG = {
    "CGH-APARECIDA": {"tabelas": ["cgh_aparecida"], "energia": ["acumulador_energia"], "descricao": "CGH Aparecida - 1 UG"},
    "CGH-FAE": {"tabelas": ["cgh_fae"], "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"], "descricao": "CGH FAE - 2 UGs"},
    "PCH-PEDRAS": {"tabelas": ["pch_pedras_ug01", "pch_pedras_ug02"], "energia": ["acum_energia", "acum_energia"], "descricao": "PCH Pedras - 2 UGs"},
    "CGH-PICADAS-ALTAS": {"tabelas": ["cgh_picadas_altas"], "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"], "descricao": "CGH Picadas Altas - 2 UGs"},
    "CGH-HOPPEN": {"tabelas": ["cgh_hoppen_ug01", "cgh_hoppen_ug02"], "energia": ["acumulador_energia", "acumulador_energia"], "descricao": "CGH Hoppen - 2 UGs"},
}

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

# ======================== SERVIÇOS ========================

class DatabaseService:
    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=os.getenv('MYSQLHOST'), user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'), database=os.getenv('MYSQLDATABASE'),
                port=int(os.getenv('MYSQLPORT', 3306))
            )
        except mysql.connector.Error as e:
            raise HTTPException(status_code=503, detail=f"Erro de conexão com o banco: {e}")
    
    def buscar_dados_usina_otimizada(self, usina: str, data_inicio: str, data_fim: str, periodo: str = 'D') -> pd.DataFrame:
        config = USINAS_CONFIG[usina]
        tabelas, colunas_energia = config["tabelas"], config["energia"]
        dfs = []

        with self.get_connection() as conn:
            for i, tabela in enumerate(tabelas):
                cols_selecionadas = colunas_energia if len(tabelas) == 1 else [colunas_energia[i]]
                col_str = ', '.join([col for col in cols_selecionadas])

                if periodo == 'M':
                    query = f"""WITH base AS (
                        SELECT
                            data_hora,
                            {col_str},
                            DATE_FORMAT(data_hora, '%Y-%m-01') AS mes_ini,
                            ROW_NUMBER() OVER (
                                PARTITION BY YEAR(data_hora), MONTH(data_hora)
                                ORDER BY data_hora ASC
                            ) AS rn_asc,
                            ROW_NUMBER() OVER (
                                PARTITION BY YEAR(data_hora), MONTH(data_hora)
                                ORDER BY data_hora DESC
                            ) AS rn_desc
                        FROM {tabela}
                        WHERE data_hora >= '{data_inicio}' AND data_hora <= '{data_fim}'
                    ),
                    filtrada AS (
                        SELECT * FROM base
                        WHERE rn_asc <= 10 OR rn_desc <= 10
                    )
                    SELECT data_hora, {col_str}
                    FROM filtrada
                    ORDER BY data_hora"""
                else:
                    query = f'select data_hora, {col_str} from {tabela} where data_hora >= "{data_inicio}" and data_hora <= "{data_fim}"'
                
                cursor = conn.cursor()
                cursor.execute(query)
                df_temp = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
                               
                if not df_temp.empty:
                    df_temp = self.tratamento_df(df_temp)
                    
                    if len(tabelas) > 1:
                        col_original = cols_selecionadas[0]
                        novo_nome = f"ug{i+1:02d}_{col_original}"
                        df_temp = df_temp.rename(columns={col_original: novo_nome})
                        df_temp['data_hora'] = df_temp['data_hora'].dt.round('min')
                    
                    dfs.append(df_temp)
            cursor.close()

        if not dfs:
            return pd.DataFrame()
        
        if len(dfs) == 1:
            return dfs[0]
        else:
            df_final = pd.merge(dfs[0], dfs[1], on='data_hora', how='outer')
            return df_final

    def tratamento_df(self, df_: pd.DataFrame) -> pd.DataFrame:
        for col in df_.dtypes.index:
            if df_[col].dtype != 'int64' and df_[col].dtype != 'float64' and col != 'data_hora':
                if pd.to_numeric(df_[col], errors='coerce').notna().all():
                    df_[col] = df_[col].astype(float)
                    df_[col] = df_[col].fillna(0)
            colunas_numericas = df_.select_dtypes(include=[np.number]).columns
            mask = (df_[colunas_numericas] >= 0).all(axis=1)
            mask_ = (df_[colunas_numericas] == 103.00).any(axis=1)
        
            df_ = df_[mask]
            df_ = df_[~mask_]
        return df_

class ProducaoService:
    def calcular_producao(self, df: pd.DataFrame, periodo: str, usina: str) -> dict:
        if df.empty:
            return {"status": "sem_dados", "usina": usina, "mensagem": "Nenhum dado encontrado."}
        
        if periodo == 'D':
            df_trat = df.groupby(df['data_hora'].dt.date).last()
        elif periodo == 'M':
            df_temp = df.copy()
            df_temp['ano_mes'] = df_temp['data_hora'].dt.strftime('%Y-%m')
            df_trat = df_temp.groupby('ano_mes').last()
            df_trat = df_trat.replace([np.nan, np.inf, -np.inf], None).fillna(0)
        elif periodo == 'H':
            df_trat = df.groupby(df['data_hora'].dt.floor('h')).last().reset_index()
            df_trat = df_trat.replace([np.nan, np.inf, -np.inf], None).fillna(0)
        else:
            raise ValueError(f"Período inválido: {periodo}")
        
        if len(USINAS_CONFIG[usina]['tabelas']) > 1:
            colunas_energia = [f'ug{i+1:02d}_{col}' for i,col in enumerate(USINAS_CONFIG[usina]['energia'])]
        else:
            colunas_energia = USINAS_CONFIG[usina]['energia']

        resultado_json = {}
        
        for col in colunas_energia:
            if col in df_trat.columns:
                valores = df_trat[col].values
                if len(valores) > 1:
                    diferencas = np.diff(valores)
                    diferencas_arredondadas = np.round(diferencas, 2)
                    
                    resultado_json[col] = [
                        {'data': df_trat.index[i], 'producao_Mwh': float(diferencas_arredondadas[i-1])}
                        for i in range(1, len(df_trat))
                    ]
                else:
                    resultado_json[col] = []
            else:
                resultado_json[col] = []

        return {'usina': usina, 'periodo': periodo, 'resultado': resultado_json}

# ======================== API E ROTAS ========================

app = FastAPI(title="ENGESEP API v1 - OTIMIZADA", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

db_service = DatabaseService()
producao_service = ProducaoService()

@app.post("/producao-acumulada")
def producao_acumulada(request: ProducaoRequest):
    if request.token and request.token != os.getenv('API_TOKEN', '123456'):
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        df = db_service.buscar_dados_usina_otimizada(request.usina, request.data_inicio, request.data_fim, request.periodo)
        resultado = producao_service.calcular_producao(df, request.periodo, request.usina)
        return resultado
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
        with db_service.get_connection():
            return {"status": "operacional", "database": "conectado"}
    except Exception as e:
        return {"status": "com_problemas", "database": "desconectado", "erro": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
