"""
API simplificada para monitoramento de produção de energia em usinas.
Autor: Miliano Fernandes de Oliveira
Data de criação: 2025-08-12
Última modificação: 2025-08-12
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
import numpy as np
import uvicorn
import os
import re

load_dotenv()

# ======================== CONFIGURAÇÃO ========================
app = FastAPI(
    title="ENGESEP API v1 - Produção de Energia",
    description="API simplificada para consulta de produção acumulada de energia em usinas",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================== MAPEAMENTO DE USINAS ========================
USINAS_CONFIG = {
    "CGH-APARECIDA": {
        "tabelas": ["cgh_aparecida"],
        "energia": ["acumulador_energia"],
        "descricao": "CGH Aparecida - 1 unidade geradora"
    },
    "CGH-FAE": {
        "tabelas": ["cgh_fae"],
        "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"],
        "descricao": "CGH FAE - 2 unidades geradoras"
    },
    "PCH-PEDRAS": {
        "tabelas": ["pch_pedras_ug01", "pch_pedras_ug02"],
        "energia": ["acum_energia", "acum_energia"],
        "descricao": "PCH Pedras - 2 unidades geradoras (tabelas separadas)"
    },
    "CGH-PICADAS-ALTAS": {
        "tabelas": ["cgh_picadas_altas"],
        "energia": ["ug01_acumulador_energia", "ug02_acumulador_energia"],
        "descricao": "CGH Picadas Altas - 2 unidades geradoras"
    },
    "CGH-HOPPEN": {
        "tabelas": ["cgh_hoppen_ug01", "cgh_hoppen_ug02"],
        "energia": ["acumulador_energia", "acumulador_energia"],
        "descricao": "CGH Hoppen - 2 unidades geradoras (tabelas separadas)"
    },
}

# ======================== MODELOS ========================
class ProducaoRequest(BaseModel):
    """Modelo simplificado de requisição para produção acumulada"""
    usina: str
    data_inicio: str
    data_fim: str
    periodo: str = 'D'  # D=Diário, M=Mensal, H=Horário
    token: Optional[str] = None
    
    @validator('usina')
    def validar_usina(cls, v):
        usina_upper = v.upper()
        if usina_upper not in USINAS_CONFIG:
            usinas_disponiveis = ", ".join(USINAS_CONFIG.keys())
            raise ValueError(f'Usina inválida. Disponíveis: {usinas_disponiveis}')
        return usina_upper
    
    @validator('data_inicio', 'data_fim')
    def validar_datas(cls, v):
        try:
            # Aceita formato YYYY-MM-DD ou DD/MM/YYYY
            if '/' in v:
                data = datetime.strptime(v, '%d/%m/%Y')
            else:
                data = datetime.strptime(v, '%Y-%m-%d')
            return data.strftime('%Y-%m-%d')  # Sempre retorna no formato SQL
        except ValueError:
            raise ValueError('Data deve estar no formato YYYY-MM-DD ou DD/MM/YYYY')
    
    @validator('periodo')
    def validar_periodo(cls, v):
        periodos_validos = {
            'D': 'D',
            'M': 'M', 
            'H': 'H',
            'DIARIO': 'D',
            'MENSAL': 'M',
            'HORARIO': 'H'
        }
        
        v_upper = v.upper()
        if v_upper in periodos_validos:
            # Normaliza para D, M ou H
            return periodos_validos.get(v_upper, v_upper)
        
        raise ValueError('Período deve ser D/Diário, M/Mensal ou H/Horário')

# ======================== BANCO DE DADOS ========================
class Database:
    """Gerenciador de conexão com o banco de dados"""
    
    @staticmethod
    def get_connection():
        """Cria uma nova conexão com o banco"""
        try:
            return mysql.connector.connect(
                host=os.getenv('MYSQLHOST'),
                user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'),
                database=os.getenv('MYSQLDATABASE'),
                port=int(os.getenv('MYSQLPORT', 3306)),
                autocommit=True
            )
        except mysql.connector.Error as e:
            raise HTTPException(status_code=500, detail=f"Erro de conexão com banco: {e}")
        
    def tratamento_df(self, df_: pd.DataFrame) -> pd.DataFrame:
        for col in df_.dtypes.index:
            if df_[col].dtype != 'int64' and df_[col].dtype != 'float64' and col != 'data_hora':
                if pd.to_numeric(df_[col], errors='coerce').notna().all():
                    df_[col] = df_[col].astype(float)
                    df_[col] = df_[col].fillna(0)
            colunas_numericas = df_.select_dtypes(include=[np.number]).columns
            mask = (df_[colunas_numericas] >= 0).all(axis=1)
        
            df_ = df_[mask]
        return df_

    def buscar_dados_usina(self, usina: str, tipo: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """
        Busca dados de produção de energia da usina especificada.
        Trata automaticamente usinas com múltiplas tabelas.
        """
        config = USINAS_CONFIG[usina]
        tabelas = config["tabelas"]
        colunas = config[tipo]
        
        todos_dados = []
        connection = None
        
        try:
            connection = Database.get_connection()
            cursor = connection.cursor()
            
            # Para cada tabela da usina
            for idx, tabela in enumerate(tabelas):
                # Determina quais colunas buscar desta tabela
                if len(tabelas) == 1:
                    # Uma tabela com múltiplas colunas
                    colunas_tabela = colunas
                else:
                    # Múltiplas tabelas, geralmente uma coluna por tabela
                    colunas_tabela = [colunas[idx]] if idx < len(colunas) else [colunas[0]]
                
                # Monta a query
                colunas_str = ', '.join([f"`{col}`" for col in colunas_tabela])
                query = f"""
                    SELECT data_hora, {colunas_str}
                    FROM `{tabela}`
                    WHERE data_hora BETWEEN %s AND %s
                    ORDER BY data_hora
                """
                
                # print(f"Query para {tabela}: {query}")  # Debug
                
                # Executa query
                cursor.execute(query, (data_inicio, data_fim))
                colunas_nomes = [desc[0] for desc in cursor.description]
                resultados = cursor.fetchall()
                
                if resultados:
                    # Converte para DataFrame
                    df_temp = pd.DataFrame(resultados, columns=colunas_nomes)
                    df_temp['data_hora'] = pd.to_datetime(df_temp['data_hora'])
                    df_temp = self.tratamento_df(df_temp)
                    
                    # Adiciona prefixo se múltiplas tabelas
                    if len(tabelas) > 1:
                        # Renomeia colunas para identificar a UG
                        for col in colunas_tabela:
                            if col in df_temp.columns:
                                novo_nome = f"ug{idx+1:02d}_{col}"
                                df_temp.rename(columns={col: novo_nome}, inplace=True)
                        df_temp['data_hora'] = df_temp['data_hora'].dt.round('min')
                    
                    todos_dados.append(df_temp)
            
            # Combina todos os DataFrames
            if not todos_dados:
                return pd.DataFrame()
            
            if len(todos_dados) == 1:
                return todos_dados[0]
            else:
                # Merge dos DataFrames por data_hora
                df_final = todos_dados[0]
                for df in todos_dados[1:]:
                    df_final = pd.merge(
                        df_final, df, 
                        on='data_hora', 
                        how='outer'
                    )
                return df_final.sort_values('data_hora')
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

# ======================== PROCESSAMENTO ========================
class ProcessadorProducao:
    """Processa dados de produção de energia"""
    
    @staticmethod
    def calcular_producao(df: pd.DataFrame, periodo: str, usina: str) -> dict:
        """Calcula a produção de energia para o período especificado"""
        
        if df.empty:
            return {
                "status": "sem_dados",
                "usina": usina,
                "mensagem": "Nenhum dado encontrado para o período especificado"
            }
        
        # Identifica colunas de energia (todas exceto data_hora)
        colunas_energia = [col for col in df.columns if col != 'data_hora']
        
        # Remove valores inválidos (103.00 = erro de leitura)
        for col in colunas_energia:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df.loc[df[col] == 103.00, col] = None
        
        # Define data_hora como índice
        df.set_index('data_hora', inplace=True)
        
        resultado_producao = {}
        producao_total = pd.Series(dtype=float)
        
        for coluna in colunas_energia:
            # Resample e pega o último valor de cada período
            valores_periodo = df[coluna].resample(periodo).last()
            
            # Calcula a diferença (produção no período)
            producao = valores_periodo.diff().fillna(0)
            
            # Remove valores negativos (possível reset de contador)
            producao[producao < 0] = 0
            
            # Adiciona ao total
            if producao_total.empty:
                producao_total = producao.copy()
            else:
                producao_total = producao_total.add(producao, fill_value=0)
            
            # Formata nome da UG
            if 'ug' in coluna.lower():
                nome_ug = coluna.split('_')[0].upper()
            else:
                nome_ug = f"UG{colunas_energia.index(coluna)+1:02d}"
            
            # Armazena resultado individual
            resultado_producao[nome_ug] = [
                {
                    "data": data.strftime('%Y-%m-%d %H:%M:%S'),
                    "producao_kwh": round(float(valor), 2)
                }
                for data, valor in producao.items()
                if valor > 0  # Só inclui períodos com produção
            ]
        
        # Calcula produção total
        producao_total_list = [
            {
                "data": data.strftime('%Y-%m-%d %H:%M:%S'),
                "producao_total_kwh": round(float(valor), 2)
            }
            for data, valor in producao_total.items()
            if valor > 0
        ]
        
        # Estatísticas
        estatisticas = {
            "producao_total_periodo": round(float(producao_total.sum()), 2),
            "producao_media": round(float(producao_total[producao_total > 0].mean()), 2) if not producao_total.empty else 0,
            "dias_com_producao": len(producao_total[producao_total > 0]),
            "primeiro_registro": df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
            "ultimo_registro": df.index.max().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return {
            "status": "sucesso",
            "usina": usina,
            "periodo": periodo,
            "unidades_geradoras": resultado_producao,
            "producao_total": producao_total_list,
            "estatisticas": estatisticas
        }

# ======================== ROTAS ========================
@app.post("/producao-acumulada")
async def producao_acumulada(request: ProducaoRequest):
    """
    Retorna a produção acumulada de energia de uma usina.
    
    A API automaticamente identifica as tabelas e colunas corretas
    baseado no nome da usina fornecido.
    
    **Usinas disponíveis:**
    - CGH-APARECIDA
    - CGH-FAE
    - PCH-PEDRAS
    - CGH-PICADAS-ALTAS
    - CGH-HOPPEN
    - CGH-GRANADA
    - CGH-BECKER
    
    **Períodos:**
    - D ou Diário: Produção diária
    - M ou Mensal: Produção mensal
    - H ou Horário: Produção por hora
    """
    
    # Verificar token (opcional)
    if request.token:
        token_valido = os.getenv('API_TOKEN', '123456')
        if request.token != token_valido:
            raise HTTPException(status_code=401, detail="Token inválido")
    
    try:
        # Buscar dados automaticamente baseado na usina
        db = Database()
        df = db.buscar_dados_usina(
            usina=request.usina,
            tipo="energia",
            data_inicio=request.data_inicio,
            data_fim=request.data_fim
        )
        print(df)
        
        # Processar dados
        resultado = ProcessadorProducao.calcular_producao(
            df=df,
            periodo=request.periodo,
            usina=request.usina
        )
        
        return resultado
        # return {
        #         "status": "sem_dados",
        #         "usina": request.usina,
        #         "mensagem": "Nenhum dado encontrado para o período especificado"
        #     }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao processar dados da usina {request.usina}: {str(e)}"
        )

@app.get("/")
async def root():
    """Rota principal com informações da API"""
    return {
        "api": "ENGESEP - Sistema de Monitoramento de Produção de Energia",
        "versao": "1.0.0",
        "endpoints": {
            "/producao-acumulada": "POST - Consulta produção de energia",
            "/usinas": "GET - Lista usinas disponíveis",
            "/docs": "GET - Documentação interativa"
        }
    }

@app.get("/usinas")
async def listar_usinas():
    """Lista todas as usinas disponíveis e suas configurações"""
    return {
        "usinas_disponiveis": [
            {
                "codigo": codigo,
                "descricao": config["descricao"],
                "num_tabelas": len(config["tabelas"]),
                "num_unidades_geradoras": len(config["colunas"])
            }
            for codigo, config in USINAS_CONFIG.items()
        ]
    }

@app.get("/health")
async def health():
    """Verifica o status da API e conexão com banco"""
    try:
        conn = Database.get_connection()
        conn.close()
        return {
            "status": "operacional",
            "database": "conectado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "com_problemas",
            "database": "desconectado",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ======================== INICIALIZAÇÃO ========================
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 ENGESEP API - Produção de Energia")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"📚 Documentação: http://{host}:{port}/docs")
    print(f"🏭 Usinas configuradas: {len(USINAS_CONFIG)}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

# """
# API de resposta do sistema de monitoramento de usinas.
# Autor: Miliano Fernandes de Oliveira
# Data de criação: 2025-08-12
# Última modificação: 2025-08-12
# """
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, validator
# from datetime import datetime, timedelta
# from typing import List, Optional
# from dotenv import load_dotenv
# import mysql.connector
# import pandas as pd
# import uvicorn
# import os
# import re

