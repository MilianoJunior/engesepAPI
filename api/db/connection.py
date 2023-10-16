import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

class Database:

    def __init__(self):
        self.host = os.getenv('MYSQLHOST')
        self.user = os.getenv('MYSQLUSER')
        self.password = os.getenv('MYSQLPASSWORD')
        self.database = os.getenv('MYSQLDATABASE')
        self.port = os.getenv('MYSQLPORT')
        self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _handle_error(self, err_msg, exception):
        full_msg = f"class Database: {err_msg}: {exception}"
        print(full_msg)
        raise Exception(full_msg)

    def _debug(self, msg):
        if os.getenv('DEBUG') == 'True':
            if 'new' in msg:
                print(f"{'-' * 20} {msg} {'-' * 20}")
            else:
                print(msg)

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
        except Exception as e:
            self._handle_error("Erro ao conectar ao banco de dados", e)

    def ensure_connection(self):
        if self.connection is None or not self.connection.is_connected():
            self.connect()

    def execute_query(self, query, params=None):
        try:
            self._debug(f"Executando query: {query}, params: {params}")
            self.ensure_connection()
            cursor = self.connection.cursor(buffered=True)
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except Exception as e:
            self._handle_error("Erro ao executar query", e)



    def fetch_all(self, query, params=None):
        cursor = self.execute_query(query, params)
        result = cursor.fetchall()
        self._debug(f"Resultado dados: {result}")
        return result

    def close(self):
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("Conexão com o banco de dados encerrada!")
        except Exception as e:
            self._handle_error("Erro ao fechar conexão", e)

# Classe para comunicação com o banco de dados MySQL
# class Database1:
#     _instance = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(Database, cls).__new__(cls)
#             cls._instance.connection = cls._connect_to_database()
#         return cls._instance
#
#     @staticmethod
#     def _connect_to_database():
#         try:
#             connection = mysql.connector.connect(
#                 host=os.getenv('MYSQLHOST'),
#                 user=os.getenv('MYSQLUSER'),
#                 password=os.getenv('MYSQLPASSWORD'),
#                 database=os.getenv('MYSQLDATABASE'),
#                 port=os.getenv('MYSQLPORT')
#             )
#             if connection.is_connected():
#                 print("Conexão com o banco de dados estabelecida!")
#                 return connection
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")
#
#     def execute_query(self, query, params=None):
#         cursor = self.connection.cursor(buffered=True)  # Use a buffered cursor
#         try:
#             if not params is None:
#                 cursor.execute(query, params)
#             else:
#                 cursor.execute(query)
#             self.connection.commit()
#             return cursor
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")
#
#     def fetch_all(self, query, params=None):
#         try:
#             cursor = self.execute_query(query, params)
#             return cursor.fetchall()
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")
#
#     def close_connection(self):
#         try:
#             if self.connection.is_connected():
#                 self.connection.close()
#                 print("Conexão com o banco de dados encerrada!")
#                 Database._instance = None  # Reset the singleton instance
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")

# Nova classe para comunicação com o banco de dados MySQL

# class Database2:
#
#     def __init__(self):
#         self.host = os.getenv('MYSQLHOST'),
#         self.user = os.getenv('MYSQLUSER'),
#         self.password = os.getenv('MYSQLPASSWORD'),
#         self.database = os.getenv('MYSQLDATABASE'),
#         self.port = os.getenv('MYSQLPORT')
#
#     def __enter__(self):
#         self.connect()
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.close()
#
#     def error(self, err):
#         print(f"class Database: Erro ao conectar ao banco de dados: {err}")
#         raise Exception(f"class Database: Erro ao conectar ao banco de dados: {err}")
#
#     def connect(self):
#         try:
#             self.connection = mysql.connector.connect(
#                 host=self.host,
#                 user=self.user,
#                 password=self.password,
#                 database=self.database,
#                 port=self.port
#             )
#         except Exception as e:
#             self.error(e)
#
#     def execute_query(self, query, params=None):
#         cursor = self.connection.cursor(buffered=True)  # Use a buffered cursor
#         try:
#             if not params is None:
#                 cursor.execute(query, params)
#             else:
#                 cursor.execute(query)
#             self.connection.commit()
#             return cursor
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")
#
#     def fetch_all(self, query, params=None):
#         try:
#             cursor = self.execute_query(query, params)
#             return cursor.fetchall()
#         except Exception as e:
#             raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")
#
#     def close(self):
#         try:
#             if self.connection.is_connected():
#                 self.connection.close()
#                 print("Conexão com o banco de dados encerrada!")
#         except Exception as e:
#             self.error(e)