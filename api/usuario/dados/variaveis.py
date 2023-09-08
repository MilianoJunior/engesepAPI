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
              'usina': None,
              'usina_id':None,
              'privilegios' : None,
    },
    'usina':{
                'usina_info': {
                                'id':None,
                                'nome': None,
                                'localizacao': None,
                                'numero_de_turbinas': None,
                                'potencia':None,
                                'nome_tabela': None
                },
                'usina_dados':turbina,
    }
}

