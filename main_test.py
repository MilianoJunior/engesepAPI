
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
from libs.email import main

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
app.post("/historico")(rotas.get_history)
app.post("/consult")(rotas.get_values)
app.post("/columns")(rotas.get_columns)
app.post("/data/producao_total")(rotas.get_production)


# 12 - Iniciar o servidor FastAPI
def run_uvicorn():
    ''' Iniciar o servidor FastAPI '''

    # ler a variável de ambiente HOST
    host = os.getenv("HOST", '0.0.0.0')

    # iniciar o servidor FastAPI na porta 8000
    uvicorn.run("main_test:app", host=host, port=8000, log_level="info")

# 13 - Criar a função de teste da API
def test_api():
    ''' Função de teste da API '''

    def imprimir_resposta(response):
        ''' Imprimir a resposta da API '''

        # Verificar se a resposta HTTP contém um corpo antes de tentar convertê-lo em JSON
        if response.content:
            try:
                response_dict = response.json()
            except ValueError:
                print("A resposta não é um JSON válido")
        else:
            print("A resposta HTTP está vazia")

        # imprimir a resposta
        for key, value in response_dict.items():
            if isinstance(value, dict):
                print(f"1 - Key: {key} ")
                for k, v in value.items():
                    print('     2 - Key: ', k, 'Value: ', v)

    def test_acumulador_energia(time, url):
        ''' Testar a API para a coluna acumulador_energia '''
        url = url.replace('rota', 'data/producao_acumulada')

        # período de teste
        periodo = ['hour', 'day', 'week', 'month', 'year']

        for p in periodo:
            # imprimir o período de teste
            print('###' * 20)
            print(f'Testando o período: {p}')
            print(url)
            print('###' * 20)
            # corpo da requisição
            body = {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": p,
                "data_inicio": "24/01/2021",
                "data_fim": "28/01/2021",
                "token": "123456",
            }

            # cabeçalho da requisição
            headers = {'Content-type': 'application/json'}

            # fazer a requisição POST
            response = requests.post(url, data=json.dumps(body), headers=headers)

            # imprimir o status code
            if response.status_code == 200:
                # imprimir a mensagem de requisição bem sucedida
                # imprimir_resposta(response)
                print(response.text)

            else:
                print(f"Erro ao fazer a requisição: {response.text}")
            print(f'Tempo de execução: {time.time() - inicio} segundos')
            print('---' * 20)

    def test_columns(time, url):
        ''' Testar a API para a coluna columns '''
        url = url.replace('rota', 'columns')

        # imprimir a url
        print('---' * 20)
        print(url)
        print('---' * 20)

        # corpo da requisição
        body = {
            "usina": "jasp_test",
            "token": "123456",
        }

        # cabeçalho da requisição
        headers = {'Content-type': 'application/json'}

        # fazer a requisição POST
        response = requests.post(url, data=json.dumps(body), headers=headers)

        # imprimir o status code
        if response.status_code == 200:
            # imprimir a mensagem de requisição bem sucedida
            imprimir_resposta(response)

        else:
            print(f"Erro ao fazer a requisição: {response.text}")
        print(f'Tempo de execução: {time.time() - inicio} segundos')
        print('---' * 20)


    def test_values(time, url):
        ''' Testar a API para a coluna acumulador_energia '''
        url = url.replace('rota', 'consult')

        # período de teste
        periodo = ['hour', 'day', 'week', 'month', 'year']

        for p in periodo:
            # imprimir o período de teste
            print('###' * 20)
            print(f'Testando o período: {p}')
            print(url)
            print('###' * 20)
            # corpo da requisição
            body = {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": p,
                "data_inicio": "24/01/2021",
                "data_fim": "28/01/2021",
                "token": "123456",
            }

            # cabeçalho da requisição
            headers = {'Content-type': 'application/json'}

            # fazer a requisição POST
            response = requests.post(url, data=json.dumps(body), headers=headers)

            # imprimir o status code
            if response.status_code == 200:
                # imprimir a mensagem de requisição bem sucedida
                # imprimir_resposta(response)
                print(response.text)

            else:
                print(f"Erro ao fazer a requisição: {response.text}")
            print(f'Tempo de execução: {time.time() - inicio} segundos')
            print('---' * 20)

    def test_historico(time, url):
        ''' Testar a API para a coluna acumulador_energia '''
        url = url.replace('rota', 'historico')

        # período de teste
        periodo = ['hour', 'day', 'week', 'month', 'year']

        for p in periodo:
            # imprimir o período de teste
            print('###' * 20)
            print(f'Testando o período: {p}')
            print(url)
            print('###' * 20)
            # corpo da requisição
            body = {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": p,
                "data_inicio": "24/01/2021",
                "data_fim": "28/01/2021",
                "token": "123456",
            }

            # cabeçalho da requisição
            headers = {'Content-type': 'application/json'}

            # fazer a requisição POST
            response = requests.post(url, data=json.dumps(body), headers=headers)

            # imprimir o status code
            if response.status_code == 200:
                # imprimir a mensagem de requisição bem sucedida
                # imprimir_resposta(response)
                print(response.text)

            else:
                print(f"Erro ao fazer a requisição: {response.text}")
            print(f'Tempo de execução: {time.time() - inicio} segundos')
            print('---' * 20)

    def test_producao_total(time, url):
        ''' Testar a API para a coluna acumulador_energia '''

        url = url.replace('rota', 'data/producao_total')

        body = {
                "usina": "cgh_aparecida",
                "token": "123456",
        }

        # cabeçalho da requisição
        headers = {'Content-type': 'application/json'}

        # fazer a requisição POST
        response = requests.post(url, data=json.dumps(body), headers=headers)

        # imprimir o status code
        if response.status_code == 200:
            # imprimir a mensagem de requisição bem sucedida
            # imprimir_resposta(response)
            print(response.text)

        else:
            print(f"Erro ao fazer a requisição: {response.text}")
        print(f'Tempo de execução: {time.time() - inicio} segundos')
        print('---' * 20)

    # Iniciar o tempo de execução=========================
    inicio = time.time()
    print('---' * 20)
    print('Iniciando a função de teste da API')
    # main()  # Enviar email
    # url da API
    # url = 'https://fastapi-production-8d7e.up.railway.app/data/producao_acumulada'
    url = 'http://127.0.0.1:8000/rota'
    # url = 'https://fastapi-production-8d7e.up.railway.app/rota'
    # # Testar a API para a coluna acumulador_energia
    # test_acumulador_energia(time, url)

    # Testar a API para a coluna columns
    # test_columns(time, url)
    # print('####################' * 20)
    # Testar a API para a coluna values
    # test_values(time, url)
    # print('####################' * 20)
    # Testar a API para a coluna historico
    # test_historico(time, url)
    print('####################' * 20)
    # Testar a API para a coluna producao_total
    test_producao_total(time, url)



