import pymongo
from bson import ObjectId # Importar ObjectId
import json # Importar json para serialização

# String de conexão e nome do banco de dados
MONGO_URI = "mongodb+srv://trindade:trindade@clustercocreateai.ykdjn.mongodb.net/?retryWrites=true&w=majority&appName=ClusterCoCreateAI"
DB_NAME = "DeepContext" # ATUALIZADO para DeepContext

# Classe para serializar ObjectId para JSON
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def list_mongo_collections(client):
    """
    Lista todas as coleções no banco de dados especificado.
    """
    try:
        db = client[DB_NAME]
        print(f"Acessando banco de dados: '{DB_NAME}'")
        
        collection_names = db.list_collection_names()
        
        if not collection_names:
            print(f"Nenhuma coleção encontrada no banco de dados '{DB_NAME}'.")
        else:
            print(f"Coleções encontradas no banco de dados '{DB_NAME}':")
            for name in collection_names:
                print(f"- {name}")
        return collection_names # Retorna os nomes para uso posterior
                
    except Exception as e:
        print(f"Erro ao listar coleções: {e}")
        return []

def get_one_document_from_collection(client, collection_name):
    """
    Busca e imprime um único documento de uma coleção especificada,
    excluindo campos com listas muito longas para melhor visualização.
    """
    try:
        db = client[DB_NAME]
        # Não é necessário verificar se collection_name está em db.list_collection_names() aqui
        # pois já é feito no loop da função main antes de chamar esta função.
        # No entanto, se esta função puder ser chamada de outros lugares, a verificação pode ser útil.
        # Para este fluxo, a verificação principal é feita em main().

        collection = db[collection_name]
        document = collection.find_one()
        
        if document:
            print(f"\nUm item da coleção '{collection_name}' (estrutura principal):")
            
            doc_to_print = document.copy()
            
            for key, value in document.items():
                if isinstance(value, list) and len(value) > 50: 
                    doc_to_print[key] = f"[Lista com {len(value)} itens, suprimida para visualização]"
            
            print(json.dumps(doc_to_print, indent=4, cls=JSONEncoder, ensure_ascii=False))
        else:
            print(f"Nenhum documento encontrado na coleção '{collection_name}'.")
            
    except Exception as e:
        print(f"Erro ao buscar documento da coleção '{collection_name}': {e}")

def main():
    """
    Função principal para conectar, listar coleções e permitir inspecionar uma coleção escolhida.
    """
    client = None
    try:
        print(f"Tentando conectar a: {MONGO_URI[:20]}...{MONGO_URI[-20:]}")
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('serverStatus') 
        print("Conexão com MongoDB estabelecida com sucesso.")
        
        available_collections = list_mongo_collections(client) 
        
        if not available_collections:
            print("Nenhuma coleção para inspecionar.")
            return

        while True:
            print("\nDigite o nome da coleção que deseja inspecionar (ou 'sair' para terminar):")
            collection_to_inspect = input("> ").strip()

            if collection_to_inspect.lower() == 'sair':
                break
            
            if collection_to_inspect in available_collections:
                get_one_document_from_collection(client, collection_to_inspect)
            else:
                print(f"Coleção '{collection_to_inspect}' não encontrada. As coleções disponíveis são: {', '.join(available_collections)}")
                
    except pymongo.errors.ConfigurationError as e:
        print(f"Erro de configuração do PyMongo: {e}")
    except pymongo.errors.OperationFailure as e:
        print(f"Falha na operação com o MongoDB: {e}")
        if hasattr(e, 'details') and e.details and 'code' in e.details and e.details['code'] == 18:
             print("Dica: Verifique se o nome de usuário e senha no MONGO_URI estão corretos.")
    except pymongo.errors.ConnectionFailure as e:
        print(f"Falha ao conectar ao MongoDB: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if client:
            client.close()
            print("\nConexão com MongoDB fechada.")

if __name__ == "__main__":
    main() 