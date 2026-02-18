# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. _meses_fechados_no_intervalo → gera lista de meses fechados entre data_inicio e data_fim
# 2. buscar_historico_cache       → lê producao_historica para meses fechados disponíveis
# 3. calcular_e_persistir_mes    → calcula um mês fechado e insere/atualiza na tabela
# 4. garantir_meses_no_cache     → verifica quais meses faltam e chama calcular_e_persistir_mes
# -------------------------------------------------------------------

import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from libs.db import Database
from libs.calculos import Calculos


# ======================== CONFIGURAÇÃO ========================

TABELA = 'producao_historica'


# ======================== FUNÇÕES ========================

def _meses_fechados_no_intervalo(data_inicio: str, data_fim: str) -> list[str]:
    """
    Retorna lista de meses no formato 'YYYY-MM' que estão fechados
    (excluindo o mês atual) dentro do intervalo [data_inicio, data_fim].
    """
    inicio = pd.to_datetime(data_inicio).to_period('M')
    fim = pd.to_datetime(data_fim).to_period('M')
    mes_atual = pd.Period(datetime.now(), 'M')

    meses = []
    cursor = inicio
    while cursor <= fim:
        if cursor < mes_atual:
            meses.append(str(cursor))
        cursor += 1
    return meses


def buscar_historico_cache(db: Database, usina: str, meses: list[str]) -> list[dict]:
    """
    Lê producao_historica para os meses informados.
    Retorna list[dict] no mesmo formato de Calculos._to_resultado_json.
    """
    if not meses:
        return []

    placeholders = ', '.join(['%s'] * len(meses))
    query = (
        f"SELECT mes, coluna, producao_mwh FROM {TABELA} "
        f"WHERE usina = %s AND mes IN ({placeholders}) "
        f"ORDER BY mes"
    )
    params = (usina, *meses)
    df = db.fetch_dataframe(query, params)
    if df is None or df.empty:
        return []

    # Pivota: linhas = meses, colunas = UG-XX Energia Acumulada
    pivot = df.pivot(index='mes', columns='coluna', values='producao_mwh')
    pivot.columns.name = None
    pivot = pivot.reset_index()

    resultado = []
    for _, row in pivot.iterrows():
        item = {'data': row['mes']}
        for col in pivot.columns:
            if col == 'mes':
                continue
            item[f'prod_{col}'] = float(row[col]) if pd.notna(row[col]) else 0.0
        resultado.append(item)
    return resultado


def calcular_e_persistir_mes(
    db: Database,
    calculos: Calculos,
    usina: str,
    mes: str,
    df_mes: pd.DataFrame,
) -> dict:
    """
    Calcula produção de um mês fechado e persiste em producao_historica.
    Retorna dict {coluna: producao_mwh} para o mês calculado.
    """
    resultado_lista = calculos.calcular_energia_acumulada(df_mes, 'M', usina)
    if not resultado_lista:
        return {}

    # resultado_lista tem exatamente 1 item (o mês calculado)
    item = next((r for r in resultado_lista if r.get('data') == mes), None)
    if item is None:
        return {}

    valores = {k.replace('prod_', ''): v for k, v in item.items() if k.startswith('prod_')}

    for coluna, producao_mwh in valores.items():
        query = (
            f"INSERT INTO {TABELA} (usina, mes, coluna, producao_mwh) "
            f"VALUES (%s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE producao_mwh = VALUES(producao_mwh), "
            f"calculado_em = CURRENT_TIMESTAMP"
        )
        db.execute_query(query, (usina, mes, coluna, producao_mwh))
        print(f"[PROD-CACHE] SET usina={usina} mes={mes} coluna={coluna!r} mwh={producao_mwh}")

    return valores


def garantir_meses_no_cache(
    db: Database,
    calculos: Calculos,
    usina: str,
    meses_necessarios: list[str],
    buscar_df_mes_fn,
) -> list[str]:
    """
    Verifica quais meses estão faltando em producao_historica e os calcula/persiste.
    buscar_df_mes_fn(mes_inicio, mes_fim) -> pd.DataFrame  (callback para buscar dados brutos)
    Retorna lista de meses que foram calculados agora (lazy fill).
    """
    if not meses_necessarios:
        return []

    placeholders = ', '.join(['%s'] * len(meses_necessarios))
    query = (
        f"SELECT DISTINCT mes FROM {TABELA} "
        f"WHERE usina = %s AND mes IN ({placeholders})"
    )
    df_existentes = db.fetch_dataframe(query, (usina, *meses_necessarios))
    meses_existentes = set(df_existentes['mes'].tolist()) if df_existentes is not None and not df_existentes.empty else set()

    meses_faltando = [m for m in meses_necessarios if m not in meses_existentes]
    calculados = []

    for mes in meses_faltando:
        mes_inicio = f"{mes}-01 00:00:00"
        # último dia do mês
        fim_periodo = pd.Period(mes, 'M').to_timestamp('D', 'E')
        mes_fim = fim_periodo.strftime('%Y-%m-%d 23:59:59')

        df_mes = buscar_df_mes_fn(mes_inicio, mes_fim)
        if df_mes is None or df_mes.empty:
            print(f"[PROD-CACHE] SKIP usina={usina} mes={mes} (sem dados)")
            continue

        calcular_e_persistir_mes(db, calculos, usina, mes, df_mes)
        calculados.append(mes)

    return calculados
