import time
import threading

_lock = threading.Lock()
_cont = 0


def desempenho(funcao):
    def wrapper(*args, **kwargs):
        global _cont
        with _lock:
            _cont += 1
            n = _cont  # captura o número desta chamada específica
        print(f"{n} - Iniciando: {funcao.__name__}")
        inicio = time.time()
        try:
            resultado = funcao(*args, **kwargs)
        except Exception as e:
            fim = time.time()
            print(f"{n} - Erro: {funcao.__name__} | Tempo: {fim - inicio:.4f} s | {e}")
            print('-' * 40)
            raise
        fim = time.time()
        print(f"{n} - Finalizado: {funcao.__name__} | Tempo: {fim - inicio:.4f} s")
        print('-' * 40)
        return resultado
    return wrapper