# load_dotenv()

# # ======================== CONFIGURAÇÃO ========================
# app = FastAPI(
#     title="ENGESEP API v1",
#     description="API simplificada para monitoramento de usinas",
#     version="1.0.0",
# )

# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Em produção, especifique os domínios
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ======================== MODELOS ========================
# class ProducaoRequest(BaseModel):
#     """Modelo de requisição para produção acumulada"""
#     tabela: str
#     colunas: List[str]
#     data_inicio: str
#     data_fim: str
#     periodo: str = 'D'  # D=Diário, M=Mensal, H=Horário
#     token: Optional[str] = None
    
#     @validator('tabela')
#     def validar_tabela(cls, v):
#         # Aceita apenas nomes de tabela seguros
#         if not re.match(r'^[a-zA-Z0-9_]+$', v):
#             raise ValueError('Nome da tabela inválido')
#         return v
    
#     @validator('data_inicio', 'data_fim')
#     def validar_datas(cls, v):
#         try:
#             # Aceita formato YYYY-MM-DD ou DD/MM/YYYY
#             if '/' in v:
#                 datetime.strptime(v, '%d/%m/%Y')
#             else:
#                 datetime.strptime(v, '%Y-%m-%d')
#             return v
#         except ValueError:
#             raise ValueError('Data deve estar no formato YYYY-MM-DD ou DD/MM/YYYY')
    
