from libs.connection import Connection
from fastapi import HTTPException
from datetime import datetime, timedelta
from libs.data import Data
from pydantic import BaseModel, validator
from typing import Optional
import re
import hashlib
import secrets


class Consulta(BaseModel):
    """
    Esta rota retorna os dados de produção acumulada para uma usina específica.

    Parâmetros:
    - `consulta`: Um objeto `Consulta` que contém os detalhes da consulta.

    Retorna:
    - Um objeto JSON contendo os dados de produção acumulada.
    """
    usina: str
    coluna: Optional[list] = ['acumulador_energia']
    periodo: Optional[str] = 'D'
    data_inicio: Optional[str] = datetime.now().strftime('%Y-%m-%d')
    data_fim: Optional[str] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    token: str

    @validator('data_inicio', 'data_fim')
    def validar_formato_data(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError('Data deve estar no formato AAAA-MM-DD')
        return v

    @validator('usina')
    def validar_nome_usina(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Nome da usina inválido')
        return v

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


class Rotas:
    ''' Classe para definição das rotas da API '''

    def __init__(self):
        self.info = "Rotas da API"
        self.data = Data()
        self.auth = Crypto()

    async def get_data(self, consulta: Consulta):
        ''' Retorna os dados do mês solicitado '''

        try:
            if not self.auth.verify_password(self.auth.hash_password(self.data.token), consulta.token):
                print('1 - Senha incorreta - ',consulta.token)
                return HTTPException(status_code=401, detail="Token inválido",
                                        headers={"status": "Token inválido"})


            dados = self.data.process(consulta)
            return dados


        except Exception as e:
            return HTTPException(status_code=404, detail=str(e),
                                 headers={"status": f"Erro ao processar a consulta: {e}"})