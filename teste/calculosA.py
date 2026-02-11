# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. calcular_producao_A → calcula produção via agrupamento first/last por período
# -------------------------------------------------------------------

import pandas as pd
from libs.usina_model import USINAS_CONFIG


def calcular_producao_A(df: pd.DataFrame, periodo: str, usina: str) -> dict:
    """Cálculo A: delta (last - first) por janela de tempo agrupada."""
    print('#####'*10)
    print('Calculando producao A')
    print(df.head())
    print('#####'*10)
    if df.empty:
        return {"status": "sem_dados", "usina": usina, "mensagem": "Nenhum dado encontrado."}

    df = df.copy()
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    df = df.sort_values('data_hora')

    # Identifica colunas de energia (já renomeadas para ugXX_ em multi-tabela)
    cfg = USINAS_CONFIG[usina]
    tabelas = cfg['tabelas']
    mapa_energia = cfg['energia']
    multi_tabela = len(tabelas) > 1

    if multi_tabela:
        colunas_energia = [
            f'ug{i+1:02d}_{mapa_energia[tab][0]}'
            for i, tab in enumerate(tabelas) if tab in mapa_energia
        ]
    else:
        # tabela única: pega todas as colunas de energia da tabela
        colunas_energia = mapa_energia.get(tabelas[0], [])

    # Seleciona frequência de agregação
    periodo = periodo.upper()
    if periodo in ('D', 'DIARIO', 'DAY'):
        freq = 'D'
    elif periodo in ('H', 'HORARIO', 'HOUR'):
        freq = 'h'
    elif periodo in ('M', 'MENSAL', 'MONTH'):
        freq = 'MS'
    else:
        raise ValueError(f"Período inválido: {periodo}")

    df_idx = df.set_index('data_hora')
    cols_existentes = [c for c in colunas_energia if c in df_idx.columns]
    if not cols_existentes:
        return {"status": "sem_dados", "usina": usina, "mensagem": "Sem colunas de energia no período."}

    agg = df_idx[cols_existentes].groupby(pd.Grouper(freq=freq)).agg(['first', 'last'])

    resultado_json = {}
    for col in cols_existentes:
        serie_first = agg[(col, 'first')]
        serie_last  = agg[(col, 'last')]

        delta = (serie_last - serie_first).clip(lower=0)
        delta = delta.round(2).dropna()

        if freq in ('D', 'h'):
            items = []
            for idx, val in delta.items():
                data_out = idx.date().isoformat() if freq == 'D' else idx.isoformat()
                items.append({'data': data_out, 'producao_Mwh': float(val)})
            resultado_json[col] = items
        elif freq == 'MS':
            resultado_json[col] = [
                {'data': idx.strftime('%Y-%m'), 'producao_Mwh': float(val)}
                for idx, val in delta.items()
            ]

    return {'usina': usina, 'periodo': periodo, 'resultado': resultado_json}