#     @validator('periodo')
#     def validar_periodo(cls, v):
#         if v not in ['D', 'M', 'H']:
#             raise ValueError('Período deve ser D (diário), M (mensal) ou H (horário)')
#         return v

# # ======================== BANCO DE DADOS ========================
# class Database:
#     """Gerenciador de conexão com o banco de dados"""
    
#     @staticmethod
#     def get_connection():
#         """Cria uma nova conexão com o banco"""
#         try:
#             return mysql.connector.connect(
#                 host=os.getenv('MYSQLHOST'),
#                 user=os.getenv('MYSQLUSER'),
#                 password=os.getenv('MYSQLPASSWORD'),
#                 database=os.getenv('MYSQLDATABASE'),
#                 port=int(os.getenv('MYSQLPORT', 3306))
#             )
#         except mysql.connector.Error as e:
#             raise HTTPException(status_code=500, detail=f"Erro de conexão: {e}")
    
#     @staticmethod
#     def fetch_data(tabela: str, colunas: List[str], data_inicio: str, data_fim: str) -> pd.DataFrame:
#         """Busca dados do banco e retorna como DataFrame"""
#         connection = None
#         try:
#             # Formatar datas para o padrão MySQL
#             if '/' in data_inicio:
#                 data_inicio = datetime.strptime(data_inicio, '%d/%m/%Y').strftime('%Y-%m-%d')
#             if '/' in data_fim:
#                 data_fim = datetime.strptime(data_fim, '%d/%m/%Y').strftime('%Y-%m-%d')
            
