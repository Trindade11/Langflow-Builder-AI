import json
from pymongo import MongoClient
from langflow.custom import Component
from langflow.io import SecretStrInput, StrInput, Output
from langflow.schema import Data

class MongoDBCollectionCounter(Component):
    display_name = "Contador de Documentos MongoDB"
    description = "Conta o número total de documentos em uma coleção MongoDB e mostra uma amostra."
    icon = "MongoDB"
    name = "MongoDBCounter"

    inputs = [
        SecretStrInput(
            name="mongodb_uri",
            display_name="MongoDB URI",
            required=True,
        ),
        StrInput(
            name="db_name",
            display_name="Database",
            value="DeepContext",
            required=True,
        ),
        StrInput(
            name="collection_name",
            display_name="Collection",
            value="knowledge_context",
            required=True,
        )
    ]

    outputs = [
        Output(name="count_results", display_name="Resultados da Contagem", method="count_documents"),
    ]

    def count_documents(self) -> Data:
        try:
            # Conecta ao MongoDB
            client = MongoClient(self.mongodb_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            
            # Conta total de documentos
            total_count = collection.count_documents({})
            
            # Pega uma pequena amostra para visualização
            sample_docs = list(collection.find({}).limit(3))
            
            # Converte ObjectId para string nos documentos da amostra
            for doc in sample_docs:
                doc['_id'] = str(doc['_id'])
            
            # Conta documentos por classificação
            pipeline = [
                {"$group": {"_id": "$classificacao", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            classificacao_counts = list(collection.aggregate(pipeline))
            
            result = {
                "total_documentos": total_count,
                "contagem_por_classificacao": classificacao_counts,
                "amostra_documentos": sample_docs,
                "mensagem": f"Total de {total_count} documentos encontrados na coleção {self.collection_name}"
            }
            
            self.status = f"Contagem concluída: {total_count} documentos"
            return Data(data=result)
            
        except Exception as e:
            self.status = f"Erro ao contar documentos: {str(e)}"
            return Data(data={"error": str(e)}) 