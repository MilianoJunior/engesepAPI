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
from apscheduler.schedulers.background import BackgroundScheduler
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

'''
Definição das rotas da API
'''
rotas = Rotas()


'''
Definição data que torna os dados da produção de energia acumulada
'''

'''
Endpoint para obter os dados da produção acumulada
Para diferentes períodos de tempo

'''
app.post("/data/producao_acumulada")(rotas.get_data)
app.post("/historico")(rotas.get_history)
app.post("/consult")(rotas.get_values)
app.post("/columns")(rotas.get_columns)


def evento():
    ''' Função para enviar email todos os dias as 08:00 '''

    # importar a função main do arquivo email.py -  A lógica está testada e enviando email corretamente
    from libs.email import main
    print('Evento disparado as 15:10')

    main()

def start_scheduler():
    ''' Iniciar o agendador APScheduler '''
    scheduler = BackgroundScheduler()
    # Agendar a função evento para ser executada todos os dias às 08:00
    scheduler.add_job(evento, 'cron', hour=15, minute=22)
    scheduler.start()

    # Garantir que o agendador pare ao desligar o programa
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()



# 12 - Iniciar o servidor FastAPI
def run_uvicorn():
    ''' Iniciar o servidor FastAPI '''

    # ler a variável de ambiente HOST
    host = os.getenv("HOST", '0.0.0.0')

    # iniciar agendador de tarefas em um thread separado
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()

    print('Servidor iniciado')

    # iniciar o servidor FastAPI na porta 8000
    uvicorn.run("main:app", host=host, port=8000, log_level="info")

# 13 - Criar a função de teste da API


# 14 - Iniciar o servidor FastAPI em um novo processo
if __name__ == "__main__":
    ''' Função principal para executar o servidor FastAPI'''
    run_uvicorn()