#             # Conectar e buscar dados
#             connection = Database.get_connection()

#             colunas = {
#                 "CGH-APARECIDA": {
#                     "table": ["cgh_aparecida"],
#                     "colunas": ["acumulador_energia"]
#                 },
#                 "CGH-FAE": {
#                     "table": ["cgh_fae"],
#                     "colunas": ["ug01_acumulador_energia", "ug02_acumulador_energia"]
#                 },
#                 "PCH-PEDRAS": {
#                     "table": ["pch_pedras_ug01", "pch_pedras_ug02"],
#                     "colunas": ["acum_energia"]
#                 },
#                 "CGH-PICADAS-ALTAS": {
#                     "table": ["cgh_picadas_altas"],
#                     "colunas": ["ug01_acumulador_energia", "ug02_acumulador_energia"]
#                 },
#                 "CGH-HOPPEN": {
#                     "table": ["cgh_hoppen_ug01", "cgh_hoppen_ug02"],
#                     "colunas": ["acumulador_energia"]
#                 }
#             }
            
#             # Construir query com placeholders seguros
#             colunas_str = ', '.join([f"`{col}`" for col in colunas])
#             query = f"""
#                 SELECT data_hora, {colunas_str} 
#                 FROM `{tabela}` 
#                 WHERE data_hora BETWEEN %s AND %s
#                 ORDER BY data_hora
#             """
            
