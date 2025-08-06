"""
Teste simples da API ENGESEP
Autor: Miliano Fernandes de Oliveira
Data de criação: 2024-12-19
"""
import requests
import json
import time
import os
from multiprocessing import Process
import uvicorn

def run_server():
    """Inicia o servidor FastAPI"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")

def test_api():
    """Testa a API com diferentes endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Lista de tokens para testar
    tokens = ["123456", "engesep", "admin", "token", "test"]
    
    # Endpoints para testar
    endpoints = [
        {
            "name": "Produção Acumulada",
            "url": "/data/producao_acumulada",
            "body": {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": "day",
                "data_inicio": "01/06/2025",
                "data_fim": "14/06/2025",
                "token": "123456"
            }
        },
        {
            "name": "Produção Acumulada",
            "url": "/data/producao_acumulada",
            "body": {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": "month",
                "data_inicio": "01/06/2025",
                "data_fim": "14/06/2025",
                "token": "123456"
            }
        },
        {
            "name": "Produção Acumulada",
            "url": "/data/producao_acumulada",
            "body": {
                "usina": "cgh_aparecida",
                "coluna": ["acumulador_energia"],
                "periodo": "hour",
                "data_inicio": "01/06/2025",
                "data_fim": "14/06/2025",
                "token": "123456"
            }
        },
        {
            "name": "Colunas",
            "url": "/columns",
            "body": {
                "usina": "cgh_aparecida",
                "token": "123456"
            }
        },
        {
            "name": "Produção Total",
            "url": "/data/producao_total",
            "body": {
                "usina": "cgh_aparecida",
                "token": "123456"
            }
        }
    ]
    
    print("🚀 Iniciando testes da API ENGESEP")
    print("=" * 60)
    
    # Testar cada endpoint
    for endpoint in endpoints:
        print(f"\n📋 Testando: {endpoint['name']}")
        print(f"🔗 URL: {base_url}{endpoint['url']}")
        print("-" * 40)
        
        # Testar com diferentes tokens
        for token in tokens:
            # Atualizar o token no body
            test_body = endpoint['body'].copy()
            test_body['token'] = token
            
            try:
                response = requests.post(
                    f"{base_url}{endpoint['url']}", 
                    json=test_body,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f"🔑 Token: {token}")
                print(f"📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Sucesso!")
                    data = response.json()
                    if isinstance(data, list):
                        print(f"📈 Dados retornados: {len(data)} registros")
                    elif isinstance(data, dict):
                        if 'df' in data:
                            if isinstance(data['df'], list):
                                print(f"📈 Dados retornados: {len(data['df'])} registros")
                            elif isinstance(data['df'], dict):
                                print(f"📈 Dados retornados: {len(data['df'])} chaves")

                            print(f"📈 Resposta: {data}")
                        else:
                            print(f"📈 Resposta: {data}")
                    break  # Se encontrou um token válido, para de testar
                    
                elif response.status_code == 401:
                    print("❌ Token inválido")
                elif response.status_code == 404:
                    print("❌ Endpoint não encontrado")
                else:
                    print(f"❌ Erro: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Erro de conexão - Servidor não está rodando")
                return
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        print("-" * 40)
    
    print("\n🎯 Testes concluídos!")

if __name__ == "__main__":
    print("🔧 Iniciando servidor...")
    
    # Iniciar servidor em processo separado
    server_process = Process(target=run_server)
    server_process.start()
    
    # Aguardar servidor inicializar
    time.sleep(3)
    
    try:
        # Executar testes
        test_api()
    finally:
        # Parar servidor
        server_process.terminate()
        server_process.join()
        print("�� Servidor parado.") 