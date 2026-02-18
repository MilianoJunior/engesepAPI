# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. __init__                → recebe Database e config, configura cache/conexão
# 2. buscar_grupo            → consulta grupo inteiro → retorna DataFrame bruto
# 3. buscar_sensor           → consulta variável individual → retorna DataFrame bruto
# 4. listar_grupos           → retorna dict de grupos e aliases disponíveis
# 5. _localizar_variavel     → encontra tabela e coluna SQL a partir do alias
# 6. _consultar              → executa query → retorna DataFrame
# 7. _montar_query           → gera SQL SELECT com filtro de data
# -------------------------------------------------------------------

import os
import re
import time
import pandas as pd
from libs.db import Database
from libs.cache_store import CacheStore
from libs.usina_model import USINAS_CONFIG, GRUPOS_IGNORADOS

# ======================== CONFIGURAÇÃO ========================

GRUPOS_STATUS = {'status'}


# ======================== MODEL ========================

class TelemetriaModel:
    def __init__(self, db: Database, config: dict = None):
        self.db = db
        self.config = config or USINAS_CONFIG
        self.cache_enabled = os.getenv('USINA_CACHE_ENABLED', '1').strip().lower() in {'1', 'true', 'yes', 'on'}
        self.cache_ttl_seconds = int(os.getenv('USINA_CACHE_TTL_SECONDS', '60'))
        self.connection_idle_ttl_seconds = int(os.getenv('USINA_CONN_IDLE_TTL_SECONDS', '180'))
        self._connection_last_used_at = None

    def buscar_grupo(self, usina: str, grupo: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Consulta todas as variáveis de um grupo → retorna DataFrame bruto."""
        cfg = self.config[usina]
        mapa = cfg.get(grupo)
        if not isinstance(mapa, dict):
            raise ValueError(f'Grupo "{grupo}" não existe para usina {usina}.')

        cache_key = f'telemetria_grupo:{usina}|{grupo}|{data_inicio}|{data_fim}'

        def _buscar_grupo():
            tabelas = cfg['tabelas']
            dfs = []
            for tabela in tabelas:
                colunas = mapa.get(tabela, [])
                if not colunas:
                    continue
                df = self._consultar(tabela, colunas, data_inicio, data_fim)
                if not df.empty:
                    dfs.append(df)
            if not dfs:
                return None
            return self._merge_dataframes(dfs)

        if self.cache_enabled:
            resultado = CacheStore.get_or_set(cache_key, _buscar_grupo, ttl_seconds=self.cache_ttl_seconds)
            return resultado if resultado is not None else pd.DataFrame()

        return _buscar_grupo() or pd.DataFrame()

    def buscar_sensor(self, usina: str, variavel: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Consulta variável individual pelo alias → retorna DataFrame bruto."""
        cache_key = f'telemetria_sensor:{usina}|{variavel}|{data_inicio}|{data_fim}'

        def _buscar_sensor():
            grupo, tabela, coluna_sql = self._localizar_variavel(usina, variavel)
            df = self._consultar(tabela, [coluna_sql], data_inicio, data_fim)
            return df if not df.empty else None

        if self.cache_enabled:
            resultado = CacheStore.get_or_set(cache_key, _buscar_sensor, ttl_seconds=self.cache_ttl_seconds)
            return resultado if resultado is not None else pd.DataFrame()

        grupo, tabela, coluna_sql = self._localizar_variavel(usina, variavel)
        df = self._consultar(tabela, [coluna_sql], data_inicio, data_fim)
        return df if not df.empty else pd.DataFrame()

    def listar_grupos(self, usina: str) -> dict:
        """Retorna dict de grupos disponíveis com suas variáveis (aliases)."""
        cfg = self.config[usina]
        grupos = {}
        for chave, mapa in cfg.items():
            if chave in GRUPOS_IGNORADOS or not isinstance(mapa, dict):
                continue
            aliases = []
            for colunas in mapa.values():
                for col in colunas:
                    alias = self._extrair_alias(col)
                    aliases.append(alias)
            grupos[chave] = aliases
        return grupos

    # ======================== PRIVADOS ========================

    def _localizar_variavel(self, usina: str, alias_buscado: str) -> tuple[str, str, str]:
        """Encontra (grupo, tabela, coluna_sql) a partir de um alias."""
        cfg = self.config[usina]
        alias_lower = alias_buscado.strip().lower()

        for grupo, mapa in cfg.items():
            if grupo in GRUPOS_IGNORADOS or not isinstance(mapa, dict):
                continue
            for tabela, colunas in mapa.items():
                for col_sql in colunas:
                    alias = self._extrair_alias(col_sql)
                    if alias.lower() == alias_lower:
                        return grupo, tabela, col_sql

        raise ValueError(
            f'Variável "{alias_buscado}" não encontrada na usina {usina}.'
        )

    def _consultar(self, tabela: str, colunas: list[str], data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Executa query e retorna DataFrame bruto."""
        self._garantir_conexao()
        query = self._montar_query(tabela, colunas, data_inicio, data_fim)
        df = self.db.fetch_dataframe(query)
        self._touch_connection()

        if df.empty:
            return df

        df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce')
        df = df[df['data_hora'].notna()].sort_values('data_hora')

        colunas_numericas = [c for c in df.columns if c != 'data_hora']
        for col in colunas_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _montar_query(self, tabela: str, colunas: list[str], data_inicio: str, data_fim: str) -> str:
        """Gera SQL SELECT com filtro de data."""
        col_str = ', '.join(colunas)
        return (
            f'SELECT data_hora, {col_str} FROM {tabela} '
            f'WHERE data_hora >= "{data_inicio}" AND data_hora <= "{data_fim}" '
            f'ORDER BY data_hora'
        )

    def _merge_dataframes(self, dfs: list[pd.DataFrame]) -> pd.DataFrame:
        """Merge outer de DataFrames por data_hora."""
        if not dfs:
            return pd.DataFrame()
        df_base = dfs[0]
        for df_temp in dfs[1:]:
            df_base = pd.merge(df_base, df_temp, on='data_hora', how='outer')
        return df_base.sort_values('data_hora').reset_index(drop=True)

    def _extrair_alias(self, coluna_sql: str) -> str:
        """Extrai alias de 'col as Alias' ou retorna nome da coluna."""
        partes = re.split(r'\s+as\s+', coluna_sql, maxsplit=1, flags=re.IGNORECASE)
        if len(partes) == 2:
            return partes[1].strip().strip("'\"`")
        return partes[0].strip()

    def _garantir_conexao(self):
        """Reutiliza conexão aberta, reconecta se necessário."""
        if self._conexao_expirada():
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

    def _conexao_expirada(self) -> bool:
        if self.connection_idle_ttl_seconds <= 0 or self._connection_last_used_at is None:
            return False
        return (time.time() - self._connection_last_used_at) > self.connection_idle_ttl_seconds
