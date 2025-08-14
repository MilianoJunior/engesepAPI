# test_api.py
# from termios import OPOST
import time
import requests
import json

# API 1
# rodada 1
# Tempo de execução: 3.584033966064453 segundos
# INFO:     127.0.0.1:50779 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.67785382270813 segundos
# INFO:     127.0.0.1:50783 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.862225294113159 segundos
# INFO:     127.0.0.1:50786 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.2053720951080322 segundos
# INFO:     127.0.0.1:50789 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.766193151473999 segundos
# rodada 2
# Tempo de execução: 4.744945049285889 segundos
# INFO:     127.0.0.1:50887 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.5644612312316895 segundos
# INFO:     127.0.0.1:50890 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.009774684906006 segundos
# INFO:     127.0.0.1:50893 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.3909690380096436 segundos
# INFO:     127.0.0.1:50896 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.855095624923706 segundos
# INFO:     127.0.0.1:50899 - "OPOST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 29.99523091316223 segundos
# Tempo de execução: 29.378562211990356 segundos



# API 2
# rodada 1
# Tempo de execução: 3.7971107959747314 segundos
# INFO:     127.0.0.1:50606 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.234118700027466 segundos
# INFO:     127.0.0.1:50609 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 5.101615905761719 segundos
# INFO:     127.0.0.1:50612 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.9254415035247803 segundos
# INFO:     127.0.0.1:50615 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.270882606506348 segundos
# rodada 2
# Tempo de execução: 3.941045045852661 segundos
# INFO:     127.0.0.1:50921 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.864314079284668 segundos
# INFO:     127.0.0.1:50924 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.7361345291137695 segundos
# INFO:     127.0.0.1:50927 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 3.293816089630127 segundos
# INFO:     127.0.0.1:50930 - "POST /producao-acumulada HTTP/1.1" 200 OK
# Tempo de execução: 4.799042224884033 segundos
# Tempo de execução: 31.324167251586914 segundos

# Configuração
BASE_URL = "http://localhost:8000"
# BASE_URL = "https://engesepapi-production.up.railway.app"

def testar_producao():
    """Testa endpoint de produção acumulada"""
    inicio = time.time()
    for periodo in ["M"]: #, "M", "H"]:
        for usina in ["CGH-APARECIDA", "CGH-FAE", "PCH-PEDRAS", "CGH-PICADAS-ALTAS", "CGH-HOPPEN"]:
            payload = {
                "usina": usina,
                "data_inicio": "10/07/2025 00:00",
                "data_fim": "13/08/2025 17:00",
                "periodo": periodo,
                "token": "123456"
            }
        
            try:
                response = requests.post(
                    f"{BASE_URL}/producao-acumulada",
                    json=payload
                )
                print(f"Usina: {usina}")
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        resposta_json = response.json()
                        print(f"Resposta: {json.dumps(resposta_json, indent=2)}")
                    except json.JSONDecodeError as e:
                        print(f"Erro ao decodificar JSON: {e}")
                        print(f"Resposta bruta: {response.text}")
                else:
                    print(f"Resposta: {response.text}")
                
                print(f"Período: {periodo}")
                print("-" * 50)
                
            except Exception as e:
                print(f"Erro na requisição para {usina}: {e}")
                print("-" * 50)
    fim = time.time()
    print(f"Tempo de execução: {fim - inicio} segundos")

if __name__ == "__main__":
    testar_producao()
# """
# API de resposta do sistema de monitoramento de usinas.
# Autor: Miliano Fernandes de Oliveira
# Data de criação: 2024-04-11
# Última modificação: 2024-04-17
# """
# from fastapi import FastAPI, HTTPException, Response
# from multiprocessing import Process
# from libs.rotas import Rotas
# import uvicorn
# import requests
# import json
# import os
# import time
# from libs.email import main
# from tabulate import tabulate

# '''
# Definição da aplicação FastAPI
# '''
# app = FastAPI()

# '''
# Definição das rotas da API
# '''
# rotas = Rotas()

