# -------------------------------------------------------------------
# TESTE FASE 3: Validar rotas da API (FastAPI)
# Uso: python -m teste.test_api_fase3
# Pré-requisito: uvicorn rodando em localhost:8000
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. testar_health             → GET /health
# 2. testar_usinas             → GET /usinas
# 3. testar_grupos             → GET /grupos/{usina}
# 4. testar_sensor_usina       → POST /sensor-usina
# 5. testar_grupo_usina        → POST /grupo-usina
# 6. testar_tabela_usina       → POST /tabela-usina
# 7. testar_producao_acumulada → POST /producao-acumulada
# 8. testar_validacoes         → erros esperados (usina inválida, data inválida)
# -------------------------------------------------------------------

import sys
import os
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ======================== CONFIGURAÇÃO ========================

BASE_URL = os.getenv('API_URL', 'http://localhost:8000')
TOKEN = os.getenv('API_TOKEN', '123456')

# Payload padrão (1 dia → 15min resolução automática)
PAYLOAD_BASE = {
    'data_inicio': '15/01/2026 00:00',
    'data_fim': '16/01/2026 00:00',
    'token': TOKEN,
}


# ======================== HELPERS ========================

def _post(rota: str, payload: dict) -> requests.Response:
    return requests.post(f'{BASE_URL}{rota}', json=payload, timeout=60)


def _get(rota: str) -> requests.Response:
    return requests.get(f'{BASE_URL}{rota}', timeout=30)


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

def testar_health():
    print('=' * 70)
    print('TESTE F3-1: GET /health')
    print('=' * 70)
    erros = []

    r = _get('/health')
    print(f'  Status: {r.status_code}')

    if r.status_code != 200:
        erros.append(f'Status {r.status_code}')
    else:
        data = r.json()
        print(f'  Response: {data}')
        if data.get('status') != 'operacional':
            erros.append(f'Status inesperado: {data}')

    _resumo('health', erros)
    return not erros


def testar_usinas():
    print('=' * 70)
    print('TESTE F3-2: GET /usinas')
    print('=' * 70)
    erros = []

    r = _get('/usinas')
    print(f'  Status: {r.status_code}')

    if r.status_code != 200:
        erros.append(f'Status {r.status_code}')
    else:
        data = r.json()
        usinas = data.get('usinas_disponiveis', [])
        print(f'  Usinas: {len(usinas)}')
        if len(usinas) == 0:
            erros.append('Nenhuma usina retornada')

    _resumo('usinas', erros)
    return not erros


def testar_grupos():
    print('=' * 70)
    print('TESTE F3-3: GET /grupos/{usina}')
    print('=' * 70)
    erros = []

    for usina in ['CGH-APARECIDA', 'CGH-FAE', 'PCH-PEDRAS']:
        r = _get(f'/grupos/{usina}')
        if r.status_code != 200:
            erros.append(f'{usina}: status {r.status_code}')
            continue

        data = r.json()
        n_grupos = len(data)
        print(f'  [OK] {usina}: {n_grupos} grupos')

    # Usina inválida
    r = _get('/grupos/USINA-FAKE')
    if r.status_code != 404:
        erros.append(f'Usina inexistente deveria retornar 404, retornou {r.status_code}')
    else:
        print(f'  [OK] USINA-FAKE: 404 (esperado)')

    _resumo('grupos', erros)
    return not erros


def testar_sensor_usina():
    print('=' * 70)
    print('TESTE F3-4: POST /sensor-usina')
    print('=' * 70)
    erros = []

    casos = [
        ('CGH-APARECIDA', 'UG-01 Potência Ativa'),
        ('CGH-APARECIDA', 'UG-01 Temp. Óleo UHLM'),
        ('CGH-FAE', 'UG-01 Potência Ativa'),
        ('PCH-PEDRAS', 'UG-02 Temp. Óleo UHLM'),
    ]

    for usina, variavel in casos:
        payload = {**PAYLOAD_BASE, 'usina': usina, 'variavel': variavel}
        r = _post('/sensor-usina', payload)

        if r.status_code != 200:
            erros.append(f'{usina}/{variavel}: status {r.status_code} - {r.text[:100]}')
            print(f'  [ERRO] {usina}/{variavel}: {r.status_code}')
            continue

        data = r.json()
        registros = data.get('registros', 0)
        n_dados = len(data.get('dados', []))
        print(f'  [OK] {usina} | "{variavel}" → {registros} registros, {n_dados} dados')

        if registros != n_dados:
            erros.append(f'{usina}/{variavel}: registros={registros} != len(dados)={n_dados}')

    # Variável inválida
    payload = {**PAYLOAD_BASE, 'usina': 'CGH-APARECIDA', 'variavel': 'SENSOR-FAKE'}
    r = _post('/sensor-usina', payload)
    if r.status_code != 400:
        erros.append(f'Variável inexistente deveria retornar 400, retornou {r.status_code}')
    else:
        print(f'  [OK] SENSOR-FAKE: 400 (esperado)')

    _resumo('sensor_usina', erros)
    return not erros


