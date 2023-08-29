from fastapi import FastAPI
from sqlalchemy import create_engine
import pandas as pd
import os
app = FastAPI()

# mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<dbname>
mysql_url = os.getenv('MYSQL_URL')
user  = os.getenv('MYSQLUSER')
password = os.getenv('MYSQLPASSWORD')
host = os.getenv('MYSQLHOST')
port = os.getenv('MYSQLPORT')
database = os.getenv('MYSQLDATABASE')
print('Informações de conexão:')
print('URL: ',mysql_url)
print('user: ',user)
print('password: ',password)
print('host: ',host)
print('port: ',port)
print('database: ',database)
print('-----------------------')
url = f'mysql://{user}:{password}@{host}:{port}/{database}'

@app.get("/")
async def root():
    try:
        # tratamento de erro da conexão
        try:
            engine = create_engine(mysql_url)
        except Exception as e:
            df = {'error 1': e}

        df = pd.read_sql(f'SELECT * FROM cgh_fae WHERE id = {id}', con=engine).to_json()
    except Exception as e:

        df = {'error': e}
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
