'''
O teste deve cobrir todas as combinações possíveis de Usinas e Períodos.

Lista de Usinas: ["CGH-APARECIDA", "CGH-FAE", "PCH-PEDRAS", "CGH-PICADAS-ALTAS", "CGH-HOPPEN"]

Lista de Períodos: ["H", "D", "M"]

Datas Fixas: Inicio "2026-01-01 00:00", Fim "2026-02-09 16:31".
'''
"""
Teste da consulta de dados para a rota /producao-acumulada.

Valida, para todas as usinas e períodos (H/D/M):
- execução da consulta sem erro;
- presença de data_hora;
- colunas de energia no padrão "UG-XX Energia Acumulada".

Uso:
    source /home/jrmfilho23/projetos/amb/bin/activate && python -m teste.A_consulta_rota01
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.usina_model import UsinaModel, USINAS_CONFIG

PERIODOS = ('H', 'D', 'M')
PADRAO_COLUNA_UG = re.compile(r'^UG-\d{2} Energia Acumulada(?: \(\d+\))?$')
DATA_INICIO_FIXA = '2026-01-01 00:00:00'
DATA_FIM_FIXA = '2026-02-09 16:31:00'


def _quantidade_ugs_esperadas(usina: str) -> int:
    cfg = USINAS_CONFIG[usina]
    mapa_energia = cfg.get('energia', {})
    total = sum(len(colunas) for colunas in mapa_energia.values())
    return total


def _validar_dataframe(usina: str, periodo: str, df, qtd_ugs_esperadas: int) -> list[str]:
    erros = []
    if df.empty:
        erros.append(f'{usina} [{periodo}] DataFrame vazio')
        return erros

    if 'data_hora' not in df.columns:
        erros.append(f'{usina} [{periodo}] sem coluna data_hora')
        return erros

    colunas_energia = [c for c in df.columns if c != 'data_hora']
    if not colunas_energia:
        erros.append(f'{usina} [{periodo}] sem colunas de energia acumulada')
        return erros

    for coluna in colunas_energia:
        if not PADRAO_COLUNA_UG.match(coluna):
            erros.append(f'{usina} [{periodo}] coluna fora do padrao: {coluna}')

    for ug_num in range(1, qtd_ugs_esperadas + 1):
        coluna_ug = f'UG-{ug_num:02d} Energia Acumulada'
        if coluna_ug not in df.columns:
            erros.append(f'{usina} [{periodo}] coluna esperada ausente: {coluna_ug}')
            continue

        nao_nulos = int(df[coluna_ug].notna().sum())
        if nao_nulos == 0:
            erros.append(f'{usina} [{periodo}] coluna {coluna_ug} com 100% NaN')

    return erros


def executar_teste_consulta_producao():
    data_inicio, data_fim = DATA_INICIO_FIXA, DATA_FIM_FIXA
    db = Database()
    usina_model = UsinaModel(db)
    erros = []

    print('=' * 80)
    print('TESTE CONSULTA /producao-acumulada (dados de energia acumulada)')
    print(f'Intervalo: {data_inicio} -> {data_fim}')
    inicio_teste = time.time()
    print('=' * 80)

    for usina in USINAS_CONFIG.keys():
        inicio_usina = time.time()
        qtd_ugs_esperadas = _quantidade_ugs_esperadas(usina)
        for periodo in PERIODOS:
            try:
                df = usina_model.buscar_dados_usina(usina, data_inicio, data_fim, periodo)
                print(df.values[0])
                print(df.values[-1])
                linhas = len(df.index)
                colunas = list(df.columns)
                info_nao_nulos = {}
                for c in colunas:
                    if c != 'data_hora':
                        info_nao_nulos[c] = int(df[c].notna().sum())

                print(
                    f'[OK] {usina} [{periodo}] -> linhas={linhas} | colunas={colunas} '
                    f'| nao_nulos={info_nao_nulos}'
                )
                erros.extend(_validar_dataframe(usina, periodo, df, qtd_ugs_esperadas))
                fim_usina = time.time()
                tempo_usina = fim_usina - inicio_usina
                print(f'Tempo de execução da usina {usina} - {periodo}: {tempo_usina:.2f} segundos')
            except Exception as exc:
                msg = f'[ERRO] {usina} [{periodo}] -> {type(exc).__name__}: {exc}'
                print(msg)
                erros.append(msg)

    print('-' * 80)
    if erros:
        print(f'Teste concluido com {len(erros)} falha(s).')
        for erro in erros:
            print(f' - {erro}')
        raise SystemExit(1)

    print('Teste concluido sem falhas.')
    fim_teste = time.time()
    tempo_execucao = fim_teste - inicio_teste
    print(f'Tempo de execução: {tempo_execucao:.2f} segundos')


if __name__ == '__main__':
    executar_teste_consulta_producao()