def testar_grupo_usina():
    print('=' * 70)
    print('TESTE F3-5: POST /grupo-usina')
    print('=' * 70)
    erros = []

    casos = [
        ('CGH-APARECIDA', 'potencia'),
        ('CGH-FAE', 'temperaturas'),
        ('PCH-PEDRAS', 'potencia'),
    ]

    for usina, grupo in casos:
        payload = {**PAYLOAD_BASE, 'usina': usina, 'grupo': grupo}
        r = _post('/grupo-usina', payload)

        if r.status_code != 200:
            erros.append(f'{usina}/{grupo}: status {r.status_code} - {r.text[:100]}')
            print(f'  [ERRO] {usina}/{grupo}: {r.status_code}')
            continue

        data = r.json()
        registros = data.get('registros', 0)
        n_dados = len(data.get('dados', []))
        print(f'  [OK] {usina} | "{grupo}" → {registros} registros, {n_dados} dados')

    # Grupo inválido
    payload = {**PAYLOAD_BASE, 'usina': 'CGH-APARECIDA', 'grupo': 'GRUPO-FAKE'}
    r = _post('/grupo-usina', payload)
    if r.status_code != 400:
        erros.append(f'Grupo inexistente deveria retornar 400, retornou {r.status_code}')
    else:
        print(f'  [OK] GRUPO-FAKE: 400 (esperado)')

    _resumo('grupo_usina', erros)
    return not erros


def testar_tabela_usina():
    print('=' * 70)
    print('TESTE F3-6: POST /tabela-usina')
    print('=' * 70)
    erros = []

    # Janela curta (1h) pra não estourar memória
    payload = {
        **PAYLOAD_BASE,
        'usina': 'CGH-APARECIDA',
        'data_inicio': '15/01/2026 08:00',
        'data_fim': '15/01/2026 09:00',
    }
    r = _post('/tabela-usina', payload)

    if r.status_code != 200:
        erros.append(f'Status {r.status_code} - {r.text[:100]}')
        print(f'  [ERRO] {r.status_code}')
    else:
        data = r.json()
        registros = data.get('registros', 0)
        tabelas = data.get('tabelas', [])
        n_colunas = len(data['dados'][0]) if data.get('dados') else 0
        print(f'  [OK] CGH-APARECIDA → {registros} registros, tabelas={tabelas}, colunas={n_colunas}')

        if registros == 0:
            erros.append('Nenhum registro retornado')

    _resumo('tabela_usina', erros)
    return not erros


def testar_producao_acumulada():
    print('=' * 70)
    print('TESTE F3-7: POST /producao-acumulada')
    print('=' * 70)
    erros = []

    payload = {**PAYLOAD_BASE, 'usina': 'CGH-APARECIDA', 'periodo': 'H'}
    r = _post('/producao-acumulada', payload)

    if r.status_code != 200:
        erros.append(f'Status {r.status_code} - {r.text[:100]}')
        print(f'  [ERRO] {r.status_code}')
    else:
        data = r.json()
        resultado = data.get('resultado', [])
        print(f'  [OK] CGH-APARECIDA (Horário) → {len(resultado)} registros')

    _resumo('producao_acumulada', erros)
    return not erros


def testar_validacoes():
    print('=' * 70)
    print('TESTE F3-8: Validações de entrada')
    print('=' * 70)
    erros = []

    # Usina inválida
    payload = {**PAYLOAD_BASE, 'usina': 'USINA-FAKE', 'variavel': 'x'}
    r = _post('/sensor-usina', payload)
    if r.status_code != 422:
        erros.append(f'Usina inválida: esperado 422, recebeu {r.status_code}')
    else:
        print(f'  [OK] Usina inválida → 422')

    # Data inválida
    payload = {**PAYLOAD_BASE, 'usina': 'CGH-APARECIDA', 'variavel': 'UG-01 Potência Ativa',
               'data_inicio': 'data-ruim'}
    r = _post('/sensor-usina', payload)
    if r.status_code != 422:
        erros.append(f'Data inválida: esperado 422, recebeu {r.status_code}')
    else:
        print(f'  [OK] Data inválida → 422')

    # Token errado
    payload = {**PAYLOAD_BASE, 'usina': 'CGH-APARECIDA', 'variavel': 'UG-01 Potência Ativa',
               'token': 'token-errado'}
    r = _post('/sensor-usina', payload)
    if r.status_code != 401:
        erros.append(f'Token errado: esperado 401, recebeu {r.status_code}')
    else:
        print(f'  [OK] Token errado → 401')

    _resumo('validacoes', erros)
    return not erros


# ======================== EXECUÇÃO ========================

if __name__ == '__main__':
    print('🔧 FASE 3: Teste das rotas da API')
    print(f'📡 Base URL: {BASE_URL}')
    print('=' * 70)
    print()

    resultados = [
        ('F3-1 health', testar_health()),
        ('F3-2 usinas', testar_usinas()),
        ('F3-3 grupos', testar_grupos()),
        ('F3-4 sensor_usina', testar_sensor_usina()),
        ('F3-5 grupo_usina', testar_grupo_usina()),
        ('F3-6 tabela_usina', testar_tabela_usina()),
        ('F3-7 producao_acumulada', testar_producao_acumulada()),
        ('F3-8 validacoes', testar_validacoes()),
    ]

    print('\n' + '=' * 70)
    print('RESULTADO FINAL FASE 3')
    print('=' * 70)
    for nome, ok in resultados:
        print(f'  {"✓" if ok else "✗"} {nome}')

    total_ok = sum(1 for _, ok in resultados if ok)
    print(f'\n{total_ok}/{len(resultados)} testes passaram.')