# 14 - Iniciar o servidor FastAPI em um novo processo
if __name__ == "__main__":
    ''' Função principal para executar o servidor FastAPI'''

    # ler a variável de ambiente DEBUG
    inicio = time.time()
    debug = 1
    # test_api()
    #
    # fim = time.time()
    # print('---' * 20)
    # print(f"Tempo de execução: {fim - inicio} segundos")


    # verificar se o modo de depuração está ativado
    if bool(debug):
        # imprimir a mensagem de depuração ativada
        print("Modo de depuração ativado.")

        # Inicialize o servidor FastAPI em um novo processo
        server_process = Process(target=run_uvicorn)
        server_process.start()

        # Espere um pouco para garantir que o servidor esteja em execução
        time.sleep(1)

        # Inicialize a função de teste em um novo processo
        test_process = Process(target=test_api)
        test_process.start()

        time.sleep(2)
        # Junte os processos para esperar que eles terminem
        test_process.join()
        server_process.terminate()
        server_process.join()
    else:
        # Iniciar o servidor FastAPI em produção
        run_uvicorn()

    # verificar o desempenho da API
    fim = time.time()
    print('---' * 20)
    print(f"Tempo de execução: {fim - inicio} segundos")




# O formato de resposta atual da API:
# {
#     "status":"ok",
#     "df":{
#             "ug01_acumulador_energia":
#                                     {
#                                         "2024-04-25T00:00:00":3561.247,
#                                         "2024-04-26T00:00:00":3561.247
#                                     },
#             "ug02_acumulador_energia":
#                                     {
#                                         "2024-04-25T00:00:00":3616.197,
#                                         "2024-04-26T00:00:00":3561.247
#                                     },
#     }
# }
#
# O formato requerido:
#
# se eu precisar acrescentar outros dias ou Unidades Geradoras (UGs), como seria a estrutura do JSON?
# {
#   "status": "ok",
#   "df": [
#         {
#           "geradora": "UG01",
#           "leitura": "2024-04-25T00:00:00",
#           "acumulado": 42.954,
#         },
#         {
#           "geradora": "UG01",
#           "leitura": "2024-04-26T00:00:00",
#           "acumulado": 42.954,
#         },
#         {
#           "geradora": "UG02",
#           "leitura": "2024-04-25T00:00:00",
#           "acumulado": 42.954
#         },
#        {
#           "geradora": "UG02",
#           "leitura": "2024-04-26T00:00:00",
#           "acumulado": 42.954,
#        },
#   ]
# }
#
# Se precisar inserir mais valores de periodos diarios, semanais, mensais e anuais, como seria a estrutura do JSON?
#
# {
#   "status": "ok",
#   "df": [
#     {
#       "geradora": "UG01",
#       "leitura": "2024-04-25T00:00:00",
#       "acumulado": 42.954
#     },
#     {
#       "geradora": "UG02",
#       "leitura": "2024-04-25T00:00:00",
#       "acumulado": 42.954
#     }
#   ]
# }
#
# É necessário fazer a conversão do formato atual para o formato requerido?




