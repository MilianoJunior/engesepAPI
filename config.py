import os

def criar_diretorio(caminho):
    if not os.path.exists(caminho):
        os.makedirs(caminho)

def criar_arquivo(caminho):
    with open(caminho, 'w') as f:
        pass

estrutura = {
    'api': {
        'usuario': {
            'autenticacao': ['auth.py'],
            'dados': ['profile.py'],
            'politicas_acesso': ['access.py']
        },
        'usina': {
            'tabela': ['usinas.py'],
            'dados_basicos': ['basic_data.py'],
            'processamento': ['energia.py', 'nivel_agua.py'],
            'resposta_app': ['resposta.py']
        },
        'views': {
            'componentes':['graficos.py','tabelas.py','menus.py','botoes.py'],
            'layout': ['compose.py','rotas.py'],
        }

    }
}

def criar_estrutura(base, estrutura):
    for dir_name, sub_dir in estrutura.items():
        novo_dir = os.path.join(base, dir_name)
        criar_diretorio(novo_dir)

        if isinstance(sub_dir, dict):
            criar_estrutura(novo_dir, sub_dir)
        else:
            for file_name in sub_dir:
                criar_arquivo(os.path.join(novo_dir, file_name))

criar_estrutura('.', estrutura)

print("Pastas e arquivos criados com sucesso!")
