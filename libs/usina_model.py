# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. carregar_config              → lê config/usinas.json e retorna dict
# 2. __init__                     → recebe config de usinas e instância de Database
# 3. buscar_dados_usina           → monta queries, busca no banco, merge multi-tabela
# 4. buscar_por_grupo             → consulta colunas de um grupo específico
# 5. _extrair_info_temporal       → detecta coluna temporal real via config identificacao
# 6. _montar_query                → gera SQL conforme período e coluna temporal da usina
# 7. _tratar_dataframe            → cast tipos, remove negativos e sentinela 103.00
# 8. _normalizar_colunas_energia  → normaliza nomes para UG-XX Energia Acumulada
# 9. _merge_dataframes            → merge outer de múltiplos DataFrames por data_hora
# -------------------------------------------------------------------

import json
import os
import re
import time
import pandas as pd
from libs.db import Database
from libs.cache_store import CacheStore

# ======================== CONFIGURAÇÃO ========================

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'usinas.json')

GRUPOS_IGNORADOS = {'descricao', 'tabelas', 'identificacao', '_obs'}


def carregar_config(path: str = CONFIG_PATH) -> dict:
    """Lê config/usinas.json e retorna dict."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


USINAS_CONFIG = carregar_config()

# ======================== MODEL ========================

class UsinaModel:
    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or USINAS_CONFIG
        self.cache_enabled = os.getenv('USINA_CACHE_ENABLED', '1').strip().lower() in {'1', 'true', 'yes', 'on'}
        self.cache_ttl_seconds = int(os.getenv('USINA_CACHE_TTL_SECONDS', '60'))
        self.connection_idle_ttl_seconds = int(os.getenv('USINA_CONN_IDLE_TTL_SECONDS', '180'))
        self.raw_df_debug = os.getenv('USINA_RAW_DF_DEBUG', '0').strip().lower() in {'1', 'true', 'yes', 'on'}
        self.raw_df_debug_print_query = os.getenv('USINA_RAW_DF_DEBUG_QUERY', '0').strip().lower() in {'1', 'true', 'yes', 'on'}
        self.raw_df_debug_rows = int(os.getenv('USINA_RAW_DF_DEBUG_ROWS', '3'))
        meses_debug_raw = os.getenv('USINA_RAW_DF_DEBUG_MESES', '').strip()
        self.raw_df_debug_meses = {m.strip() for m in meses_debug_raw.split(',') if m.strip()}
        self._connection_last_used_at = None

    def buscar_dados_usina(self, usina: str, data_inicio: str, data_fim: str, periodo: str = 'D') -> pd.DataFrame:
        """
        Busca apenas dados de Energia Acumulada para uso na rota /producao-acumulada.
        Retorna DataFrame com coluna data_hora e colunas normalizadas:
        - UG-01 Energia Acumulada
        - UG-02 Energia Acumulada
        """
        cfg = self.config[usina]
        mapa_energia = cfg['energia']
        periodo = (periodo or 'D').upper()[0]
        query_periodo = self._resolver_periodo_base(periodo)
        if self.raw_df_debug:
            print(
                f"[RAW-DEBUG] usina={usina} periodo_solicitado={periodo} "
                f"periodo_query={query_periodo} "
                f"obs={'consulta_mensal_sql_ativa' if query_periodo == 'M' else 'consulta_sql_nao_agregada'}"
            )
        cache_key = self._cache_key_dados_usina_base(usina, data_inicio, data_fim, query_periodo)

        def _buscar():
            dfs = self._coletar_dataframes(
                usina=usina,
                tabelas=cfg['tabelas'],
                mapa_colunas=mapa_energia,
                data_inicio=data_inicio,
                data_fim=data_fim,
                periodo=query_periodo,
                preparar_energia=True,
            )
            return self._merge_dataframes(dfs)

        if self.cache_enabled:
            resultado = CacheStore.get_or_set(cache_key, _buscar, ttl_seconds=self.cache_ttl_seconds)
            return resultado.copy(deep=False) if resultado is not None else pd.DataFrame()

        return _buscar()

    def buscar_por_grupo(self, usina: str, grupo: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Consulta colunas de um grupo específico (energia, temperaturas, etc.)."""
        cfg = self.config[usina]
        tabelas = cfg['tabelas']
        mapa = cfg.get(grupo, {})
        if not isinstance(mapa, dict):
            return pd.DataFrame()

        dfs = self._coletar_dataframes(
            usina=usina,
            tabelas=tabelas,
            mapa_colunas=mapa,
            data_inicio=data_inicio,
            data_fim=data_fim,
            periodo='H',
            preparar_energia=False,
        )
        return self._merge_dataframes(dfs)

    def _coletar_dataframes(
        self,
        usina: str,
        tabelas: list[str],
        mapa_colunas: dict,
        data_inicio: str,
        data_fim: str,
        periodo: str,
        preparar_energia: bool,
    ) -> list[pd.DataFrame]:
        """
        Coleta DataFrames de um mapa de colunas por tabela.
        Suporta:
        - usina com 1 tabela e múltiplas UGs (múltiplas colunas na mesma query)
        - usina com múltiplas tabelas e 1 UG por tabela (merge posterior por data_hora)
        """
        dfs = []
        self._garantir_conexao()
        for tabela in tabelas:
            colunas = mapa_colunas.get(tabela, [])
            if not colunas:
                continue

            info_temporal = self._extrair_info_temporal(usina, tabela)
            query = self._montar_query(tabela, colunas, data_inicio, data_fim, periodo, info_temporal)
            df_temp = self.db.fetch_dataframe(query)
            self._touch_connection()
            self._log_raw_dataframe(usina, tabela, periodo, colunas, query, df_temp)

            if df_temp.empty:
                continue

            if preparar_energia:
                df_temp = self._tratar_dataframe(df_temp)
                if df_temp.empty:
                    continue
                df_temp = self._normalizar_colunas_energia_acumulada(df_temp)
                if df_temp.empty:
                    continue

            dfs.append(df_temp)

        return dfs

    def _extrair_info_temporal(self, usina: str, tabela: str) -> dict:
        """
        Detecta coluna temporal real via config identificacao.
        Suporta usinas com 'Time_Stamp as data_hora' + 'Time_Stamp_ms'.
        Retorna dict com col_real, col_ms, select_expr, order_by.
        """
        id_cols = self.config.get(usina, {}).get('identificacao', {}).get(tabela, [])
        col_real = 'data_hora'
        col_ms = None

        for col_def in id_cols:
            col_lower = col_def.lower().strip()
            if ' as ' in col_lower and 'data_hora' in col_lower:
                parts = re.split(r'\s+as\s+', col_def, maxsplit=1, flags=re.IGNORECASE)
                col_real = parts[0].strip()
            elif col_lower.endswith('_ms'):
                col_ms = col_def.strip()

        if col_real == 'data_hora':
            return {
                'col_real': 'data_hora',
                'col_ms': None,
                'select_expr': 'data_hora',
                'order_by': 'data_hora',
            }

        return {
            'col_real': col_real,
            'col_ms': col_ms,
            'select_expr': f'{col_real} AS data_hora',
            'order_by': f'{col_real}, {col_ms}' if col_ms else col_real,
        }

    def _montar_query(self, tabela: str, colunas: list, data_inicio: str, data_fim: str, periodo: str, info_temporal: dict = None) -> str:
        """Gera SQL conforme período e coluna temporal da usina."""
        if info_temporal is None:
            info_temporal = {'col_real': 'data_hora', 'col_ms': None, 'select_expr': 'data_hora', 'order_by': 'data_hora'}

        col_str = ', '.join(colunas)
        select_data = info_temporal['select_expr']
        where_col = info_temporal['col_real']
        order_col = info_temporal['order_by']

        if periodo == 'M':
            base_select_cols = []
            outer_select_cols = []

            for i, coluna in enumerate(colunas, start=1):
                expr, alias = self._split_coluna_expr(coluna)
                alias_interno = f'energia_{i}'
                base_select_cols.append(f'{expr} AS {alias_interno}')
                if alias:
                    outer_select_cols.append(f"{alias_interno} AS '{alias}'")
                else:
                    outer_select_cols.append(alias_interno)

            base_cols_str = ',\n                    '.join(base_select_cols)
            outer_cols_str = ', '.join(outer_select_cols)

            return f"""WITH base AS (
                SELECT
                    {select_data},
                    {base_cols_str},
                    DATE_FORMAT({where_col}, '%Y-%m-01') AS mes_ini,
                    ROW_NUMBER() OVER (
                        PARTITION BY YEAR({where_col}), MONTH({where_col})
                        ORDER BY {order_col} ASC
                    ) AS rn_asc,
                    ROW_NUMBER() OVER (
                        PARTITION BY YEAR({where_col}), MONTH({where_col})
                        ORDER BY {order_col} DESC
                    ) AS rn_desc
                FROM {tabela}
                WHERE {where_col} >= '{data_inicio}' AND {where_col} <= '{data_fim}'
            ),
            filtrada AS (
                SELECT * FROM base
                WHERE rn_asc <= 10 OR rn_desc <= 10
            )
            SELECT data_hora, {outer_cols_str}
            FROM filtrada
            ORDER BY data_hora"""

        return (
            f'SELECT {select_data}, {col_str} FROM {tabela} '
            f'WHERE {where_col} >= "{data_inicio}" AND {where_col} <= "{data_fim}" '
            f'ORDER BY {order_col}'
        )

    def _garantir_conexao(self):
        """Reutiliza conexão aberta quando possível e reconecta se necessário."""
        if self._conexao_expirada_por_inatividade():
            self.db.close()

        conn = self.db.connection
        if conn is None:
            self.db.connect()
            self._touch_connection()
            return

        try:
            if not conn.is_connected():
                self.db.connect()
                self._touch_connection()
                return
            conn.ping(reconnect=True, attempts=1, delay=0)
            self._touch_connection()
        except Exception:
            self.db.connect()
            self._touch_connection()

    def _touch_connection(self):
        self._connection_last_used_at = time.time()

    def _conexao_expirada_por_inatividade(self) -> bool:
        if self.connection_idle_ttl_seconds <= 0:
            return False
        if self._connection_last_used_at is None:
            return False
        return (time.time() - self._connection_last_used_at) > self.connection_idle_ttl_seconds

    def _resolver_periodo_base(self, periodo: str) -> str:
        # H, D e M podem compartilhar a mesma consulta base de energia acumulada.
        if periodo in {'H', 'D', 'M'}:
            return 'H'
        return periodo

    def _cache_key_dados_usina_base(self, usina: str, data_inicio: str, data_fim: str, query_periodo: str) -> str:
        return f"usina_dados_base:{usina}|{query_periodo}|{data_inicio}|{data_fim}"

    def _split_coluna_expr(self, coluna: str) -> tuple[str, str | None]:
        """
        Divide expressão SQL em (expressão, alias), quando existir.
        """
        partes = re.split(r'\s+as\s+', coluna, maxsplit=1, flags=re.IGNORECASE)
        expr = partes[0].strip()
        if len(partes) == 1:
            return expr, None
        alias = partes[1].strip().strip("`'\"")
        return expr, alias

    def _tratar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza tipos e remove registros inválidos para cálculo de produção."""
        if df.empty:
            return df

        df = df.copy()
        if 'data_hora' in df.columns:
            df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce')
            df = df[df['data_hora'].notna()]

        colunas_numericas = [c for c in df.columns if c != 'data_hora']
        for col in colunas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        if not colunas_numericas:
            return df

        mask_numerico = df[colunas_numericas].notna().all(axis=1)
        mask_positivo = (df[colunas_numericas] >= 0).all(axis=1)
        mask_sentinela = (df[colunas_numericas] == 103.00).any(axis=1)

        df = df[mask_numerico & mask_positivo & ~mask_sentinela]
        return df

    def _eh_coluna_energia_acumulada(self, nome_coluna: str) -> bool:
        nome = nome_coluna.lower()
        return 'energia' in nome and ('acumul' in nome or 'acum_' in nome or 'acum' in nome)

    def _normalizar_colunas_energia_acumulada(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Mantém apenas data_hora + Energia Acumulada, normalizando para:
        - UG-01 Energia Acumulada
        - UG-02 Energia Acumulada
        """
        colunas_energia = [
            c for c in df.columns
            if c != 'data_hora' and self._eh_coluna_energia_acumulada(c)
        ]
        if not colunas_energia:
            colunas_energia = [c for c in df.columns if c != 'data_hora']

        df = df[['data_hora', *colunas_energia]].copy()

        renomear = {}
        nomes_usados = set()
        for idx, coluna in enumerate(colunas_energia, start=1):
            ug_match = re.search(r'ug[-_\s]?0?(\d+)', coluna, flags=re.IGNORECASE)
            ug_num = int(ug_match.group(1)) if ug_match else idx
            nome_base = f'UG-{ug_num:02d} Energia Acumulada'

            nome_final = nome_base
            sufixo = 2
            while nome_final in nomes_usados:
                nome_final = f'{nome_base} ({sufixo})'
                sufixo += 1

            nomes_usados.add(nome_final)
            renomear[coluna] = nome_final

        df = df.rename(columns=renomear)
        if 'data_hora' in df.columns:
            df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce').dt.floor('min')
            df = df[df['data_hora'].notna()]

        return df

    def _merge_dataframes(self, dfs: list) -> pd.DataFrame:
        """Merge outer de DataFrames por data_hora. Retorna vazio se lista vazia."""
        if not dfs:
            return pd.DataFrame()
        df_base = dfs[0]
        for df_temp in dfs[1:]:
            df_base = pd.merge(df_base, df_temp, on='data_hora', how='outer')

        return df_base.sort_values('data_hora').reset_index(drop=True)

    def _log_raw_dataframe(
        self,
        usina: str,
        tabela: str,
        periodo: str,
        colunas_sql: list[str],
        query: str,
        df_raw: pd.DataFrame,
    ):
        if not self.raw_df_debug:
            return

        print(
            f"[RAW-DEBUG] usina={usina} tabela={tabela} periodo_query={periodo} "
            f"rows={len(df_raw)} cols={list(df_raw.columns)} colunas_sql={colunas_sql}"
        )
        if self.raw_df_debug_print_query:
            print(f"[RAW-DEBUG] query={query}")

        if df_raw.empty:
            print("[RAW-DEBUG] dataframe_vazio")
            return

        if 'data_hora' not in df_raw.columns:
            print("[RAW-DEBUG] sem_coluna_data_hora")
            return

        df = df_raw.copy()
        df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce')
        df = df[df['data_hora'].notna()].sort_values('data_hora')
        if df.empty:
            print("[RAW-DEBUG] sem_data_hora_valida")
            return

        colunas_numericas = [c for c in df.columns if c != 'data_hora']
        for col in colunas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        chave_mes = df['data_hora'].dt.to_period('M').astype(str)
        meses = sorted(chave_mes.unique().tolist())
        for mes in meses:
            if self.raw_df_debug_meses and mes not in self.raw_df_debug_meses:
                continue

            df_mes = df[chave_mes == mes]
            if df_mes.empty:
                continue

            print(f"[RAW-DEBUG][MES] mes={mes} rows={len(df_mes)}")
            for col in colunas_numericas:
                serie = df_mes[col]
                serie_valid = serie.dropna()
                first_val = float(serie_valid.iloc[0]) if not serie_valid.empty else None
                last_val = float(serie_valid.iloc[-1]) if not serie_valid.empty else None
                min_val = float(serie_valid.min()) if not serie_valid.empty else None
                max_val = float(serie_valid.max()) if not serie_valid.empty else None
                zeros = int((serie == 0).sum())
                sentinela_103 = int((serie == 103.00).sum())
                negativos = int((serie < 0).sum())
                nulos = int(serie.isna().sum())

                print(
                    f"[RAW-DEBUG][MES][COL] mes={mes} coluna={col} "
                    f"validos={int(serie_valid.shape[0])} nulos={nulos} zeros={zeros} "
                    f"sentinela103={sentinela_103} negativos={negativos} "
                    f"first={first_val} last={last_val} min={min_val} max={max_val}"
                )

            if self.raw_df_debug_rows > 0:
                amostra = pd.concat(
                    [
                        df_mes.head(self.raw_df_debug_rows),
                        df_mes.tail(self.raw_df_debug_rows),
                    ]
                ).drop_duplicates().sort_values('data_hora')
                print("[RAW-DEBUG][MES][AMOSTRA]")
                print(amostra.to_string(index=False))
