from pydantic import BaseModel

class Usina(BaseModel):
    nome: str
    numero_turbinas: int
    localizacao: str
    potencia_instalada: float

class Usinas:

    def __init__(self, db):
        self.db = db
        self.table = 'Usinas'
        self.fields = ['id', 'nome', 'numero_turbinas','localizacao','potencia_instalada']

    def get_usinas(self):
        ''' Função de consulta de usinas '''
        try:
            query = f"SELECT * FROM {self.table}"
            result = self.db.fetch_all(query)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            print(f"Failed to connect to database: {err}")
            raise

    def get_usina_id(self, id):
        ''' Função de consulta de usinas '''
        try:
            query = f"SELECT * FROM {self.table} WHERE id='{id}'"
            result = self.db.fetch_all(query)
            if len(result) == 0:
                return False
            else:
                return result
        except Exception as err:
            print(f"Failed to connect to database: {err}")
            raise

    def create_usina(self, usina: Usina):
        ''' Função de criação de usina '''
        try:
            query = f"INSERT INTO {self.table} (nome, numero_turbinas, localizacao, potencia_instalada) VALUES ('{usina.nome}', '{usina.numero_turbinas}', '{usina.localizacao}', '{usina.potencia_instalada}')"
            self.db.execute_query(query)
            return {'status': 'Usina criada com sucesso.'}
        except Exception as err:
            print(f"Failed to connect to database: {err}")
            raise