turbina = {
                'status_ativacao': None,
                'nome_turbina': None,
                'data': None,
                'energia_acumulada': None,
                'geracao_mensal': None,
                'geracao_diaria': None,
                'ultimos':None,
}
variaveis = {
    'token':'',
    'user':{
              'id': None,
              'nome':None,
              'telefone':None,
              'nascimento': None,
              'email':None,
              'senha':None,
              'imagem': None,
              'usina': None,
              'usina_id':None,
              'status' : None,
              'ultimo_acesso' : None,
              'numero_acessos': None,
              'acessos_consecutivos': None,
              'created_at':None,
              'updated_at': None
    },
    'usina':{
                'usina_info': {
                                'id':None,
                                'nome': None,
                                'local': None,
                                'cidade': None,
                                'numero_de_turbinas': None,
                                'potencia':None,
                                'nome_tabela': None,
                                'inicio_funcionamento': None,
                                'created_at':None,
                                'updated_at': None

                },
                'usina_dados':[],

    }
}