# main.py
"""
API simplificada para monitoramento de produção de energia em usinas.
Autor: Miliano Fernandes de Oliveira
Data de criação: 2025-08-12
Última modificação: 2025-08-12
"""
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

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# ======================== CONFIGURAÇÃO ========================

# Mapeamento de usinas (poderia ser movido para um arquivo config.py)
USINAS_CONFIG = {
    "CGH-APARECIDA": {"tabelas": ["cgh_aparecida"], "energia": ["acumulador_energia"], "descricao": "CGH Aparecida - 1 UG"},
    "CGH-FAE": {"tabelas": ["cgh_fae"], "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"], "descricao": "CGH FAE - 2 UGs"},
    "PCH-PEDRAS": {"tabelas": ["pch_pedras_ug01", "pch_pedras_ug02"], "energia": ["acum_energia", "acum_energia"], "descricao": "PCH Pedras - 2 UGs"},
    "CGH-PICADAS-ALTAS": {"tabelas": ["cgh_picadas_altas"], "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"], "descricao": "CGH Picadas Altas - 2 UGs"},
    "CGH-HOPPEN": {"tabelas": ["cgh_hoppen_ug01", "cgh_hoppen_ug02"], "energia": ["acumulador_energia", "acumulador_energia"], "descricao": "CGH Hoppen - 2 UGs"},
}

# ======================== MODELOS (Schemas Pydantic) ========================

class ProducaoRequest(BaseModel):
    """Modelo de requisição para produção acumulada."""
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

    # MODIFICADO AQUI
    @field_validator('data_inicio', 'data_fim')
    def formatar_data_hora(cls, v: str):
        """Valida e converte o formato de data e hora para o padrão do banco de dados."""
        try:
            # Converte a string de entrada para um objeto datetime
            dt_obj = datetime.strptime(v, '%d/%m/%Y %H:%M')
            # Retorna a data e hora no formato 'YYYY-MM-DD HH:MM:SS' para a query SQL
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Formato de data e hora inválido. Use 'DD/MM/YYYY HH:mm'.")

    @field_validator('periodo')
    def normalizar_periodo(cls, v):
        return v.upper()[0]

# ======================== SERVIÇOS ========================

