# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. __init__        → carrega configurações do .env
# 2. connect         → abre conexão MySQL
# 3. execute_query   → executa query com commit (INSERT/UPDATE/DELETE)
# 4. fetch_data      → executa SELECT, retorna lista de dicts
# 5. fetch_dataframe → executa SELECT, retorna pd.DataFrame
# 6. close           → encerra conexão
# -------------------------------------------------------------------

import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
from dotenv import load_dotenv
from libs.utils import desempenho

load_dotenv()

class Database:
    @desempenho
    def __init__(self):
        self.host = os.getenv('MYSQLHOST')
        self.user = os.getenv('MYSQLUSER')
        self.password = os.getenv('MYSQLPASSWORD')
        self.database = os.getenv('MYSQLDATABASE')
        self.port = os.getenv('MYSQLPORT')
        self.connection_timeout = int(os.getenv('MYSQLCONNECTIONTIMEOUT', 10))
        self.connection = None

    @desempenho 
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                connection_timeout=self.connection_timeout
            )
            return self.connection
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise Exception(f"Erro ao conectar ao banco de dados: {e}")

    @desempenho
    def execute_query(self, query, params=None):
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Erro ao executar query: {e}")
        finally:
            cursor.close()

    @desempenho
    def fetch_data(self, query, params=None):
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in result]
        except Error as e:
            raise Exception(f"Erro ao buscar dados: {e}")
        finally:
            cursor.close()

    @desempenho
    def fetch_dataframe(self, query, params=None) -> pd.DataFrame:
        """Executa SELECT e retorna pd.DataFrame direto."""
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        except Error as e:
            raise Exception(f"Erro ao buscar dados: {e}")
        finally:
            cursor.close()

    def close(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
            except Error as e:
                pass
        self.connection = None