"""
Faz o gerenciamento de dados da aplicação
"""
import pandas as pd
from libs.connection import Connection
from fastapi import HTTPException
from datetime import datetime, timedelta


class Data:
    """
    Classe que gerencia os dados da aplicação
    """
    def __init__(self):
        ''' Inicializa a classe Data '''

        # Conectar ao banco de dados
        self.connection = Connection()

        # Definir token
        self.token = self.connection.token

        # Definir os períodos
        self.periodos = {
                        'day': 'D',
                        'week': 'W',
                        'month': 'M',
                        'year': 'Y',
                        'hour': 'H',
                    }

    def process(self, consulta):
        ''' Processa os dados da consulta '''

        try:

            # substituir a string do período pelo valor correspondente
            consulta.periodo = self.periodos.get(consulta.periodo, 'D')

            # Sanitização das entradas
            consulta = self.sanitize(consulta)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {consulta.usina};"

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # declara variável para armazenar as colunas
            columns = 'data_hora,'

            # verificar se a coluna solicitada existe
            for column in df_columns['Field'].values:
                if all([name in column for name in consulta.coluna]):
                    columns += column + ','

            # tratar a string columns
            columns = columns[:-1]

            # criar a query
            query = f"SELECT {columns} FROM {consulta.usina} WHERE data_hora BETWEEN '{consulta.data_inicio}' AND '{consulta.data_fim}';"


            # executar a query com a função fetch_all
            df = self.connection.fetch_all(query)

            # verificar se o DataFrame está vazio
            self.is_empty(df)

            # converter a coluna data_hora para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])

            # data_hora como índice
            df.set_index('data_hora', inplace=True)

            # criar um DataFrame para armazenar os dados da produção de energia
            df_producao = pd.DataFrame()

            # Calcular a produção de energia para determinado periodo
            for column in df.columns:
                if 'acumulador_energia' in column:
                    df_producao[column] = self.calculate_production(df, column, period=consulta.periodo)

            # Substituir valores NaN antes de converter o DataFrame em um dicionário
            df_producao.fillna(0, inplace=True)

            # verificar se o DataFrame de produção está vazio
            self.is_empty(df_producao)

            # retornar o DataFrame de produção
            return {"status": "ok", "df": df_producao.to_dict()}

        except Exception as e:
            raise Exception(f"Erro ao processar os dados da consulta {e}")


    def calculate_production(self, df, column, period):
        '''Calcula a produção de energia corrigida para o período especificado de maneira ajustada.'''

        try:
            # converter a column para float
            df[column] = df[column].astype(float)

            # define o nome da coluna
            columnp = column + '_p'

            # Resample para o período desejado e calcula a diferença entre o primeiro e o último valor do período
            df_resampled = df.resample(period).agg({column: ['first', 'last']})

            # Calcula a diferença entre o último e o primeiro valor para obter a produção de energia no período
            df_resampled[columnp] = round(df_resampled[(column, 'last')] - df_resampled[(column, 'first')],3)

            # Limpa o DataFrame para remover níveis múltiplos nas colunas
            df_resampled.columns = ['First Value', 'Last Value', columnp]

            # Remove linhas onde a produção é NaN ou 0, pois isso indica que não houve produção no período
            df_resampled = df_resampled[df_resampled[columnp].notna() & (df_resampled[columnp] != 0)]

            # exclui as colunas First Value e Last Value
            df_resampled = df_resampled.drop(columns=['First Value', 'Last Value'])

            return df_resampled

        except Exception as e:
            raise Exception(f"Erro ao calcular a produção de energia {e}")

    def sanitize(self, consulta):
        ''' Sanitização das entradas '''

        try:
            # Sanitização das entradas
            consulta.usina = consulta.usina.replace("'", "").replace(";", "").replace("=", "")
            consulta.coluna = [col.replace("'", "").replace(";", "").replace("=", "") for col in consulta.coluna]
            consulta.periodo = consulta.periodo.replace("'", "").replace(";", "").replace("=", "")
            consulta.data_inicio = consulta.data_inicio.replace("'", "").replace(";", "").replace("=", "")
            consulta.data_fim = consulta.data_fim.replace("'", "").replace(";", "").replace("=", "")

            return consulta

        except Exception as e:
            raise Exception(f"Erro ao sanitizar as entradas {e}")

    def is_empty(self, df):
        ''' Verifica se o DataFrame é vazio '''

        try:

            # verificar se o DataFrame está vazio
            if df.empty:
                raise Exception("Sem dados para o período solicitado.")

            return True

        except Exception as e:
            raise Exception(f"Erro ao verificar se o DataFrame é vazio {e}")

