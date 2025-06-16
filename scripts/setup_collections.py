import json
import random
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pymongo
from pymongo.operations import SearchIndexModel

# Carrega variáveis de ambiente
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI não encontrada nas variáveis de ambiente. Configure o arquivo .env")

DB_NAME = "DeepContext"
TARGET_COLLECTION_NAME = "knowledge_documentation"
VECTOR_INDEX_NAME = "vector_index_knowledge_documentation"
EMBEDDING_FIELD_NAME = "embedding"
VECTOR_DIMENSIONS = 1536

def create_collection_if_not_exists(db, collection_name):
    """
    Cria uma coleção se ela ainda não existir.
    """
    if collection_name not in db.list_collection_names():
        try:
            db.create_collection(collection_name)
            print(f"Coleção '{collection_name}' criada com sucesso em '{DB_NAME}'.")
        except pymongo.errors.CollectionInvalid:
            print(f"Coleção '{collection_name}' já existe em '{DB_NAME}'. (Detectado via CollectionInvalid)")
        except Exception as e:
            print(f"Erro ao tentar criar a coleção '{collection_name}': {e}")
    else:
        print(f"Coleção '{collection_name}' já existe em '{DB_NAME}'.")

def create_vector_search_index_if_not_exists(db, collection_name, index_name, embedding_field, dimensions):
    """
    Cria um índice de busca vetorial do Atlas Search se ele ainda não existir.
    """
    try:
        collection = db.get_collection(collection_name)
        existing_indexes = list(collection.list_search_indexes())
        for index in existing_indexes:
            if index['name'] == index_name:
                print(f"Índice de busca vetorial '{index_name}' já existe na coleção '{collection_name}'.")
                return

        index_model = SearchIndexModel(
            name=index_name,
            definition={
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        embedding_field: [
                            {
                                "type": "vector",
                                "dimensions": dimensions,
                                "similarity": "cosine",
                            }
                        ]
                    }
                }
            }
        )
        
        collection.create_search_index(model=index_model)

        print(f"Criação do índice de busca vetorial '{index_name}' iniciada na coleção '{collection_name}'.")
        print("Nota: A construção do índice pode levar alguns minutos no Atlas.")

    except pymongo.errors.OperationFailure as e:
        if "Index already exists" in str(e) or "index with name" in str(e).lower() and "already exists" in str(e).lower() or e.code == 85:
            print(f"Índice de busca vetorial '{index_name}' já existe na coleção '{collection_name}'. (Detectado via OperationFailure)")
        elif "Command not found" in str(e) or "no such command" in str(e).lower() or "Unknown command" in str(e).lower():
            print(f"Erro: O comando para criar índices de busca não foi encontrado ou não é suportado. Certifique-se de que está conectado a um cluster MongoDB Atlas (M10+) com o Search habilitado e usando uma versão compatível do PyMongo.")
        else:
            print(f"Falha na operação com o MongoDB ao tentar criar o índice de busca vetorial '{index_name}': {e}")
            if hasattr(e, 'details'): print(f"Detalhes do erro: {e.details}")
    except AttributeError as e:
        if "'Collection' object has no attribute 'list_search_indexes'" in str(e) or \
           "'Collection' object has no attribute 'create_search_index'" in str(e):
            print(f"Erro: Parece que a versão do PyMongo ou o tipo de servidor MongoDB não suporta a API de Atlas Search Indexes desta forma. Verifique a compatibilidade. Detalhes: {e}")
        else:
            print(f"Ocorreu um AttributeError inesperado: {e}") 
            raise e
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao tentar criar o índice de busca vetorial '{index_name}': {e}")

def main():
    client = None
    try:
        print(f"Tentando conectar a: {MONGO_URI[:20]}...{MONGO_URI[-20:]}")
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('serverStatus') 
        print("Conexão com MongoDB estabelecida com sucesso.")
        
        db = client[DB_NAME]
        print(f"Acessando banco de dados: '{DB_NAME}'")
        
        create_collection_if_not_exists(db, TARGET_COLLECTION_NAME)
        
        create_vector_search_index_if_not_exists(db, 
                                                 TARGET_COLLECTION_NAME, 
                                                 VECTOR_INDEX_NAME, 
                                                 EMBEDDING_FIELD_NAME, 
                                                 VECTOR_DIMENSIONS)
                
    except pymongo.errors.ConfigurationError as e:
        print(f"Erro de configuração do PyMongo: {e}")
    except pymongo.errors.OperationFailure as e:
        print(f"Falha na operação geral com o MongoDB: {e}")
        if hasattr(e, 'details') and e.details and 'code' in e.details and e.details['code'] == 18: # Auth error
             print("Dica: Verifique se o nome de usuário e senha no MONGO_URI estão corretos.")
    except pymongo.errors.ConnectionFailure as e:
        print(f"Falha ao conectar ao MongoDB: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado na função main: {e}")
    finally:
        if client:
            client.close()
            print("\nConexão com MongoDB fechada.")

if __name__ == "__main__":
    main() 