import pandas as pd

class Response:

    def __init__(self, db, table):
        self.db = db
        self.table = table
    def prod_energia(self, df, var, periodo):
        try:
            resultado = df.resample(periodo)[var].apply(self.compute_energy_production).to_frame()
            return resultado
        except Exception as e:
            print(e)
            raise Exception(f"Falha nos calculos de geração de energia: {e}")

'''      
  usina_dados
    status_ativacao
    None: <class 'NoneType'>
    nome_turbina
    None: <class 'NoneType'>
    data
    None: <class 'NoneType'>
    energia_acumulada
    None: <class 'NoneType'>
    geracao_mensal
    None: <class 'NoneType'>
    geracao_diaria
    None: <class 'NoneType'>
    ultimos
    None: <class 'NoneType'>
'''