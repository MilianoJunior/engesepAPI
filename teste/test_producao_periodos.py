# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. _post           → faz POST na API e retorna JSON
# 2. _validar_resp   → valida estrutura da resposta
# 3. testar_periodo  → testa um período específico para uma usina
# 4. main            → roda todos os testes
# -------------------------------------------------------------------

import requests
import json
from datetime import datetime, timedelta

# ======================== CONFIGURAÇÃO ========================

BASE_URL = "http://localhost:8000"
TOKEN = None  # Preencher se necessário

DATA_FIM = datetime.now().strftime('%d/%m/%Y %H:%M')
DATA_INICIO_6M = (datetime.now() - timedelta(days=180)).strftime('%d/%m/%Y %H:%M')
DATA_INICIO_7D = (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y %H:%M')

USINAS_TESTE = ['PCH-PEDRAS', 'CGH-HOPPEN']

# ======================== FUNÇÕES ========================

def _post(rota: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}{rota}", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ❌ ERRO HTTP: {e}")
        return None


def _validar_resp(resp: dict, periodo: str) -> bool:
    if not resp:
        return False
    if 'resultado' not in resp:
        print(f"  ❌ Chave 'resultado' ausente na resposta")
        return False
    resultado = resp['resultado']
    if not isinstance(resultado, list):
        print(f"  ❌ 'resultado' não é lista: {type(resultado)}")
        return False
    if not resultado:
        print(f"  ⚠️  Lista vazia (pode ser normal se não há dados)")
        return True

    primeiro = resultado[0]
    if 'data' not in primeiro:
        print(f"  ❌ Campo 'data' ausente no primeiro item: {primeiro}")
        return False

    # Valida formato da data por período
    data_str = primeiro['data']
    if periodo == 'M' and len(data_str) != 7:
        print(f"  ❌ Período M: esperado 'YYYY-MM', recebido '{data_str}'")
        return False
    if periodo == 'D' and len(data_str) != 10:
        print(f"  ❌ Período D: esperado 'YYYY-MM-DD', recebido '{data_str}'")
        return False

    # Valida que há pelo menos uma coluna de produção
    colunas_prod = [k for k in primeiro if k.startswith('prod_')]
    if not colunas_prod:
        print(f"  ❌ Nenhuma coluna 'prod_*' no resultado: {list(primeiro.keys())}")
        return False

    return True


def testar_periodo(usina: str, periodo: str, data_inicio: str):
    print(f"\n  [{periodo}] usina={usina} | {data_inicio} → {DATA_FIM}")
    payload = {
        'usina': usina,
        'periodo': periodo,
        'data_inicio': data_inicio,
        'data_fim': DATA_FIM,
    }
    if TOKEN:
        payload['token'] = TOKEN

    inicio = datetime.now()
    resp = _post('/producao-acumulada', payload)
    elapsed = (datetime.now() - inicio).total_seconds()

    if not resp:
        return

    ok = _validar_resp(resp, periodo)
    n = len(resp.get('resultado', []))
    status = '✅' if ok else '❌'
    print(f"  {status} items={n} tempo={elapsed:.2f}s")

    if ok and resp.get('resultado'):
        primeiro = resp['resultado'][0]
        ultimo = resp['resultado'][-1]
        print(f"     primeiro: {primeiro}")
        print(f"     último:   {ultimo}")


def main():
    print("=" * 60)
    print("TESTE: /producao-acumulada — todos os períodos")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for usina in USINAS_TESTE:
        print(f"\n{'─' * 50}")
        print(f"USINA: {usina}")
        print(f"{'─' * 50}")

        # Mensal — usa cache lazy fill (só para M)
        testar_periodo(usina, 'M', DATA_INICIO_6M)

        # Diário — fluxo original, sem cache de banco
        testar_periodo(usina, 'D', DATA_INICIO_7D)

        # Horário — fluxo original, sem cache de banco
        testar_periodo(usina, 'H', DATA_INICIO_7D)

    print(f"\n{'=' * 60}")
    print("FIM DOS TESTES")
    print("=" * 60)


if __name__ == '__main__':
    main()
