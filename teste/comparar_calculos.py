# -------------------------------------------------------------------
# TESTE: Compara cálculo A (first/last) vs cálculo B (.diff)
# Busca dados de cada usina e compara os resultados lado a lado.
# Uso: python -m teste.comparar_calculos
# -------------------------------------------------------------------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.usina_model import UsinaModel, USINAS_CONFIG
from libs.calculosA import calcular_producao_A
from libs.calculosB import calcular_producao_B

# Período de teste (ajuste conforme necessário)
DATA_INICIO = '2025-01-01 00:00:00'
DATA_FIM = '2025-01-31 23:59:00'
PERIODOS = ['D', 'M', 'H']


def comparar(usina_model: UsinaModel, usina: str, periodo: str):
    """Busca dados e compara os dois cálculos."""
    print(f'\n--- {usina} [{periodo}] ---')

    df = usina_model.buscar_dados_usina(usina, DATA_INICIO, DATA_FIM, periodo)

    if df.empty:
        print('  SEM DADOS')
        return

    res_a = calcular_producao_A(df, periodo, usina)
    res_b = calcular_producao_B(df, periodo, usina)

    # Compara por coluna de energia
    colunas_a = set(res_a.get('resultado', {}).keys())
    colunas_b = set(res_b.get('resultado', {}).keys())

    todas = colunas_a | colunas_b
    if not todas:
        print('  Nenhuma coluna de resultado')
        return

    for col in sorted(todas):
        dados_a = {item['data']: item['producao_Mwh'] for item in res_a.get('resultado', {}).get(col, [])}
        # calculosB usa 'prod_coluna' como chave
        col_b = col if col in res_b.get('resultado', {}) else f'prod_{col}'
        dados_b = {item['data']: item['producao_Mwh'] for item in res_b.get('resultado', {}).get(col_b, [])}

        datas = sorted(set(dados_a.keys()) | set(dados_b.keys()))

        print(f'\n  Coluna: {col}')
        print(f'  {"Data":<20} {"Calc_A":>12} {"Calc_B":>12} {"Diff":>12}')
        print(f'  {"-"*56}')

        for data in datas:
            val_a = dados_a.get(data, '-')
            val_b = dados_b.get(data, '-')
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                diff = round(val_a - val_b, 4)
                marca = ' ⚠' if abs(diff) > 0.01 else ''
            else:
                diff = '?'
                marca = ' ⚠'
            print(f'  {data:<20} {val_a:>12} {val_b:>12} {diff:>12}{marca}')


if __name__ == '__main__':
    db = Database()
    usina_model = UsinaModel(db)

    for usina in USINAS_CONFIG:
        for periodo in PERIODOS:
            comparar(usina_model, usina, periodo)

    print('\n' + '=' * 60)
    print('Comparação concluída.')
