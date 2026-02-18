# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. __init__        → carrega configurações do .env e cria pool de conexões
# 2. connect         → compat. legada (no-op, pool gerencia conexões)
# 3. execute_query   → executa query com commit (INSERT/UPDATE/DELETE)
# 4. fetch_data      → executa SELECT, retorna lista de dicts
# 5. fetch_dataframe → executa SELECT, retorna pd.DataFrame
# 6. close           → compat. legada (no-op, pool gerencia conexões)
# -------------------------------------------------------------------

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import threading
import pandas as pd
import os
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
from libs.utils import desempenho

load_dotenv()


def _env_first(*keys):
    """Retorna o primeiro valor de env não vazio para as chaves informadas."""
    for key in keys:
        value = os.getenv(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def _to_int(value, default, env_name):
    """Converte string de env para inteiro com fallback e erro explícito."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Variável de ambiente inválida: {env_name}={value!r}. Use um número inteiro."
        ) from exc


def _parse_mysql_url(mysql_url: str | None) -> dict:
    if not mysql_url:
        return {}
    parsed = urlparse(mysql_url)
    database = parsed.path.lstrip("/") if parsed.path else None
    return {
        "host": parsed.hostname,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else None,
        "database": database or None,
        "port": parsed.port,
    }


class Database:
    @desempenho
    def __init__(self):
        url_cfg = _parse_mysql_url(_env_first("MYSQL_URL", "DATABASE_URL"))

        self.host = _env_first("MYSQL_HOST", "MYSQLHOST") or url_cfg.get("host")
        self.user = _env_first("MYSQL_USER", "MYSQLUSER") or url_cfg.get("user")
        self.password = (
            _env_first("MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD", "MYSQLPASSWORD")
            or url_cfg.get("password")
        )
        self.database = _env_first("MYSQL_DATABASE", "MYSQLDATABASE") or url_cfg.get("database")
        self.port = _to_int(
            _env_first("MYSQL_PORT", "MYSQLPORT") or url_cfg.get("port"),
            default=3306,
            env_name="MYSQL_PORT/MYSQLPORT",
        )
        self.connection_timeout = _to_int(
            _env_first("MYSQL_CONNECTION_TIMEOUT"),
            default=10,
            env_name="MYSQL_CONNECTION_TIMEOUT",
        )
        self.pool_size = _to_int(
            _env_first("MYSQL_POOL_SIZE"),
            default=5,
            env_name="MYSQL_POOL_SIZE",
        )
        # Compat. legada: alguns módulos acessam db.connection diretamente
        self.connection = None
        self._validate_config()
        self._pool = None
        self._pool_lock = threading.Lock()

    def _validate_config(self):
        obrigatorias = {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
        }
        faltantes = [campo for campo, valor in obrigatorias.items() if valor is None or str(valor).strip() == ""]
        if faltantes:
            raise ValueError(
                "Configuração MySQL incompleta. "
                f"Campos ausentes: {', '.join(faltantes)}. "
                "Defina MYSQL_HOST/MYSQL_USER/MYSQL_ROOT_PASSWORD/MYSQL_DATABASE "
                "(ou aliases legados, ou MYSQL_URL)."
            )

    def _criar_pool(self) -> MySQLConnectionPool:
        return MySQLConnectionPool(
            pool_name="engesep_pool",
            pool_size=self.pool_size,
            pool_reset_session=True,
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            connection_timeout=self.connection_timeout,
        )

    def _get_conn(self):
        """Pega uma conexão do pool. Cria o pool na primeira chamada (lazy). Sempre devolver com conn.close()."""
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:  # double-checked locking
                    self._pool = self._criar_pool()
        return self._pool.get_connection()

    # compat. legada — módulos que chamam db.connect() continuam funcionando
    @desempenho
    def connect(self):
        pass

    # compat. legada — módulos que chamam db.close() continuam funcionando
    def close(self):
        pass

    @desempenho
    def execute_query(self, query, params=None):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor
            except Error as e:
                conn.rollback()
                raise Exception(f"Erro ao executar query: {e}")
            finally:
                cursor.close()
        finally:
            conn.close()

    @desempenho
    def fetch_data(self, query, params=None):
        conn = self._get_conn()
        try:
            cursor = conn.cursor(buffered=True)
            try:
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in result]
            except Error as e:
                raise Exception(f"Erro ao buscar dados: {e}")
            finally:
                cursor.close()
        finally:
            conn.close()

    @desempenho
    def fetch_dataframe(self, query, params=None) -> pd.DataFrame:
        """Executa SELECT e retorna pd.DataFrame. Thread-safe via pool."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor(buffered=True)
            try:
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                return pd.DataFrame(rows, columns=columns)
            except Error as e:
                raise Exception(f"Erro ao buscar dados: {e}")
            finally:
                cursor.close()
        finally:
            conn.close()

