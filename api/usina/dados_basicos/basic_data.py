# # 1 - importar as bibliotecas necessárias
# from fastapi import FastAPI, HTTPException, Response
# from datetime import datetime, timedelta
# from multiprocessing import Process
# from dotenv import load_dotenv
# from pydantic import BaseModel
# from typing import Optional
# import mysql.connector
# import pandas as pd
# import requests
# import uvicorn
# import time
# import json
# import os
#
# # verificar o desempenho da API
# inicio = time.time()
#
# # variavel global para contagem
# cont = 0
#
# # 3 - instanciar o FastAPI
# app = FastAPI(debug=False)
#
#
# # 4 - criar a classe Consulta herda BaseModel para receber os dados da requisição
# class Consulta(BaseModel):
#     ''' Classe para receber os dados da requisição '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 4 - Classe Consulta : {round(time.time() - inicio, 4)} segundos")
#     usina: str
#     coluna: Optional[list] = ['acumulador_energia']
#     periodo: Optional[str] = 'D'
#     data_inicio: Optional[str] = datetime.now().strftime('%Y-%m-%d')
#     data_fim: Optional[str] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
#
#
# # 5 - criar a rota para receber os dados da requisição
# @app.post("/data/")
# def get_data(consulta: Consulta):
#     ''' Retorna os dados do mês solicitado '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 5 - Função get_data: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # Sanitização das entradas
#         consulta = sanitize(consulta)
#
#         # consultar as colunas que existem na tabela
#         query_columns = f"SHOW COLUMNS FROM {consulta.usina};"
#
#         # executar a query com a função fetch_all
#         df_columns = fetch_all(query_columns)
#
#         # verificar se o DataFrame está vazio
#         is_empty(df_columns)
#
#         # declara variável para armazenar as colunas
#         columns = 'data_hora,'
#
#         # verificar se a coluna solicitada existe
#         for column in df_columns['Field'].values:
#             if all([name in column for name in consulta.coluna]):
#                 columns += column + ','
#
#         # tratar a string columns
#         columns = columns[:-1]
#
#         # criar a query
#         query = f"SELECT {columns} FROM {consulta.usina} WHERE data_hora BETWEEN '{consulta.data_inicio}' AND '{consulta.data_fim}';"
#
#         # executar a query com a função fetch_all
#         df = fetch_all(query)
#
#         # verificar se o DataFrame está vazio
#         is_empty(df)
#
#         # criar um DataFrame para armazenar os dados da produção de energia
#         df_producao = pd.DataFrame()
#
#         # Calcular a produção de energia para determinado periodo
#         for column in df.columns:
#             if 'acumulador_energia' in column:
#                 df_producao[column] = calculate_production(df, column, period=consulta.periodo)
#
#         # Substituir valores NaN antes de converter o DataFrame em um dicionário
#         df_producao.fillna(0, inplace=True)
#
#         # verificar se o DataFrame de produção está vazio
#         is_empty(df_producao)
#
#         # retornar o DataFrame de produção
#         return {"status": "ok", "df": df_producao.to_dict()}
#
#     except Exception as e:
#         return HTTPException(status_code=404, detail=str(e), headers={"status": f"Erro ao processar a consulta: {e}"})
#
#
# # 16 - Sanitização das entradas
# def sanitize(consulta):
#     ''' Sanitização das entradas '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 16 - Função sanitize: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # Sanitização das entradas
#         consulta.usina = consulta.usina.replace("'", "").replace(";", "").replace("=", "")
#         consulta.coluna = [col.replace("'", "").replace(";", "").replace("=", "") for col in consulta.coluna]
#         consulta.periodo = consulta.periodo.replace("'", "").replace(";", "").replace("=", "")
#         consulta.data_inicio = consulta.data_inicio.replace("'", "").replace(";", "").replace("=", "")
#         consulta.data_fim = consulta.data_fim.replace("'", "").replace(";", "").replace("=", "")
#
#         return consulta
#     except Exception as e:
#         raise Exception(f"Erro ao sanitizar as entradas {e}")
#
#
# # 15 - Verifica se o dataframe é vazio
# def is_empty(df):
#     ''' Verifica se o DataFrame é vazio '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 15 - Função is_empty: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # verificar se o DataFrame está vazio
#         if df.empty:
#             raise Exception("Sem dados para o período solicitado.")
#         return True
#     except Exception as e:
#         raise Exception(f"Erro ao verificar se o DataFrame é vazio {e}")
#
#
# # 6 - Criar a função para conectar ao banco de dados
# def connect():
#     ''' Função para conectar ao banco de dados '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 6 - Função connect: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # objeto de conexão
#         connection = mysql.connector.connect(
#             host=os.getenv('MYSQLHOST'),
#             user=os.getenv('MYSQLUSER'),
#             password=os.getenv('MYSQLPASSWORD'),
#             database=os.getenv('MYSQLDATABASE'),
#             port=os.getenv('MYSQLPORT'),
#             use_pure=True,
#             connection_timeout=30
#         )
#
#         # retornar a conexão
#         return connection
#     except Exception as e:
#         return None
#
#
# # 7 - Criar a função para fechar a conexão com o banco de dados
# def close(connection):
#     ''' Função para fechar a conexão com o banco de dados '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 7 - Função close: {round(time.time() - inicio, 4)} segundos")
#     try:
#         if connection and connection.is_connected():
#             connection.close()
#     except Exception as e:
#         raise Exception(f"Erro ao fechar conexão {e}")
#
#
# # 8 - Criar a função para executar a query
# def execute_query(query, params=None):
#     ''' Função para executar a query '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 8 - Função execute_query: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # conectar ao banco de dados
#         connection = connect()
#
#         # verificar se a conexão é válida
#         if connection is None:
#             raise Exception("Erro ao conectar ao banco de dados")
#
#         # criar o cursor
#         cursor = connection.cursor(buffered=True)
#
#         # executar a query
#         cursor.execute(query, params or ())
#
#         # commit
#         connection.commit()
#
#         # fechar a conexão
#         close(connection)
#
#         # retornar o cursor com os dados
#         return cursor
#     except Exception as e:
#         raise Exception(f"Erro ao executar query : {e}")
#
#
# # 9 - Criar a função para executar a consulta e transformar os dados em um DataFrame
# def fetch_all(query, params=None):
#     ''' Função para executar a consulta e transformar os dados em um DataFrame '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 9 - Função fetch_all: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # Executar a query
#         cursor = execute_query(query, params)
#
#         # Obter os nomes das colunas do cursor
#         columns = cursor.column_names
#
#         # inverter o nome das colunas
#         columns = [reverse_rename(col) for col in columns]
#
#         # Obter todos os dados
#         result = cursor.fetchall()
#
#         # Criar um DataFrame com os dados e as colunas
#         df = pd.DataFrame(result, columns=columns)
#
#         # converter a coluna data_hora para datetime
#         if 'data_hora' in df.columns:
#             df['data_hora'] = pd.to_datetime(df['data_hora'])
#
#             # converte data_hora como index
#             df = df.set_index('data_hora')
#
#         # retornar o DataFrame
#         return df
#     except Exception as e:
#         raise Exception(f"Erro fetch all : {e}")
#
#
# # 10 - Criar a função para inverter o nome das colunas
# def reverse_rename(abbr):
#     ''' Função para inverter o nome das colunas '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 10 - Função reverse_rename: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # mapeamento dos nomes das colunas
#         mapping = {
#             'id': 'id',
#             '101s': 'ug01_status',
#             '201ae': 'ug01_acumulador_energia',
#             '301na': 'ug01_nivel_agua',
#             '401tfA': 'ug01_tensao_fase_A',
#             '501tfB': 'ug01_tensao_fase_B',
#             '601tfC': 'ug01_tensao_fase_C',
#             '701cfA': 'ug01_corrente_fase_A',
#             '801cfB': 'ug01_corrente_fase_B',
#             '901cfC': 'ug01_corrente_fase_C',
#             '1001te': 'ug01_tensao_excitacao',
#             '1101ce': 'ug01_corrente_excitacao',
#             '1201f': 'ug01_frequencia',
#             '1301pa': 'ug01_potencia_ativa',
#             '1401pr': 'ug01_potencia_reativa',
#             '1501pa': 'ug01_potencia_aparente',
#             '1601f': 'ug01_fp',
#             '1701d': 'ug01_distribuidor',
#             '1801v': 'ug01_velocidade',
#             '1901hm': 'ug01_horimetro_mecanico',
#             '2001he': 'ug01_horimetro_eletrico',
#             '2101teA': 'ug01_temp_enrol_A',
#             '2201teB': 'ug01_temp_enrol_B',
#             '2301teC': 'ug01_temp_enrol_C',
#             '2401tme': 'ug01_temp_mancal_estat',
#             '2501tmc': 'ug01_temp_mancal_comb',
#             '2601tme': 'ug01_temp_mancal_escora',
#             '2701tou': 'ug01_temp_oleo_uhrv',
#             '2801tou': 'ug01_temp_oleo_uhlm',
#             '2901tc': 'ug01_temp_csu2',
#             '3001te': 'ug01_temp_excitatriz',
#             '3101vmgx': 'ug01_vibr_mancal_guia_x',
#             '3201vmgY': 'ug01_vibr_mancal_guia_Y',
#             '3301vmcX': 'ug01_vibr_mancal_comb_X',
#             '3401vmcY': 'ug01_vibr_mancal_comb_Y',
#             '3501vmcZ': 'ug01_vibr_mancal_comb_Z',
#             '3601clA': 'ug01_corrente_linha_A',
#             '3701clB': 'ug01_corrente_linha_B',
#             '3801clC': 'ug01_corrente_linha_C',
#             '3901csP': 'ug01_corrente_seq_P',
#             '4001csN': 'ug01_corrente_seq_N',
#             '4101csZ': 'ug01_corrente_seq_Z',
#             '4201tb': 'ug01_tensao_barra',
#             '4301tt': 'ug01_tensao_te',
#             '4402s': 'ug02_status',
#             '4502ae': 'ug02_acumulador_energia',
#             '4602tfA': 'ug02_tensao_fase_A',
#             '4702tfB': 'ug02_tensao_fase_B',
#             '4802tfC': 'ug02_tensao_fase_C',
#             '4902cfA': 'ug02_corrente_fase_A',
#             '5002cfB': 'ug02_corrente_fase_B',
#             '5102cfC': 'ug02_corrente_fase_C',
#             '5202te': 'ug02_tensao_excitacao',
#             '5302ce': 'ug02_corrente_excitacao',
#             '5402f': 'ug02_frequencia',
#             '5502pa': 'ug02_potencia_ativa',
#             '5602pr': 'ug02_potencia_reativa',
#             '5702pa': 'ug02_potencia_aparente',
#             '5802f': 'ug02_fp',
#             '5902d': 'ug02_distribuidor',
#             '6002v': 'ug02_velocidade',
#             '6102hm': 'ug02_horimetro_mecanico',
#             '6202he': 'ug02_horimetro_eletrico',
#             '6302teA': 'ug02_temp_enrol_A',
#             '6402teB': 'ug02_temp_enrol_B',
#             '6502teC': 'ug02_temp_enrol_C',
#             '6602tme': 'ug02_temp_mancal_estat',
#             '6702tmc': 'ug02_temp_mancal_comb',
#             '6802tme': 'ug02_temp_mancal_escora',
#             '6902tou': 'ug02_temp_oleo_uhrv',
#             '7002tou': 'ug02_temp_oleo_uhlm',
#             '7102tc': 'ug02_temp_csu2',
#             '7202te': 'ug02_temp_excitatriz',
#             '7302vmgx': 'ug02_vibr_mancal_guia_x',
#             '7402vmgY': 'ug02_vibr_mancal_guia_Y',
#             '7502vmcX': 'ug02_vibr_mancal_comb_X',
#             '7602vmcY': 'ug02_vibr_mancal_comb_Y',
#             '7702vmcZ': 'ug02_vibr_mancal_comb_Z',
#             'data_hora': 'data_hora'
#         }
#
#         # seleciona o valor de acordo com dict
#         valor = mapping.get(abbr, abbr)
#
#         # retorna o valor
#         return valor
#     except Exception as e:
#         raise Exception(f"Erro ao executar transformação {e}")
#
#
# # 11 - Calcular a produção de energia para determinado periodo
# def calculate_production(df, column, period):
#     """ Calcula a produção de energia corrigida para o período especificado de maneira ajustada."""
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 11 - Calcular produção de energia: {round(time.time() - inicio, 4)} segundos")
#     try:
#         # converter a column para float
#         df[column] = df[column].astype(float)
#
#         # define o nome da coluna
#         columnp = column + '_p'
#
#         # Resample para o período desejado e calcula a diferença entre o primeiro e o último valor do período
#         df_resampled = df.resample(period).agg({column: ['first', 'last']})
#
#         # Calcula a diferença entre o último e o primeiro valor para obter a produção de energia no período
#         df_resampled[columnp] = df_resampled[(column, 'last')] - df_resampled[(column, 'first')]
#
#         # Limpa o DataFrame para remover níveis múltiplos nas colunas
#         df_resampled.columns = ['First Value', 'Last Value', columnp]
#
#         # Remove linhas onde a produção é NaN ou 0, pois isso indica que não houve produção no período
#         df_resampled = df_resampled[df_resampled[columnp].notna() & (df_resampled[columnp] != 0)]
#
#         # exclui as colunas First Value e Last Value
#         df_resampled = df_resampled.drop(columns=['First Value', 'Last Value'])
#
#         # retorna o DataFrame
#         return df_resampled
#     except Exception as e:
#         raise Exception(f"Erro ao calcular a produção de energia {e}")
#
#
# # 12 - Iniciar o servidor FastAPI
# def run_uvicorn():
#     ''' Iniciar o servidor FastAPI '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 12 - Função run_uvicorn: {round(time.time() - inicio, 4)} segundos")
#     # ler a variável de ambiente HOST
#     host = os.getenv("HOST", '0.0.0.0')
#
#     # iniciar o servidor FastAPI na porta 8000
#     uvicorn.run("main:app", host=host, port=8000, log_level="info")
#
#
# # 13 - Criar a função de teste da API
# def test_api():
#     ''' Função de teste da API '''
#     global cont, inicio
#     cont += 1
#     print(f"{cont} - 13 - Função test_api: {round(time.time() - inicio, 4)} segundos")
#     # url da API
#     url = 'http://127.0.0.1:8000/rota/'
#
#     # substituir a rota por data
#     url = url.replace('rota', 'data')
#
#     # corpo da requisição
#     body = {
#         "usina": "cgh_granada",
#         "coluna": ["acumulador_energia"],
#         "periodo": "D",
#         'data_inicio': '2024-01-01',
#         'data_fim': '2024-01-31',
#     }
#
#     # cabeçalho da requisição
#     headers = {'Content-type': 'application/json'}
#
#     # fazer a requisição POST
#     response = requests.post(url, data=json.dumps(body), headers=headers)
#
#     # imprimir o status code
#     if response.status_code == 200:
#         # imprimir a mensagem de requisição bem sucedida
#         print('Requisição bem sucedida')
#
#         # Verificar se a resposta HTTP contém um corpo antes de tentar convertê-lo em JSON
#         if response.content:
#             try:
#                 response_dict = response.json()
#             except ValueError:
#                 print("A resposta não é um JSON válido")
#         else:
#             print("A resposta HTTP está vazia")
#
#         # imprimir a resposta
#         for key, value in response_dict.items():
#             if isinstance(value, dict):
#                 print(f"{key}:")
#                 for k, v in value.items():
#                     print(f"    {k}: {v}")
#
#
# # 14 - Iniciar o servidor FastAPI em um novo processo
# if __name__ == "__main__":
#     ''' Função principal para executar o servidor FastAPI'''
#
#     # 2 - carregar as variáveis de ambiente
#     load_dotenv()
#
#     cont += 1
#     print(f"{cont} - 14 - Função __main__: {round(time.time() - inicio, 4)} segundos")
#
#     # ler a variável de ambiente DEBUG
#     debug = os.getenv("DEBUG", 0)
#
#     # verificar se o modo de depuração está ativado
#     if bool(debug):
#         # imprimir a mensagem de depuração ativada
#         print("Modo de depuração ativado.")
#
#         # Inicialize o servidor FastAPI em um novo processo
#         server_process = Process(target=run_uvicorn)
#         server_process.start()
#
#         # Espere um pouco para garantir que o servidor esteja em execução
#         time.sleep(1)
#
#         # Inicialize a função de teste em um novo processo
#         test_process = Process(target=test_api)
#         test_process.start()
#
#         time.sleep(2)
#         # Junte os processos para esperar que eles terminem
#         test_process.join()
#         server_process.terminate()
#         server_process.join()
#     else:
#         # Iniciar o servidor FastAPI em produção
#         run_uvicorn()
#
#     # verificar o desempenho da API
#     fim = time.time()
#     print('---' * 20)
#     print(f"Tempo de execução: {fim - inicio} segundos")
#     # Tempo de execução: 8.309549808502197 segundos
#     # Tempo de execução: 8.518847227096558 segundos
#
# '''
# Explicação do código:
#
# 1 - Importar as bibliotecas necessárias
# 2 - Carregar as variáveis de ambiente
# 3 - Instanciar o FastAPI
# 4 - Criar a classe Consulta herda BaseModel para receber os dados da requisição
# 5 - Criar a rota para receber os dados da requisição
# 6 - Criar a função para conectar ao banco de dados
# 7 - Criar a função para fechar a conexão com o banco de dados
# 8 - Criar a função para executar a query
# 9 - Criar a função para executar a consulta e transformar os dados em um DataFrame
# 10 - Criar a função para inverter o nome das colunas
# 11 - Calcular a produção de energia para determinado periodo
# 12 - Iniciar o servidor FastAPI
# 13 - Criar a função de teste da API
# 14 - Iniciar o servidor FastAPI em um novo processo
#
#
# '''
#
# '''
# Está implementado para a CGH Ponte Caída a interface de supervisório mais atualizada, com testes e validações de dados
# de acordo com a interface em produção.
# '''
#
# '''
# Foi realizado as alterações necessárias na Granada, o nível de água foi ajustado.
# '''
#
# '''
# 0.0, '2024-01-12T00:00:00': 3620.0, '2024-01-13T00:00:00': 3550.0, '2024-01-14T00:00:00': 3400.0, '2024-01-15T00:00:00': 3360.0, '20
# 24-01-17T00:00:00': 3970.0, '2024-01-20T00:00:00': 8340.0, '2024-01-21T00:00:00': 10020.0, '2024-01-22T00:00:00': 1750.0, '2024-01-23T00:00:00': 7020.0, '2024-01-24T00:00:00': 10160.0, '2024-01-25T00:00:00': 6840.0, '2024-01-26T00:00:00': 2400.0, '2024-01-30T00:00:00': 5860.0}
#     ug02_acumulador_energia: {'2024-01-03T00:00:00': 10370.0, '2024-01-04T00:00:00': 10110.0, '2024-01-05T00:00:00': 11690.0, '2024-01-06T00
# :00:00': 12290.0, '2024-01-12T00:00:00': 1440.0, '2024-01-13T00:00:00': 0.0, '2024-01-14T00:00:00': 0.0, '2024-01-15T00:00:00': 1600.0, '202
# 4-01-17T00:00:00': 1600.0, '2024-01-20T00:00:00': 7570.0, '2024-01-21T00:00:00': 4460.0, '2024-01-22T00:00:00': 5940.0, '2024-01-23T00:00:00': 1910.0, '2024-01-24T00:00:00': 10480.0, '2024-01-25T00:00:00': 10390.0, '2024-01-26T00:00:00': 12900.0, '2024-01-30T00:00:00': 0.0}
# '''
#
# # importações
# # from mysql.connector import errorcode
# # from multiprocessing import Process
# # from pydantic import BaseModel
# # from dotenv import load_dotenv
# # from fastapi import FastAPI
# # import mysql.connector
# # import pandas as pd
# # import os
# # import time
# #
# #
# # # minhas classes
# # # from api.usuario.autenticacao.auth import AuthenticationManager
# # # from api.testes.testes import test_api, list_installed_packages
# #
# # app = FastAPI()
# #
# # '''Sistema de autenticação'''
# #
# # app.get('/')  # registro a função home no app
# # def read_root():
# #     return {"Hello": "Engesep API"}
# # # auth = AuthenticationManager()  # registro a classe Auth no app
# # # app.post('/login/')(auth.authenticate)  # registro a função login no app
# # #
# # # '''Sistema de rotas por token'''
# # # app.post('/data/')(auth.data)  # verifica se o token é válido e retorna os dados
# # # app.post('/logout/')(auth.logout)  # registro a função logout no app
# # # app.post('/cadastro/')(auth.create_profile)  # registro a função logout no app
# # # app.post('/periodo/')(auth.periodo)  # registro a função alterar senha no app
# #
# # def run_uvicorn():
# #     import uvicorn
# #     host = os.getenv("HOST", "127.0.0.1")
# #     uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")
# #
# # if __name__ == "__main__":
# #     teste = False
# #     if teste:
# #         installed_packages = list_installed_packages()
# #         for package, version in installed_packages.items():
# #             print(f"{package}=={version}")
# #
# #         # Inicialize o servidor FastAPI em um novo processo
# #         server_process = Process(target=run_uvicorn)
# #         server_process.start()
# #
# #         # Espere um pouco para garantir que o servidor esteja em execução
# #         import time
# #         time.sleep(2)
# #
# #         # Inicialize a função de teste em um novo processo
# #         test_process = Process(target=test_api)
# #         test_process.start()
# #
# #         # Junte os processos para esperar que eles terminem
# #         test_process.join()
# #         server_process.terminate()
# #         server_process.join()
# #     else:
# #         run_uvicorn()
#
# # altura = 200
# # largura = altura * 1.618
# # tamanho = (largura, altura)
#
# '''
# Como posso modelar a estrutura das pastas e classes para a api?
#
# A api necessita das seguintes funções:
#
# # Usuário
#     ## 1. Sistema de autenticação
#         ### 1.1 Função de login
#         ### 1.2 Função de cadastro
#         ### 1.3 Função de recuperação de senha
#         ### 1.5 Função de alteração de dados do usuário
#         ### 1.6 Função de exclusão de usuário
#         ### 1.7 Função de consulta de usuário
#         ### 1.8 Função de logout
#
#     ## 2. Sistema de políticas de acesso
#         ### 2.1 Função de cadastro de políticas de acesso
#         ### 2.2 Função de alteração de políticas de acesso
#         ### 2.3 Função de exclusão de políticas de acesso
#         ### 2.4 Função de consulta de políticas de acesso
#         ### 2.5 Função de aplicação de políticas de acesso
#
# # Dados da usina
#     ## 1. Sistema da tabela, usinas
#         ### 1.1 Função de cadastro dos dados da usina
#         ### 1.2 Função de alteração dos dados da usina
#         ### 1.3 Função de exclusão dos dados da usina
#         ### 1.4 Função de consulta dos dados da usina
#         ### 1.5 Função de consulta o número de UGs da usina
#
#     ## 2. Sistema básicos para os dados da usina
#         ### 2.1 Função de inserção dos dados na usina
#         ### 2.2 Função de alteração dos dados da usina
#         ### 2.3 Função de exclusão dos dados da usina
#         ### 2.4 Função de consulta dos dados da usina
#
#     ## 3. Sistema de processamento dos dados da usina
#         ### 3.1 Função que faz a consulta por período e retorna o valor mensal de energia gerada para cada UG
#         ### 3.2 Função que faz a consulta por período e retorna o valor mensal de energia gerada para as UGs
#         ### 3.3 Função que faz a consulta por período e retorna o valor diario de energia gerada para cada UG
#         ### 3.4 Função que faz a consulta por período e retorna o valor diario de energia gerada para as UGs
#         ### 3.5 Função que faz a consulta por período e retorna o valor horario de energia gerada para cada UG
#         ### 3.6 Função que faz a consulta por período e retorna o valor horario de energia gerada para as UGs
#         ### 3.7 Função que faz a consulta por período e retorna o valor mensal do nível de água
#         ### 3.8 Função que faz a consulta por período e retorna o valor diario do nível de água
#         ### 3.9 Função que faz a consulta por período e retorna o valor horario do nível de água
#         ### 3.10 Função que faz a consulta o último valor de energia gerada para cada UG
#         ### 3.11 Função que faz a consulta o último valor acumulado para todas as UGs
#
#     ## 4. Sistema de resposta para o aplicativo
#         ### 4.1 Função que retorna o json padrão para o aplicativo
#         ### 4.2 Função que valida os dados
#         ### 4.3 Função que formata os dados
#
# # Visualização dos dados
#     ## 1. Sistema de visualização dos dados
#         ### 1.1 Função que requisita os dados da usina
#         ### 1.2 Função que gerar os gráficos
#         ### 1.3 Função que organiza os gráficos nos templates
#
#
# 281.65 * 200 = 563300
#
# '''
#
# '''
# Se me permitem expor uma análise e talvez apontar algumas ações que podem ajudar nessa questão do efetivo da PACH.
#
# Informações:
#
#     - De acordo com o portal de transparência, existem 252 servidores lotados na PACH, 188 efetivos e 64 comissionados.
#     - Aproximadamente, a PACH tem 1300 detentos, com previsão diária de 1000 movimentações, além dos visitantes, advogados e atendimentos emergênciais.
#     - A distribuição dos pavilhões está disposta em um espaço físico de 56.000 m².
#
# Análise:
#
# - A quantidade de servidores não reflete a
# '''
# '''
# from fastapi import FastAPI, HTTPException, Response
# from pydantic import BaseModel
# from api.usina.resposta_app.resposta import Connection
# from api.db.connection import Database
# from api.testes.testes import test_api
# from multiprocessing import Process
# from dotenv import load_dotenv
# from typing import Optional
# import os
#
# load_dotenv()
#
# app = FastAPI()
#
#
#
# class Consulta(BaseModel):
#     usina: str
#     periodo: Optional[dict] = None
#
#
# @app.post("/data/")
# def get_data(consulta: Consulta):
#
#     try:
#         print("Requisição recebida. data")
#         print(f"Usina: {consulta.usina}, Período: {consulta.periodo}")
#
#         # formatar o périodo
#         inicio = consulta.periodo['inicio']
#         fim = consulta.periodo['fim']
#
#         # Verifica se a usina é válida
#         consult = Connection()
#
#         query = f"SELECT * FROM {consulta.usina} WHERE data_hora BETWEEN {inicio} AND {fim}"
#
#         df = consult.fetch_all(query)
#
#         if df.empty:
#             raise Exception("Sem dados para o período solicitado.")
#
#         return Response(data={"status": "ok","df":df.to_dict(orient='records')})
#         #
#         # return Response(data={"status": "Nenhum dado encontrado","df":df.to_dict(orient='records')})
#         # if not consult.check_usina():
#         #     return {"erro": "Usina não encontrada."}
#         # else:
#         #     print("Usina encontrada.")
#         # return {"status": "ok"}
#     except Exception as e:
#         print(f"Capturou o Erro: {e}")
#         return HTTPException(status_code=404, detail=str(e), headers={"status": "Erro ao processar a consulta"})
#
#
#
#     # print(f"Usina: {usina}, Período: {periodo}")
#
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str = None):
#     return {"item_id": item_id, "q": q}
#
#
# def run_uvicorn():
#     import uvicorn
#     host = os.getenv("HOST", '0.0.0.0')
#     uvicorn.run("main:app", host=host, port=8000, log_level="info")
#
# if __name__ == "__main__":
#
#     debug = os.getenv("DEBUG", False)
#     debug = 1
#
#     if bool(debug):
#         print("Modo de depuração ativado.")
#         # Inicialize o servidor FastAPI em um novo processo
#         # test_api()
#         server_process = Process(target=run_uvicorn)
#         server_process.start()
#
#         # Espere um pouco para garantir que o servidor esteja em execução
#         import time
#         time.sleep(2)
#
#         # Inicialize a função de teste em um novo processo
#         test_process = Process(target=test_api)
#         test_process.start()
#
#         time.sleep(2)
#         # Junte os processos para esperar que eles terminem
#         test_process.join()
#         server_process.terminate()
#         server_process.join()
#     else:
#         run_uvicorn()
# '''