#             # Usar pandas para ler direto do banco
#             df = pd.read_sql(
#                 query, 
#                 connection, 
#                 params=(data_inicio, data_fim),
#                 parse_dates=['data_hora']
#             )
            
#             return df
            
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {e}")
#         finally:
#             if connection and connection.is_connected():
#                 connection.close()

# # ======================== PROCESSAMENTO ========================
# class ProcessadorProducao:
#     """Processa dados de produção de energia"""
    
#     @staticmethod
#     def calcular_producao(df: pd.DataFrame, periodo: str, colunas: List[str]) -> dict:
#         """Calcula a produção de energia para o período especificado"""
        
#         if df.empty:
#             return {"status": "sem_dados", "dados": []}
        
#         # Remover valores inválidos (103.00 = erro de leitura)
#         for col in colunas:
#             if col in df.columns:
#                 df = df[df[col] != 103.00]
#                 df[col] = pd.to_numeric(df[col], errors='coerce')
        
#         resultado = {}
        
#         for coluna in colunas:
#             if coluna not in df.columns:
#                 continue
                
#             if periodo == 'D':
#                 # Agrupamento diário
#                 df_agrupado = df.set_index('data_hora').resample('D')[coluna].last()
#                 producao = df_agrupado.diff().fillna(0)
                
#             elif periodo == 'M':
#                 # Agrupamento mensal
#                 df_agrupado = df.set_index('data_hora').resample('M')[coluna].last()
#                 producao = df_agrupado.diff().fillna(0)
                
#             elif periodo == 'H':
#                 # Agrupamento horário
#                 df_agrupado = df.set_index('data_hora').resample('H')[coluna].last()
#                 producao = df_agrupado.diff().fillna(0)
            
#             # Converter para formato de resposta
#             resultado[coluna] = [
#                 {
#                     "data": str(data),
#                     "valor": round(float(valor), 2) if pd.notna(valor) else 0
#                 }
#                 for data, valor in producao.items()
#             ]
        
