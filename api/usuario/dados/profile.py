# Autor: Miliano Fernandes de Oliveira Junior
import json
import os

class Profile:

    def __init__(self, db, name='profile'):
        self.name = name
        self.db = db

    def _debug(self, msg):
        if os.getenv('DEBUG') == 'True':
            if 'new' in msg:
                print(f"{'-'*20} {msg} {'-'*20}")
            else:
                print(msg)

    def get_profile_id(self, id):
        ''' Função de consulta de usuário '''
        try:
            query = "SELECT * FROM usuarios WHERE id=%s"
            result = self.db.fetch_all(query, (id,))
            return result if result else False
        except Exception as err:
            raise Exception(f"Failed get profile: {err}")

    def get_profile(self, email):
        ''' Função de consulta de usuário '''
        try:
            print('Buscando usuário ...')
            query = "SELECT * FROM usuarios WHERE email=%s"
            result = self.db.fetch_all(query, (email,))
            print('Usuário: ', result)
            return result if result else False
        except Exception as err:
            raise Exception(f"Failed get profile: {err}")

    def modify_password(self, email: str, password: str):
        ''' Função de alteração de senha '''
        try:
            query = "UPDATE usuarios SET senha=%s WHERE email=%s"
            self.db.execute_query(query, (password, email))
            return {'status': 'Senha alterada com sucesso.'}
        except Exception as err:
            raise Exception(f"Failed modify password: {err}")

    def create_profile(self, user):
        ''' Função de cadastro de usuário '''
        try:
            query = "INSERT INTO usuarios (nome, telefone, nascimento, email, senha, usina, id_usina, privilegios) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            params = (user.nome, user.telefone, user.nascimento, user.email, user.password, user.usina, user.id_usina, user.privilegios)
            self.db.execute_query(query, params)
            return {'status': 'Usuário cadastrado com sucesso.'}
        except Exception as err:
            raise Exception(f"Failed create profile: {err}")


