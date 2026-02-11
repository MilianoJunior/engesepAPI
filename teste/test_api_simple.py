"""
Teste simples da API ENGESEP
Testa os 3 endpoints reais: /producao-acumulada (POST), /usinas (GET), /health (GET)
"""
import requests
import json

#BASE_URL = "http://localhost:8000"
BASE_URL = "https://engesepapi-production.up.railway.app"
TOKEN_VALIDO = "123456"
TOKENS_INVALIDOS = ["engesep", "admin", "token", "test"]

# ======================== HELPERS ========================

def print_header(nome, url, metodo="POST"):
    print(f"\n📋 Testando: {nome}")
    print(f"🔗 {metodo} {url}")
    print("-" * 50)

def print_resultado(status, body, token=None):
    prefixo = f"🔑 Token: {token} | " if token else ""
    if status == 200:
        print(f"{prefixo}✅ {status}")
        print(f"📈 {json.dumps(body, indent=2, ensure_ascii=False)}")
    else:
        print(f"{prefixo}❌ {status} - {body}")

# ======================== TESTES ========================

def testar_producao_acumulada():
    """Testa POST /producao-acumulada com diferentes usinas e períodos"""
    url = f"{BASE_URL}/producao-acumulada"

    usinas = ["CGH-APARECIDA", "CGH-FAE", "PCH-PEDRAS", "CGH-PICADAS-ALTAS", "CGH-HOPPEN"]
    periodos = ["D", "M"]

    for usina in usinas:
        for periodo in periodos:
            print_header(f"Produção {usina} [{periodo}]", url)

            payload = {
                "usina": usina,
                "data_inicio": "01/01/2026 00:00",
                "data_fim": "31/01/2026 23:59",
                "periodo": periodo,
                "token": TOKEN_VALIDO
            }

            try:
                resp = requests.post(url, json=payload, timeout=30)
                print_resultado(resp.status_code, resp.json())
            except requests.exceptions.ConnectionError:
                print("❌ Servidor não está rodando")
                return False
            except Exception as e:
                print(f"❌ Erro: {e}")

    return True

def testar_token_invalido():
    """Testa POST /producao-acumulada com tokens inválidos"""
    url = f"{BASE_URL}/producao-acumulada"
    print_header("Tokens inválidos", url)

    payload = {
        "usina": "CGH-APARECIDA",
        "data_inicio": "01/01/2025 00:00",
        "data_fim": "31/01/2025 23:59",
        "periodo": "D",
    }

    for token in TOKENS_INVALIDOS:
        payload["token"] = token
        try:
            resp = requests.post(url, json=payload, timeout=10)
            print_resultado(resp.status_code, resp.json(), token)
        except Exception as e:
            print(f"🔑 Token: {token} | ❌ Erro: {e}")

def testar_validacao():
    """Testa validação de entrada: usina inválida e data sem hora"""
    url = f"{BASE_URL}/producao-acumulada"
    print_header("Validação de entrada", url)

    casos = [
        {"desc": "Usina inválida", "body": {"usina": "INVALIDA", "data_inicio": "01/01/2025 00:00", "data_fim": "31/01/2025 23:59", "periodo": "D", "token": TOKEN_VALIDO}},
        {"desc": "Data sem hora", "body": {"usina": "CGH-APARECIDA", "data_inicio": "01/01/2025", "data_fim": "31/01/2025", "periodo": "D", "token": TOKEN_VALIDO}},
    ]

    for caso in casos:
        try:
            resp = requests.post(url, json=caso["body"], timeout=10)
            esperado = resp.status_code == 422
            icone = "✅" if esperado else "⚠️"
            print(f"  {icone} {caso['desc']} → {resp.status_code} (esperado: 422)")
        except Exception as e:
            print(f"  ❌ {caso['desc']} → Erro: {e}")

def testar_usinas():
    """Testa GET /usinas"""
    url = f"{BASE_URL}/usinas"
    print_header("Listar Usinas", url, metodo="GET")

    try:
        resp = requests.get(url, timeout=10)
        print_resultado(resp.status_code, resp.json())
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando")
    except Exception as e:
        print(f"❌ Erro: {e}")

def testar_health():
    """Testa GET /health"""
    url = f"{BASE_URL}/health"
    print_header("Health Check", url, metodo="GET")

    try:
        resp = requests.get(url, timeout=10)
        print_resultado(resp.status_code, resp.json())
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando")
    except Exception as e:
        print(f"❌ Erro: {e}")

# ======================== MAIN ========================

if __name__ == "__main__":
    print("🚀 Testes da API ENGESEP")
    print("=" * 50)

    testar_health()
    testar_usinas()

    if testar_producao_acumulada():
        testar_token_invalido()
        testar_validacao()

    print("\n" + "=" * 50)
    print("🎯 Testes concluídos!")
