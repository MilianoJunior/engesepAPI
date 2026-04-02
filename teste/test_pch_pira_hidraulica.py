# -------------------------------------------------------------------
# TESTE: PCH-PIRA grupo hidraulica (tabela mc01Analogicas)
# Uso: python -m teste.test_pch_pira_hidraulica
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. testar_config_hidraulica  → valida mapeamento no usinas.json
# 2. testar_tabela_existe       → verifica se mc01Analogicas existe no banco
# 3. testar_colunas_existem     → valida colunas NVMontante e NvJusante
# 4. testar_consulta_direta     → SELECT direto na tabela sem passar pelo model
# 5. testar_buscar_grupo        → busca via TelemetriaModel.buscar_grupo
# 6. testar_buscar_sensor       → busca via TelemetriaModel.buscar_sensor
# -------------------------------------------------------------------

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.telemetria_model import TelemetriaModel
from libs.usina_model import USINAS_CONFIG

# ======================== CONFIGURAÇÃO ========================

USINA = 'PCH-PIRA'
GRUPO = 'hidraulica'
TABELA = 'mc01Analogicas'
# Janela ampla pra garantir dados
DATA_INICIO = '2026-03-01 00:00:00'
DATA_FIM = '2026-04-02 23:59:59'

COLUNAS_ESPERADAS = ['NVMontante', 'NvJusante']
ALIASES_ESPERADOS = ['Nível Montante', 'Nível Jusante']


# ======================== TESTES ========================

def testar_config_hidraulica():
    """Valida que o mapeamento no usinas.json está correto."""
    print('=' * 70)
    print('TESTE 1: Validar config hidraulica no usinas.json')
    print('=' * 70)

    cfg = USINAS_CONFIG.get(USINA)
    if not cfg:
        print(f'  [ERRO] Usina {USINA} não encontrada no config')
        return False

    hidraulica = cfg.get(GRUPO)
    if not hidraulica:
        print(f'  [ERRO] Grupo "{GRUPO}" não encontrado para {USINA}')
        return False

    if not isinstance(hidraulica, dict):
        print(f'  [ERRO] Grupo "{GRUPO}" não é dict: {type(hidraulica)}')
        return False

    tabelas_grupo = list(hidraulica.keys())
    colunas = hidraulica.get(TABELA, [])

    print(f'  Tabelas no grupo: {tabelas_grupo}')
    print(f'  Colunas mapeadas: {colunas}')

    tabelas_config = cfg.get('tabelas', [])
    tabela_no_config = TABELA in tabelas_config
    print(f'  Tabela "{TABELA}" em cfg["tabelas"]? {tabela_no_config}')

    if not tabela_no_config:
        print(f'  ⚠️  ALERTA: "{TABELA}" NÃO está em tabelas={tabelas_config}')
        print(f'     Isso pode causar busca vazia no TelemetriaModel.buscar_grupo')

    if not colunas:
        print(f'  [ERRO] Nenhuma coluna mapeada para {TABELA}')
        return False

    print(f'  [OK] Config válida: {len(colunas)} colunas em {TABELA}')
    return True


def testar_tabela_existe(db: Database):
    """Verifica se mc01Analogicas existe no banco."""
    print('\n' + '=' * 70)
    print('TESTE 2: Tabela mc01Analogicas existe?')
    print('=' * 70)

    try:
        df = db.fetch_dataframe(f"SHOW TABLES LIKE '{TABELA}'")
        if df.empty:
            print(f'  [ERRO] Tabela {TABELA} NÃO existe no banco')
            return False
        print(f'  [OK] Tabela {TABELA} existe')
        return True
    except Exception as e:
        print(f'  [ERRO] {type(e).__name__}: {e}')
        return False


def testar_colunas_existem(db: Database):
    """Valida que as colunas NVMontante e NvJusante existem na tabela."""
    print('\n' + '=' * 70)
    print('TESTE 3: Colunas existem na tabela?')
    print('=' * 70)

    try:
        df = db.fetch_dataframe(f"SHOW COLUMNS FROM {TABELA}")
        colunas_banco = list(df.iloc[:, 0]) if not df.empty else []
        print(f'  Colunas na tabela: {colunas_banco[:15]}...')

        erros = []
        for col in COLUNAS_ESPERADAS:
            if col in colunas_banco:
                print(f'  [OK] {col} encontrada')
            else:
                print(f'  [ERRO] {col} NÃO encontrada')
                erros.append(col)

        # Verifica coluna temporal
        col_temporal = 'Time_Stamp' if 'Time_Stamp' in colunas_banco else 'data_hora'
        print(f'  Coluna temporal detectada: {col_temporal}')

        return not erros
    except Exception as e:
        print(f'  [ERRO] {type(e).__name__}: {e}')
        return False


