# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. __init__        → carrega configurações do .env
# 2. connect         → abre conexão MySQL
# 3. execute_query   → executa query com commit (INSERT/UPDATE/DELETE)
# 4. fetch_data      → executa SELECT, retorna lista de dicts
# 5. fetch_dataframe → executa SELECT, retorna pd.DataFrame
# 6. close           → encerra conexão
# -------------------------------------------------------------------

import mysql.connector
from mysql.connector import Error
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
        self.connection = None
        self._validate_config()

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

    @desempenho 
    def connect(self):
        try:
            print(f"host: {self.host}")
            print(f"user: {self.user}")
            print(f"password: {self.password}")
            print(f"database: {self.database}")
            print(f"port: {self.port}")
            print(f"connection_timeout: {self.connection_timeout}")
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                connection_timeout=self.connection_timeout
            )
            return self.connection
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise Exception(f"Erro ao conectar ao banco de dados: {e}")
        except Exception as e:
            print(f"Erro de configuração/conexão MySQL: {e}")
            raise Exception(f"Erro de configuração/conexão MySQL: {e}")

    @desempenho
    def execute_query(self, query, params=None):
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Erro ao executar query: {e}")
        finally:
            cursor.close()

    @desempenho
    def fetch_data(self, query, params=None):
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in result]
        except Error as e:
            raise Exception(f"Erro ao buscar dados: {e}")
        finally:
            cursor.close()

    @desempenho
    def fetch_dataframe(self, query, params=None) -> pd.DataFrame:
        """Executa SELECT e retorna pd.DataFrame direto."""
        if self.connection is None:
            self.connect()
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        except Error as e:
            raise Exception(f"Erro ao buscar dados: {e}")
        finally:
            cursor.close()

    def close(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
            except Error as e:
                pass
        self.connection = None
