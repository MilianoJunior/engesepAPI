# -------------------------------------------------------------------
# TESTE: Consulta último registro de cada grupo/tabela
# Valida que todas as colunas do JSON retornam dados do banco.
# Uso: python -m teste.testar_grupos
# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. testar_configuracao → consulta último registro de cada grupo/tabela no banco
# -------------------------------------------------------------------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database
from libs.usina_model import USINAS_CONFIG, GRUPOS_IGNORADOS


def testar_configuracao(db: Database):
    """Consulta o último registro de cada grupo/tabela e imprime o resultado."""
    config = USINAS_CONFIG
    db.connect()
    try:
        for usina, cfg in config.items():
            print(f'\n{"=" * 60}')
            print(f'USINA: {usina} — {cfg.get("descricao", "")}')
            print(f'{"=" * 60}')

            tabelas = cfg['tabelas']
            grupos = [g for g in cfg if g not in GRUPOS_IGNORADOS]

            for grupo in grupos:
                mapa = cfg[grupo]
                if not isinstance(mapa, dict):
                    continue

                for tabela in tabelas:
                    colunas = mapa.get(tabela)
                    if not colunas:
                        continue

                    col_str = ', '.join(colunas)
                    query = (
                        f'SELECT data_hora, {col_str} FROM {tabela} '
                        f'ORDER BY data_hora DESC LIMIT 1'
                    )

                    try:
                        df = db.fetch_dataframe(query)
                        if df.empty:
                            print(f'  [{grupo}] {tabela}: SEM DADOS')
                        else:
                            data_hora = df['data_hora'].iloc[0]
                            valores = df.drop(columns=['data_hora']).iloc[0].to_dict()
                            print(f'  [{grupo}] {tabela} | último: {data_hora}')
                            for col, val in valores.items():
                                print(f'    {col}: {val}')
                    except Exception as e:
                        print(f'  [{grupo}] {tabela}: ERRO — {e}')

            print()
    finally:
        db.close()


if __name__ == '__main__':
    db = Database()
    testar_configuracao(db)
