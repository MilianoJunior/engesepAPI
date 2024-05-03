'''
Estou criando uma API para um sistema de monitoramento de usinas hidrelétricas. A classe que se conecta com o banco de dados
é a Connection, que está no arquivo libs/data.py. Estou pensando em usar o pattern Singleton para garantir que apenas uma
instância da conexão seja criada. O que você acha?
'''


'''
converto um dataframe para um dicionário:

{"status":"ok","df":{"ug01_acumulador_energia":{"2024-04-30T00:00:00":0.793},"ug02_acumulador_energia":{"2024-04-30T00:00:00":1.033},"ug03_acumulador_energia":{"2024-04-30T00:00:00":-1.001},"ug04_acumulador_energia":{"2024-04-30T00:00:00":2.761}}}


Mas preciso alterar para o seguinte formato:

{
  "status": "ok",
  "df": [
    {
      "geradora": "UG01",
      "leituras": [
        {
          "leitura": "2024-04-25T00:00:00",
          "acumulado": 42.954
        },
        {
          "leitura": "2024-04-26T00:00:00",
          "acumulado": 42.954
        }
      ]
    },
    {
      "geradora": "UG02",
      "leituras": [
        {
          "leitura": "2024-04-25T00:00:00",
          "acumulado": 42.954
        },
        {
          "leitura": "2024-04-26T00:00:00",
          "acumulado": 42.954
        }
   ]
    }
    ]
}

pode criar uma função que converta o dicionário para o formato desejado?

'''

'''
{   
    "status":"ok",
    "df":[
            {
                "geradora":"UG01",
                "leituras":[
                        {
                            "leitura":"2024-04-28T00:00:00",
                            "acumulado":0.793
                        }
            ]},
            {   
                "geradora":"UG02",
                "leituras":[
                        {
                            "leitura":"2024-04-28T00:00:00",
                            "acumulado":1.033
                        }
                ]},
            {
                "geradora":"UG03",
                "leituras":[
                        {
                            "leitura":"2024-04-28T00:00:00",
                            "acumulado":-1.001
                        }
                ]},
            {
                "geradora":"UG04",
                "leituras":[
                        {
                            "leitura":"2024-04-28T00:00:00",
                            "acumulado":2.761
                        }
                ]}
            ]
}


'''