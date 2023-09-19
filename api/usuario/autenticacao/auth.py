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
from fastapi import HTTPException
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO,  # ou DEBUG, ERROR, etc.
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler("my_api.log")])

logger = logging.getLogger(__name__)

class User(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    nome: str
    email: str
    password: str
    telefone: str
    nascimento: str
    usina: str
    id_usina: int
    privilegios: str
    token: str

class Token(BaseModel):
    token: str

class Usina(BaseModel):
    nome: str
    numero_turbinas: int
    localizacao: str
    potencia_instalada: float

class Periodo(BaseModel):
    periodo: str
    data_inicio: str
    data_final: str
    token: str

class Crypto:

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


class TokenManager:
    TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=6)

    def __init__(self, db):
        self.db = db

    def verify_token(self, token: str) -> dict:
        if not self.verify_token_exists(token):
            return {'status': 'Token não encontrado.', 'data': None}
        if not self.verify_token_expired(token):
            return {'status': 'Token inativo.', 'data': None}
        user_id = self.get_user_id_from_token(token)
        return {'status': 'Token válido.', 'data': user_id}

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        query = "SELECT userid FROM Tokens WHERE token=%s"
        result = self.db.fetch_all(query, (token,))
        if result:
            return result[0][0]
        return None

    def generate_token(self) -> str:
        return secrets.token_hex(16)

    def register_token(self, user_id: str, expiration_time: Optional[datetime.datetime] = None):
        if expiration_time is None:
            expiration_time = datetime.datetime.now() + self.TOKEN_EXPIRATION_TIME
        expiration_time_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO Tokens (Userid, token, expiration_time) VALUES (%s, %s, %s)"
        token = self.generate_token()
        self.db.execute_query(query, (user_id, token, expiration_time_str))
        return token

    def remove_token(self, token: str):
        query = "DELETE FROM Tokens WHERE token=%s"
        self.db.execute_query(query, (token,))

    def verify_token_exists(self, token: str) -> bool:
        query = "SELECT token FROM Tokens WHERE token=%s"
        result = self.db.fetch_all(query, (token,))
        return bool(result)

    def verify_token_expired(self, token: str) -> bool:
        query = "SELECT expiration_time FROM Tokens WHERE token=%s"
        result = self.db.fetch_all(query, (token,))
        if result:
            expiration_time = result[0][0]
            if datetime.datetime.now() > expiration_time:
                return False
        return True

    def verify_token_admin(self, token) -> bool:
        ''' Função de verificação de token se é administrador '''
        userid = self.get_user_id_from_token(token)
        if not userid:
            return False
        query = f"SELECT privilegios FROM usuarios WHERE id='{userid}'"
        result = self.db.fetch_all(query)
        if result:
            if result[0][0] == 2:
                return True
        return False

