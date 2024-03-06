from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():

    # criar dados de teste para verificar a quantidade maxima de dados que podem ser retornados
    dados = ''
    for i in range(100000):
        dados += f'{i},'

    print(len(dados))
    return {"Hello": dados}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


def run_uvicorn():
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")

if __name__ == "__main__":
    run_uvicorn()






# importações
# from mysql.connector import errorcode
# from multiprocessing import Process
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from fastapi import FastAPI
# import mysql.connector
# import pandas as pd
# import os
# import time
#
#
# # minhas classes
# # from api.usuario.autenticacao.auth import AuthenticationManager
# # from api.testes.testes import test_api, list_installed_packages
#
# app = FastAPI()
#
# '''Sistema de autenticação'''
#
# app.get('/')  # registro a função home no app
# def read_root():
#     return {"Hello": "Engesep API"}
# # auth = AuthenticationManager()  # registro a classe Auth no app
# # app.post('/login/')(auth.authenticate)  # registro a função login no app
# #
# # '''Sistema de rotas por token'''
# # app.post('/data/')(auth.data)  # verifica se o token é válido e retorna os dados
# # app.post('/logout/')(auth.logout)  # registro a função logout no app
# # app.post('/cadastro/')(auth.create_profile)  # registro a função logout no app
# # app.post('/periodo/')(auth.periodo)  # registro a função alterar senha no app
#
# def run_uvicorn():
#     import uvicorn
#     host = os.getenv("HOST", "127.0.0.1")
#     uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")
#
# if __name__ == "__main__":
#     teste = False
#     if teste:
#         installed_packages = list_installed_packages()
#         for package, version in installed_packages.items():
#             print(f"{package}=={version}")
#
#         # Inicialize o servidor FastAPI em um novo processo
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
#         # Junte os processos para esperar que eles terminem
#         test_process.join()
#         server_process.terminate()
#         server_process.join()
#     else:
#         run_uvicorn()



'''
Como posso modelar a estrutura das pastas e classes para a api?

A api necessita das seguintes funções:

# Usuário
    ## 1. Sistema de autenticação
        ### 1.1 Função de login
        ### 1.2 Função de cadastro
        ### 1.3 Função de recuperação de senha
        ### 1.5 Função de alteração de dados do usuário
        ### 1.6 Função de exclusão de usuário
        ### 1.7 Função de consulta de usuário
        ### 1.8 Função de logout
        
    ## 2. Sistema de políticas de acesso
        ### 2.1 Função de cadastro de políticas de acesso
        ### 2.2 Função de alteração de políticas de acesso
        ### 2.3 Função de exclusão de políticas de acesso
        ### 2.4 Função de consulta de políticas de acesso
        ### 2.5 Função de aplicação de políticas de acesso
    
# Dados da usina
    ## 1. Sistema da tabela, usinas
        ### 1.1 Função de cadastro dos dados da usina
        ### 1.2 Função de alteração dos dados da usina
        ### 1.3 Função de exclusão dos dados da usina
        ### 1.4 Função de consulta dos dados da usina
        ### 1.5 Função de consulta o número de UGs da usina
            
    ## 2. Sistema básicos para os dados da usina
        ### 2.1 Função de inserção dos dados na usina
        ### 2.2 Função de alteração dos dados da usina
        ### 2.3 Função de exclusão dos dados da usina
        ### 2.4 Função de consulta dos dados da usina
    
    ## 3. Sistema de processamento dos dados da usina
        ### 3.1 Função que faz a consulta por período e retorna o valor mensal de energia gerada para cada UG
        ### 3.2 Função que faz a consulta por período e retorna o valor mensal de energia gerada para as UGs
        ### 3.3 Função que faz a consulta por período e retorna o valor diario de energia gerada para cada UG
        ### 3.4 Função que faz a consulta por período e retorna o valor diario de energia gerada para as UGs
        ### 3.5 Função que faz a consulta por período e retorna o valor horario de energia gerada para cada UG
        ### 3.6 Função que faz a consulta por período e retorna o valor horario de energia gerada para as UGs
        ### 3.7 Função que faz a consulta por período e retorna o valor mensal do nível de água
        ### 3.8 Função que faz a consulta por período e retorna o valor diario do nível de água
        ### 3.9 Função que faz a consulta por período e retorna o valor horario do nível de água
        ### 3.10 Função que faz a consulta o último valor de energia gerada para cada UG
        ### 3.11 Função que faz a consulta o último valor acumulado para todas as UGs
        
    ## 4. Sistema de resposta para o aplicativo
        ### 4.1 Função que retorna o json padrão para o aplicativo
        ### 4.2 Função que valida os dados
        ### 4.3 Função que formata os dados

# Visualização dos dados
    ## 1. Sistema de visualização dos dados
        ### 1.1 Função que requisita os dados da usina
        ### 1.2 Função que gerar os gráficos
        ### 1.3 Função que organiza os gráficos nos templates

'''

'''

'''