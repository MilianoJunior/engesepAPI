# importações
from mysql.connector import errorcode
from multiprocessing import Process
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI
import mysql.connector
import pandas as pd
import os

# minhas classes
from api.usuario.autenticacao.auth import AuthenticationManager
# from api.usuario.dados import profile
# from api.usuarios.politicas_acesso import access

app = FastAPI()

'''Sistema de autenticação'''

auth = AuthenticationManager()  # registro a classe Auth no app
print('Classe Auth registrada no app com sucesso.')
app.post('/login/')(auth.authenticate)  # registro a função login no app

'''Sistema de rotas por token'''
# app.post('/token/')(auth.token)  # registro a função token no app
'''
Função que se conecta ao banco de dados.
'''
'''
Sistema de autenticação
'''
'''Testes unitários'''
def test_api():
    import requests
    import json
    import unittest
    print('------------------------')
    print('\nTestes unitários\n')
    print('------------------------')
    cont = 0
    def print_teste(var,response, cont=cont):
        cont += 1
        teste = "True" if response.json()['status'] == var else "Erro"
        if teste == "Erro":
            print(response.json())
        print(cont, teste + ' - ' + var)
        print('-------------------------------------------------')

    # Test Login
    url = 'http://127.0.0.1:8000/login/'
    body = {
            "email": "milianojunior39@gmail.com",
            "password": "123456"
        }
    headers = {'Content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    # login com sucesso
    var = 'Usuário autenticado com sucesso.'
    print_teste(var,response)
    # login com falha no usuário
    body = {
            "email": "milianojunior39@g",
            "password": "123456"
        }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    var = 'Usuário não encontrado.'
    print_teste(var,response)
    # login com falha na senha
    body = {
            "email": "milianojunior39@gmail.com",
            "password": "1234567"
        }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    var = 'Senha incorreta.'
    print_teste(var,response)


def run_uvicorn():
    import uvicorn
    uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")

if __name__ == "__main__":
    teste = True
    if teste:
        # Inicialize o servidor FastAPI em um novo processo
        server_process = Process(target=run_uvicorn)
        server_process.start()

        # Espere um pouco para garantir que o servidor esteja em execução
        import time
        time.sleep(2)

        # Inicialize a função de teste em um novo processo
        test_process = Process(target=test_api)
        test_process.start()

        # Junte os processos para esperar que eles terminem
        test_process.join()
        server_process.terminate()
        server_process.join()
    else:
        import uvicorn
        uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")



# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info")


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