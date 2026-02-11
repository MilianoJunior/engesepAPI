import time

cont = 0
def desempenho(funcao):
    def wrapper(*args, **kwargs):
        global cont
        cont += 1
        print(f"{cont} - Iniciando: {funcao.__name__}")
        inicio = time.time()
        resultado = funcao(*args, **kwargs)
        fim = time.time()
        print(f"{cont} - Finalizado: {funcao.__name__} | Tempo: {fim - inicio:.4f} s")
        print('-'*40)
        return resultado
    return wrapper 