#         return {
#             "status": "sucesso",
#             "periodo": periodo,
#             "dados": resultado
#         }

# # ======================== AUTENTICAÇÃO SIMPLES ========================
# def verificar_token(token: str) -> bool:
#     """Verifica se o token é válido (implementação simplificada)"""
#     token_valido = os.getenv('API_TOKEN', '123456')
#     return token == token_valido

# # ======================== ROTAS ========================
# @app.post("/data/producao_acumulada")
# async def producao_acumulada(request: ProducaoRequest):
#     """
#     Retorna a produção acumulada de energia.
    
#     Períodos disponíveis:
#     - D: Diário
#     - M: Mensal
#     - H: Horário
#     """
    
#     # Verificar token (opcional)
#     if request.token and not verificar_token(request.token):
#         raise HTTPException(status_code=401, detail="Token inválido")
    
#     try:
#         # Buscar dados
#         df = Database.fetch_data(
#             tabela=request.tabela,
#             colunas=request.colunas,
#             data_inicio=request.data_inicio,
#             data_fim=request.data_fim
#         )
        
#         # Processar dados
#         resultado = ProcessadorProducao.calcular_producao(
#             df=df,
#             periodo=request.periodo,
#             colunas=request.colunas
#         )
        
#         return resultado
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# @app.get("/")
# async def root():
#     """Rota de verificação"""
#     return {
#         "status": "online",
#         "api": "ENGESEP v1",
#         "endpoints": ["/data/producao_acumulada"]
#     }

# @app.get("/health")
# async def health():
#     """Health check da API"""
#     try:
#         # Testa conexão com banco
#         conn = Database.get_connection()
#         conn.close()
#         return {"status": "healthy", "database": "connected"}
#     except:
#         return {"status": "unhealthy", "database": "disconnected"}

# # ======================== INICIALIZAÇÃO ========================
# if __name__ == "__main__":
#     host = os.getenv("HOST", "0.0.0.0")
#     port = int(os.getenv("PORT", 8000))
    
#     print(f"🚀 Servidor iniciando em {host}:{port}")
    
#     uvicorn.run(
#         "main:app",
#         host=host,
#         port=port,
#         reload=True,  # Desativar em produção
#         log_level="info"
#     )




# """
# API de resposta do sistema de monitoramento de usinas.
# Autor: Miliano Fernandes de Oliveira
# Data de criação: 2025-08-12
# Última modificação: 2025-08-12
# """
# from fastapi import FastAPI
# from multiprocessing import Process
# import uvicorn
# import json
# import os
# import time
# from fastapi.middleware.cors import CORSMiddleware
# from datetime import datetime, timedelta
# from fastapi import Request, HTTPException
# from dotenv import load_dotenv
# import mysql.connector
# import pandas as pd

# load_dotenv()

# '''Definição da aplicação FastAPI'''
# app = FastAPI(
#     title="ENGESEP",
#     description="Documentação da API ENGESEP",
#     version="1.0.0",
# )

# # configurar o CORS
# origins = [
#     "http://localhost",
#     "http://0.0.0.0",
#     "https://engeapp.flutterflow.app",  # Inclua o domínio do seu app
#     "https://fastapi-production-8d7e.up.railway.app",  # Inclua o domínio do Railway
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# async def connect_db():
#     # Obter as variáveis de ambiente
#     host = os.getenv('MYSQLHOST')
#     user = os.getenv('MYSQLUSER')
#     password = os.getenv('MYSQLPASSWORD')
#     database = os.getenv('MYSQLDATABASE')
#     port = os.getenv('MYSQLPORT')
#     token = os.getenv('TOKEN')

#     # Conectar ao banco de dados
#     connection = mysql.connector.connect(
#         host=host,
#         user=user,
#         password=password,
#         database=database,
#         port=port,
#     )
#     return connection

