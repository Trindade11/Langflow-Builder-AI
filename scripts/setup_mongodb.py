import pymongo

# String de conexão fornecida
MONGO_URI = "mongodb+srv://trindade:trindade@clustercocreateai.ykdjn.mongodb.net/?retryWrites=true&w=majority&appName=ClusterCoCreateAI"
DB_NAME = "langflow_builder_ai"

# Estrutura inicial de exemplo para components
component_example = {
    "name": "ChatInput",
    "display_name": "Chat Input",
    "description": "Recebe mensagens do usuário no chat.",
    "category": "input",
    "tags": ["chat", "entrada", "mensagem"],
    "icon": "MessagesSquare",
    "minimized": True,
    "inputs": ["MessageText", "FileInput"],
    "outputs": ["Message"],
    "parameters": [],
    "libraries": ["langflow.inputs", "langflow.io"],
    "relations": [],
    "vector": [],
    "metadata": {}
}

# Estrutura inicial de exemplo para io_types
io_type_example = {
    "_id": "Message",
    "name": "Message",
    "display_name": "Mensagem",
    "description": "Objeto que representa uma mensagem de chat, incluindo texto, remetente, arquivos e propriedades visuais.",
    "category": "output",
    "examples": [
        {
            "text": "Olá, tudo bem?",
            "sender": "Usuário",
            "files": []
        }
    ],
    "vector": [],
    "related_types": ["Text", "File"],
    "metadata": {
        "fields": [
            {"name": "text", "type": "str", "description": "Conteúdo textual da mensagem"},
            {"name": "sender", "type": "str", "description": "Remetente da mensagem"},
            {"name": "files", "type": "list", "description": "Arquivos anexados"}
        ]
    }
}

def main():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Cria as coleções se não existirem
    components = db["components"]
    io_types = db["io_types"]

    # Insere exemplos se as coleções estiverem vazias
    if components.count_documents({}) == 0:
        components.insert_one(component_example)
        print("Exemplo de componente inserido.")
    else:
        print("Coleção components já possui documentos.")

    if io_types.count_documents({}) == 0:
        io_types.insert_one(io_type_example)
        print("Exemplo de io_type inserido.")
    else:
        print("Coleção io_types já possui documentos.")

    print("Setup concluído!")

if __name__ == "__main__":
    main() 