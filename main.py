from fastapi import FastAPI
import mysql.connector
from mysql.connector import errorcode
from pydantic import BaseModel
from pydantic import ValidationError
import pandas as pd
import os

mysql_url = os.getenv('MYSQL_URL')
user  = os.getenv('MYSQLUSER')
password = os.getenv('MYSQLPASSWORD')
host = os.getenv('MYSQLHOST')
port = os.getenv('MYSQLPORT')
database = os.getenv('MYSQLDATABASE')
port = os.getenv('MYSQLPORT')

config = {
    'host': host,
    'user': user,
    'password': password,
    'database': database,
    'port': port,
}

# preciso criar um comando sql para criar um banco de dados com base nesta classe: User
# preciso acrescentar um campo para o id como chave primaria
# class User(BaseModel):
#     name: str
#     tel: str
#     birth: str
#     email: str
#     password: str
#     usina: str
#     id_usina: int
#     privilegios: int

query = f"CREATE TABLE usuarios (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(255), telefone VARCHAR(255), nascimento VARCHAR(255), email VARCHAR(255), senha VARCHAR(255), usina VARCHAR(255), id_usina INT, privilegios INT)"
# preciso criar um comando sql para criar um banco de dados com base nesta classe: Usinas
# preciso acrescentar um campo para o id da usina
# class Usinas(BaseModel):
#     nome: str
#     table_name: str
#     numero_turbinas: int
#     localizacao: str
#     potencia_instalada: float
#
# class Cghs(BaseModel):
#     df: pd.DataFrame

class User:
    password: str
    user: str

# user = 'miliano'
# telefone = '123456789'
# nascimento = '01/01/2000'
# email = 'jrmfilho23@gmail.com'
# senha = '123456'
# usina = 'cgh fae'
# id_usina = 1
# privilegios = 1
#
#
# values = ','.join([user, telefone, nascimento, email, senha, usina, id_usina, privilegios])
# print(values)
#
# raise Exception
app = FastAPI()

'''
Função que se conecta ao banco de dados.
'''
def connect_database():
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        raise

'''
Sistema de autenticação
'''
@app.post('/login')
def login(user, password):
    try:
        connection = connect_database()
        cursor = connection.cursor()
        query = f"SELECT * FROM usuarios WHERE email='{user}' AND senha='{password}'"
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            return {'status': 'Usuário não encontrado.'}
        else:
            return {'status': 'Usuário encontrado.'}
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        raise
    finally:
        cursor.close()
        connection.close()

@app.post('/cadastro')
def cadastro(user, telefone, nascimento, email, senha, usina, id_usina, privilegios):
    try:
        connection = connect_database()
        cursor = connection.cursor()
        query = f"SELECT * FROM usuarios WHERE email='{user}'"
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            values = (user, telefone, nascimento, email, senha, usina, id_usina, privilegios)
            query = f"INSERT INTO usuarios (nome, telefone, nascimento, email, senha, usina, id_usina, privilegios) VALUES {values}"
            cursor.execute(query)
            connection.commit()
            return {'status': 'Usuário cadastrado com sucesso.'}
        else:
            return {'status': 'Usuário já cadastrado.'}
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        raise
    finally:
        cursor.close()
        connection.close()

'''
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
        

'''