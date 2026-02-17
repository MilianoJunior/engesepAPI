# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. buscar_todos_dados  → SELECT * na tabela cgh_aparecida via Database
# 2. salvar_csv           → salva DataFrame em CSV com timestamp no nome
# 3. main                 → orquestra busca e salvamento
# -------------------------------------------------------------------

import os
import sys
from datetime import datetime

# Ajusta path para importar libs do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.db import Database

# -------------------------------------------------------------------
# CONFIGURAÇÕES
# -------------------------------------------------------------------
TABELA = 'cgh_aparecida'
USINA = 'CGH-APARECIDA'
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------------------------
# FUNÇÕES
# -------------------------------------------------------------------
def buscar_todos_dados(db: Database) -> 'pd.DataFrame':
    """SELECT * na tabela cgh_aparecida, ordenado por data_hora."""
    db.connect()
    query = f'SELECT * FROM {TABELA} ORDER BY data_hora'
    return db.fetch_dataframe(query)


def salvar_csv(df: 'pd.DataFrame', diretorio: str) -> str:
    """Salva DataFrame em CSV. Retorna caminho do arquivo gerado."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f'{USINA}_{timestamp}.csv'
    caminho = os.path.join(diretorio, nome_arquivo)
    df.to_csv(caminho, index=False, encoding='utf-8-sig', sep=';')
    return caminho


# -------------------------------------------------------------------
# EXECUÇÃO
# -------------------------------------------------------------------
if __name__ == '__main__':
    db = Database()
    try:
        print(f'Buscando todos os dados de {USINA} ({TABELA})...')
        df = buscar_todos_dados(db)

        if df.empty:
            print('Nenhum dado encontrado.')
            sys.exit(0)

        print(f'Registros: {len(df)} | Colunas: {list(df.columns)}')
        caminho = salvar_csv(df, OUTPUT_DIR)
        print(f'CSV salvo: {caminho}')
    except Exception as e:
        print(f'Erro: {e}')
        sys.exit(1)
    finally:
        db.close()
