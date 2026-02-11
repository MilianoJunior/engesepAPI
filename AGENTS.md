# Instrucoes locais para o agente

## Ambiente Python obrigatorio

- Sempre executar comandos Python e testes usando o ambiente virtual:
  - `source /home/jrmfilho23/projetos/amb/bin/activate`
- Ao rodar qualquer teste/comando, preferir no mesmo comando:
  - `source /home/jrmfilho23/projetos/amb/bin/activate && <comando>`

## Exemplos

- `source /home/jrmfilho23/projetos/amb/bin/activate && pytest -q`
- `source /home/jrmfilho23/projetos/amb/bin/activate && python -m py_compile main.py libs/*.py teste/*.py`
- `source /home/jrmfilho23/projetos/amb/bin/activate && uvicorn main:app --reload`
