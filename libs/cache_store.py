# -------------------------------------------------------------------
# FLUXO DO MÓDULO
# 1. get              → busca valor no cache (verifica TTL, purga expirados)
# 2. set              → armazena valor com TTL e controle de memória
# 3. clear            → limpa todo o cache
# 4. delete_by_prefix → remove chaves por prefixo
# -------------------------------------------------------------------

import os
import time
import threading
from typing import Any


class CacheStore:
    """Armazém global de cache com expiração simples (TTL). Thread-safe via RLock."""
    _data: dict = {}
    _expiry: dict = {}
    _bytes: dict = {}
    _created_at: dict = {}
    _lock = threading.RLock()

    @classmethod
    def _memory_log_enabled(cls) -> bool:
        return os.getenv('CACHE_PRINT_MEMORY', '0').strip().lower() in {'1', 'true', 'yes', 'on'}

    @classmethod
    def _estimate_size_bytes(cls, value: Any) -> int:
        if hasattr(value, 'memory_usage'):
            try:
                return int(value.memory_usage(deep=True).sum())
            except Exception:
                pass
        if hasattr(value, '__sizeof__'):
            try:
                return int(value.__sizeof__())
            except Exception:
                pass
        try:
            import sys
            return int(sys.getsizeof(value))
        except Exception:
            return 0

    @classmethod
    def _memory_report(cls) -> str:
        total = sum(cls._bytes.values())
        return f"mem_total_mb={total / (1024 ** 2):.3f} items={len(cls._data)}"

    @classmethod
    def _max_bytes(cls) -> int:
        mb = float(os.getenv('CACHE_MAX_MB', '64'))
        if mb <= 0:
            return 0
        return int(mb * 1024 * 1024)

    @classmethod
    def _delete_key(cls, key: str):
        cls._data.pop(key, None)
        cls._expiry.pop(key, None)
        cls._bytes.pop(key, None)
        cls._created_at.pop(key, None)

    @classmethod
    def _purge_expired(cls):
        now = time.time()
        expiradas = [k for k, exp in cls._expiry.items() if now >= exp]
        for key in expiradas:
            cls._delete_key(key)

    @classmethod
    def _evict_until_fit(cls, incoming_bytes: int):
        max_bytes = cls._max_bytes()
        if max_bytes <= 0:
            return
        total = sum(cls._bytes.values())
        while cls._data and (total + incoming_bytes) > max_bytes:
            key_antiga = min(cls._created_at, key=cls._created_at.get)
            print(f"[CACHE] EVICT key={key_antiga!r}")
            cls._delete_key(key_antiga)
            total = sum(cls._bytes.values())

    @classmethod
    def get(cls, key: str):
        with cls._lock:
            cls._purge_expired()
            if key not in cls._data:
                print(f"[CACHE] MISS key={key!r}")
                return None
            if time.time() < cls._expiry.get(key, 0):
                extra = f" {cls._memory_report()}" if cls._memory_log_enabled() else ''
                print(f"[CACHE] HIT key={key!r}{extra}")
                return cls._data[key]
            print(f"[CACHE] EXPIRED key={key!r}")
            cls._delete_key(key)
            return None

    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: int = 60):
        with cls._lock:
            cls._purge_expired()
            if key in cls._data:
                cls._delete_key(key)
            incoming_bytes = cls._estimate_size_bytes(value)
            max_bytes = cls._max_bytes()
            if max_bytes > 0 and incoming_bytes > max_bytes:
                print(f"[CACHE] SKIP_TOO_LARGE key={key!r} item_mb={incoming_bytes / (1024 ** 2):.3f}")
                return
            cls._evict_until_fit(incoming_bytes)
            cls._data[key] = value
            cls._expiry[key] = time.time() + ttl_seconds
            cls._bytes[key] = incoming_bytes
            cls._created_at[key] = time.time()
            extra = f" {cls._memory_report()}" if cls._memory_log_enabled() else ''
            print(f"[CACHE] SET key={key!r}{extra}")

    @classmethod
    def clear(cls):
        with cls._lock:
            print(f"[CACHE] CLEAR key={'*'!r}")
            cls._data = {}
            cls._expiry = {}
            cls._bytes = {}
            cls._created_at = {}

    @classmethod
    def delete_by_prefix(cls, prefix: str):
        with cls._lock:
            keys_to_delete = [k for k in cls._data.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                cls._delete_key(k)
            print(f"[CACHE] DELETED_PREFIX prefix={prefix!r} count={len(keys_to_delete)}")
