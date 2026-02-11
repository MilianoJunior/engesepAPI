"""
Validador completo da rota /producao-acumulada usando dados de referencia em teste/dados.py.

Cobertura:
- Todas as usinas com casos definidos em dados.py
- Todos os periodos definidos por usina (H/D/M)
"""

import calendar
import time
from datetime import datetime
import requests
from fastapi import HTTPException

from teste import dados as dados_ref
from libs.usina_model import USINAS_CONFIG
from main import ProducaoRequest, producao_acumulada

BASE_URL = "http://localhost:8000"
TOKEN_VALIDO = "123456"
TOLERANCIA = 0.06


def _parse_datetime_flex(valor: str) -> datetime:
    formatos = (
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )
    for fmt in formatos:
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de data/hora nao suportado: {valor}")


def _to_api_datetime(valor: str, fim: bool = False) -> str:
    valor = str(valor).strip()
    if len(valor) == 7 and valor[4] == "-":
        ano = int(valor[0:4])
        mes = int(valor[5:7])
        if fim:
            dia = calendar.monthrange(ano, mes)[1]
            dt = datetime(ano, mes, dia, 23, 59)
        else:
            dt = datetime(ano, mes, 1, 0, 0)
    else:
        dt = _parse_datetime_flex(valor)
    return dt.strftime("%d/%m/%Y %H:%M")


def _normalizar_data_esperada(valor: str, periodo: str) -> str:
    if periodo == "M":
        return str(valor).strip()[:7]

    dt = _parse_datetime_flex(str(valor).strip())
    if periodo == "D":
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:00")


def _normalizar_data_recebida(valor: str, periodo: str) -> str:
    valor = str(valor).strip()
    if periodo == "M":
        return valor[:7]

    if "T" in valor:
        dt = datetime.fromisoformat(valor)
    else:
        dt = _parse_datetime_flex(valor)

    if periodo == "D":
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:00")


def _extrair_ugs_esperadas(item: dict) -> dict[str, float]:
    saida = {}
    for k, v in item.items():
        if not k.endswith("(MWh)"):
            continue
        ug = k.replace(" (MWh)", "").strip()
        saida[ug] = round(float(v), 3)
    return saida


def _extrair_esperado(caso: dict) -> dict[str, dict[str, float]]:
    periodo = str(caso.get("periodo", "D")).upper()[0]
    serie = {}
    for item in caso.get("dados", []):
        chave = _normalizar_data_esperada(item.get("data_hora", ""), periodo)
        if chave:
            serie[chave] = _extrair_ugs_esperadas(item)
    return serie


def _extrair_recebido(body: dict, periodo: str) -> dict[str, dict[str, float]]:
    serie = {}
    for item in body.get("resultado", []):
        data = item.get("data")
        if not data:
            continue
        chave = _normalizar_data_recebida(data, periodo)
        ugs = {}
        for k, v in item.items():
            if not k.startswith("prod_"):
                continue
            nome = k.replace("prod_", "").replace(" Energia Acumulada", "").strip()
            ugs[nome] = round(float(v), 3)
        serie[chave] = ugs
    return serie


def _cases_dados() -> list[dict]:
    todos = []
    for conjunto in (
        dados_ref.aparecida,
        dados_ref.FAE,
        dados_ref.pedras,
        dados_ref.picadas_altas,
        dados_ref.hoppen,
    ):
        todos.extend(conjunto)
    return todos


def _payload(caso: dict) -> dict:
    periodo = str(caso.get("periodo", "D")).upper()[0]
    return {
        "usina": str(caso["usina"]).upper(),
        "data_inicio": _to_api_datetime(caso["data_inicio"], fim=False),
        "data_fim": _to_api_datetime(caso["data_final"], fim=True),
        "periodo": periodo,
        "token": TOKEN_VALIDO,
    }


def _detectar_modo_execucao() -> str:
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        if resp.status_code < 500:
            return "http"
    except Exception:
        pass
    return "local"


def _post_producao(payload: dict, modo: str):
    if modo == "http":
        resp = requests.post(f"{BASE_URL}/producao-acumulada", json=payload, timeout=180)
        return resp.status_code, resp.text, resp.json() if resp.status_code == 200 else None

    try:
        req = ProducaoRequest(**payload)
        body = producao_acumulada(req)
        return 200, str(body), body
    except HTTPException as exc:
        body_txt = str(exc.detail) if exc.detail else str(exc)
        return int(exc.status_code), body_txt, None
    except Exception as exc:
        return 500, str(exc), None


def _soma_ugs(ugs: dict[str, float]) -> float:
    return round(sum(float(v) for v in ugs.values()), 3)


