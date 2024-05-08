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
    data_inicio: Optional[str] = datetime.now().strftime('%d/%m/%Y')
    data_fim: Optional[str] = (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')
    token: str

    @validator('data_inicio', 'data_fim')
    def validar_formato_data(cls, v):
        try:
            # Tentar analisar a data no formato 'DD/MM/AAAA'
            data = datetime.strptime(v, '%d/%m/%Y')
        except ValueError:
            try:
                # Se a data não está no formato 'DD/MM/AAAA', tentar analisar no formato 'AAAA-MM-DD'
                data = datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                # Se a data não está em nenhum dos formatos, lançar um erro
                raise ValueError('Data deve estar no formato DD/MM/AAAA ou AAAA-MM-DD')
        # Reformatar a data para o formato 'AAAA-MM-DD'
        return data.strftime('%Y-%m-%d')

    @validator('usina')
    def validar_nome_usina(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Nome da usina inválido')
        return v

class Column(BaseModel):

    usina: str
    token: str

    @validator('usina')
    def validar_nome_usina(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Nome da usina inválido')
        return v

    @validator('token')
    def validar_token(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError('Token inválido')
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


    async def get_history(self,consulta: Consulta):
        ''' Retorna o histórico de dados da usina solicitada '''

        try:
            if not self.auth.verify_password(self.auth.hash_password(self.data.token), consulta.token):
                return HTTPException(status_code=401, detail="Token inválido",
                                        headers={"status": "Token inválido"})

            historico = self.data.get_historico(consulta)
            return historico

        except Exception as e:
            return HTTPException(status_code=404, detail=str(e),
                                 headers={"status": f"Erro ao processar a consulta: {e}"})

    async def get_data(self, consulta: Consulta):
        ''' Retorna os dados do mês solicitado '''

        try:
            print('1 - Consulta - ',consulta)
            if not self.auth.verify_password(self.auth.hash_password(self.data.token), consulta.token):
                print('1 - Senha incorreta - ',consulta.token)
                return HTTPException(status_code=401, detail="Token inválido",
                                        headers={"status": "Token inválido"})


            dados = self.data.process(consulta)
            return dados

        except Exception as e:
            print('1 - GET DATA - ERRO:  ',e)
            return HTTPException(status_code=404, detail=str(e),
                                 headers={"status": f"Erro ao processar a consulta: {e}"})


    async def get_values(self,consulta: Consulta):
        ''' Retorna os valores da tabela solicitada '''

        try:
            if not self.auth.verify_password(self.auth.hash_password(self.data.token), consulta.token):
                return HTTPException(status_code=401, detail="Token inválido",
                                        headers={"status": "Token inválido"})

            print('1 - Consulta - ',consulta)
            values = self.data.get_data(consulta)
            return values

        except Exception as e:
            print('2 - Consulta - ERRO: ',consulta)
            return HTTPException(status_code=404, detail=str(e),
                                 headers={"status": f"Erro ao processar a consulta: {e}"})

    async def get_columns(self,column: Column):
        ''' Retorna as colunas da tabela solicitada '''

        try:
            if not self.auth.verify_password(self.auth.hash_password(self.data.token), column.token):
                return HTTPException(status_code=401, detail="Token inválido",
                                        headers={"status": "Token inválido"})

            columns = self.data.get_columns(column)
            return columns

        except Exception as e:
            print('2 - Column - ERRO: ', column)
            return HTTPException(status_code=404, detail=str(e),
                                 headers={"status": f"Erro ao processar a consulta: {e}"})