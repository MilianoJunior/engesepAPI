# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. carregar_dados      → model (bruto) + processador (filtro + resample)
# 2. main (streamlit)    → sidebar seleção + plotly chart + tabela
# -------------------------------------------------------------------
# Uso: streamlit run teste/visualizar_fase2.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from libs.db import Database
from libs.telemetria_model import TelemetriaModel
from libs.processador_telemetria import processar_sensor

# ======================== CONFIGURAÇÃO ========================

CASOS = [
    ('CGH-APARECIDA', 'UG-01 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-APARECIDA', 'UG-01 Temp. Óleo UHLM',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-FAE', 'UG-01 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-FAE', 'UG-02 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('PCH-PEDRAS', 'UG-01 Tensão Fase A',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('PCH-PEDRAS', 'UG-02 Temp. Óleo UHLM',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-HOPPEN', 'UG-01 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-HOPPEN', 'UG-02 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),
]


# ======================== FUNÇÕES ========================

def _converter_data(v: str) -> str:
    return datetime.strptime(v, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')


@st.cache_resource
def get_model():
    return TelemetriaModel(Database())


@st.cache_data(ttl=300)
def carregar_dados(usina: str, variavel: str, dt_ini: str, dt_fim: str) -> pd.DataFrame:
    """Model (bruto) → Processador (filtro + resample)."""
    model = get_model()
    dt_ini_sql = _converter_data(dt_ini)
    dt_fim_sql = _converter_data(dt_fim)
    df_bruto = model.buscar_sensor(usina, variavel, dt_ini_sql, dt_fim_sql)
    return processar_sensor(df_bruto, dt_ini_sql, dt_fim_sql)


def criar_grafico(df: pd.DataFrame, variavel: str) -> go.Figure:
    """Gráfico Plotly com eixo Y ajustado ao range real."""
    col_valor = [c for c in df.columns if c != 'data_hora'][0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['data_hora'],
        y=df[col_valor],
        mode='lines',
        name=col_valor,
        line=dict(color='#3b82f6', width=1.5),
    ))

    y_min = df[col_valor].min()
    y_max = df[col_valor].max()
    margem = (y_max - y_min) * 0.1 if y_max != y_min else 1

    fig.update_layout(
        title=variavel,
        xaxis_title='Data/Hora',
        yaxis_title='Valor',
        yaxis=dict(range=[y_min - margem, y_max + margem]),
        template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=50, b=50),
    )
    return fig


# ======================== STREAMLIT ========================

st.set_page_config(page_title='Fase 2 — Validação', layout='wide')
st.title('📊 Fase 2 — Outliers + Resolução Automática')

# Sidebar
labels = [f'{u} | {v}' for u, v, _, _ in CASOS]
selecionado = st.sidebar.selectbox('Caso de teste:', labels)
idx = labels.index(selecionado)
usina, variavel, dt_ini, dt_fim = CASOS[idx]

st.sidebar.markdown('---')
st.sidebar.markdown(f'**Usina:** `{usina}`')
st.sidebar.markdown(f'**Variável:** `{variavel}`')
st.sidebar.markdown(f'**Período:** `{dt_ini}` → `{dt_fim}`')

# Dados
with st.spinner('Consultando banco...'):
    df = carregar_dados(usina, variavel, dt_ini, dt_fim)

if df.empty:
    st.warning(f'Sem dados para {usina} / {variavel}')
    st.stop()

col_valor = [c for c in df.columns if c != 'data_hora'][0]

# Métricas
c1, c2, c3, c4 = st.columns(4)
c1.metric('Registros', len(df))
c2.metric('Mín', f'{df[col_valor].min():.3f}')
c3.metric('Máx', f'{df[col_valor].max():.3f}')
c4.metric('Média', f'{df[col_valor].mean():.3f}')

# Gráfico
fig = criar_grafico(df, variavel)
st.plotly_chart(fig, use_container_width=True)

# Tabela
with st.expander('Ver tabela completa'):
    st.dataframe(df, width='stretch')

# Todos os gráficos
st.sidebar.markdown('---')
mostrar_todos = st.sidebar.checkbox('Exibir todos os gráficos')

if mostrar_todos:
    st.markdown('---')
    st.subheader('Todos os casos')

    for u, v, di, df_raw in CASOS:
        df_caso = carregar_dados(u, v, di, df_raw)
        if df_caso.empty:
            st.warning(f'⚠️ {u} / {v}: sem dados')
            continue

        col_v = [c for c in df_caso.columns if c != 'data_hora'][0]

        c1, c2, c3 = st.columns(3)
        c1.metric('Registros', len(df_caso))
        c2.metric('Mín', f'{df_caso[col_v].min():.3f}')
        c3.metric('Máx', f'{df_caso[col_v].max():.3f}')

        fig_caso = criar_grafico(df_caso, f'{u} — {v}')
        st.plotly_chart(fig_caso, use_container_width=True)
