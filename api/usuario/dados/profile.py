## 1. Sistema de autenticação
### 1.1 Função de login
### 1.2 Função de cadastro
### 1.3 Função de recuperação de senha
### 1.5 Função de alteração de dados do usuário
### 1.6 Função de exclusão de usuário
### 1.7 Função de consulta de usuário
### 1.8 Função de logout

import json
# import mysql.connector
import os
# from dotenv import load_dotenv
# load_dotenv()
#
# user  = os.getenv('MYSQLUSER')
# password = os.getenv('MYSQLPASSWORD')
# host = os.getenv('MYSQLHOST')
# database = os.getenv('MYSQLDATABASE')
# port = os.getenv('MYSQLPORT')
#
#
#
# config = {
#     'host': host,
#     'user': user,
#     'password': password,
#     'database': database,
#     'port': port,
# }

class Profile:

    def __init__(self, db, name='profile'):
        self.name = name
        self.db = db

    def get_profile(self, email):
        ''' Função de consulta de usuário '''
        try:
            query = f"SELECT * FROM usuarios WHERE email='{email}'"
            result = self.db.fetch_all(query)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            print(f"Failed to connect to database: {err}")
            raise

    def modify_password(self, email: str, password: str):
        # Store the hashed password in the database
        # For demonstration, I'm assuming a table named "users" with columns "email" and "password"
        query = update = f"UPDATE usuarios SET senha='{password}' WHERE email='{email}'"
        self.db.execute_query(query)

        print(f"Password for {email} stored successfully!")

    # async def update_profile(self, user):
    #     ''' Função de alteração de dados do usuário '''
    #     try:
    #         connection = await self.connect_database()
    #         cursor = connection.cursor()
    #         update = f"UPDATE usuarios SET nome='{user.nome}', telefone='{user.telefone}', nascimento='{user.nascimento}', email='{user.email}', senha='{user.senha}', usina='{user.usina}', id_usina='{user.id_usina}', privilegios='{user.privilegios}' WHERE nome='{user.nome}'"
    #         cursor.execute(update)
    #         connection.commit()
    #         return {'status': 'Usuário atualizado com sucesso.'}
    #     except mysql.connector.Error as err:
    #         print(f"Failed to connect to database: {err}")
    #         raise
    #     finally:
    #         cursor.close()
    #         connection.close()
    #
    # async def delete_profile(self, user):
    #     ''' Função de exclusão de usuário '''
    #     try:
    #         connection = await self.connect_database()
    #         cursor = connection.cursor()
    #         delete = f"DELETE FROM usuarios WHERE nome='{user.nome}'"
    #         cursor.execute(delete)
    #         connection.commit()
    #         return {'status': 'Usuário excluído com sucesso.'}
    #     except mysql.connector.Error as err:
    #         print(f"Failed to connect to database: {err}")
    #         raise
    #     finally:
    #         cursor.close()
    #         connection.close()
    #
    # async def recovery_password(self, user):
    #     ''' Função de recuperação de senha '''
    #     try:
    #         connection = await self.connect_database()
    #         cursor = connection.cursor()
    #         query = f"SELECT * FROM usuarios WHERE nome='{user.nome}'"
    #         cursor.execute(query)
    #         result = cursor.fetchall()
    #         if len(result) == 0:
    #             return {'status': 'Usuário não encontrado.'}
    #         else:
    #             return result
    #     except mysql.connector.Error as err:
    #         print(f"Failed to connect to database: {err}")
    #         raise
    #     finally:
    #         cursor.close()
    #         connection.close()
    #
    # async def logout_profile(self, user):
    #     ''' Função de logout '''
    #     try:
    #         connection = await self.connect_database()
    #         cursor = connection.cursor()
    #         query = f"SELECT * FROM usuarios WHERE nome='{user.nome}'"
    #         cursor.execute(query)
    #         result = cursor.fetchall()
    #         if len(result) == 0:
    #             return {'status': 'Usuário não encontrado.'}
    #         else:
    #             return {'status': 'Usuário encontrado.'}
    #     except mysql.connector.Error as err:
    #         print(f"Failed to connect to database: {err}")
    #         raise
    #     finally:
    #         cursor.close()
    #         connection.close()

    # @app.post('/cadastro/')
    # async def cadastro(user: User):
    #     try:
    #         connection = connect_database()
    #         cursor = connection.cursor()
    #         query = f"SELECT * FROM usuarios WHERE nome='{user.nome}'"
    #         cursor.execute(query)
    #         result = cursor.fetchall()
    #         print('Resultados: ', result)
    #         if len(result) == 0:
    #             values = (user.nome, user.telefone, user.nascimento, user.email, user.senha, user.usina, user.id_usina, user.privilegios)
    #             query = f"INSERT INTO usuarios (nome, telefone, nascimento, email, senha, usina, id_usina, privilegios) VALUES {values}"
    #             cursor.execute(query)
    #             connection.commit()
    #             return {'status': 'Usuário cadastrado com sucesso.'}
    #         else:
    #             print('Usuário já cadastrado.')
    #             return {'status': 'Usuário já cadastrado.'}
    #     except mysql.connector.Error as err:
    #         print(f"Failed to connect to database: {err}")
    #         raise
    #     finally:
    #         if 'cursor' in locals() and cursor:
    #             cursor.close()
    #         if 'connection' in locals() and connection:
    #             connection.close()