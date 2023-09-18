import time

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Response:

    def __init__(self, db, table):
        self.db = db.connection
        self.table = table
        self.divisores ={
            'cgh_parisoto': {'energia': 1, 'agua': 1},
            'cgh_maria_luz': {'energia': 1000, 'agua': 100},
            'cgh_fae': {'energia': 1, 'agua': 1000},
            'cgh_granada': {'energia': 1000, 'agua': 100},
        }
        self.ugs = {}
    def get_periodo(self, data_inicio, data_final, periodo):
        select_col = self.get_columns()
        if any([val is None for val in select_col.values()]):
            cols = ','.join(select_col.keys())
        else:
            cols = ','.join(select_col.values())
        columns = select_col.keys()
        cols += ',data_hora'
        columns = list(columns) + ['data_hora']
        df_consulta = self.consulta_geracao(cols, data_inicio, data_final)
        df_consulta.columns = columns
        df_consulta = self.filtro_divisores(df_consulta)
        df_consulta['data_hora'] = pd.to_datetime(df_consulta['data_hora'])
        df_consulta = df_consulta.set_index('data_hora')
        for column in df_consulta.columns:
            if 'energia' in column:
                key_a = column.split('_')
                nome = key_a.pop(0)
                self.ugs[nome] = {}
                self.ugs[nome]['geracao'] = self.prod_energia(df_consulta, column, periodo)
        return self.ugs
    def get_data_app(self):
        select_col = self.get_columns()
        data_final = datetime.now().strftime("%Y-%m-%d")
        data_inicio = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
        self.get_data(select_col, data_inicio, data_final, 'Diário', self.divisores[self.table])
        return self.ugs
    def get_data(self, select_col, data_inicio, data_fim, periodo, divisores):
        if any([val is None for val in select_col.values()]):
            cols = ','.join(select_col.keys())
        else:
            cols = ','.join(select_col.values())
        columns = select_col.keys()
        cols += ',data_hora'
        columns = list(columns) + ['data_hora']
        try:
            result = self.get_activation(cols)
            result.columns = columns
            result = self.filtro_divisores(result)
            result['data_hora'] = pd.to_datetime(result['data_hora'])
            self.separar_ugs(result)
            df_consulta= self.consulta_geracao(cols, data_inicio, data_fim)
            df_consulta.columns = columns
            df_consulta = self.filtro_divisores(df_consulta)
            df_consulta['data_hora'] = pd.to_datetime(df_consulta['data_hora'])
            df_consulta = df_consulta.set_index('data_hora')
            for column in df_consulta.columns:
                if 'energia' in column:
                    key_a = column.split('_')
                    nome = key_a.pop(0)
                    self.ugs[nome]['geracao_mensal'] = self.prod_energia(df_consulta, column, "M")
                    self.ugs[nome]['geracao_diaria'] = self.prod_energia(df_consulta, column, "D")
                if 'nivel' in column:
                    self.ugs['gerais']['nivel_media_diaria'] = self.nivel_media_diaria(df_consulta, column)
        except Exception as e:
            raise Exception(f"Falha nos calculos de geração de energia: {e}")
    def nivel_media_diaria(self, df, col):
        ''' Função de cálculo da média diária de nível de água dos ultimos 30 dias'''
        try:
            df = df[df.index >= datetime.now() - relativedelta(days=30)]
            resultado = df.resample('D')[col].mean().to_frame()
            resultado[col] = resultado[col].apply(lambda x: round(x,2))
            resultado.index = resultado.index.map(lambda x: x.strftime('%d-%m-%Y'))
            return resultado.to_dict()
        except Exception as e:
            raise Exception(f"Falha filtro divisores linha 114: {e}")
    def compute_energy_production(self, series):
        ''' Função que filtra os valores de energia e retorna a diferença entre o último e o primeiro valor válido do mês '''
        try:
            # Se a série estiver vazia ou todos os valores forem 0, retorne 0
            if series.empty or all(series == 0):
                return 0
            # Obter o último índice válido diferente de zero
            last_valid_index = series.loc[series != 0].last_valid_index()
            # Se não houver valor válido, retorne 0
            if not last_valid_index:
                return 0
            # Retornar a diferença entre o último e o primeiro valor válido do mês
            return round(series.at[last_valid_index] - series.iloc[0],2)
        except Exception as e:
            raise Exception(f"Falha compute energy linha 128: {e}")
    def prod_energia(self, df, var, periodo):
        ''' Função de cálculo de produção de energia por período '''
        try:
            if periodo == 'D':
                df = df[df.index >= datetime.now() - relativedelta(days=30)]
            resultado = df.resample(periodo)[var].apply(self.compute_energy_production).to_frame()
            resultado.index = resultado.index.map(lambda x: x.strftime('%d-%m-%Y'))
            resultado = resultado.to_dict()
            return resultado
        except Exception as e:
            raise Exception(f"Falha nos calculos producao de energia linha 138: {e}")

    def consulta_geracao(self, cols, inicio, fim):
        try:
            query = f"SELECT {cols} FROM {self.table} WHERE data_hora BETWEEN '{inicio}' AND '{fim}'"
            df_consulta = pd.read_sql(query, self.db)
            return df_consulta
        except Exception as e:
            raise Exception(f"Falha nos calculos de geração de energia: {e}")

    def get_activation(self, cols):
        try:
            query = f"SELECT {cols} FROM {self.table} ORDER BY id DESC LIMIT 1"
            result = pd.read_sql(query, self.db)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            raise Exception(f"Falha consulta get acticvation linha 73: {err}")

    def separar_ugs(self, df):
        try:
            for col in df.columns:
                key_a = col.split('_')
                nome = key_a.pop(0)
                key_b = '_'.join(key_a)
                value = float(df[col].values[0])
                if 'ug' in nome and not 'nivel' in key_b:
                    if nome not in self.ugs:
                        self.ugs[nome] = {}
                    self.ugs[nome][key_b] = value
                else:
                    if 'gerais' not in self.ugs:
                        self.ugs['gerais'] = {}
                    if 'hora' in key_b:
                        dt = df[col].apply(lambda x: x.strftime('%d/%m/%Y %H:%M:%S'))
                        self.ugs['gerais'][key_b] = dt.values[0]
                    else:
                        self.ugs['gerais'][key_b] = value
            return df
        except Exception as e:
            raise Exception(f"Falha separa ugs linha 104: {e}")
    def filtro_divisores(self,df):
        try:
            for col in df.columns:
                for key, value in self.divisores[self.table].items():
                    if key in col:
                        valor = round(df[col] / value,2)
                        df[col] = valor
            return df
        except Exception as e:
            raise Exception(f"Falha filtro divisores linha 114: {e}")

    def get_columns(self):
        try:
            columns_query = f'SHOW COLUMNS FROM {self.table};'
            columns = pd.read_sql(columns_query, self.db)
            colunas = {}
            for col in columns.values:
                if col[0] != 'id' and col[0] != 'data_hora':
                    nome = self.reverse_rename(col[0])
                    colunas[col[0]] = nome
            selecao = {}
            for key, value in colunas.items():
                if value is None:
                    if 'energia' in key or 'nivel' in key or 'status' in key:
                        selecao[key] = value
                else:
                    if 'energia' in value or 'nivel' in value or 'status' in value:
                        selecao[value] = key
            return selecao
        except mysql.connector.Error as err:
            raise Exception(f"Falha nos calculos de geração de energia: {e}")

    def reverse_rename(self, abbr):
        try:
            mapping = {
                '101s': 'ug01_status',
                '201ae': 'ug01_acumulador_energia',
                '301na': 'ug01_nivel_agua',
                '401tfA': 'ug01_tensao_fase_A',
                '501tfB': 'ug01_tensao_fase_B',
                '601tfC': 'ug01_tensao_fase_C',
                '701cfA': 'ug01_corrente_fase_A',
                '801cfB': 'ug01_corrente_fase_B',
                '901cfC': 'ug01_corrente_fase_C',
                '1001te': 'ug01_tensao_excitacao',
                '1101ce': 'ug01_corrente_excitacao',
                '1201f': 'ug01_frequencia',
                '1301pa': 'ug01_potencia_ativa',
                '1401pr': 'ug01_potencia_reativa',
                '1501pa': 'ug01_potencia_aparente',
                '1601f': 'ug01_fp',
                '1701d': 'ug01_distribuidor',
                '1801v': 'ug01_velocidade',
                '1901hm': 'ug01_horimetro_mecanico',
                '2001he': 'ug01_horimetro_eletrico',
                '2101teA': 'ug01_temp_enrol_A',
                '2201teB': 'ug01_temp_enrol_B',
                '2301teC': 'ug01_temp_enrol_C',
                '2401tme': 'ug01_temp_mancal_estat',
                '2501tmc': 'ug01_temp_mancal_comb',
                '2601tme': 'ug01_temp_mancal_escora',
                '2701tou': 'ug01_temp_oleo_uhrv',
                '2801tou': 'ug01_temp_oleo_uhlm',
                '2901tc': 'ug01_temp_csu2',
                '3001te': 'ug01_temp_excitatriz',
                '3101vmgx': 'ug01_vibr_mancal_guia_x',
                '3201vmgY': 'ug01_vibr_mancal_guia_Y',
                '3301vmcX': 'ug01_vibr_mancal_comb_X',
                '3401vmcY': 'ug01_vibr_mancal_comb_Y',
                '3501vmcZ': 'ug01_vibr_mancal_comb_Z',
                '3601clA': 'ug01_corrente_linha_A',
                '3701clB': 'ug01_corrente_linha_B',
                '3801clC': 'ug01_corrente_linha_C',
                '3901csP': 'ug01_corrente_seq_P',
                '4001csN': 'ug01_corrente_seq_N',
                '4101csZ': 'ug01_corrente_seq_Z',
                '4201tb': 'ug01_tensao_barra',
                '4301tt': 'ug01_tensao_te',
                '4402s': 'ug02_status',
                '4502ae': 'ug02_acumulador_energia',
                '4602tfA': 'ug02_tensao_fase_A',
                '4702tfB': 'ug02_tensao_fase_B',
                '4802tfC': 'ug02_tensao_fase_C',
                '4902cfA': 'ug02_corrente_fase_A',
                '5002cfB': 'ug02_corrente_fase_B',
                '5102cfC': 'ug02_corrente_fase_C',
                '5202te': 'ug02_tensao_excitacao',
                '5302ce': 'ug02_corrente_excitacao',
                '5402f': 'ug02_frequencia',
                '5502pa': 'ug02_potencia_ativa',
                '5602pr': 'ug02_potencia_reativa',
                '5702pa': 'ug02_potencia_aparente',
                '5802f': 'ug02_fp',
                '5902d': 'ug02_distribuidor',
                '6002v': 'ug02_velocidade',
                '6102hm': 'ug02_horimetro_mecanico',
                '6202he': 'ug02_horimetro_eletrico',
                '6302teA': 'ug02_temp_enrol_A',
                '6402teB': 'ug02_temp_enrol_B',
                '6502teC': 'ug02_temp_enrol_C',
                '6602tme': 'ug02_temp_mancal_estat',
                '6702tmc': 'ug02_temp_mancal_comb',
                '6802tme': 'ug02_temp_mancal_escora',
                '6902tou': 'ug02_temp_oleo_uhrv',
                '7002tou': 'ug02_temp_oleo_uhlm',
                '7102tc': 'ug02_temp_csu2',
                '7202te': 'ug02_temp_excitatriz',
                '7302vmgx': 'ug02_vibr_mancal_guia_x',
                '7402vmgY': 'ug02_vibr_mancal_guia_Y',
                '7502vmcX': 'ug02_vibr_mancal_comb_X',
                '7602vmcY': 'ug02_vibr_mancal_comb_Y',
                '7702vmcZ': 'ug02_vibr_mancal_comb_Z',
            }
            valor = mapping.get(abbr, None)
            return valor
        except Exception as e:
            raise Exception(f"Falha na decodificacao do nome da tabela: {e}")

