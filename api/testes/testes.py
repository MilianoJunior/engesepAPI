import requests
import json
from multiprocessing import Process
import pkg_resources


'''Testes unitários'''
def test_api():
    import requests
    import json
    import unittest
    print('------------------------')
    print('\nTestes unitários\n')
    print('------------------------')
    testes = {
        'consulta': True, # consulta de dados
        'login': False,
        'cadastro': False,
        'token': False,
        'mensal': False,
        'logout': False,
    }
    on = False
    if on:
        url = 'https://fastapi-production-8d7e.up.railway.app/rota/'
    else:
        url = 'http://127.0.0.1:8000/rota/'
    cont = 0
    def print_teste(var,response,cont=cont):
        cont += 1
        # if response.status_code == 200:
        # print('Print: ', response.headers) #dir(response))
        teste = "True" if response['headers']['status'] == var else "Erro"
        if teste == "Erro":
            print(response.detail)
        print(cont, teste + ' - ' + var)
        print('-------------------------------------------------')
        return cont

    def recursive_attributes(dados, depth=0, max_depth=30):
        # Limit recursion depth to avoid infinite loops
        if depth > max_depth:
            return
        # Loop through each attribute
        for key, value in dados.items():
            try:
                if isinstance(value, dict):
                    print("  " * depth + f"{key}")
                    recursive_attributes(value, depth + 1, max_depth)
                else:
                    print("  " * depth + f"{key}: {value}")
            except Exception as e:
                print("  " * depth + f"Error getting {value}: {e}")

    if testes['consulta']:
        print('------------------------')
        print('Test Consulta')
        print('------------------------')
        url = url.replace('rota', 'data')
        body = {
            "usina": "cgh_grannada",
            "periodo": {
                        'inicio':'2024-03-01',
                        'fim':'2024-03-31',
            }
        }
        print(url)
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Erro ao processar a consulta'
        recursive_attributes(dict(response.json()))
        cont = print_teste(var, dict(response.json()), cont)

        print('------------------------')

        body = {
            "usina": "cgh_granada",
            "periodo": {
                'inicio': '2024-01-01',
                'fim': '2024-01-31',
            }
        }
        print(url)
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Erro ao processar a consulta'
        recursive_attributes(dict(response.json()))
        cont = print_teste(var, dict(response.json()), cont)


        # body = {
        #     "usina": "cgh_granada",
        #     "periodo": {
        #         'inicio': '2024-01-01',
        #         'fim': '2024-01-31',
        #     }
        # }
        # print(url)
        # headers = {'Content-type': 'application/json'}
        # response = requests.post(url, data=json.dumps(body), headers=headers)
        # var = 'Nenhum dado encontrado'
        # cont = print_teste(var, response, cont)
        # print('Json: ', response.json())
        # print('------------------------')
        # print(' Code: ', response.status_code)
        # if response.status_code == 200:
        #     recursive_attributes(response.json()['data'])

    if testes['login']:
        print('------------------------')
        print('Test Login')
        print('------------------------')

        url = url.replace('rota', 'login')
        body = {
                "email": "milianojunior39@gmail.com",
                "password": "123456"
            }
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        # # login com sucesso
        var = 'Usuário autenticado com sucesso.'
        cont = print_teste(var,response, cont)
        print(response.json())
        token_valido = response.json()['token']
        # login com falha no usuário
        body = {
                "email": "milianojunior39@g",
                "password": "123456"
            }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Usuário não encontrado.'
        cont = print_teste(var,response,cont)
        # login com falha na senha
        body = {
                "email": "milianojunior39@gmail.com",
                "password": "1234567"
            }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Senha incorreta.'
        cont = print_teste(var, response, cont)

    if testes['cadastro']:
        print('------------------------')
        print('Test Cadastro')
        print('------------------------')
        url = url.replace('login', 'cadastro')
        body = {
            "email": "leonardo@gmail.com",
            "password": "123456",
            "nome": "parisoto",
            "telefone": "11999999999",
            "nascimento": "1999-01-01",
            "usina": "cgh_grandada",
            "id_usina": "4",
            "privilegios": "1",
            "token": token_valido
        }
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        # # login com sucesso
        var = 'Usuário cadastrado com sucesso.'
        cont = print_teste(var, response, cont)
        # usuário já cadastrado
        body = {
            "email": "maria_luz@gmail.com",
            "password": "123456",
            "nome": "maria luz",
            "telefone": "11999999999",
            "nascimento": "1999-01-01",
            "usina": "cgh_maria_luz",
            "id_usina": "1",
            "privilegios": "1",
            "token": token_valido
        }
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        # # login com sucesso
        var = 'Usuário já cadastrado.'
        cont = print_teste(var, response, cont)
        # usuário que não tem permissão para cadastrar
        body = {
            "email": "maria_luz@gmail.com",
            "password": "123456",
            "nome": "maria luz",
            "telefone": "11999999999",
            "nascimento": "1999-01-01",
            "usina": "cgh_maria_luz",
            "id_usina": "1",
            "privilegios": "1",
            "token": "jskajllkk"
        }
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        # # login com sucesso
        var = 'Usuário sem permissão para cadastrar.'
        cont = print_teste(var, response, cont)

    if testes['token']:
        print('------------------------')
        print('Test Token')
        print('------------------------')
        # verifica se o token é válido e retorna os dados
        url = url.replace('cadastro', 'data')
        body = {
                "token":'eec330f9a0e0b58adb00f1beaedc0274'
            }
        var = 'Token não encontrado.'
        response = requests.post(url, data=json.dumps(body), headers=headers)
        cont = print_teste(var,response,cont)
        # verifica se o token é válido e retorna os dados
        body = {
                "token":'eec330f9a0e0b58adb00f1beaedc02c7' # token inválido
            }
        var = 'Token inativo.'
        response = requests.post(url, data=json.dumps(body), headers=headers)
        cont=print_teste(var,response,cont)
        # verifica se o token é válido e retorna os dados
        body = {
                "token":token_valido # token válido
            }
        headers = {'Content-type': 'application/json'}
        var = 'Token válido.'
        response = requests.post(url, data=json.dumps(body), headers=headers)
        cont = print_teste(var, response, cont)
        if response.status_code == 200:
            recursive_attributes(response.json()['data'])
    if testes['mensal']:
        print('------------------------')
        print('Test consulta Diária e Mensal')
        print('------------------------')
        url = url.replace('data', 'periodo')
        body = {
            "periodo": "D",
            "data_inicio": "2023-01-01",
            "data_final": "2023-12-31",
            "token": token_valido  # token válido
        }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Token não encontrado.'
        cont = print_teste(var, response, cont)
        if response.status_code == 200:
            recursive_attributes(response.json()['data'])
        body = {
            "periodo": "M",
            "data_inicio": "2023-01-01",
            "data_final": "2023-12-31",
            "token": token_valido  # token válido
        }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Token não encontrado.'
        cont = print_teste(var, response, cont)
        if response.status_code == 200:
            recursive_attributes(response.json()['data'])

    if testes['logout']:
        print('------------------------')
        print('Test Logout')
        print('------------------------')
        url = url.replace('periodo', 'logout')
        body = {
            "token": token_valido  # token válido
        }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Usuário deslogado com sucesso.'
        cont = print_teste(var, response, cont)
        # teste de login com token desativado
        url = url.replace('logout', 'data')
        response = requests.post(url, data=json.dumps(body), headers=headers)
        var = 'Token não encontrado.'
        cont = print_teste(var, response, cont)

# Listar os pacotes instalados
def list_installed_packages():
    packages = {}
    for distribution in pkg_resources.working_set:
        packages[distribution.project_name] = distribution.version
    return packages