def _imprimir_tabela(
    usina: str,
    periodo: str,
    esperado: dict[str, dict[str, float]],
    recebido: dict[str, dict[str, float]],
) -> list[str]:
    erros = []
    datas = sorted(set(esperado) | set(recebido))
    ugs = sorted({ug for m in esperado.values() for ug in m} | {ug for m in recebido.values() for ug in m})

    col_data = 20
    col_num = 11
    col_delta = 10
    col_status = 10
    largura = col_data + (len(ugs) * col_num * 2) + col_delta + col_status + 3
    print("-" * largura)
    header = f"{'Data':<{col_data}}"
    header += "".join(f"{(ug + ' Rec.'):>{col_num}}" for ug in ugs)
    header += "".join(f"{(ug + ' Esp.'):>{col_num}}" for ug in ugs)
    header += f"{'Delta':>{col_delta}}{'Status':>{col_status}}"
    print(header)
    print("-" * largura)
    for data in datas:
        esp = esperado.get(data)
        rec = recebido.get(data)
        esp_map = esp if esp is not None else {}
        rec_map = rec if rec is not None else {}

        if esp is None:
            status = "EXTRA"
            delta = _soma_ugs(rec_map)
            erros.append(f"{usina}[{periodo}] data extra: {data} -> {delta:.3f}")
        elif rec is None:
            status = "AUSENTE"
            delta = round(-_soma_ugs(esp_map), 3)
            erros.append(f"{usina}[{periodo}] data ausente: {data} (esp {_soma_ugs(esp_map):.3f})")
        else:
            delta = round(_soma_ugs(rec_map) - _soma_ugs(esp_map), 3)
            divergencia_ug = False
            for ug in ugs:
                diff_ug = round(float(rec_map.get(ug, 0.0)) - float(esp_map.get(ug, 0.0)), 3)
                if abs(diff_ug) > TOLERANCIA:
                    divergencia_ug = True
                    break
            ok = (abs(delta) <= TOLERANCIA) and (not divergencia_ug)
            status = "OK" if ok else "DIVERGE"
            if not ok:
                erros.append(
                    f"{usina}[{periodo}] {data}: esp_total={_soma_ugs(esp_map):.3f} "
                    f"rec_total={_soma_ugs(rec_map):.3f} diff={delta:.3f}"
                )

        linha = f"{data:<{col_data}}"
        linha += "".join(f"{float(rec_map.get(ug, 0.0)):>{col_num}.3f}" for ug in ugs)
        linha += "".join(f"{float(esp_map.get(ug, 0.0)):>{col_num}.3f}" for ug in ugs)
        linha += f"{delta:>{col_delta}.3f}{status:>{col_status}}"
        print(linha)
    return erros


def executar_validacao():
    inicio = time.time()
    casos = _cases_dados()
    if not casos:
        raise SystemExit("Nenhum caso encontrado em teste/dados.py")

    periodos_por_usina_esperados = {u: {"H", "D", "M"} for u in USINAS_CONFIG.keys()}
    periodos_por_usina_dados = {u: set() for u in USINAS_CONFIG.keys()}
    erros = []

    print("=" * 95)
    print("VALIDACAO DE RESULTADOS /producao-acumulada COM BASE EM teste/dados.py")
    print("=" * 95)
    modo = _detectar_modo_execucao()
    print(f"Modo de execucao: {'API HTTP (localhost:8000)' if modo == 'http' else 'Rota local (main.producao_acumulada)'}")

    for i, caso in enumerate(casos, start=1):
        periodo = str(caso.get("periodo", "D")).upper()[0]
        usina = str(caso.get("usina", "")).upper()
        if usina in periodos_por_usina_dados:
            periodos_por_usina_dados[usina].add(periodo)

        payload = _payload(caso)
        print(f"\n[CASO {i}] {usina} [{periodo}]")
        print(f"Intervalo API: {payload['data_inicio']} -> {payload['data_fim']}")

        try:
            status, body_txt, body_json = _post_producao(payload, modo)
        except Exception as exc:
            erros.append(f"{usina}[{periodo}] erro de requisicao: {exc}")
            print(f"Erro de requisicao: {exc}")
            continue

        if status != 200:
            erros.append(f"{usina}[{periodo}] status={status} body={body_txt}")
            print(f"Erro HTTP: {status}")
            continue

        esperado = _extrair_esperado(caso)
        recebido = _extrair_recebido(body_json, periodo)
        erros_caso = _imprimir_tabela(usina, periodo, esperado, recebido)
        erros.extend(erros_caso)

        soma_esp = round(sum(_soma_ugs(v) for v in esperado.values()), 3)
        soma_rec = round(sum(_soma_ugs(v) for v in recebido.values()), 3)
        print("-" * 95)
        print(
            f"Resumo -> itens_esp={len(esperado)} itens_rec={len(recebido)} "
            f"soma_esp={soma_esp:.3f} soma_rec={soma_rec:.3f} delta={soma_rec-soma_esp:.3f}"
        )
        print(f"Status do caso: {'OK' if not erros_caso else 'COM DIVERGENCIAS'}")

    faltas = []
    for usina, periodos_observados in periodos_por_usina_dados.items():
        faltando = sorted(periodos_por_usina_esperados[usina] - periodos_observados)
        if faltando:
            faltas.append(f"{usina}: faltam casos em dados.py para periodo(s) {', '.join(faltando)}")

    print("\n" + "=" * 95)
    print("RESUMO FINAL")
    print("=" * 95)
    if faltas:
        print("Cobertura de casos em teste/dados.py:")
        for f in faltas:
            print(f" - {f}")
    else:
        print("Cobertura completa de H/D/M para todas as usinas.")

    if erros:
        print(f"\nResultado: FALHA com {len(erros)} divergencia(s).")
        for e in erros[:60]:
            print(f" - {e}")
        if len(erros) > 60:
            print(f" - ... ({len(erros)-60} divergencias adicionais omitidas)")
        print(f"Tempo total: {time.time()-inicio:.2f}s")
        raise SystemExit(1)

    print("\nResultado: SUCESSO sem divergencias.")
    print(f"Tempo total: {time.time()-inicio:.2f}s")


if __name__ == "__main__":
    executar_validacao()