class DatabaseService:
    """Gerencia a conexão e a busca de dados no banco."""
    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=os.getenv('MYSQLHOST'), user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'), database=os.getenv('MYSQLDATABASE'),
                port=int(os.getenv('MYSQLPORT', 3306))
            )
        except mysql.connector.Error as e:
            raise HTTPException(status_code=503, detail=f"Erro de conexão com o banco: {e}")
        
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


    def buscar_dados_usina(self, usina: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        config = USINAS_CONFIG[usina]
        tabelas, colunas_energia = config["tabelas"], config["energia"]
        dfs = []

        with self.get_connection() as conn:
            for i, tabela in enumerate(tabelas):
                cols_selecionadas = colunas_energia if len(tabelas) == 1 else [colunas_energia[i]]
                col_str = ', '.join([col for col in cols_selecionadas])
                
                query = f'select data_hora, {col_str} from {tabela} where data_hora >= "{data_inicio}" and data_hora <= "{data_fim}"'
                # print(query)
                
                cursor = conn.cursor()
                cursor.execute(query)
                df_temp = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
                
                # Usar context manager do pandas para a query
                # df_temp = pd.read_sql(query, conn, params=(f'{data_inicio} 00:00:00', f'{data_fim} 23:59:59'))
                # print(df_temp.columns, df_temp.shape)
                
                if not df_temp.empty:
                    df_temp = self.tratamento_df(df_temp)
                    # print(df_temp.columns, df_temp.shape, len(tabelas))
                    # print('inicio', df_temp.values[0])
                    # print('fim', df_temp.values[-1])
                    # print('--------------------------------')
                    
                    # Renomeia colunas para evitar conflitos no merge
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
        
        # Merge de todos os dataframes em um só
        #df_final = reduce(lambda left, right: pd.merge(left, right, on='data_hora', how='outer'), dfs)
        # return df_final.sort_values('data_hora').set_index('data_hora')

class ProducaoService:
    """Processa os dados de produção de energia."""

    def calcular_producao(self, df: pd.DataFrame, periodo: str, usina: str) -> dict:
        if df.empty:
            return {"status": "sem_dados", "usina": usina, "mensagem": "Nenhum dado encontrado."}
        
        if periodo == 'D':
            df_trat = df.groupby(df['data_hora'].dt.date).last()
        elif periodo == 'M':
            df['ano_mes'] = df['data_hora'].dt.strftime('%Y-%m')
            df_trat = df.groupby('ano_mes').last()
            df_trat = df_trat.replace([np.nan, np.inf, -np.inf], None)
            df_trat = df_trat.fillna(0).infer_objects(copy=False)
        elif periodo == 'H':
            df['hora'] = df['data_hora'].dt.floor('h') 
            df_trat = df.groupby('hora').last().reset_index()
            df_trat = df_trat.replace([np.nan, np.inf, -np.inf], None)
            df_trat = df_trat.fillna(0).infer_objects(copy=False)
        else:
            raise ValueError(f"Período inválido: {periodo}")
        
        if len(USINAS_CONFIG[usina]['tabelas']) > 1:
            colunas_energia = [f'ug{i+1:02d}_{col}' for i,col in enumerate(USINAS_CONFIG[usina]['energia'])]
        else:
            colunas_energia = USINAS_CONFIG[usina]['energia']

        resultado_json = {}
        for col in colunas_energia:
            resultado_json[col] = []
            for i in range(1, len(df_trat)):
                value = round(df_trat[col].values[i] - df_trat[col].values[i-1],2)
                resultado_json[col].append({'data': df_trat.index[i], 'producao_Mwh': value})

        return {'usina':usina, 'periodo':periodo, 'resultado':resultado_json}
        
        # return resultado_json
        
        # Calcula a produção para cada período (diferença do acumulador)
        # producao_periodo = df.resample(periodo).last().diff().fillna(0)
        # producao_periodo[producao_periodo < 0] = 0 # Corrige resets do contador

        # producao_total_serie = producao_periodo.sum(axis=1)

        # # Formata a saída
        # resultado_json = {f"UG{i+1:02d}": 
        #                     [{'data': idx.strftime('%Y-%m-%d %H:%M:%S'), 'producao_Mwh': round(val, 2)} 
        #                      for idx, val in col.items() if val > 0]
        #                   for i, (nome_col, col) in enumerate(producao_periodo.items())}

        # total_list = [{'data': idx.strftime('%Y-%m-%d %H:%M:%S'), 'producao_total_kwh': round(val, 2)} 
        #               for idx, val in producao_total_serie.items() if val > 0]
        
        # estatisticas = {
        #     "producao_total_periodo": round(producao_total_serie.sum(), 2),
        #     "producao_media_diaria": round(producao_total_serie[producao_total_serie > 0].mean(), 2) if not producao_total_serie.empty else 0,
        #     "dias_com_producao": int((producao_total_serie > 0).sum()),
        #     "primeiro_registro": df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
        #     "ultimo_registro": df.index.max().strftime('%Y-%m-%d %H:%M:%S')
        # }

        # return {
        #     "status": "sucesso", "usina": usina, "periodo": periodo,
        #     "unidades_geradoras": resultado_json,
        #     "producao_total": total_list,
        #     "estatisticas": estatisticas
        # }

# ======================== CONFIGURAÇÃO DA API E ROTAS ========================

app = FastAPI(title="ENGESEP API v1", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

# Injeção de Dependência
db_service = DatabaseService()
producao_service = ProducaoService()

@app.post("/producao-acumulada")
def producao_acumulada(request: ProducaoRequest):
    # A verificação de token poderia ser um `Depends` também
    if request.token and request.token != os.getenv('API_TOKEN', '123456'):
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        df = db_service.buscar_dados_usina(request.usina, request.data_inicio, request.data_fim)
        # resultado = producao_service
        resultado = producao_service.calcular_producao(df, request.periodo, request.usina)
        return resultado
    except Exception as e:
        # Evita expor detalhes internos em produção
        print(f"Erro inesperado: {e}") # Log para debug
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar dados da usina {request.usina}.")

@app.get("/usinas")
def listar_usinas():
    """Lista as usinas disponíveis e suas configurações."""
    return {
        "usinas_disponiveis": [
            {"codigo": codigo, **config} for codigo, config in USINAS_CONFIG.items()
        ]
    }

@app.get("/health")
def health_check():
    """Verifica a saúde da API e do banco de dados."""
    try:
        with db_service.get_connection():
            return {"status": "operacional", "database": "conectado"}
    except Exception as e:
        return {"status": "com_problemas", "database": "desconectado", "erro": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)