# -------------------------------------------------------------------
# TESTE FASE 1: Validar TelemetriaModel (consulta por grupo e sensor)
# Uso: python -m teste.test_telemetria_model
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. testar_listar_grupos        → valida listagem de grupos e aliases
# 2. testar_buscar_grupo         → consulta grupo completo para cada usina
# 3. testar_buscar_sensor        → consulta variável individual
# 4. testar_variavel_inexistente → valida erro para alias inválido
# 5. testar_grupo_inexistente    → valida erro para grupo inválido
# -------------------------------------------------------------------

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.telemetria_model import TelemetriaModel
from libs.usina_model import USINAS_CONFIG, GRUPOS_IGNORADOS

DATA_INICIO = '2026-01-01 00:00:00'
DATA_FIM = '2026-01-01 01:00:00'


def testar_listar_grupos():
    """Valida que listar_grupos retorna grupos com aliases não-vazios."""
    print('=' * 70)
    print('TESTE 1: listar_grupos')
    print('=' * 70)
    model = TelemetriaModel(Database())
    erros = []

    for usina in USINAS_CONFIG:
        grupos = model.listar_grupos(usina)
        if not grupos:
            erros.append(f'{usina}: nenhum grupo retornado')
            continue

        print(f'\n{usina}:')
        for grupo, aliases in grupos.items():
            if not aliases:
                erros.append(f'{usina}/{grupo}: sem aliases')
            print(f'  {grupo}: {len(aliases)} variáveis')

    _resumo('listar_grupos', erros)
    return not erros


def testar_buscar_grupo():
    """Consulta o primeiro grupo de cada usina e valida retorno."""
    print('\n' + '=' * 70)
    print('TESTE 2: buscar_grupo')
    print('=' * 70)
    db = Database()
    model = TelemetriaModel(db)
    erros = []

    for usina in USINAS_CONFIG:
        grupos = model.listar_grupos(usina)
        grupo_teste = next(iter(grupos))

        try:
            df = model.buscar_grupo(usina, grupo_teste, DATA_INICIO, DATA_FIM)
            linhas = len(df)
            colunas = list(df.columns) if not df.empty else []
            print(f'  [OK] {usina}/{grupo_teste} -> {linhas} registros, colunas={colunas[:3]}...')

            if not df.empty and 'data_hora' not in df.columns:
                erros.append(f'{usina}/{grupo_teste}: sem data_hora no retorno')

        except Exception as e:
            msg = f'{usina}/{grupo_teste}: {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    _resumo('buscar_grupo', erros)
    return not erros


def _converter_data(v: str) -> str:
    """Simula o validator do Pydantic: DD/MM/YYYY HH:mm → YYYY-MM-DD HH:MM:SS."""
    from datetime import datetime
    dt_obj = datetime.strptime(v, '%d/%m/%Y %H:%M')
    return dt_obj.strftime('%Y-%m-%d %H:%M:%S')


def testar_buscar_sensor():
    """Testa leitura individual de sensores simulando payloads reais."""
    print('\n' + '=' * 70)
    print('TESTE 3: buscar_sensor (simulação payload)')
    print('=' * 70)
    db = Database()
    model = TelemetriaModel(db)
    erros = []

    # Payloads reais: janelas de 1h (compatíveis com períodos válidos)
    # (usina, variavel, data_inicio, data_fim)
    CASOS = [
        # ── Aparecida (1 UG / 1 tabela) ──
        ('CGH-APARECIDA', 'UG-01 Potência Ativa',
         '15/01/2026 08:00', '15/01/2026 09:00'),

        ('CGH-APARECIDA', 'UG-01 Temp. Óleo UHLM',
         '10/01/2026 10:00', '10/01/2026 11:00'),

        # ── FAE (2 UGs / 1 tabela) ──
        ('CGH-FAE', 'UG-01 Potência Ativa',
         '05/01/2026 08:00', '05/01/2026 09:00'),

        ('CGH-FAE', 'UG-02 Potência Ativa',
         '05/01/2026 08:00', '05/01/2026 09:00'),

        ('CGH-FAE', 'UG-01 Fator de Potência',
         '05/01/2026 14:00', '05/01/2026 15:00'),

        ('CGH-FAE', 'UG-02 Fator de Potência',
         '05/01/2026 14:00', '05/01/2026 15:00'),

        # ── Pedras (2 UGs / 2 tabelas) ──
        ('PCH-PEDRAS', 'UG-01 Tensão Fase A',
         '20/01/2026 08:00', '20/01/2026 09:00'),

        ('PCH-PEDRAS', 'UG-02 Tensão Fase A',
         '20/01/2026 08:00', '20/01/2026 09:00'),

        ('PCH-PEDRAS', 'UG-01 Temp. Óleo UHLM',
         '01/01/2026 00:00', '01/01/2026 01:00'),

        ('PCH-PEDRAS', 'UG-02 Temp. Óleo UHLM',
         '01/01/2026 00:00', '01/01/2026 01:00'),

        # ── Hoppen (2 UGs / 2 tabelas) ──
        ('CGH-HOPPEN', 'UG-01 Fator de Potência',
         '01/01/2026 12:00', '01/01/2026 13:00'),

        ('CGH-HOPPEN', 'UG-02 Fator de Potência',
         '01/01/2026 12:00', '01/01/2026 13:00'),
    ]

    for usina, variavel, dt_ini_raw, dt_fim_raw in CASOS:
        try:
            dt_ini = _converter_data(dt_ini_raw)
            dt_fim = _converter_data(dt_fim_raw)

            df = model.buscar_sensor(usina, variavel, dt_ini, dt_fim)
            linhas = len(df)
            ncols = len(df.columns) if not df.empty else 0

            print(f'  [OK] "{variavel}" -> {linhas} registros, {ncols} colunas')

            if not df.empty:
                _imprimir_tabela(df, variavel)

            if not df.empty and ncols != 2:
                erros.append(f'{usina}/"{variavel}": esperado 2 colunas, recebeu {ncols}: {list(df.columns)}')

        except Exception as e:
            msg = f'{usina}/"{variavel}": {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    _resumo('buscar_sensor', erros)
    return not erros


