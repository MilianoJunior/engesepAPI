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

    def converter_dicionario(self, original):
        ''' Converte o dicionário de leituras em um formato mais legível '''

        resultado = {"status": original["status"], "df": []}
        cont = 0
        for key, value in original["df"].items():
            # Extração do código da geradora
            cont += 1
            if 'ug' in key:
                geradora = key.split('_')[0].upper()
            else:
                geradora = 'UG0'+str(cont)

            # Cria uma lista de leituras; aqui estamos assumindo que value é um dicionário de leituras
            leituras = []
            for data, acumulado in value.items():
                leituras.append({"leitura": data, "acumulado": acumulado})

            # Adiciona a entrada da geradora no resultado
            resultado["df"].append({"geradora": geradora, "leituras": leituras})
        return resultado

    def converter_historico(self, dados):
        ''' Converte o dicionário de leituras em um formato mais legível '''

        # Pegar as chaves de cada unidade geradora
        unidades = list(dados['df'].keys())


        # Pegar todas as datas disponíveis nos dados
        datas = list(dados['df'][unidades[0]].keys())

        # Inicializar lista para os dados convertidos
        dados_convertidos = []

        # Iterar sobre cada data
        for data in datas:
            # Inicializar um dicionário com a data de leitura e converte para string
            entrada = {"leitura": data.strftime('%Y-%m-%dT%H:%M:%S')}
            ugs = 0

            # Adicionar o valor acumulado de cada unidade
            for unidade in unidades:
                if 'ug' in unidade:
                    nome_chave = f"acumulado_{unidade.split('_')[0]}"
                else:
                    ugs += 1
                    nome_chave = f"acumulado_ug0{ugs}"
                entrada[nome_chave] = dados['df'][unidade][data]

            # Adicionar a entrada convertida na lista
            dados_convertidos.append(entrada)

        # Retornar a lista no formato desejado
        return dados_convertidos

    def production_all(self, consulta):
        ''' Retorna os valores das colunas solicitadas '''

        try:
            # Sanitização das entradas
            consulta = self.sanitize(consulta)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {consulta['usina']};"

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # declara variável para armazenar as colunas
            columns = 'data_hora,'

            # verificar se a coluna solicitada existe
            for column in df_columns['Field'].values:
                if 'energia' in column:
                    columns += column + ','

            # tratar a string columns
            columns = columns[:-1]

            # criar a query que retorna os últimos valores de produção diferentes de zero
            query = f"SELECT {columns} FROM {consulta['usina']} WHERE data_hora IS NOT NULL ORDER BY data_hora DESC LIMIT 1;"

            # executar a query com a função fetch_all
            df = self.connection.fetch_all(query)

            # verificar se o DataFrame está vazio
            self.is_empty(df)

            # converter a coluna data_hora para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])

            # data_hora como índice
            df.set_index('data_hora', inplace=True)

            # Somar os valores de produção de energia de todas as unidades geradoras em uma única coluna
            df['producao_total'] = df[[column for column in df.columns if 'energia' in column]].sum(axis=1)

            # converter o DataFrame em um dicionário
            return {"status": "ok", "df": [{ "leitura": df.index[0].strftime('%Y-%m-%dT%H:%M:%S') ,"total": round(df['producao_total'].values[0],3)}]}


        except Exception as e:
            raise Exception(f"Erro: {e}")

    def history(self, consulta):

        try:
            # substituir a string do período pelo valor correspondente
            consulta.periodo = self.periodos.get(consulta.periodo, 'D')

            # Sanitização das entradas
            consulta = self.sanitize(consulta)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {consulta['usina']};"

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # declara variável para armazenar as colunas
            columns = 'data_hora,'

            # verificar se a coluna solicitada existe
            for column in df_columns['Field'].values:
                if any([name in column for name in consulta['coluna']]):
                    columns += column + ','

            # tratar a string columns
            columns = columns[:-1]

            # criar a query
            query = f"SELECT {columns} FROM {consulta['usina']} WHERE data_hora BETWEEN '{consulta['data_inicio']}' AND '{consulta['data_fim']}';"

            # executar a query com a função fetch_all
            df = self.connection.fetch_all(query)

            # verificar se o DataFrame está vazio
            self.is_empty(df)

            # converter a coluna data_hora para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])

            # data_hora como índice
            df.set_index('data_hora', inplace=True)

            # ---------------------------------------------------------------
            # criar um DataFrame para armazenar os dados da produção de energia
            df_producao = pd.DataFrame()
            # print('Calculando produção de energia')

            for column in df.columns:
                if 'acumulador_energia' in column:
                    df_producao[column] = self.calculate_production(df, column, period=consulta['periodo'])

            # # resample para o período desejado
            # df_producao = df.resample(consulta['periodo']).mean().round(3)

            # Substituir valores NaN antes de converter o DataFrame em um dicionário
            df_producao.fillna(0, inplace=True)



            # converter o DataFrame em um dicionário
            converter_dicionario = self.converter_historico({"status": "ok", "df": df_producao.to_dict()})

            return converter_dicionario

        except Exception as e:
            raise Exception(f"Erro: {e}")



    def consult(self, consulta):
        ''' Retorna os valores das colunas solicitadas '''

        try:
            # substituir a string do período pelo valor correspondente
            consulta.periodo = self.periodos.get(consulta.periodo, 'D')

            # Sanitização das entradas
            consulta = self.sanitize(consulta)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {consulta['usina']};"

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # declara variável para armazenar as colunas
            columns = 'data_hora,'

            # verificar se a coluna solicitada existe
            for column in df_columns['Field'].values:
                if any([name in column for name in consulta['coluna']]):
                    columns += column + ','

            # tratar a string columns
            columns = columns[:-1]

            # criar a query
            query = f"SELECT {columns} FROM {consulta['usina']} WHERE data_hora BETWEEN '{consulta['data_inicio']}' AND '{consulta['data_fim']}';"

            # executar a query com a função fetch_all
            df = self.connection.fetch_all(query)

            # verificar se o DataFrame está vazio
            self.is_empty(df)

            # converter a coluna data_hora para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])

            # data_hora como índice
            df.set_index('data_hora', inplace=True)

            # resample para o período desejado
            df_producao = df.resample(consulta['periodo']).mean().round(3)

            # Substituir valores NaN antes de converter o DataFrame em um dicionário
            df_producao.fillna(0, inplace=True)

            # converter o DataFrame em um dicionário
            converter_dicionario = self.converter_dicionario({"status": "ok", "df": df_producao.to_dict()})

            # return {"status": "ok", "df": df_producao.to_dict()}
            return converter_dicionario

        except Exception as e:
            raise Exception(f"Erro: {e}")

    def production_acumulated(self, consulta):
        ''' Processa os dados da consulta '''

        try:
            # substituir a string do período pelo valor correspondente
            consulta.periodo = self.periodos.get(consulta.periodo, 'D')

            # Sanitização das entradas
            consulta = self.sanitize(consulta)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {consulta['usina']};"

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # declara variável para armazenar as colunassas
            columns = 'data_hora,'

            # verificar se a coluna solicitada existe
            for column in df_columns['Field'].values:
                if all([name in column for name in consulta['coluna']]):
                    columns += column + ','

            # tratar a string columns
            columns = columns[:-1]

            # criar a query
            query = f"SELECT {columns} FROM {consulta['usina']} WHERE data_hora BETWEEN '{consulta['data_inicio']}' AND '{consulta['data_fim']}';"

            # print(query)
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
                    dados = self.calculate_production(df, column, period=consulta['periodo'])
                    df_producao[column] = dados

            # Substituir valores NaN antes de converter o DataFrame em um dicionário
            # df_producao.fillna(0, inplace=True)

            # verificar se o DataFrame de produção está vazio
            self.is_empty(df_producao)


            converter_dicionario = self.converter_dicionario({"status": "ok", "df": df_producao.to_dict()})

            # retornar o DataFrame de produção
            # return {"status": "ok", "df": df_producao.to_dict()}
            return converter_dicionario
        except Exception as e:
            raise Exception(f"Erro ao processar os dados da consulta {e}")

    def columns(self, column):
        ''' Retorna as colunas da tabela solicitada '''

        try:

            # Sanitização das entradas
            # print(column, type(column), column.dict())
            column = self.sanitize(column)

            # consultar as colunas que existem na tabela
            query_columns = f"SHOW COLUMNS FROM {column['usina']};"
            # print(query_columns)

            # executar a query com a função fetch_all
            df_columns = self.connection.fetch_all(query_columns)

            # verificar se o DataFrame está vazio
            self.is_empty(df_columns)

            # retornar as colunas
            return {"status": "ok", "columns": df_columns['Field'].to_dict()}

        except Exception as e:
            raise Exception(f"Erro ao retornar as colunas da tabela solicitada {e}")


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
            # df_resampled = df_resampled[df_resampled[columnp].notna()]
            # Substituir valores NaN por 0
            df_resampled[columnp].fillna(0, inplace=True)

            # & (df_resampled[columnp] != 0)]

            # exclui as colunas First Value e Last Value
            df_resampled = df_resampled.drop(columns=['First Value', 'Last Value'])

            return df_resampled

        except Exception as e:
            raise Exception(f"Erro ao calcular a produção de energia {e}")

    def sanitize(self, consulta):
        ''' Sanitização das entradas '''

        try:
            # Sanitização das entradas
            consulta = consulta.dict()
            for key, value in consulta.items():
                if isinstance(value, list):
                    consulta[key] = [str(v).replace("'", "").replace(";", "").replace("=", "") for v in value]
                else:
                    consulta[key] = str(value).replace("'", "").replace(";", "").replace("=", "")

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

