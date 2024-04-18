"""
API de resposta do sistema de monitoramento de usinas.
Autor: Miliano Fernandes de Oliveira
Data de criação: 2024-04-11
Última modificação: 2024-04-17
"""
from fastapi import FastAPI, HTTPException, Response
from multiprocessing import Process
from libs.rotas import Rotas
import uvicorn
import requests
import json
import os
import time

'''
Definição da aplicação FastAPI
'''
app = FastAPI()

'''
Definição das rotas da API
'''
rotas = Rotas()


'''
Definição data que torna os dados da produção de energia acumulada
'''
app.post("/data/producao_acumulada")(rotas.get_data)


# 12 - Iniciar o servidor FastAPI
def run_uvicorn():
    ''' Iniciar o servidor FastAPI '''

    # ler a variável de ambiente HOST
    host = os.getenv("HOST", '0.0.0.0')

    # iniciar o servidor FastAPI na porta 8000
    uvicorn.run("main:app", host=host, port=8000, log_level="info")

# 13 - Criar a função de teste da API


# 14 - Iniciar o servidor FastAPI em um novo processo
if __name__ == "__main__":
    ''' Função principal para executar o servidor FastAPI'''
    run_uvicorn()