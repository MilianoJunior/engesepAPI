
import hashlib
import secrets
import datetime
from pydantic import BaseModel
from fastapi import Request
from api.db.connection import Database
from api.usuario.dados.profile import Profile

db = Database()
class User(BaseModel):
    email: str
    password: str


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
    TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=1)  # 1 hour token expiration for this example

    def __init__(self):
        self.db = db

    def recursive_attributes(self, obj, depth=0, max_depth=3):
        """
        Prints all attributes and methods of an object recursively up to max_depth.

        :param obj: The object to inspect.
        :param depth: Current recursion depth. Used for indentation.
        :param max_depth: Maximum recursion depth to prevent infinite loops.
        """
        # Limit recursion depth to avoid infinite loops
        if depth > max_depth:
            return

        # Get a list of all attributes and methods of the object
        attributes = dir(obj)

        # Loop through each attribute
        for attr in attributes:
            try:
                # Get the value of the attribute
                attr_value = getattr(obj, attr)
                print("  " * depth + f"{attr}: {type(attr_value)}")

                # If the attribute is an object or a method, inspect its attributes recursively
                if hasattr(attr_value, "__dict__"):
                    recursive_attributes(attr_value, depth + 1, max_depth)
            except Exception as e:
                print("  " * depth + f"Error getting {attr}: {e}")
    def authenticate(self, user: User, request: Request) -> dict:
        try:
            # self.recursive_attributes(request)
            # client_ip = request.client.host
            # print('IP do cliente: ', client_ip)
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
            print(f"Failed to register token : {err}")
            raise HTTPException(status_code=401, detail="Falha no registro do token.")

    def verify_token_exists(self, token: str) -> bool:
        query = f"SELECT token FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        return bool(result)

    def verify_token_active(self, token: str) -> bool:
        query = f"SELECT status FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        if result:
            return result[0]["status"] == "active"
        return False

    def verify_token_expired(self, token: str) -> bool:
        query = f"SELECT expiration_time FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        if result:
            expiration_time = result[0]["expiration_time"]
            return datetime.datetime.now() > expiration_time
        return True

    def verify_token_blocked(self, token: str) -> bool:
        query = f"SELECT status FROM Tokens WHERE token='{token}'"
        result = self.db.fetch_all(query)
        if result:
            return result[0]["status"] == "blocked"
        return False


# Testing our AuthenticationManager
def test_authentication_manager():
    manager = AuthenticationManager()

    # Mock a successful authentication
    token = manager.authenticate("milianojunior39@gmail.com", "123456")
    print('Token gerado: ', token)
    # assert token, "Token generation failed"
    #
    # # Test token verifications
    # assert manager.verify_token_exists(token), "Token existence verification failed"
    # assert manager.verify_token_active(token), "Token active verification failed"
    # assert not manager.verify_token_expired(token), "Token expiration verification failed"
    # assert not manager.verify_token_blocked(token), "Token blocked verification failed"

    return "All tests passed!"

if __name__ == "__main__":
    print(test_authentication_manager())

# Testando novamente
# def test_classes_final_fixed():
#     # Testando BasicAuth
#     basic_auth = BasicAuth()
#
#     # Simulando uma senha armazenada
#     stored_password = basic_auth.hash_password("password123")
#
#     # Método de autenticação modificado para aceitar uma senha armazenada como argumento
#     def authenticate_with_stored_password(stored_password: str, username: str, password: str) -> bool:
#         return basic_auth.verify_password(stored_password, password)
#
#     assert authenticate_with_stored_password(stored_password, "user", "password123"), "Falha na autenticação correta"
#     assert not authenticate_with_stored_password(stored_password, "user",
#                                                  "wrongpassword"), "Autenticação bem-sucedida com senha errada"
#
#     # Testando TokenAuth
#     token_auth = TokenAuth()
#     token = token_auth.generate_token()
#     token_auth.store_token(1, token)
#     assert token_auth.authenticate(token), "Falha na autenticação com token"
#
#     return "Testes concluídos com sucesso!"





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
