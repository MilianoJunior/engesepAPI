# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. __init__             → recebe Database e config, configura cache/conexão
# 2. buscar_grupo         → consulta todas as variáveis de um grupo com downsampling
# 3. buscar_sensor        → consulta variável individual pelo alias com downsampling
# 4. listar_grupos        → retorna dict de grupos e aliases disponíveis por usina
# 5. _localizar_variavel  → encontra tabela e coluna SQL a partir do alias
# 6. _consultar           → executa query, aplica downsampling, retorna list[dict]
# 7. _aplicar_periodo     → resample por média (ou .last() para status)
# 8. _montar_query        → gera SQL SELECT com filtro de data
# 9. _to_json             → converte DataFrame para list[dict] JSON-safe
# -------------------------------------------------------------------

import os
import re
import time
import pandas as pd
from libs.db import Database
from libs.cache_store import CacheStore
from libs.usina_model import USINAS_CONFIG, GRUPOS_IGNORADOS

# ======================== CONFIGURAÇÃO ========================

PERIODOS_VALIDOS = {
    '1min': '1min',
    '5min': '5min',
    '30min': '30min',
    '1h': '1h',
    '1d': '1D',
}

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

    def buscar_grupo(self, usina: str, grupo: str, data_inicio: str, data_fim: str, periodo: str = '1min') -> list[dict]:
        """Consulta todas as variáveis de um grupo (temperaturas, eletrica, etc.)."""
        cfg = self.config[usina]
        mapa = cfg.get(grupo)
        if not isinstance(mapa, dict):
            raise ValueError(f'Grupo "{grupo}" não existe para usina {usina}.')

        cache_key = f'telemetria_grupo:{usina}|{grupo}|{periodo}|{data_inicio}|{data_fim}'
        if self.cache_enabled:
            cached = CacheStore.get(cache_key)
            if cached is not None:
                return cached

        tabelas = cfg['tabelas']
        eh_status = grupo in GRUPOS_STATUS
        dfs = []

        for tabela in tabelas:
            colunas = mapa.get(tabela, [])
            if not colunas:
                continue
            df = self._consultar(tabela, colunas, data_inicio, data_fim)
            if not df.empty:
                dfs.append(df)

        if not dfs:
            return []

        resultado_df = self._merge_dataframes(dfs)
        resultado_df = self._aplicar_periodo(resultado_df, periodo, usar_last=eh_status)
        resultado = self._to_json(resultado_df)

        if self.cache_enabled:
            CacheStore.set(cache_key, resultado, ttl_seconds=self.cache_ttl_seconds)
        return resultado

    def buscar_sensor(self, usina: str, variavel: str, data_inicio: str, data_fim: str, periodo: str = '1min') -> list[dict]:
        """Consulta variável individual pelo alias (ex: 'UG-01 Temp. Óleo UHLM')."""
        cache_key = f'telemetria_sensor:{usina}|{variavel}|{periodo}|{data_inicio}|{data_fim}'
        if self.cache_enabled:
            cached = CacheStore.get(cache_key)
            if cached is not None:
                return cached

        grupo, tabela, coluna_sql = self._localizar_variavel(usina, variavel)
        eh_status = grupo in GRUPOS_STATUS

        df = self._consultar(tabela, [coluna_sql], data_inicio, data_fim)
        if df.empty:
            return []

        df = self._aplicar_periodo(df, periodo, usar_last=eh_status)
        resultado = self._to_json(df)

        if self.cache_enabled:
            CacheStore.set(cache_key, resultado, ttl_seconds=self.cache_ttl_seconds)
        return resultado

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
        """Executa query e retorna DataFrame com data_hora + colunas aliasadas."""
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

    def _aplicar_periodo(self, df: pd.DataFrame, periodo: str, usar_last: bool = False) -> pd.DataFrame:
        """Resample do DataFrame pela frequência do período."""
        if df.empty:
            return df

        freq = PERIODOS_VALIDOS.get(periodo, '1min')
        if freq == '1min':
            return df

        df = df.set_index('data_hora')
        if usar_last:
            df = df.resample(freq).last()
        else:
            df = df.resample(freq).mean()

        df = df.dropna(how='all').reset_index()
        return df

    def _montar_query(self, tabela: str, colunas: list[str], data_inicio: str, data_fim: str) -> str:
        """Gera SQL SELECT com filtro de data."""
        col_str = ', '.join(colunas)
        return (
            f'SELECT data_hora, {col_str} FROM {tabela} '
            f'WHERE data_hora >= "{data_inicio}" AND data_hora <= "{data_fim}" '
            f'ORDER BY data_hora'
        )

    def _to_json(self, df: pd.DataFrame) -> list[dict]:
        """Converte DataFrame para list[dict] com data_hora ISO."""
        if df.empty:
            return []

        resultado = []
        for _, row in df.iterrows():
            item = {}
            for col, val in row.items():
                if col == 'data_hora':
                    item[col] = val.isoformat() if hasattr(val, 'isoformat') else str(val)
                elif pd.notna(val):
                    item[col] = round(float(val), 3) if isinstance(val, (int, float)) else val
                else:
                    item[col] = None
            resultado.append(item)
        return resultado

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
