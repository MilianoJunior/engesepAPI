# ENGESEP
## 📝 _API EngeSEP para conexão com o banco de dados.

API desenvolvida para a aquisição de dados do banco de dados da EngeSEP, faz uso da framework FastAPI para a criação de rotas e conexão com o banco de dados.
Os dados são retornados no formato JSON. Com as seguintes funcionalidades:

-   Consulta de dados
-   Inserção de dados
-   Atualização de dados
-   Exclusão de dados
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