'''
A ordem dos fatores importa! Por que o STF vem a muito tempo espantando a população brasileira com suas decisões. 
Se tornou um órgão político e não mais um órgão de justiça. A depredação do dia 8 de janeiro de 2023, em Brasília,
é uma resposta a essas decisões.
O que a mídia e o governo faz é criar narrativas para manipular a população. Escalando suas ações para um estado de
abuso de poder que se torna insustentável. 
'''

'''
Quer mudar a resposta do endpoint:https://fastapi-production-8d7e.up.railway.app/data/producao_acumulada
De:
{
    "status":"ok",
    "df":[
            {
                 "geradora":"UG01",
                 "leituras":[
                                {
                                    "leitura":"2024-04-28T00:00:00",
                                    "acumulado":3562.337
                                }
                            ]
            },
            {
                "geradora":"UG02",
                "leituras":[
                                {
                                    "leitura":"2024-04-28T00:00:00",
                                    "acumulado":3616.877
                                }
                            ]
            }
        ]
}
Para:
[
  {
    "leitura": "2024-04-25T00:00:00",
    "acumulado_ug01": 3561.247,
    "acumulado_ug02": 3561.247,
    "acumulado_ug03": 3561.247,
    "acumulado_ug04": 3561.247
  },
  {
    "leitura": "2024-04-26T00:00:00",
    "acumulado_ug01": 3761.247,
    "acumulado_ug02": 3761.247,
    "acumulado_ug03": 3761.247,
    "acumulado_ug04": 3761.247
  }
]



'''