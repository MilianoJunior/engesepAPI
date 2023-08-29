from fastapi import FastAPI
from sqlalchemy import create_engine
import pandas as pd
import os
app = FastAPI()

mysql_url = os.getenv('MYSQL_URL')
print('URL: ',mysql_url)
@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}


@app.get("consulta_id/{id}")
async def consulta_id(id: int):
    try:
        engine = create_engine(mysql_url)

        df = pd.read_sql(f'SELECT * FROM cgh_fae WHERE id = {id}', con=engine)
        return df.to_json()
    except Exception as e:
        query = f'SELECT * FROM cgh_fae WHERE id = {id}'
        return {'error': e,
                'query': query}