# '''
# Definição data que torna os dados da produção de energia acumulada
# '''
# app.post("/data/producao_acumulada")(rotas.get_production_acumulated)
# app.post("/historico")(rotas.get_history)
# app.post("/consult")(rotas.get_consult)
# app.post("/columns")(rotas.get_columns)
# app.post("/data/producao_total")(rotas.get_production_all)

# # 12 - Iniciar o servidor FastAPI
# def run_uvicorn():
#     ''' Iniciar o servidor FastAPI '''

#     # ler a variável de ambiente HOST
#     host = os.getenv("HOST", '0.0.0.0')

#     # iniciar o servidor FastAPI na porta 8000
#     uvicorn.run("main_test:app", host=host, port=8000, log_level="info")

# # 13 - Criar a função de teste da API
# def test_api():
#     ''' Função de teste da API '''

#     def imprimir_resposta(response):
#         ''' Imprimir a resposta da API '''

#         print('---' * 20)
#         print('Imprimindo a resposta da API')
#         response_dict = response.json()

#         # imprimir a resposta
#         formatted_json = json.dumps(response_dict, indent=4)

#         print(formatted_json)

#     def test_endpoint(endpoint, body, description=""):
#         ''' Testar um endpoint específico '''
#         url = f'http://localhost:8000/{endpoint}'
        
#         print('=' * 60)
#         print(f'Testando: {description}')
#         print(f'Endpoint: {endpoint}')
#         print(f'URL: {url}')
#         print('=' * 60)
        
#         headers = {'Content-type': 'application/json'}
        
#         try:
#             response = requests.post(url, data=json.dumps(body), headers=headers)
            
#             print(f'Status Code: {response.status_code}')
            
#             if response.status_code == 200:
#                 print('✅ Requisição bem-sucedida!')
#                 imprimir_resposta(response)
#             else:
#                 print(f'❌ Erro na requisição: {response.status_code}')
#                 print(f'Resposta: {response.text}')
                
#         except Exception as e:
#             print(f'❌ Erro de conexão: {e}')
            
#         print(f'Tempo de execução: {time.time() - inicio:.2f} segundos')
#         print('-' * 60)

#     # Iniciar o tempo de execução=========================
#     inicio = time.time()
#     print('---' * 20)
#     print('Iniciando a função de teste da API')
#     print('---' * 20)

#     # Configurações de teste
#     base_url = 'http://localhost:8000'
    
#     # Teste 1: Produção Acumulada
#     test_endpoint(
#         'data/producao_acumulada',
#         {
#             "usina": "cgh_granada",
#             "coluna": ["acumulador_energia"],
#             "periodo": "day",
#             "data_inicio": "01/09/2024",
#             "data_fim": "14/10/2024",
#             "token": "123456",
#         },
#         "Produção Acumulada - Energia"
#     )

#     # Teste 2: Histórico
#     test_endpoint(
#         'historico',
#         {
#             "usina": "cgh_becker",
#             "coluna": ["energia"],
#             "periodo": "day",
#             "data_inicio": "01/10/2024",
#             "data_fim": "14/10/2024",
#             "token": "123456",
#         },
#         "Histórico de Energia"
#     )

#     # Teste 3: Consulta
#     test_endpoint(
#         'consult',
#         {
#             "usina": "cgh_becker",
#             "coluna": ["ug01_status"],
#             "periodo": "hour",
#             "data_inicio": "08/10/2024",
#             "data_fim": "09/10/2024",
#             "token": "123456",
#         },
#         "Consulta de Status UG01"
#     )

#     # Teste 4: Colunas
#     test_endpoint(
#         'columns',
#         {
#             "usina": "cgh_aparecida",
#             "token": "123456",
#         },
#         "Listagem de Colunas"
#     )

#     # Teste 5: Produção Total
#     test_endpoint(
#         'data/producao_total',
#         {
#             "usina": "cgh_aparecida",
#             "token": "123456",
#         },
#         "Produção Total"
#     )

