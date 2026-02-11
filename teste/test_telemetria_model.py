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
            dados = model.buscar_grupo(usina, grupo_teste, DATA_INICIO, DATA_FIM)
            linhas = len(dados)
            colunas = list(dados[0].keys()) if dados else []
            print(f'  [OK] {usina}/{grupo_teste} -> {linhas} registros, colunas={colunas[:3]}...')

            if dados and 'data_hora' not in dados[0]:
                erros.append(f'{usina}/{grupo_teste}: sem data_hora no retorno')

        except Exception as e:
            msg = f'{usina}/{grupo_teste}: {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    _resumo('buscar_grupo', erros)
    return not erros


def testar_buscar_sensor():
    """Consulta uma variável individual de cada usina."""
    print('\n' + '=' * 70)
    print('TESTE 3: buscar_sensor')
    print('=' * 70)
    db = Database()
    model = TelemetriaModel(db)
    erros = []

    for usina in USINAS_CONFIG:
        grupos = model.listar_grupos(usina)
        # Pega primeira variável do primeiro grupo
        primeiro_grupo = next(iter(grupos))
        variavel = grupos[primeiro_grupo][0]

        try:
            dados = model.buscar_sensor(usina, variavel, DATA_INICIO, DATA_FIM)
            linhas = len(dados)
            print(f'  [OK] {usina}/"{variavel}" -> {linhas} registros')

            if dados:
                chaves = list(dados[0].keys())
                if len(chaves) != 2:
                    erros.append(f'{usina}/"{variavel}": esperado 2 colunas (data_hora + valor), recebeu {len(chaves)}: {chaves}')

        except Exception as e:
            msg = f'{usina}/"{variavel}": {type(e).__name__}: {e}'
            print(f'  [ERRO] {msg}')
            erros.append(msg)

    _resumo('buscar_sensor', erros)
    return not erros


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

    ok1 = testar_listar_grupos()
    ok2 = testar_buscar_grupo()
    ok3 = testar_buscar_sensor()
    ok4 = testar_variavel_inexistente()
    ok5 = testar_grupo_inexistente()

    print('\n' + '=' * 70)
    total_ok = sum([ok1, ok2, ok3, ok4, ok5])
    print(f'RESULTADO FASE 1: {total_ok}/5 testes passaram')
    if total_ok < 5:
        raise SystemExit(1)
    print('✅ FASE 1 APROVADA')
