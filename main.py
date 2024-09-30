"""
API de resposta do sistema de monitoramento de usinas.
Autor: Miliano Fernandes de Oliveira
Data de criação: 2024-04-11
Última modificação: 2024-04-17
"""
from fastapi import FastAPI
from multiprocessing import Process
from libs.rotas import Rotas
import uvicorn
import requests
import json
import os
import time
from fastapi.middleware.cors import CORSMiddleware
# from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import threading

'''
Definição da aplicação FastAPI
'''

app = FastAPI(
    title="ENGESEP",
    description="Documentação da API ENGESEP",
    version="1.0.0",
)

# configurar o CORS
origins = [
    "http://localhost",
    "http://0.0.0.0",
    "https://engeapp.flutterflow.app",  # Inclua o domínio do seu app
    "https://fastapi-production-8d7e.up.railway.app",  # Inclua o domínio do Railway
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
Definição das rotas da API
'''
rotas = Rotas()


'''Endpoint para obter os dados da produção de energia acumulada em diferentes períodos de tempo'''
app.post("/data/producao_acumulada")(rotas.get_production_acumulated)

'''Endpoint para obter os dados de qualquer coluna em diferentes períodos de tempo, menos a coluna da produção de energia acumulada'''
app.post("/historico")(rotas.get_history)

''' Endpoint para obter os valores das colunas da tabela solicitada'''
app.post("/consult")(rotas.get_consult)

''' Endpoint para obter as colunas da tabela solicitada '''
app.post("/columns")(rotas.get_columns)

''' Endpoint para obter os dados da produção total de energia '''
app.post("/data/producao_total")(rotas.get_production_all)


# 12 - Iniciar o servidor FastAPI
def run_uvicorn():
    ''' Iniciar o servidor FastAPI '''

    # ler a variável de ambiente HOST
    host = os.getenv("HOST", '0.0.0.0')

    print('Servidor iniciado')

    # iniciar o servidor FastAPI na porta 8000
    uvicorn.run("main:app", host=host, port=8000, log_level="info")

# 13 - Criar a função de teste da API


# 14 - Iniciar o servidor FastAPI em um novo processo
if __name__ == "__main__":
    ''' Função principal para executar o servidor FastAPI'''
    run_uvicorn()