# async def get_data(tabela, colunas, data_inicio, data_fim):
#     # Conectar ao banco de dados
#     connection = await connect_db()
#     cursor = connection.cursor()
#     colunas_ = ','.join(colunas)
#     query = f"SELECT data_hora, {colunas_} FROM {tabela} WHERE data_hora BETWEEN '{data_inicio}' AND '{data_fim}'"
#     cursor.execute(query)
#     result = cursor.fetchall()
#     connection.close()
#     return result

# async def calculate_data(df, periodo, colunas_energia):
#     if isinstance(colunas_energia, str):
#         colunas_energia = [colunas_energia]

#     mask = (df[colunas_energia] == 103.00).any(axis=1)
#     df = df[~mask]

#     if periodo == 'D':
#         df_diario = df.groupby(df['data_hora'].dt.date).last()

#         for col in colunas_energia:
#             if col in df_diario.columns:
#                 df_diario[col] = pd.to_numeric(df_diario[col], errors='coerce').astype(float)

#         # Calcular a produção (diferença entre valores consecutivos)
#         producao = df_diario[colunas_energia[0]].diff().fillna(0)

#         return producao

#     if periodo == 'M':
#         df['ano_mes'] = df['data_hora'].dt.strftime('%Y-%m')
#         df_mensal = df.groupby('ano_mes').last()

#         for col in colunas_energia:
#             if col in df_mensal.columns:
#                 df_mensal[col] = pd.to_numeric(df_mensal[col], errors='coerce').astype(float)

#         if len(df_mensal) < 6:
#             last_month = df_mensal.index[0]
#             after_last_month = datetime.strptime(last_month, '%Y-%m') - timedelta(days=30)
#             after_last_month = after_last_month.strftime('%Y-%m')
#             for col in colunas_energia:
#                 df_mensal.loc[after_last_month, col] = 0
#             df_mensal = df_mensal.sort_index()

#         # Calcular a produção (diferença entre valores consecutivos)
#         producao = df_mensal[colunas_energia[0]].diff().fillna(0)

#         return producao

#     if periodo == 'H':
#         df['hora'] = df['data_hora'].dt.floor('H')  # ou .dt.round('H') se preferir arredondar
#         df_hora = df.groupby('hora').last().reset_index()

#         for col in colunas_energia:
#             if col in df_hora.columns:
#                 df_hora[col] = pd.to_numeric(df_hora[col], errors='coerce').astype(float)

#         # Calcular a produção (diferença entre valores consecutivos)
#         producao = df_hora[colunas_energia[0]].diff().fillna(0)
#         producao.index = df_hora['hora']

#         return producao

# def sanitize(query):
#     ''' Sanitização das entradas '''
#     query = query.replace("'", "").replace(";", "").replace("=", "")
#     return query

# '''Definição das rotas da API'''
# app.post("/data/producao_acumulada")
# async def producao_acumulada(request: Request):
#     '''Endpoint para obter os dados da produção de energia acumulada em diferentes períodos de tempo'''
#     try:
#         data = await request.json()
#         data_inicio = data['data_inicio']
#         data_fim = data['data_fim']
#         colunas = data['colunas']
#         periodo = data['periodo']
#         tabela = data['tabela']
#         df = await get_data(tabela, data_inicio, data_fim)
#         producao = await calculate_data(df, periodo, colunas)
#         return producao
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao obter os dados: {e}")
    


# # 12 - Iniciar o servidor FastAPI
# def run_uvicorn():
#     ''' Iniciar o servidor FastAPI '''

#     # ler a variável de ambiente HOST
#     host = os.getenv("HOST", '0.0.0.0')

#     print('Servidor iniciado')

#     # iniciar o servidor FastAPI na porta 8000
#     uvicorn.run("main:app", host=host, port=8000, log_level="info")
    
# # 14 - Iniciar o servidor FastAPI em um novo processo
# if __name__ == "__main__":
#     ''' Função principal para executar o servidor FastAPI'''
#     run_uvicorn()