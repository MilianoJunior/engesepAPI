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

'''

Tenho o seguinte dicionário:

{
    "status":"ok",
    "df":{
            "ug01_acumulador_energia":{"2024-04-25T00:00:00":1744.76,"2024-04-26T00:00:00":3563.13},
            "ug02_acumulador_energia":{"2024-04-25T00:00:00":1820.297,"2024-04-26T00:00:00":3617.91},
            "ug03_acumulador_energia":{"2024-04-25T00:00:00":1755.511,"2024-04-26T00:00:00":3586.81},
            "ug04_acumulador_energia":{"2024-04-25T00:00:00":1862.897,"2024-04-26T00:00:00":3697.36}
            }
}


Mas preciso alterar para o seguinte formato:

{[
  {
    "leitura": "2024-04-25T00:00:00",
    "acumulado_ug01": 3561.247,
    "acumulado_ug02": 3561.247,
    "acumulado_ug03": 3561.247,
    "acumulado_ug04": 3561.247
  },
  {
    "leitura": "2024-04-26T00:00:00",
    "acumulado_ug01": 3761.247,
    "acumulado_ug02": 3761.247,
    "acumulado_ug03": 3761.247,
    "acumulado_ug04": 3761.247
  }
]}

pode criar uma função que converta o dicionário para o formato desejado?

[{"leitura":"2024-04-24T00:00:00","acumulado_acumulador":164.708},{"leitura":"2024-04-25T00:00:00","acumulado_acumulador":196.808},{"leitura":"2024-04-26T00:00:00","acumulado_acumulador":238.472},{"leitura":"2024-04-27T00:00:00","acumulado_acumulador":274.603}]

'''