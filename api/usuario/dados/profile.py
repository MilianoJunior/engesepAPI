# Autor: Miliano Fernandes de Oliveira Junior
import json
import os

class Profile:

    def __init__(self, db, name='profile'):
        self.name = name
        self.db = db


    def get_profile_id(self, id):
        ''' Função de consulta de usuário '''
        try:
            query = f"SELECT * FROM usuarios WHERE id='{id}'"
            result = self.db.fetch_all(query)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            raise Exception(f"Failed get profile line 48: {err}")

    def get_profile(self, email):
        ''' Função de consulta de usuário '''
        try:
            query = f"SELECT * FROM usuarios WHERE email='{email}'"
            result = self.db.fetch_all(query)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            raise Exception(f"Failed get profile line 48: {err}")

    def modify_password(self, email: str, password: str):
        ''' Função de alteração de senha '''
        try:
            query = update = f"UPDATE usuarios SET senha='{password}' WHERE email='{email}'"
            self.db.execute_query(query)
            return {'status': 'Senha alterada com sucesso.'}
        except Exception as err:
            raise Exception(f"Failed modify password line 57: {err}")
    def create_profile(self, user):
        ''' Função de cadastro de usuário '''
        try:
            query = f"INSERT INTO usuarios (nome, telefone, nascimento, email, senha, usina, id_usina, privilegios) VALUES ('{user.nome}', '{user.telefone}', '{user.nascimento}', '{user.email}', '{user.password}', '{user.usina}', '{user.id_usina}', '{user.privilegios}')"
            self.db.execute_query(query)
            return {'status': 'Usuário cadastrado com sucesso.'}
        except Exception as err:
            raise Exception(f"Failed create profile line 66: {err}")

