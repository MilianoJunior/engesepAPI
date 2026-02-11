# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. _converter_data     → DD/MM/YYYY HH:mm → YYYY-MM-DD HH:MM:SS
# 2. carregar_dados      → executa buscar_sensor para todos os casos
# 3. main (streamlit)    → sidebar para filtro + gráfico de linha
# -------------------------------------------------------------------
# Uso: streamlit run teste/visualizar_sensores.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from datetime import datetime
from libs.db import Database
from libs.telemetria_model import TelemetriaModel

# ======================== CONFIGURAÇÃO ========================

CASOS = [
    # ── Aparecida (1 UG / 1 tabela) ──
    ('CGH-APARECIDA', 'UG-01 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-APARECIDA', 'UG-01 Temp. Óleo UHLM',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    # ── FAE (2 UGs / 1 tabela) ──
    ('CGH-FAE', 'UG-01 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-FAE', 'UG-02 Potência Ativa',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-FAE', 'UG-01 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-FAE', 'UG-02 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    # ── Pedras (2 UGs / 2 tabelas) ──
    ('PCH-PEDRAS', 'UG-01 Tensão Fase A',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('PCH-PEDRAS', 'UG-02 Tensão Fase A',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('PCH-PEDRAS', 'UG-01 Temp. Óleo UHLM',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('PCH-PEDRAS', 'UG-02 Temp. Óleo UHLM',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    # ── Hoppen (2 UGs / 2 tabelas) ──
    ('CGH-HOPPEN', 'UG-01 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),

    ('CGH-HOPPEN', 'UG-02 Fator de Potência',
     '15/01/2026 00:00', '16/01/2026 00:00'),
]


# ======================== FUNÇÕES ========================

def _converter_data(v: str) -> str:
    """DD/MM/YYYY HH:mm → YYYY-MM-DD HH:MM:SS."""
    return datetime.strptime(v, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')


@st.cache_resource
def get_model():
    """Instância única do TelemetriaModel."""
    return TelemetriaModel(Database())


@st.cache_data(ttl=300)
def carregar_dados(usina: str, variavel: str, dt_ini: str, dt_fim: str) -> pd.DataFrame:
    """Busca sensor e retorna DataFrame."""
    model = get_model()
    dt_ini_sql = _converter_data(dt_ini)
    dt_fim_sql = _converter_data(dt_fim)
    return model.buscar_sensor(usina, variavel, dt_ini_sql, dt_fim_sql)


# ======================== STREAMLIT ========================

st.set_page_config(page_title='Validação Sensores', layout='wide')
st.title('📊 Validação de Sensores — TelemetriaModel')

# Sidebar: seleção de caso
labels = [f'{u} | {v} ({di} → {df})' for u, v, di, df in CASOS]
selecionado = st.sidebar.selectbox('Selecione o caso de teste:', labels)
idx = labels.index(selecionado)
usina, variavel, dt_ini, dt_fim = CASOS[idx]

st.sidebar.markdown('---')
st.sidebar.markdown(f'**Usina:** `{usina}`')
st.sidebar.markdown(f'**Variável:** `{variavel}`')
st.sidebar.markdown(f'**Período:** `{dt_ini}` → `{dt_fim}`')

# Carregar dados
with st.spinner('Consultando banco...'):
    df = carregar_dados(usina, variavel, dt_ini, dt_fim)

if df.empty:
    st.warning(f'Sem dados para {usina} / {variavel} no período selecionado.')
    st.stop()

col_valor = [c for c in df.columns if c != 'data_hora'][0]

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric('Registros', len(df))
col2.metric('Mín', f'{df[col_valor].min():.3f}')
col3.metric('Máx', f'{df[col_valor].max():.3f}')
col4.metric('Média', f'{df[col_valor].mean():.3f}')

# Gráfico
st.subheader(f'{variavel}')
chart_df = df.set_index('data_hora')[[col_valor]]
st.line_chart(chart_df)

# Tabela
with st.expander('Ver tabela completa'):
    st.dataframe(df, use_container_width=True)

# Rodapé
st.sidebar.markdown('---')
st.sidebar.markdown('**Todos os casos:**')
mostrar_todos = st.sidebar.checkbox('Exibir todos os gráficos')

if mostrar_todos:
    st.markdown('---')
    st.subheader('Todos os casos de teste')

    for i, (u, v, di, df_raw) in enumerate(CASOS):
        df_caso = carregar_dados(u, v, di, df_raw)
        if df_caso.empty:
            st.warning(f'⚠️ {u} / {v}: sem dados')
            continue

        col_v = [c for c in df_caso.columns if c != 'data_hora'][0]
        st.markdown(f'**{u} — {v}** ({di} → {df_raw})')

        c1, c2, c3 = st.columns(3)
        c1.metric('Registros', len(df_caso))
        c2.metric('Mín', f'{df_caso[col_v].min():.3f}')
        c3.metric('Máx', f'{df_caso[col_v].max():.3f}')

        chart = df_caso.set_index('data_hora')[[col_v]]
        st.line_chart(chart)
