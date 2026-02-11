# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. processar_sensor    → recebe DF bruto → filtra outliers → resample automático
# 2. processar_grupo     → idem para grupo (múltiplas colunas)
# 3. filtrar_outliers    → IQR: substitui outliers pelo último valor válido (ffill)
# 4. calcular_resolucao  → define freq de resample com base no intervalo
# 5. aplicar_resample    → resample por média (ou .last() para status)
# -------------------------------------------------------------------

import pandas as pd

# ======================== CONFIGURAÇÃO ========================

# Resolução automática baseada no intervalo solicitado
RESOLUCAO_AUTO = [
    (1,    '1min'),   # ≤ 1h  → raw
    (24,   '15min'),  # ≤ 1d  → 15min
    (None, '30min'),  # > 1d  → 30min
]

IQR_FATOR = 1.5

GRUPOS_STATUS = {'status'}


# ======================== FUNÇÕES PÚBLICAS ========================

def processar_sensor(df: pd.DataFrame, data_inicio: str, data_fim: str,
                     grupo: str = '') -> pd.DataFrame:
    """Pipeline completo: outliers → resolução → resample (1 variável)."""
    if df.empty:
        return df

    eh_status = grupo in GRUPOS_STATUS

    if not eh_status:
        df = filtrar_outliers(df)

    freq = calcular_resolucao(data_inicio, data_fim)
    df = aplicar_resample(df, freq, usar_last=eh_status)

    return df


def processar_grupo(df: pd.DataFrame, data_inicio: str, data_fim: str,
                    grupo: str = '') -> pd.DataFrame:
    """Pipeline completo para grupo (múltiplas colunas)."""
    return processar_sensor(df, data_inicio, data_fim, grupo)


# ======================== FUNÇÕES DE PROCESSAMENTO ========================

def filtrar_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Substitui outliers (IQR) pelo último valor válido (ffill)."""
    if df.empty:
        return df

    df = df.copy()
    colunas = [c for c in df.columns if c != 'data_hora']

    for col in colunas:
        serie = df[col]
        q1 = serie.quantile(0.25)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1

        limite_inf = q1 - IQR_FATOR * iqr
        limite_sup = q3 + IQR_FATOR * iqr

        mascara = (serie < limite_inf) | (serie > limite_sup)
        if mascara.any():
            df.loc[mascara, col] = pd.NA
            df[col] = df[col].ffill()

    return df


def calcular_resolucao(data_inicio: str, data_fim: str) -> str:
    """Define frequência de resample com base no intervalo solicitado."""
    dt_ini = pd.to_datetime(data_inicio)
    dt_fim = pd.to_datetime(data_fim)
    delta_horas = (dt_fim - dt_ini).total_seconds() / 3600

    for limite, freq in RESOLUCAO_AUTO:
        if limite is None or delta_horas <= limite:
            return freq

    return '30min'


def aplicar_resample(df: pd.DataFrame, freq: str, usar_last: bool = False) -> pd.DataFrame:
    """Resample do DataFrame pela frequência calculada."""
    if df.empty or freq == '1min':
        return df

    df = df.set_index('data_hora')
    if usar_last:
        df = df.resample(freq).last()
    else:
        df = df.resample(freq).mean()

    df = df.dropna(how='all').reset_index()
    return df
