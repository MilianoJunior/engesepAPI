import mysql.connector
from mysql.connector import Error
import unittest
from dotenv import load_dotenv
import os

load_dotenv()

# Classe para comunicação com o banco de dados MySQL
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = cls._connect_to_database()
        return cls._instance

    @staticmethod
    def _connect_to_database():
        try:
            connection = mysql.connector.connect(
                host=os.getenv('MYSQLHOST'),
                user=os.getenv('MYSQLUSER'),
                password=os.getenv('MYSQLPASSWORD'),
                database=os.getenv('MYSQLDATABASE'),
                port=os.getenv('MYSQLPORT')
            )
            if connection.is_connected():
                print("Conexão com o banco de dados estabelecida!")
                return connection
        except Exception as e:
            raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor(buffered=True)  # Use a buffered cursor
        try:
            if not params is None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except Exception as e:
            raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")

    def fetch_all(self, query, params=None):
        try:
            cursor = self.execute_query(query, params)
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")

    def close_connection(self):
        try:
            if self.connection.is_connected():
                self.connection.close()
                print("Conexão com o banco de dados encerrada!")
                Database._instance = None  # Reset the singleton instance
        except Exception as e:
            raise Exception(f"class Database: Erro ao conectar ao banco de dados: {e}")