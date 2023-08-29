from fastapi import FastAPI
import mysql.connector
from mysql.connector import errorcode
import pandas as pd
import os




# mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<dbname>
mysql_url = os.getenv('MYSQL_URL')
user  = os.getenv('MYSQLUSER')
password = os.getenv('MYSQLPASSWORD')
host = os.getenv('MYSQLHOST')
port = os.getenv('MYSQLPORT')
database = os.getenv('MYSQLDATABASE')
config = {
    'user': user,
    'password': password,
    'host': host,
    'database': database,
    'raise_on_warnings': True
}
print('Informações de conexão:')
print('URL: ',mysql_url)
print('user: ',user)
print('password: ',password)
print('host: ',host)
print('port: ',port)
print('database: ',database)
print('-----------------------')
url = f'mysql://{user}:{password}@{host}:{port}/{database}'

app = FastAPI()
@app.get("/")
async def root():
    try:
        # tratamento de erro da conexão
        try:
            engine = mysql.connector.connect(**config)
        except Exception as e:
            erro_1 = f'Erro na conexão com o banco de dados 1:{str(e)}'

        df = pd.read_sql(f'SELECT * FROM cgh_fae WHERE id = 2', con=engine).to_json()
    except Exception as e:
        erro_2 = f'Erro na conexão com o banco de dados 2:{str(e)}'
        df = {'error': erro_1 + "\n" + erro_2}
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!", 'df': df}


@app.get("/consulta_id/{id}")
async def consulta_id(id: int):
    try:
        engine = create_engine(mysql_url)

        df = pd.read_sql(f'SELECT * FROM cgh_fae WHERE id = {id}', con=engine)
        return df.to_json()
    except Exception as e:
        query = f'SELECT * FROM cgh_fae WHERE id = {id}'
        return {'error': e,
                'query': query}
