import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

'''
     1- passo: configurar variaveis
     2- passo: aquisição de dados
     3- passo: tratamento de dados
     4- passo: envio de email

'''
'''
 configurações da variáveis
'''
# Obtenha a data de hoje e a data de amanhã
data_hoje = datetime.today().strftime('%d/%m/%Y')
data_amanha = (datetime.today() + timedelta(days=1)).strftime('%d/%m/%Y')

# Defina a URL da API que você deseja chamar
url = 'https://fastapi-production-8d7e.up.railway.app/consult'

# Defina o JSON que você deseja enviar no corpo da solicitação
data = {
    "usina": "cgh_aparecida",
    "coluna": ["acumulador_energia"],
    "periodo": "hour",
    "data_inicio": data_hoje,
    "data_fim": data_amanha,
    "token": "123456"
}

# Defina o cabeçalho da solicitação
headers = {'Content-type': 'application/json'}


'''
    Envio de email
'''
def enviar_email(assunto, corpo):
    ''' Envia um e-mail com o assunto e corpo fornecidos '''

    try:
        # Configurações do servidor SMTP
        smtp_server = 'smtp.gmail.com'  # Substitua pelo seu servidor SMTP
        porta = 587  # Porta SMTP padrão

        # Informações de login
        email_envio = os.getenv('email')  # Seu endereço de e-mail
        senha = os.getenv('senhaemail')  # Sua senha de e-mail

        # Destinatário do e-mail
        # destinatario = 'financeiro@engesep.com.br'  # Endereço de e-mail do destinatário
        destinatario = os.getenv('emaildestinatario') # Endereço de e-mail do destinatário

        # Criação do objeto MIMEMultipart
        msg = MIMEMultipart()

        # Configurações do e-mail
        msg['From'] = email_envio
        msg['To'] = destinatario
        msg['Subject'] = assunto

        # Corpo do e-mail
        corpo_email = corpo
        msg.attach(MIMEText(corpo_email, 'plain'))

        # Conexão com o servidor SMTP
        server = smtplib.SMTP(smtp_server, porta)
        server.starttls()

        # Faça login no servidor SMTP
        server.login(email_envio, senha)

        # Envie o e-mail
        texto_email = msg.as_string()
        server.sendmail(email_envio, destinatario, texto_email)

        # Encerre a conexão com o servidor SMTP
        server.quit()

        return True

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
'''
 Aquisição de dados
'''
def consultar_api(url, data, headers):
    ''' Consulta a API com os dados fornecidos '''
    try:
        # Faça a solicitação POST com o JSON como dados
        # response = requests.post(url, json=json.dumps(data), headers=headers)
        response = requests.post(url, json=data)
        response_json = response.json()

        return response_json
    except Exception as e:
        print(f"Erro ao consultar a API: {e}")
        return 'Erro ao consultar a API'


'''
    Tratamento de dados
'''
def trata_dados(response_json):
    ''' Trata os dados da API '''
    if 'df' in response_json and response_json['df']:
        leituras = response_json['df'][0]['leituras']

        if leituras:

            usina = "CGH_Aparecida"
            # Pegue o último valor da lista de leituras
            ultima_leitura = leituras[-1]

            # Extraia a data e hora da última leitura
            data_hora_str = ultima_leitura['leitura']

            # Converta a string de data e hora para um objeto datetime
            data_hora = datetime.fromisoformat(data_hora_str)

            # Formate a data e hora no formato desejado
            data_hora_formatada = data_hora.strftime('%d/%m/%Y %H:%M:%S')

            # Extraia o valor final da última leitura
            valor_final = ultima_leitura['acumulado']
            print(f'Usina: CGH_Aparecida\nData e hora: {data_hora_formatada}\nValor final: {valor_final}')
            # Crie o corpo do e-mail
            corpo_email = f"""
            Usina: {usina}
            Data e hora: {data_hora_formatada}
            Valor final: {valor_final}
            """
            # Envie o e-mail
            if enviar_email("Leitura de energia", corpo_email):
                print("E-mail enviado com sucesso!")
            else:
                print("Erro ao enviar e-mail.")


def main():
    resposta = consultar_api(url, data, headers)
    trata_dados(resposta)