class AuthenticationManager:
    def __init__(self):
        self.db = Database()
        self.crypt = Crypto()
        self.users = Profile(self.db)
        self.usinas = Usinas(self.db)
        self.token_manager = TokenManager(self.db)
        self.variaveis = variaveis  # Esta variável parece ser global, certifique-se de que isso é intencional.

    def authenticate(self, user: User) -> dict:
        try:
            print('Autenticando usuário...')
            print(user.email, type(user.email))
            print(user.password, type(user.password))
            print('          ')
            userd = self.users.get_profile(user.email)
            if not userd:
                return {'status': 'Usuário não encontrado.'}
            stored_password = userd[0][5]
            user_id = userd[0][0]
            if self.crypt.verify_password(stored_password, user.password):
                token = self.token_manager.register_token(user_id)
                return {'token': token, 'status': 'Usuário autenticado com sucesso.'}
            else:
                logger.info(f"Senha incorreta: {user_id}!")
                return {'status': 'Senha incorreta.'}

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=401, detail="Falha no login.")

    def logout(self, token: Token) -> dict:
        try:
            self.token_manager.remove_token(token.token)
            return {'status': 'Usuário deslogado com sucesso.'}
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise HTTPException(status_code=401, detail="Falha no logout.")

    def create_profile(self, user: UserCreate):
        ''' Função de cadastro de usuário '''
        try:
            userd = self.users.get_profile(user.email)
            admin = self.token_manager.verify_token_admin(user.token)
            if not admin:
                return {'status': 'Usuário sem permissão para cadastrar.'}
            if not userd:
                user.password = self.crypt.hash_password(user.password)
                result = self.users.create_profile(user)
                return result
            return {'status': 'Usuário já cadastrado.'}
        except Exception as err:
            logger.error(f"Create profile error: {err}")
            raise HTTPException(status_code=401, detail="Falha no cadastro.")

    def data(self, token: Token) -> dict:
        """Faz a autenticação do token e retorna os dados do usuário."""
        try:
            start_time = time.time()

            # Verificar token
            authentication = self.token_manager.verify_token(token.token)
            self._log_duration(start_time, 'Tempo de verificação do token')

            if authentication['status'] != 'Token válido.':
                return authentication

            # Preencher variáveis
            user_id = authentication['data']
            variaveis['token'] = token.token

            # Obter dados do usuário
            self.get_user(user_id)
            self._log_duration(start_time, 'Tempo de verificação do Usuário')

            # Obter dados da usina
            self.get_usina(self.variaveis['user']['usina_id'])
            self._log_duration(start_time, 'Tempo de busca de dados da usina')

            # Obter dados processados da usina
            self.get_usina_dados(self.variaveis['user']['usina'])
            self._log_duration(start_time, 'Tempo de busca de dados processados')

            return {'status': 'Token válido.', 'data': self.variaveis}
        except Exception as err:
            logger.error(f"Data error: {err}")
            raise HTTPException(status_code=401, detail=f"Falha na consulta de dados: {err}.")

    def periodo(self, month: Periodo) -> dict:
        """Realiza consultas com base no período fornecido."""
        try:
            start_time = time.time()

            # Verificar token
            authentication = self.token_manager.verify_token(month.token)
            self._log_duration(start_time, 'Tempo de verificação do Mensal')

            if authentication['status'] != 'Token válido.':
                return authentication

            # Obter tabela do usuário
            user_id = authentication['data']
            user_table = self.users.get_profile_id(user_id)[0][6]
            response = Response(self.db, user_table)

            # Consultar dados do período
            result = response.get_periodo(month.data_inicio, month.data_final, month.periodo)
            self._log_duration(start_time, 'Tempo de busca de dados mensais')

            if result:
                return {'status': 'Dados encontrados.', 'data': result}
            return {'status': 'Dados não encontrados.'}
        except Exception as err:
            logger.error(f"Periodo error: {err}")
            raise HTTPException(status_code=401, detail="Falha na consulta.")

    def get_user(self, id: str) -> None:
        try:
            result = self.users.get_profile_id(id)
            if result:
                self.variaveis['user']['id'] = result[0][0]
                self.variaveis['user']['nome'] = result[0][1]
                self.variaveis['user']['telefone'] = result[0][2]
                self.variaveis['user']['nascimento'] = result[0][3]
                self.variaveis['user']['email'] = result[0][4]
                self.variaveis['user']['usina'] = result[0][6]
                self.variaveis['user']['usina_id'] = result[0][7]
                self.variaveis['user']['privilegios'] = result[0][8]
        except Exception as err:
            logger.error(f"Get user error: {err}")
            raise HTTPException(status_code=401, detail="Falha na consulta.")

    def get_usina(self, usina_id: int)->None:
        try:
            result = self.usinas.get_usina_id(usina_id)
            if result:
                self.variaveis['usina']['usina_info']['id'] = result[0][0]
                self.variaveis['usina']['usina_info']['nome'] = result[0][1]
                self.variaveis['usina']['usina_info']['localizacao'] = result[0][3]
                self.variaveis['usina']['usina_info']['numero_de_turbinas'] = result[0][2]
                self.variaveis['usina']['usina_info']['potencia'] = result[0][4]
                self.variaveis['usina']['usina_info']['nome_tabela'] = self.variaveis['user']['usina']
        except Exception as err:
            logger.error(f"Get usina error: {err}")
            raise HTTPException(status_code=401, detail="Falha na consulta.")

    def get_usina_dados(self, nome_tabela: int)->None:
        ''' Função de consulta de usinas '''
        try:
            response = Response(self.db, nome_tabela)
            result = response.get_data_app()
            if result:
                self.variaveis['usina']['usina_dados'] = result
        except Exception as err:
            logger.error(f"Get usina dados error: {err}")
            raise HTTPException(status_code=401, detail="Falha na consulta.")

    def _log_duration(self, start_time, message):
        """Helper para registrar a duração de uma operação."""
        duration = time.time() - start_time
        logging.info(f"{message}: {duration:.2f} segundos")










