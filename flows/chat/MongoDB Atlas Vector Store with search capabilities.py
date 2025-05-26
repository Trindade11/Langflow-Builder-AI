import tempfile
import time
from typing import Any, Dict, List, Optional

import certifi
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from langchain_community.vectorstores import MongoDBAtlasVectorSearch

from langflow.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from langflow.helpers.data import docs_to_data
from langflow.io import (
    BoolInput,
    DropdownInput,
    HandleInput,
    IntInput,
    SecretStrInput,
    StrInput,
)
from langflow.schema import Data


class MongoVectorStoreComponent(LCVectorStoreComponent):
    display_name = "MongoDB Atlas"
    description = "MongoDB Atlas Vector Store with search capabilities"
    name = "MongoDBAtlasVector"
    icon = "MongoDB"
    INSERT_MODES = ["append", "overwrite"]
    SIMILARITY_OPTIONS = ["cosine", "euclidean", "dotProduct"]
    QUANTIZATION_OPTIONS = ["scalar", "binary"]

    inputs = [
        SecretStrInput(
            name="mongodb_atlas_cluster_uri",
            display_name="MongoDB Atlas Cluster URI",
            required=True,
        ),
        BoolInput(
            name="enable_mtls",
            display_name="Enable mTLS",
            value=False,
            advanced=True,
            required=True,
        ),
        SecretStrInput(
            name="mongodb_atlas_client_cert",
            display_name="MongoDB Atlas Combined Client Certificate",
            required=False,
            advanced=True,
            info="Client certificate + private key PEM, if using mTLS.",
        ),
        StrInput(name="db_name", display_name="Database Name", required=True),
        StrInput(name="collection_name", display_name="Collection Name", required=True),
        StrInput(
            name="index_name",
            display_name="Index Name",
            required=True,
            info="Name of the Atlas Search vector index.",
        ),
        *LCVectorStoreComponent.inputs,
        DropdownInput(
            name="insert_mode",
            display_name="Insert Mode",
            options=INSERT_MODES,
            value=INSERT_MODES[0],
            advanced=True,
            info="How to insert new documents (append or overwrite).",
        ),
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            value=20,
            advanced=True,
        ),
        MultilineInput(
            name="setores",
            display_name="Filtro por Setores",
            info="Lista de setores para filtrar (ex: ['Risco', 'Operacional']).",
            advanced=True,
            required=False,
        ),
        StrInput(
            name="min_similarity_score",
            display_name="Score Mínimo de Similaridade",
            info="Filtra resultados abaixo deste score (0.0-1.0).",
            advanced=True,
            required=False,
        ),
        IntInput(
            name="number_dimensions",
            display_name="Number of Dimensions",
            value=1536,
            advanced=True,
            required=True,
        ),
        DropdownInput(
            name="similarity",
            display_name="Similarity",
            options=SIMILARITY_OPTIONS,
            value=SIMILARITY_OPTIONS[0],
            advanced=True,
        ),
        DropdownInput(
            name="quantization",
            display_name="Quantization",
            options=QUANTIZATION_OPTIONS,
            value=None,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> MongoDBAtlasVectorSearch:
        # Configura cliente MongoDB, com mTLS se habilitado
        client_cert_path = None
        if self.enable_mtls and self.mongodb_atlas_client_cert:
            pem = self.mongodb_atlas_client_cert.strip().replace(" ", "\n")
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(pem.encode("utf-8"))
                client_cert_path = tmp.name

        client = (
            MongoClient(
                self.mongodb_atlas_cluster_uri,
                tls=True,
                tlsCertificateKeyFile=client_cert_path,
                tlsCAFile=certifi.where(),
            )
            if self.enable_mtls
            else MongoClient(self.mongodb_atlas_cluster_uri)
        )
        collection = client[self.db_name][self.collection_name]

        # Prepara documentos
        docs: List[Any] = []
        for item in (self._prepare_ingest_data() or []):
            docs.append(item.to_lc_document() if isinstance(item, Data) else item)

        if docs:
            if self.insert_mode == "overwrite":
                collection.delete_many({})
            return MongoDBAtlasVectorSearch.from_documents(
                documents=docs,
                embedding=self.embedding,
                collection=collection,
                index_name=self.index_name,
            )

        return MongoDBAtlasVectorSearch(
            embedding=self.embedding,
            collection=collection,
            index_name=self.index_name,
        )

    def _parse_setores(self, raw: Optional[str]) -> Optional[List[str]]:
        if not raw or not raw.strip():
            return None
        try:
            import ast
            raw = raw.strip()
            if raw.startswith('[') and raw.endswith(']'):
                parsed = ast.literal_eval(raw)
                return [str(x) for x in parsed] if isinstance(parsed, list) else None
            if ',' in raw:
                return [x.strip().strip("'\"") for x in raw.split(',')]
            return [raw.strip().strip("'\"")]
        except Exception:
            return None

    def _create_setores_filter(self, setores: Optional[List[str]]) -> Optional[Dict[str, Any]]:
        if not setores:
            return None
        return {"setores": {"$in": setores}}

    def search_documents(self) -> List[Data]:
        vs = self.build_vector_store()
        self.verify_search_index(vs._collection)

        if not isinstance(self.search_query, str) or not self.search_query:
            return []

        # Define número de resultados
        k = self.number_of_results

        setores_list = self._parse_setores(self.setores)
        mongo_filter = self._create_setores_filter(setores_list)

        try:
            if mongo_filter:
                docs_scores = vs.similarity_search_with_score(
                    query=self.search_query,
                    k=k,
                    filter=mongo_filter,
                )
            else:
                docs_scores = vs.similarity_search_with_score(
                    query=self.search_query,
                    k=k,
                )
        except TypeError:
            # Fallback manual
            all_scores = vs.similarity_search_with_score(query=self.search_query, k=k*3)
            docs_scores = [item for item in all_scores if self._matches_setores(item[0], setores_list)][:k]

        # Filtra por score mínimo
        if self.min_similarity_score:
            try:
                min_s = float(self.min_similarity_score)
                filtered = []
                for doc, score in docs_scores:
                    sim = (1/(1+score)) if self.similarity == "euclidean" else score
                    if sim >= min_s:
                        filtered.append((doc, score))
                docs_scores = filtered
            except ValueError:
                pass

        # Prepara dados de saída
        processed = []
        for entry in docs_scores:
            doc, score = entry if isinstance(entry, tuple) else (entry, None)
            if score is not None:
                doc.metadata['similarity_score'] = float(score)
            doc.metadata = {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.metadata.items()}
            processed.append(doc)

        data = docs_to_data(processed)
        self.status = data
        return data

    def _matches_setores(self, doc: Data, setores_list: Optional[List[str]]) -> bool:
        if not setores_list:
            return True
        val = doc.metadata.get('setores')
        if isinstance(val, list):
            return any(s in val for s in setores_list)
        return isinstance(val, str) and val in setores_list

    def verify_search_index(self, collection) -> None:
        indexes = collection.list_search_indexes()
        names = {idx['name']: idx['type'] for idx in indexes}
        if self.index_name not in names or names[self.index_name] != 'vectorSearch':
            fields = [
                {"type": "vector", "path": self.index_field, "numDimensions": self.number_dimensions, "similarity": self.similarity, "quantization": self.quantization},
                {"type": "filter", "path": "setores"},
            ]
            model = SearchIndexModel(definition={"fields": fields}, name=self.index_name, type="vectorSearch")
            collection.create_search_index(model)
            time.sleep(20)