# resposta = consultar_api(url, data, headers)
#
# trata_dados(resposta)



# # Faça a solicitação POST com o JSON como dados
# response = requests.post(url, json=json.dump(data), headers=headers)
# response_json = response.json()


# Função para enviar e-mail
# def enviar_email(assunto, corpo):
#     # Configurações do servidor SMTP
#     smtp_server = 'smtp.gmail.com'  # Substitua pelo seu servidor SMTP
#     porta = 587  # Porta SMTP padrão
#
#     # Informações de login
#     email_envio = 'felipemcco@gmail.com'  # Seu endereço de e-mail
#     senha = 'iozx znli ujnb tqwt'  # Sua senha de e-mail
#
#     # Destinatário do e-mail
#     # destinatario = 'financeiro@engesep.com.br'  # Endereço de e-mail do destinatário
#     destinatario = 'milianojunior39@gmail.com'  # Endereço de e-mail do destinatário
#
#     # Criação do objeto MIMEMultipart
#     msg = MIMEMultipart()
#
#     # Configurações do e-mail
#     msg['From'] = email_envio
#     msg['To'] = destinatario
#     msg['Subject'] = assunto
#
#     # Corpo do e-mail
#     corpo_email = corpo
#     msg.attach(MIMEText(corpo_email, 'plain'))
#
#     # Conexão com o servidor SMTP
#     server = smtplib.SMTP(smtp_server, porta)
#     server.starttls()
#
#     # Faça login no servidor SMTP
#     server.login(email_envio, senha)
#
#     # Envie o e-mail
#     texto_email = msg.as_string()
#     server.sendmail(email_envio, destinatario, texto_email)
#
#     # Encerre a conexão com o servidor SMTP
#     server.quit()
#
#
# def aquisicao_dados():
#     # Obtenha a data de hoje e a data de amanhã
#     data_hoje = datetime.today().strftime('%d/%m/%Y')
#     data_amanha = (datetime.today() + timedelta(days=1)).strftime('%d/%m/%Y')
#
#     # Defina a URL da API que você deseja chamar
#     url = 'https://fastapi-production-8d7e.up.railway.app/consult'
#
#     # Defina o JSON que você deseja enviar no corpo da solicitação
#     data = {
#         "usina": "cgh_aparecida",
#         "coluna": ["acumulador_energia"],
#         "periodo": "hour",
#         "data_inicio": data_hoje,
#         "data_fim": data_amanha,
#         "token": "123456"
#     }
#
#     # Defina o cabeçalho da solicitação
#     headers = {'Content-type': 'application/json'}
#
#     # Faça a solicitação POST com o JSON como dados
#     response = requests.post(url, json=json.dump(data), headers=headers)
#     response_json = response.json()
#
#     return response_json
#
#
# # Verifique se 'df' está presente na resposta e se não está vazio
# if 'df' in response_json and response_json['df']:
#     # Acesse a usina
#     usina = "CGH_Aparecida"
#
#     # Acesse a lista de leituras
#     leituras = response_json['df'][0]['leituras']
#
#     # Verifique se a lista de leituras não está vazia
#     if leituras:
#         # Pegue o último valor da lista de leituras
#         ultima_leitura = leituras[-1]
#
#         # Extraia a data e hora da última leitura
#         data_hora_str = ultima_leitura['leitura']
#
#         # Converta a string de data e hora para um objeto datetime
#         data_hora = datetime.fromisoformat(data_hora_str)
#
#         # Formate a data e hora no formato desejado
#         data_hora_formatada = data_hora.strftime('%d/%m/%Y %H:%M:%S')
#
#         # Extraia o valor final da última leitura
#         valor_final = ultima_leitura['acumulado']
#
#         # Crie o corpo do e-mail
#         corpo_email = f"""
#         Usina: {usina}
#         Data e hora: {data_hora_formatada}
#         Valor final: {valor_final}
#         """
#
#         # Envie o e-mail
#         enviar_email("Leitura de energia", corpo_email)
#
#         print("E-mail enviado com sucesso!")
#     else:
#         print("Não há leituras disponíveis.")
# else:
#     print("Não há dados disponíveis na resposta.")