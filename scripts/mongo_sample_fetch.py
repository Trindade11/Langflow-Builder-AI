import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

MONGO_URI = os.getenv("MONGODB_ATLAS_URI")
DB_NAME = os.getenv("MONGODB_ATLAS_DB", "DeepContext")
COLLECTION_NAME = os.getenv("MONGODB_ATLAS_COLLECTION", "knowledge_nodes")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

doc = collection.find_one()

print("Exemplo de documento em knowledge_nodes:")
print(doc) 