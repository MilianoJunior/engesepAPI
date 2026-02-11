# -------------------------------------------------------------------
# TESTE FASE 2: Validar ProcessadorTelemetria (filtro + resolução)
# Uso: python -m teste.test_telemetria_fase2
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. testar_filtro_outliers   → valida IQR + ffill (sem perda de pontos)
# 2. testar_resolucao_auto    → valida resample automático por intervalo
# 3. testar_pipeline_completo → model (bruto) + processador (filtro + resample)
# -------------------------------------------------------------------

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from libs.db import Database
from libs.telemetria_model import TelemetriaModel
from libs.processador_telemetria import (
    filtrar_outliers, calcular_resolucao, processar_sensor
)


# ======================== HELPERS ========================

def _converter_data(v: str) -> str:
    """DD/MM/YYYY HH:mm → YYYY-MM-DD HH:MM:SS."""
    return datetime.strptime(v, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')


def _resumo(nome: str, erros: list):
    print('-' * 70)
    if erros:
        print(f'{nome}: FALHOU ({len(erros)} erros)')
        for e in erros:
            print(f'  ✗ {e}')
    else:
        print(f'{nome}: OK')
    print()


# ======================== TESTES ========================

def testar_filtro_outliers():
    """Valida que outliers são substituídos (ffill), sem perder registros."""
    print('=' * 70)
    print('TESTE F2-1: Filtro de outliers (IQR + ffill)')
    print('=' * 70)
    erros = []

    # Simula DataFrame com outlier óbvio
    dados = {
        'data_hora': pd.date_range('2026-01-15 08:00', periods=10, freq='1min'),
        'temperatura': [35.0, 35.2, 34.8, 35.1, 3276.7, 35.0, 34.9, 35.3, 35.1, 34.7]
    }
    df = pd.DataFrame(dados)
    total_antes = len(df)

    df_filtrado = filtrar_outliers(df)
    total_depois = len(df_filtrado)

    # Não pode perder registros
    if total_antes != total_depois:
        erros.append(f'Perdeu registros: {total_antes} → {total_depois}')

    # O outlier (3276.7) deve ter sido substituído
    max_val = df_filtrado['temperatura'].max()
    if max_val > 100:
        erros.append(f'Outlier não filtrado: max={max_val}')

    # O valor substituído deve ser o anterior (ffill → 35.1)
    valor_substituido = df_filtrado.iloc[4]['temperatura']
    if abs(valor_substituido - 35.1) > 0.01:
        erros.append(f'ffill incorreto: esperado ~35.1, recebeu {valor_substituido}')

    print(f'  Antes: max={df["temperatura"].max():.1f}')
    print(f'  Depois: max={max_val:.1f}')
    print(f'  Registros: {total_antes} → {total_depois}')
    print(f'  Valor substituído (idx 4): {valor_substituido}')

    _resumo('filtro_outliers', erros)
    return not erros


def testar_resolucao_auto():
    """Valida que a resolução é calculada corretamente pelo intervalo."""
    print('=' * 70)
    print('TESTE F2-2: Resolução automática')
    print('=' * 70)
    erros = []

    casos = [
        ('2026-01-15 08:00:00', '2026-01-15 09:00:00', '1min',  '≤1h → 1min'),
        ('2026-01-15 08:00:00', '2026-01-15 08:30:00', '1min',  '30min → 1min'),
        ('2026-01-15 00:00:00', '2026-01-16 00:00:00', '15min', '1d → 15min'),
        ('2026-01-15 00:00:00', '2026-01-15 12:00:00', '15min', '12h → 15min'),
        ('2026-01-01 00:00:00', '2026-01-07 00:00:00', '30min', '7d → 30min'),
        ('2026-01-01 00:00:00', '2026-01-03 00:00:00', '30min', '2d → 30min'),
    ]

    for dt_ini, dt_fim, esperado, desc in casos:
        resultado = calcular_resolucao(dt_ini, dt_fim)
        status = '✓' if resultado == esperado else '✗'
        print(f'  [{status}] {desc}: {resultado}')
        if resultado != esperado:
            erros.append(f'{desc}: esperado {esperado}, recebeu {resultado}')

    _resumo('resolucao_auto', erros)
    return not erros


def testar_pipeline_completo():
    """Model (bruto) + ProcessadorTelemetria (filtro + resample)."""
    print('=' * 70)
    print('TESTE F2-3: Pipeline completo (model → processador)')
    print('=' * 70)
    db = Database()
    model = TelemetriaModel(db)
    erros = []

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

    for usina, variavel, dt_ini_raw, dt_fim_raw in CASOS:
        try:
            dt_ini = _converter_data(dt_ini_raw)
            dt_fim = _converter_data(dt_fim_raw)

            # 1. Model busca dados brutos
            df_bruto = model.buscar_sensor(usina, variavel, dt_ini, dt_fim)

            # 2. Processador filtra + resample
            df_final = processar_sensor(df_bruto, dt_ini, dt_fim)

            linhas_bruto = len(df_bruto)
            linhas_final = len(df_final)
            ncols = len(df_final.columns) if not df_final.empty else 0

            print(f'  [OK] "{variavel}" -> bruto={linhas_bruto}, final={linhas_final}, colunas={ncols}')

            if not df_final.empty:
                col_valor = [c for c in df_final.columns if c != 'data_hora'][0]
                print(f'       min={df_final[col_valor].min():.3f}  '
                      f'max={df_final[col_valor].max():.3f}  '
                      f'media={df_final[col_valor].mean():.3f}')

            if not df_final.empty and ncols != 2:
                erros.append(f'{usina}/"{variavel}": esperado 2 colunas, recebeu {ncols}')

        except Exception as e:
            msg = f'{usina}/"{variavel}": {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    _resumo('pipeline_completo', erros)
    return not erros


# ======================== EXECUÇÃO ========================

if __name__ == '__main__':
    print('🔧 FASE 2: Teste ProcessadorTelemetria (filtro + resolução)')
    print('=' * 70)
    print()

    r1 = testar_filtro_outliers()
    r2 = testar_resolucao_auto()
    r3 = testar_pipeline_completo()

    print('\n' + '=' * 70)
    print('RESULTADO FINAL FASE 2')
    print('=' * 70)
    testes = [('F2-1 filtro_outliers', r1), ('F2-2 resolucao_auto', r2), ('F2-3 pipeline_completo', r3)]
    for nome, ok in testes:
        print(f'  {"✓" if ok else "✗"} {nome}')

    total_ok = sum(1 for _, ok in testes if ok)
    print(f'\n{total_ok}/{len(testes)} testes passaram.')