def _imprimir_tabela(df: pd.DataFrame, variavel: str):
    """Imprime mini-tabela com 2 primeiros e 2 últimos registros."""
    col_valor = [c for c in df.columns if c != 'data_hora'][0]
    linhas_show = pd.concat([df.head(2), df.tail(2)]).drop_duplicates()

    print(f'       {"data_hora":<26} {col_valor}')
    print(f'       {"-"*26} {"-"*20}')
    exibidos = 0
    for _, row in linhas_show.iterrows():
        dt = row['data_hora']
        dt_str = dt.strftime('%Y-%m-%d %H:%M:%S') if hasattr(dt, 'strftime') else str(dt)
        val = row[col_valor]
        val_str = f'{val:.3f}' if isinstance(val, (int, float)) else str(val)
        print(f'       {dt_str:<26} {val_str}')
        exibidos += 1
        if exibidos == 2 and len(linhas_show) > 2:
            print(f'       {"...":<26} ...')
    print()


def testar_variavel_inexistente():
    """Valida que buscar_sensor com alias inválido levanta ValueError."""
    print('\n' + '=' * 70)
    print('TESTE 4: variável inexistente')
    print('=' * 70)
    model = TelemetriaModel(Database())
    usina = next(iter(USINAS_CONFIG))

    try:
        model.buscar_sensor(usina, 'VARIAVEL_QUE_NAO_EXISTE', DATA_INICIO, DATA_FIM)
        print('  [FALHA] Deveria ter levantado ValueError')
        return False
    except ValueError as e:
        print(f'  [OK] ValueError: {e}')
        return True
    except Exception as e:
        print(f'  [FALHA] Erro inesperado: {type(e).__name__}: {e}')
        return False


def testar_grupo_inexistente():
    """Valida que buscar_grupo com grupo inválido levanta ValueError."""
    print('\n' + '=' * 70)
    print('TESTE 5: grupo inexistente')
    print('=' * 70)
    model = TelemetriaModel(Database())
    usina = next(iter(USINAS_CONFIG))

    try:
        model.buscar_grupo(usina, 'grupo_falso', DATA_INICIO, DATA_FIM)
        print('  [FALHA] Deveria ter levantado ValueError')
        return False
    except ValueError as e:
        print(f'  [OK] ValueError: {e}')
        return True
    except Exception as e:
        print(f'  [FALHA] Erro inesperado: {type(e).__name__}: {e}')
        return False


def _resumo(nome: str, erros: list[str]):
    print('-' * 70)
    if erros:
        print(f'{nome}: FALHA com {len(erros)} erro(s)')
        for e in erros:
            print(f'  - {e}')
    else:
        print(f'{nome}: OK')


if __name__ == '__main__':
    print('🔧 FASE 1: Teste do TelemetriaModel')
    print('=' * 70)

    # ok1 = testar_listar_grupos()
    # ok2 = testar_buscar_grupo()
    ok3 = testar_buscar_sensor()
    # ok4 = testar_variavel_inexistente()
    # ok5 = testar_grupo_inexistente()

    print('\n' + '=' * 70)
    # total_ok = sum([ok1, ok2, ok3, ok4, ok5])
    # print(f'RESULTADO FASE 1: {total_ok}/5 testes passaram')
    # if total_ok < 5:
    #     raise SystemExit(1)
    # print('✅ FASE 1 APROVADA')
