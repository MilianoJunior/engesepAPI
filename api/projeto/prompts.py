'''
Como posso modelar a estrutura das pastas e classes para a api?

A api necessita das seguintes funções:

# Usuário
    ## 1. Sistema de autenticação
        ### 1.1 Função de login
        ### 1.2 Função de cadastro
        ### 1.3 Função de recuperação de senha
        ### 1.5 Função de alteração de dados do usuário
        ### 1.6 Função de exclusão de usuário
        ### 1.7 Função de consulta de usuário
        ### 1.8 Função de logout

    ## 2. Sistema de políticas de acesso
        ### 2.1 Função de cadastro de políticas de acesso
        ### 2.2 Função de alteração de políticas de acesso
        ### 2.3 Função de exclusão de políticas de acesso
        ### 2.4 Função de consulta de políticas de acesso
        ### 2.5 Função de aplicação de políticas de acesso

# Dados da usina
    ## 1. Sistema da tabela, usinas
        ### 1.1 Função de cadastro dos dados da usina
        ### 1.2 Função de alteração dos dados da usina
        ### 1.3 Função de exclusão dos dados da usina
        ### 1.4 Função de consulta dos dados da usina
        ### 1.5 Função de consulta o número de UGs da usina

    ## 2. Sistema básicos para os dados da usina
        ### 2.1 Função de inserção dos dados na usina
        ### 2.2 Função de alteração dos dados da usina
        ### 2.3 Função de exclusão dos dados da usina
        ### 2.4 Função de consulta dos dados da usina

    ## 3. Sistema de processamento dos dados da usina
        ### 3.1 Função que faz a consulta por período e retorna o valor mensal de energia gerada para cada UG
        ### 3.2 Função que faz a consulta por período e retorna o valor mensal de energia gerada para as UGs
        ### 3.3 Função que faz a consulta por período e retorna o valor diario de energia gerada para cada UG
        ### 3.4 Função que faz a consulta por período e retorna o valor diario de energia gerada para as UGs
        ### 3.5 Função que faz a consulta por período e retorna o valor horario de energia gerada para cada UG
        ### 3.6 Função que faz a consulta por período e retorna o valor horario de energia gerada para as UGs
        ### 3.7 Função que faz a consulta por período e retorna o valor mensal do nível de água
        ### 3.8 Função que faz a consulta por período e retorna o valor diario do nível de água
        ### 3.9 Função que faz a consulta por período e retorna o valor horario do nível de água
        ### 3.10 Função que faz a consulta o último valor de energia gerada para cada UG
        ### 3.11 Função que faz a consulta o último valor acumulado para todas as UGs

    ## 4. Sistema de resposta para o aplicativo
        ### 4.1 Função que retorna o json padrão para o aplicativo
        ### 4.2 Função que valida os dados
        ### 4.3 Função que formata os dados

# Visualização dos dados
    ## 1. Sistema de visualização dos dados
        ### 1.1 Função que requisita os dados da usina
        ### 1.2 Função que gerar os gráficos
        ### 1.3 Função que organiza os gráficos nos templates

'''
api_info = {
    "Título": "Criação de API com FastAPI em Python",
    "Níveis de autenticação": {
        "Autenticação básica": {
            "Informação": "Usuário e senha"
        },
        "Autenticação por token": {
            "Informação": "Gerar e armazenar tokens para autenticação"
        }
    },
    "Banco de Dados": {
        "MySQL": {
            "Comunicação": "Comunicação com várias tabelas do banco de dados",
            "Uso": "Banco de dados utilizado para armazenar os dados"
        }
    },
    "Comunicação entre API e aplicativo": {
        "Utilização de endpoints": {
            "Descrição": "Definir endpoints para cada funcionalidade"
        },
        "Consumo da API pelo aplicativo": {
            "Processo": "Envio das requisições para a API"
        }
    },
    "Ferramentas": {
        "FastAPI": {
            "Descrição": "Framework para criação de APIs rápidas em Python"
        },
        "Python": {
            "Descrição": "Linguagem de programação utilizada para desenvolver a API"
        },
        "Git": {
            "Descrição": "Sistema de controle de versão para o código fonte da API"
        },
        "railway": {
            "Descrição": "Plataforma web onde o projeto pode ser hospedado e compartilhado"
        }
    },
    "Requisitos": {
        "Alta qualidade": {
            "Descrição": "A API deve ser desenvolvida com boas práticas de código"
        },
        "Detalhado": {
            "Descrição": "Todos os aspectos da comunicação entre a API e o banco de dados devem ser considerados"
        },
        "Vários níveis": {
            "Descrição": "A API precisa ter diferentes níveis de autenticação e funcionalidades"
        },
        "Sem Identificadores": {
            "Descrição": "Não utilizar identificadores sensíveis na API"
        },
        "Utilizar o idioma português": {
            "Descrição": "Todo o código, documentação e comentários devem ser escritos em português"
        }
    }
}
modelo = '''
Por favor, crie uma classe Python para comunicação com o banco de dados. Considerando que você seja um programador
experiente e que já tenha trabalhado com banco de dados, você pode criar a classe com os recursos que achar necessário e usar
os design patterns que achar melhor.. A classe deve ter os seguintes recursos:

[RECURSO 1]
[RECURSO 2]
[RECURSO 3]
...
Além disso, inclua as importações de bibliotecas necessárias e forneça testes unitários para validar a funcionalidade da classe.
'''
prompts = {
	"1": '''Pode criar uma classe em python que contenha os métodos para cada funcionalidade da API?
			"Autenticação básica": {
					"Informação": "Usuário e senha"
				},
				"Autenticação por token": {
					"Informação": "Gerar e armazenar tokens para autenticação"
				}
		    Se for necessario, pode criar mais classes para organizar melhor o código. E também pode criar 
		    mais métodos para cada funcionalidade, assim como os comandos sql para criar as tabelas no banco de dados.
        ''',

    "2": '''
        Por favor, crie uma classe Python para comunicação com o banco de dados. Considerando que você seja um programador
        experiente e que já tenha trabalhado com banco de dados, você pode criar a classe com os recursos que achar necessário e usar
        os design patterns que achar melhor.
         
        A classe deve ter os seguintes recursos:
        
        "MySQL": {
            "declaração de variáveis": "Declaração das variáveis de conexão com o banco de dados MySQL, usando o dotenv",
            "comunicação": "Comunicação separados em diferentes métodos para cada funcionalidade",
            "testes": "Testes unitários para validar a funcionalidade da classe"
        }
        Além disso, inclua as importações de bibliotecas necessárias e possíveis comandos sql para criar as tabelas no banco de dados.
    ''',
    "3": '''
        Por favor, crie uma classe Python gerenciar todos os métodos e lógica do sistema de autenticação. Considerando que você seja um programador
        experiente e que já tenha trabalhado com banco de dados, você pode criar a classe com os recursos que achar necessário e usar
        os design patterns que achar melhor.. A classe deve ter os seguintes recursos:
        
        Tratar os dados de entrada de autenticação, sendo o login(email) e senha, e retornar o token de acesso.
        Registrar o token de acesso no banco de dados.
        Verificar se o token de acesso existe no banco de dados.
        Verificar se o token de acesso está ativo.
        Verificar se o token de acesso está expirado.
        Verificar se o token de acesso está bloqueado.
        
        Tenhos as seguintes classe e métodos para ajudar:
            class BasicAuth:
            
                @staticmethod
                def hash_password(password: str, salt: bytes = None) -> str:
                
                @staticmethod
                def verify_password(stored_password: str, provided_password: str) -> bool:
                
            class Database:
            
                @staticmethod
                def _connect_to_database():
                
                def execute_query(self, query):
                
                def fetch_all(self, query):
                
                def close_connection(self):
        
        Além disso, inclua as importações de bibliotecas necessárias e forneça testes unitários para validar a funcionalidade da classe.
    ''',
    "4": '''
    Por favor, inplemente uma classe Python para gerenciar os métodos de autenticação por token. Considerando que você seja um programador
    experiente e que já tenha trabalhado com banco de dados, você pode criar a classe com os recursos que achar necessário e usar
    os design patterns que achar melhor.. A classe deve ter os seguintes recursos:

    Tratar os dados de entrada de autenticação, sendo o login(email) e senha, e retornar o token de acesso.
    Registrar o token de acesso no banco de dados.
    Verificar se o token de acesso existe no banco de dados.
    Verificar se o token de acesso está ativo.
    Verificar se o token de acesso está expirado.
    Verificar se o token de acesso está bloqueado.

    Tenhos as seguintes classe e métodos para ajudar:
        class BasicAuth:

            @staticmethod
            def hash_password(password: str, salt: bytes = None) -> str:

            @staticmethod
            def verify_password(stored_password: str, provided_password: str) -> bool:

        class Database:

            @staticmethod
            def _connect_to_database():

            def execute_query(self, query):

            def fetch_all(self, query):

            def close_connection(self):

    Além disso, inclua as importações de bibliotecas necessárias e forneça testes unitários para validar a funcionalidade da classe.
''',

}