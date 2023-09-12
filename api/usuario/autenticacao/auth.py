
import hashlib
import secrets
import datetime
import time
from pydantic import BaseModel
from fastapi import Request
from api.db.connection import Database
from api.usuario.dados.profile import Profile
from api.usuario.dados.variaveis import variaveis
from api.usina.tabela.usinas import Usinas
from api.usina.resposta_app.resposta import Response

class User(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    token: str

class Usina(BaseModel):
    nome: str
    numero_turbinas: int
    localizacao: str
    potencia_instalada: float
class BasicAuth:

    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> str:
        """Hash a password for storing."""
        if salt is None:
            salt = hashlib.sha256(secrets.token_bytes(12)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.decode() + pwdhash.hex()

    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """Verify a stored password against one provided by user."""
        salt = stored_password[:64].encode('ascii')
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwdhash.hex() == stored_password


class AuthenticationManager:
    TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=6)  # 1 hour token expiration for this example

    def __init__(self):
        self.db = Database()
        self.variaveis = variaveis
        self.usinas = Usinas(self.db)

    def authenticate(self, user: User, request: Request) -> dict:
        try:
            userd = Profile(self.db).get_profile(user.email)
            if not userd:
                return {'status': 'Usuário não encontrado.'}
            stored_password = userd[0][5]
            user_id = userd[0][0]
            if BasicAuth.verify_password(stored_password, user.password):
                token = secrets.token_hex(16)
                expiration_time = datetime.datetime.now() + self.TOKEN_EXPIRATION_TIME
                expiration_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
                self.register_token(user_id, token, expiration_time)
                return {'token': token, 'status': 'Usuário autenticado com sucesso.'}
            else:
                return {'status': 'Senha incorreta.'}
        except Exception as err:
            print(f"Failed to Login : {err}")
            raise HTTPException(status_code=401, detail="Falha no login.")
    def register_token(self,user_id: str, token: str, expiration_time: datetime.datetime):
        try:
            query = f"INSERT INTO Tokens (Userid, token, expiration_time) VALUES ('{user_id}','{token}','{expiration_time}')"
            self.db.execute_query(query)
        except Exception as err:
            raise HTTPException(status_code=401, detail="Falha no registro do token.")

    def verify_token(self, token: Token) -> dict:
        if not self.verify_token_exists(token.token):
            return {'status': 'Token não encontrado.', 'data': None}
        if not self.verify_token_expired(token.token):
            return {'status': 'Token inativo.', 'data': None}
        user_id = self.get_user_token(token.token)
        return {'status': 'Token válido.', 'data': user_id}

    def verify_token_exists(self, token: str) -> bool:
        query = f"SELECT token FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        return bool(result)

    def verify_token_expired(self, token: str) -> bool:
        query = f"SELECT expiration_time FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        if result:
            expiration_time = result[0][0]
            print('Tempo de expiração: ', expiration_time, datetime.datetime.now())
            if datetime.datetime.now() > expiration_time:
                return False
        return True

    def data(self, token: Token) -> dict:
        def recursive_attributes(dados, depth=0, max_depth=30):
            # Limit recursion depth to avoid infinite loops
            if depth > max_depth:
                return
            # Loop through each attribute
            for key, value in dados.items():
                try:
                    if isinstance(value, dict):
                        print("--" * depth + f"{key}")
                        recursive_attributes(value, depth + 1, max_depth)
                    else:
                        print("  " * depth + f"{key}: {value} , {type(key)}: {type(value)}")
                except Exception as e:
                    print("  " * depth + f"Error getting {value}: {e}")
        "Faz a autenticação do token e retorna os dados do usuário."
        inicio = time.time()
        authentication = self.verify_token(token)
        print('########################################################################')
        print('1 - Tempo de verificação do token: ', time.time() - inicio)
        print('########################################################################')
        if authentication['status'] != 'Token válido.':
            return authentication
        # início do preenchimento das variáveis
        user_id = authentication['data']
        # preenche as variáveis com os dados do token
        variaveis['token'] = token.token
        # preenche as variáveis com os dados do usuário
        self.get_user(user_id)
        print('########################################################################')
        print('2 - Tempo de verificação do Usuário: ', time.time() - inicio)
        print('########################################################################')
        # preenche as variáveis com os dados da usina
        self.get_usina(self.variaveis['user']['usina_id'])
        # preenche as variáveis com os dados das turbinas
        print('########################################################################')
        print('3 - Tempo de busca de dados da usina: ', time.time() - inicio)
        print('########################################################################')
        self.get_usina_dados(self.variaveis['user']['usina'])
        print('########################################################################')
        print('4 - Tempo de busca de dados processados: ', time.time() - inicio)
        print('########################################################################')
        # time.sleep(3)
        # print('Variáveis: ', self.variaveis)
        # recursive_attributes(self.variaveis)
        return {'status': 'Token válido.', 'data': self.variaveis}

    def get_user_token(self, token: str) -> str:
        query = f"SELECT userid FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        if result:
            return result[0][0]
        return None

    def get_user(self, user_id: str) -> None:
        query = f"SELECT * FROM usuarios WHERE id='{user_id}'"
        result = self.db.fetch_all(query)
        print('Usuário: ', result)
        if result:
            self.variaveis['user']['id'] = result[0][0]
            self.variaveis['user']['nome'] = result[0][1]
            self.variaveis['user']['telefone'] = result[0][2]
            self.variaveis['user']['nascimento'] = result[0][3]
            self.variaveis['user']['email'] = result[0][4]
            self.variaveis['user']['usina'] = result[0][6]
            self.variaveis['user']['usina_id'] = result[0][7]
            self.variaveis['user']['privilegios'] = result[0][8]
    def get_usina(self, usina_id: int)->None:
        result = self.usinas.get_usina_id(usina_id)
        print('Usina: ', result)
        if result:
            self.variaveis['usina']['usina_info']['id'] = result[0][0]
            self.variaveis['usina']['usina_info']['nome'] = result[0][1]
            self.variaveis['usina']['usina_info']['localizacao'] = result[0][3]
            self.variaveis['usina']['usina_info']['numero_de_turbinas'] = result[0][2]
            self.variaveis['usina']['usina_info']['potencia'] = result[0][4]
            self.variaveis['usina']['usina_info']['nome_tabela'] = self.variaveis['user']['usina']

    def get_usina_dados(self, nome_tabela: int)->None:
        ''' Função de consulta de usinas '''
        try:
            response = Response(self.db, nome_tabela)
            result = response.get_data_app()
            print('Dados da usina: ', result)
            if result:
                self.variaveis['usina']['usina_dados'] = result
        except Exception as err:
            print(f"Failed to connect to database: {err}")
            raise

    def create_usinas_test(self):
        us = Usinas(self.db)
        usina = Usina(nome='CGH Maria da Luz', numero_turbinas=1, localizacao='Abelardo do Luz - SC, 89830-000', potencia_instalada=0.1)
        us.create_usina(usina)
        usina = Usina(nome='CGH Granada', numero_turbinas=2, localizacao='Romelândia - SC, 89908-000', potencia_instalada=3.0)
        us.create_usina(usina)










# class Auth:
#     profile = Profile()
#
#     def __init__(self, name='auth'):
#         self.name = name
#         print('Classe Auth criada com sucesso.', type(self.profile))
#     async def login(self, user: User):
#         ''' Função de login '''
#         try:
#             # verifica se o usuário existe
#             print('Usuário: ', user.email, 'Profile: ', self.profile)
#             result = self.profile.get_profile(user)
#             print('1- Resultados: ', result,'\n')
#             if not result:
#                 return {'status': 'Usuário não cadastrado.'}
#             self.policy = PolicyAccess(user)
#             # verifica se a senha está correta
#             if result[0][5] != user.senha:
#                 return {'status': 'Senha incorreta.'}
#             # verifica se o usuário está ativo
#             print('2- Usuário ativo: ', result[0][5], user.senha,'\n')
#             if not result[0][6]:
#                 return {'status': 'Usuário inativo.'}
#             # cria o token de acesso
#             access_token = self.policy.create_access_token(data={"sub": result[0][1]})
#             print('3- Token de acesso criado com sucesso: ', access_token,'\n')
#             return {'status': 'Login realizado com sucesso.', 'token': access_token}
#         except Exception as err:
#             print(f"Failed to Login : {err}")
#             raise HTTPException(status_code=401, detail="Falha no login.")
#         finally:
#             cursor.close()
#             connection.close()
#
#     async def cadastro(self, user: User):
#         ''' Função de cadastro '''
#         try:
#             connection = await self.connect_database()
#             cursor = connection.cursor()
#             query = f"SELECT * FROM usuarios WHERE nome='{user.nome}'"
#             cursor.execute(query)
#             result = cursor.fetchall()
#             print('Resultados: ', result)
#             if len(result) == 0:
#                 values = (user.nome, user.telefone, user.nascimento, user.email, user.senha, user.usina, user.id_usina, user.privilegios)
#                 query = f"INSERT INTO usuarios (nome, telefone, nascimento, email, senha, usina, id_usina, privilegios) VALUES {values}"
#                 cursor.execute(query)
#                 connection.commit()
#                 return {'status': 'Usuário cadastrado com sucesso.'}
#             else:
#                 print('Usuário já cadastrado.')
#                 return {'status': 'Usuário já cadastrado.'}
#         except mysql.connector.Error as err:
#             print(f"Failed to connect to database: {err}")
#             raise
#         finally:
#             if 'cursor' in locals() and cursor:
#                 cursor.close()
#             if 'connection' in locals() and connection:
#                 connection.close()