#     # Teste com diferentes períodos
#     periodos = ['hour', 'day', 'week', 'month', 'year']
#     for periodo in periodos:
#         test_endpoint(
#             'data/producao_acumulada',
#             {
#                 "usina": "cgh_granada",
#                 "coluna": ["acumulador_energia"],
#                 "periodo": periodo,
#                 "data_inicio": "01/09/2024",
#                 "data_fim": "14/10/2024",
#                 "token": "123456",
#             },
#             f"Produção Acumulada - Período {periodo.upper()}"
#         )

#     print('=' * 60)
#     print('🎯 TESTE COMPLETO!')
#     print(f'⏱️  Tempo total de execução: {time.time() - inicio:.2f} segundos')
#     print('=' * 60)

# # 14 - Iniciar o servidor FastAPI em um novo processo
# if __name__ == "__main__":
#     ''' Função principal para executar o servidor FastAPI'''

#     # ler a variável de ambiente DEBUG
#     inicio = time.time()
#     debug = 1

#     # verificar se o modo de depuração está ativado
#     if bool(debug):
#         # imprimir a mensagem de depuração ativada
#         print("Modo de depuração ativado.")

#         # Inicialize o servidor FastAPI em um novo processo
#         server_process = Process(target=run_uvicorn)
#         server_process.start()

#         # Espere um pouco para garantir que o servidor esteja em execução
#         time.sleep(2)

#         # Inicialize a função de teste em um novo processo
#         test_process = Process(target=test_api)
#         test_process.start()

#         time.sleep(3)
#         # Junte os processos para esperar que eles terminem
#         test_process.join()
#         server_process.terminate()
#         server_process.join()
#     else:
#         # Iniciar o servidor FastAPI em produção
#         run_uvicorn()

#     # verificar o desempenho da API
#     fim = time.time()
#     print('---' * 20)
#     print(f"Tempo de execução: {fim - inicio} segundos")



# '''
#  Questões do aplicativo:
#  1 - Toda vez que o aplicativo

# '''
# # O formato de resposta atual da API:
# # {
# #     "status":"ok",
# #     "df":{
# #             "ug01_acumulador_energia":
# #                                     {
# #                                         "2024-04-25T00:00:00":3561.247,
# #                                         "2024-04-26T00:00:00":3561.247
# #                                     },
# #             "ug02_acumulador_energia":
# #                                     {
# #                                         "2024-04-25T00:00:00":3616.197,
# #                                         "2024-04-26T00:00:00":3561.247
# #                                     },
# #     }
# # }
# #
# # O formato requerido:
# #
# # se eu precisar acrescentar outros dias ou Unidades Geradoras (UGs), como seria a estrutura do JSON?
# # {
# #   "status": "ok",
# #   "df": [
# #         {
# #           "geradora": "UG01",
# #           "leitura": "2024-04-25T00:00:00",
# #           "acumulado": 42.954,
# #         },
# #         {
# #           "geradora": "UG01",
# #           "leitura": "2024-04-26T00:00:00",
# #           "acumulado": 42.954,
# #         },
# #         {
# #           "geradora": "UG02",
# #           "leitura": "2024-04-25T00:00:00",
# #           "acumulado": 42.954
# #         },
# #        {
# #           "geradora": "UG02",
# #           "leitura": "2024-04-26T00:00:00",
# #           "acumulado": 42.954,
# #        },
# #   ]
# # }
# #
# # Se precisar inserir mais valores de periodos diarios, semanais, mensais e anuais, como seria a estrutura do JSON?
# #
# # {
# #   "status": "ok",
# #   "df": [
# #     {
# #       "geradora": "UG01",
# #       "leitura": "2024-04-25T00:00:00",
# #       "acumulado": 42.954
# #     },
# #     {
# #       "geradora": "UG02",
# #       "leitura": "2024-04-25T00:00:00",
# #       "acumulado": 42.954
# #     }
# #   ]
# # }
# #
# # É necessário fazer a conversão do formato atual para o formato requerido?




