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
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def execute_query(self, query):
        cursor = self.connection.cursor(buffered=True)  # Use a buffered cursor
        try:
            cursor.execute(query)
            self.connection.commit()
            return cursor
        except Error as e:
            print(f"Erro ao executar a query: {e}")
            return None

    def fetch_all(self, query):
        cursor = self.execute_query(query)
        return cursor.fetchall()

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Conexão com o banco de dados encerrada!")
            Database._instance = None  # Reset the singleton instance

if __name__ == "__main__":
    db = Database()
    cursor = db.fetch_all("SELECT * FROM usuarios")
    print(cursor)
    # if cursor:
    #     for row in cursor:  # Read the results
    #         print(row)





# import mysql.connector
# from mysql.connector import Error
# import unittest
# from dotenv import load_dotenv
# import os
# from unittest.mock import patch, Mock
#
# load_dotenv()
#
# # Classe para comunicação com o banco de dados MySQL
# class Database:
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
#                 host=os.getenv('MYSQLHOST', 'containers-us-west-66.railway.app'),
#                 user=os.getenv('MYSQLUSER', 'root'),
#                 password=os.getenv('MYSQLPASSWORD', 'AIgi26lIFr70Rz6uGUbQ'),
#                 database=os.getenv('MYSQLDATABASE', 'railway'),
#                 port=os.getenv('MYSQLPORT', '7438')
#             )
#             if connection.is_connected():
#                 print("Conexão com o banco de dados estabelecida!")
#                 return connection
#         except Error as e:
#             print(f"Erro ao conectar ao banco de dados: {e}")
#             return None
#
#     def execute_query(self, query):
#         cursor = self.connection.cursor()
#         try:
#             cursor.execute(query)
#             self.connection.commit()
#             return cursor
#         except Error as e:
#             print(f"Erro ao executar a query: {e}")
#             return None
#
#     def fetch_all(self, query):
#         cursor = self.execute_query(query)
#         return cursor.fetchall()
#
#     def close_connection(self):
#         if self.connection.is_connected():
#             self.connection.close()
#             print("Conexão com o banco de dados encerrada!")
#             Database._instance = None  # Reset the singleton instance
#
#
#
# if __name__ == "__main__":
#     # unittest.main()
#     db = Database()
#     print(db.execute_query("SELECT * FROM usuarios"))


# Testes unitários
# class TestDatabase(unittest.TestCase):
#
#     @patch.object(Database, '_connect_to_database')
#     def test_connection(self, mock_connection):
#         mock_connection.return_value = Mock(is_connected=Mock(return_value=True))
#         db = Database()
#         self.assertIsNotNone(db.connection)
#
#     @patch.object(Database, '_connect_to_database')
#     def test_query_execution(self, mock_connection):
#         mock_connection.return_value = Mock(is_connected=Mock(return_value=True))
#         query = "SELECT * FROM usuarios"
#         db = Database()
#         result = db.execute_query(query)
#         self.assertIsNotNone(result)

# if __name__ == "__main__":
#     unittest.main()

# Testes unitários
# class TestDatabase(unittest.TestCase):
#
#     @patch.object(Database, '_connect_to_database')
#     def test_connection(self, mock_connection):
#         mock_connection.return_value = Mock(is_connected=Mock(return_value=True))
#         db = Database()
#         self.assertIsNotNone(db.connection)
#
#     @patch.object(Database, '_connect_to_database')
#     def test_query_execution(self, mock_connection):
#         mock_connection.return_value = Mock(is_connected=Mock(return_value=True))
#         query = "SELECT * FROM usuarios"
#         db = Database()
#         result = db.execute_query(query)
#         print(result)
#         self.assertIsNotNone(result)
#
# if __name__ == "__main__":
#     unittest.main()

# # Importações necessárias
# import mysql.connector
# from mysql.connector import Error
# import unittest
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
#
# # Classe para comunicação com o banco de dados MySQL
# class Database:
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
#                 host = os.getenv('MYSQLHOST','containers-us-west-66.railway.app'),
#                 user = os.getenv('MYSQLUSER','root'),
#                 password = os.getenv('MYSQLPASSWORD','AIgi26lIFr70Rz6uGUbQ'),
#                 database = os.getenv('MYSQLDATABASE','railway'),
#                 port = os.getenv('MYSQLPORT','7438')
#             )
#             if connection.is_connected():
#                 print("Conexão com o banco de dados estabelecida!")
#                 return connection
#         except Error as e:
#             print(f"Erro ao conectar ao banco de dados: {e}")
#             return None
#
#     def execute_query(self, query):
#         cursor = self.connection.cursor()
#         try:
#             cursor.execute(query)
#             self.connection.commit()
#             return cursor
#         except Error as e:
#             print(f"Erro ao executar a query: {e}")
#             return None
#
#     def fetch_all(self, query):
#         cursor = self.execute_query(query)
#         return cursor.fetchall()
#
#     def close_connection(self):
#         if self.connection.is_connected():
#             self.connection.close()
#             print("Conexão com o banco de dados encerrada!")
#
# # Testes unitários
# class TestDatabase(unittest.TestCase):
#     def test_connection(self):
#         db = Database()
#         self.assertIsNotNone(db.connection)
#
#     def test_query_execution(self):
#         # comandos sql para consulta
#         query = "SELECT * FROM usuarios"
#         db = Database()
#         result = db.execute_query(query)
#
#         self.assertIsNotNone(result)
#
# if __name__ == "__main__":
#     unittest.main()