def testar_consulta_direta(db: Database):
    """SELECT direto na tabela para validar dados."""
    print('\n' + '=' * 70)
    print('TESTE 4: Consulta direta na tabela')
    print('=' * 70)

    # Testa com Time_Stamp (padrão PCH-PIRA) e fallback data_hora
    queries = [
        (
            'Time_Stamp',
            f"SELECT Time_Stamp AS data_hora, NVMontante, NvJusante "
            f"FROM {TABELA} "
            f"WHERE Time_Stamp >= '{DATA_INICIO}' AND Time_Stamp <= '{DATA_FIM}' "
            f"ORDER BY Time_Stamp LIMIT 10"
        ),
        (
            'data_hora',
            f"SELECT data_hora, NVMontante, NvJusante "
            f"FROM {TABELA} "
            f"WHERE data_hora >= '{DATA_INICIO}' AND data_hora <= '{DATA_FIM}' "
            f"ORDER BY data_hora LIMIT 10"
        ),
    ]

    for col_temporal, query in queries:
        try:
            print(f'\n  Tentando com coluna temporal: {col_temporal}')
            df = db.fetch_dataframe(query)

            if df.empty:
                print(f'  [AVISO] Query retornou vazio (col={col_temporal})')
                continue

            print(f'  [OK] {len(df)} registros retornados')
            print(f'  Colunas: {list(df.columns)}')
            print(f'\n  Primeiros registros:')
            print(df.to_string(index=False))
            return True

        except Exception as e:
            print(f'  [ERRO] {col_temporal}: {type(e).__name__}: {e}')

    print('  [ERRO] Nenhuma query retornou dados')
    return False


def testar_buscar_grupo(model: TelemetriaModel):
    """Testa buscar_grupo via TelemetriaModel."""
    print('\n' + '=' * 70)
    print('TESTE 5: TelemetriaModel.buscar_grupo')
    print('=' * 70)

    try:
        df = model.buscar_grupo(USINA, GRUPO, DATA_INICIO, DATA_FIM)

        if df.empty:
            print(f'  [AVISO] DataFrame vazio — provavelmente bug de mapeamento tabelas[]')
            return False

        print(f'  [OK] {len(df)} registros')
        print(f'  Colunas: {list(df.columns)}')
        _imprimir_amostra(df)
        return True

    except Exception as e:
        print(f'  [ERRO] {type(e).__name__}: {e}')
        return False


def testar_buscar_sensor(model: TelemetriaModel):
    """Testa buscar_sensor para cada alias do grupo hidraulica."""
    print('\n' + '=' * 70)
    print('TESTE 6: TelemetriaModel.buscar_sensor')
    print('=' * 70)

    erros = []
    for alias in ALIASES_ESPERADOS:
        try:
            df = model.buscar_sensor(USINA, alias, DATA_INICIO, DATA_FIM)

            if df.empty:
                print(f'  [AVISO] "{alias}" retornou vazio')
                erros.append(f'{alias}: vazio')
                continue

            print(f'  [OK] "{alias}" → {len(df)} registros, colunas={list(df.columns)}')
            _imprimir_amostra(df)

        except Exception as e:
            msg = f'{alias}: {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    if erros:
        print(f'\n  {len(erros)} erro(s):')
        for e in erros:
            print(f'    - {e}')
        return False

    return True


# ======================== HELPERS ========================

def _imprimir_amostra(df: pd.DataFrame, n: int = 3):
    """Imprime amostra do DataFrame."""
    amostra = pd.concat([df.head(n), df.tail(n)]).drop_duplicates()
    print(f'\n  Amostra ({len(amostra)} linhas):')
    print('  ' + amostra.to_string(index=False).replace('\n', '\n  '))
    print()


# ======================== EXECUÇÃO ========================

if __name__ == '__main__':
    print(f'🔧 TESTE: {USINA} — grupo {GRUPO}')
    print('=' * 70)

    db = Database()
    model = TelemetriaModel(db)

    resultados = {
        'config':          testar_config_hidraulica(),
        'tabela_existe':   testar_tabela_existe(db),
        'colunas_existem': testar_colunas_existem(db),
        'consulta_direta': testar_consulta_direta(db),
        'buscar_grupo':    testar_buscar_grupo(model),
        'buscar_sensor':   testar_buscar_sensor(model),
    }

    print('\n' + '=' * 70)
    print('RESUMO FINAL')
    print('=' * 70)
    total_ok = sum(resultados.values())
    total = len(resultados)
    for nome, ok in resultados.items():
        status = '✅' if ok else '❌'
        print(f'  {status} {nome}')

    print(f'\n  Resultado: {total_ok}/{total} testes passaram')

    if total_ok < total:
        print('\n  ⚠️  Há falhas — verificar mapeamento e coluna temporal')
