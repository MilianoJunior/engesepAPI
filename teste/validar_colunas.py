# -------------------------------------------------------------------
# TESTE: Validar colunas do banco vs config/usinas.json
# Executa SHOW COLUMNS em cada tabela e compara com os grupos do JSON.
# Uso: python -m teste.validar_colunas
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. _extrair_nome_coluna    → remove alias SQL ('col as label' → 'col')
# 2. validar_colunas_config  → SHOW COLUMNS vs JSON, imprime faltantes e extras
# -------------------------------------------------------------------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.usina_model import USINAS_CONFIG, GRUPOS_IGNORADOS


def _extrair_nome_coluna(col_sql: str) -> str:
    """Extrai nome real da coluna, removendo alias SQL ('col as label' → 'col')."""
    if ' as ' in col_sql.lower():
        return col_sql[:col_sql.lower().index(' as ')].strip()
    return col_sql.strip()


def validar_colunas_config(db: Database):
    """Compara colunas do banco (SHOW COLUMNS) com colunas distribuídas nos grupos do JSON."""
    config = USINAS_CONFIG
    tem_falha = False

    db.connect()
    try:
        for usina, cfg in config.items():
            tabelas = cfg['tabelas']
            grupos = [g for g in cfg if g not in GRUPOS_IGNORADOS]

            for tabela in tabelas:
                rows = db.fetch_data(f'SHOW COLUMNS FROM {tabela}')
                colunas_banco = {row['Field'] for row in rows}

                colunas_json = set()
                for grupo in grupos:
                    mapa = cfg[grupo]
                    if not isinstance(mapa, dict):
                        continue
                    for col in mapa.get(tabela, []):
                        colunas_json.add(_extrair_nome_coluna(col))

                for col in cfg.get('identificacao', {}).get(tabela, []):
                    colunas_json.add(col)

                no_banco_sem_grupo = colunas_banco - colunas_json
                no_json_sem_banco = colunas_json - colunas_banco

                if no_banco_sem_grupo or no_json_sem_banco:
                    tem_falha = True
                    print(f'\n⚠ {usina} → {tabela}')
                    if no_banco_sem_grupo:
                        print(f'  NO BANCO mas SEM GRUPO no JSON:')
                        for col in sorted(no_banco_sem_grupo):
                            print(f'    - {col}')
                    if no_json_sem_banco:
                        print(f'  NO JSON mas NÃO EXISTE no banco:')
                        for col in sorted(no_json_sem_banco):
                            print(f'    - {col}')

        if not tem_falha:
            print('\n✔ Todas as colunas do banco estão mapeadas nos grupos do JSON.')
    finally:
        db.close()


if __name__ == '__main__':
    db = Database()
    validar_colunas_config(db)
