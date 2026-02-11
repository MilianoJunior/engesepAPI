# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. calcular_producao_B → calcula produção via .diff() sobre último valor por janela
# 2. _resolver_colunas_energia → identifica colunas de energia no DataFrame real
# -------------------------------------------------------------------

import pandas as pd
from datetime import datetime, timedelta
from libs.utils import desempenho
from libs.usina_model import USINAS_CONFIG


def _resolver_colunas_energia(df: pd.DataFrame, usina: str) -> list:
    """Identifica colunas de energia no DataFrame (já renomeadas para ugXX_ em multi-tabela)."""
    cfg = USINAS_CONFIG[usina]
    tabelas = cfg['tabelas']
    mapa_energia = cfg['energia']
    multi_tabela = len(tabelas) > 1

    if multi_tabela:
        colunas = [
            f'ug{i+1:02d}_{mapa_energia[tab][0]}'
            for i, tab in enumerate(tabelas) if tab in mapa_energia
        ]
    else:
        colunas = mapa_energia.get(tabelas[0], [])

    return [c for c in colunas if c in df.columns]


@desempenho
def calcular_producao_B(df: pd.DataFrame, periodo: str, usina: str) -> dict:
    """Cálculo B: .diff() sobre último valor agrupado por período (D/M/H)."""
    print('#####'*10)
    print('Calculando producao B')
    print(df.head())
    print('#####'*10)
    if df.empty:
        return {"status": "sem_dados", "usina": usina, "mensagem": "Nenhum dado encontrado."}

    df = df.copy()
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    df = df.sort_values('data_hora')

    colunas_energia = _resolver_colunas_energia(df, usina)
    if not colunas_energia:
        return {"status": "sem_dados", "usina": usina, "mensagem": "Sem colunas de energia no período."}

    # Remove sentinela 103.00
    mask = (df[colunas_energia] == 103.00).any(axis=1)
    df = df[~mask]

    periodo = periodo.upper()

    if periodo in ('D', 'DIARIO', 'DAY'):
        df_agrupado = df.groupby(df['data_hora'].dt.date).last()
        df_agrupado[colunas_energia] = df_agrupado[colunas_energia].apply(pd.to_numeric, errors='coerce').astype(float)

        for col in colunas_energia:
            df_agrupado[f'prod_{col}'] = df_agrupado[col].diff()

        df_agrupado = df_agrupado.fillna(0)
        df_agrupado = df_agrupado.drop(columns=['data_hora'], errors='ignore')
        df_agrupado = df_agrupado.drop(columns=colunas_energia)

    elif periodo in ('M', 'MENSAL', 'MONTH'):
        df['ano_mes'] = df['data_hora'].dt.strftime('%Y-%m')
        df_agrupado = df.groupby('ano_mes').last()
        df_agrupado[colunas_energia] = df_agrupado[colunas_energia].apply(pd.to_numeric, errors='coerce').astype(float)

        if len(df_agrupado) < 6:
            last_month = df_agrupado.index[0]
            after_last_month = datetime.strptime(last_month, '%Y-%m') - timedelta(days=30)
            after_last_month = after_last_month.strftime('%Y-%m')
            for col in colunas_energia:
                df_agrupado.loc[after_last_month, col] = 0
            df_agrupado = df_agrupado.sort_index()

        for col in colunas_energia:
            df_agrupado[f'prod_{col}'] = df_agrupado[col].diff()

        df_agrupado = df_agrupado.fillna(0)
        df_agrupado = df_agrupado.drop(columns=colunas_energia)
        if 'data_hora' in df_agrupado.columns:
            df_agrupado = df_agrupado.drop(columns=['data_hora'])

    elif periodo in ('H', 'HORARIO', 'HOUR'):
        df['hora'] = df['data_hora'].dt.floor('h')
        df_agrupado = df.groupby('hora').last().reset_index()
        df_agrupado[colunas_energia] = df_agrupado[colunas_energia].apply(pd.to_numeric, errors='coerce').astype(float)

        for col in colunas_energia:
            df_agrupado[f'prod_{col}'] = df_agrupado[col].diff()

        df_agrupado = df_agrupado.fillna(0)
        df_agrupado = df_agrupado.drop(columns=colunas_energia)
        df_agrupado = df_agrupado.drop(columns=['data_hora'], errors='ignore')
        df_agrupado.set_index('hora', inplace=True)
    else:
        raise ValueError(f"Período inválido: {periodo}")

    # Converte para formato JSON compatível com calculosA
    resultado_json = {}
    for col in df_agrupado.columns:
        items = []
        for idx, val in df_agrupado[col].items():
            if isinstance(idx, str):
                data_out = idx
            elif hasattr(idx, 'isoformat'):
                data_out = idx.isoformat()
            else:
                data_out = str(idx)
            items.append({'data': data_out, 'producao_Mwh': float(val)})
        resultado_json[col] = items

    return {'usina': usina, 'periodo': periodo, 'resultado': resultado_json}
