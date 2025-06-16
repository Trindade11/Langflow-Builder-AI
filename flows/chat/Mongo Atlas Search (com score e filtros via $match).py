import json
import re
from typing import List, Union, Dict, Any

from pymongo import MongoClient
from langflow.custom import Component
from langflow.inputs import (
    SecretStrInput,
    StrInput,
    IntInput,
    MultilineInput,
    HandleInput,
    DataInput,
)
from langflow.schema import Data, Message
from langflow.template import Output


class MongoAtlasSearchWithFilters(Component):
    display_name = "Mongo Atlas Search Avançado (com search_instruction, setor e status)"
    icon = "MongoDB"
    description = "Busca em Atlas Search utilizando 'search_instruction' JSON, com filtros de governança por setor e status."

    inputs = [
        SecretStrInput(
            name="mongodb_uri",
            display_name="MongoDB URI",
            required=True,
        ),
        StrInput(
            name="db_name",
            display_name="Database",
            required=True,
        ),
        StrInput(
            name="collection_name",
            display_name="Collection",
            required=True,
        ),
        StrInput(
            name="index_name",
            display_name="Atlas Index Name",
            value="default_knowledge_context",
            required=True,
        ),
        DataInput(
            name="search_instruction_data",
            display_name="Search Instruction (Data Object)",
            info="Objeto Data contendo o JSON/dicionário com as instruções de busca.",
            input_types=["Data"],
            required=True,
        ),
        MultilineInput(
            name="user_sector",
            display_name="Filtro de Setor do Usuário (Obrigatório)",
            value='[]',
            info='Array JSON de setores permitidos. Ex.: ["Risco"]. Garante governança.',
            required=True,
        ),
        StrInput(
            name="doc_status",
            display_name="Filtro de Status do Documento",
            value='ativo',
            info='Status do documento para filtrar (ex: "ativo", "revisão"). Deixe vazio para não filtrar por status.',
            required=False,
        ),
        MultilineInput(
            name="min_score_fallback",
            display_name="Score Mínimo (Fallback)",
            value="0.0",
            info="Score mínimo. Usado se não especificado em search_instruction.",
            required=False,
        ),
        IntInput(
            name="limit_fallback",
            display_name="Result Limit (Fallback)",
            value=20,
            info="Limite de resultados. Usado se não especificado em search_instruction.",
            required=False,
        ),
    ]

    outputs = [
        Output(
            name="results",
            display_name="Search Results",
            method="search_documents",
        ),
    ]

    def _parse_user_sector(self) -> List[str]:
        """Parse the user_sector input into a list of strings."""
        sectors = []
        raw_sectors = self.user_sector
        if isinstance(raw_sectors, str) and raw_sectors.strip():
            try:
                parsed_sectors = json.loads(raw_sectors)
                if isinstance(parsed_sectors, list):
                    sectors = [str(s).strip() for s in parsed_sectors if str(s).strip()]
                elif isinstance(parsed_sectors, str) and parsed_sectors.strip():
                    sectors = [parsed_sectors.strip()]
            except json.JSONDecodeError:
                sectors = [s.strip() for s in raw_sectors.split(',') if s.strip()]
        elif isinstance(raw_sectors, list):
            sectors = [str(s).strip() for s in raw_sectors if str(s).strip()]
        
        return sectors

    def _parse_search_instruction_from_data(self) -> Dict[str, Any]:
        """Parse and validate the search_instruction from Data object."""
        raw_instruction = self.search_instruction_data

        if not raw_instruction or not hasattr(raw_instruction, 'data'):
            self.status = "Search instruction Data object não recebido ou inválido."
            return {}
        
        instruction_payload = raw_instruction.data

        if isinstance(instruction_payload, dict):
            return instruction_payload
        elif isinstance(instruction_payload, str):
            try:
                loaded_instruction = json.loads(instruction_payload)
                if isinstance(loaded_instruction, dict):
                    return loaded_instruction
                else:
                    self.status = "Search instruction (string JSON) não resultou em um dicionário."
                    return {}
            except json.JSONDecodeError as e:
                self.status = f"Falha ao decodificar string JSON da search_instruction: {e}"
                return {}
        else:
            self.status = f"Conteúdo da search_instruction (Data.data) não é dict nem string JSON. Tipo: {type(instruction_payload)}"
            return {}

    def _build_search_pipeline(self, instruction: Dict[str, Any], user_allowed_sectors: List[str], doc_status_filter: str) -> List[Dict[str, Any]]:
        """Builds the MongoDB aggregation pipeline with search_instruction, sector, and status filters."""
        pipeline: List[Dict[str, Any]] = []
        
        if "search_clause" not in instruction or not isinstance(instruction["search_clause"], dict):
            self.status = "Erro: 'search_clause' não fornecida ou inválida."
            raise ValueError("A 'search_clause' é obrigatória na search_instruction.")

        search_stage = {
            "$search": {
                "index": self.index_name,
                **instruction["search_clause"]
            }
        }
        pipeline.append(search_stage)

        pipeline.append({
            "$set": {
                "search_score": {"$meta": "searchScore"}
            }
        })

        min_score_val = instruction.get("min_score", self.min_score_fallback)
        min_score = 0.0
        if isinstance(min_score_val, (float, int)):
            min_score = float(min_score_val)
        elif isinstance(min_score_val, str):
            try:
                min_score = float(min_score_val.strip())
            except ValueError:
                self.status += " Alerta: min_score inválido, usando 0.0."
        
        if min_score > 0:
            pipeline.append({"$match": {"search_score": {"$gte": min_score}}})
        
        if user_allowed_sectors:
            pipeline.append({"$match": {"setores": {"$in": user_allowed_sectors}}})

        if doc_status_filter:
            pipeline.append({"$match": {"status": doc_status_filter}})

        if "filter_stages" in instruction and isinstance(instruction["filter_stages"], list):
            for match_filter in instruction["filter_stages"]:
                if isinstance(match_filter, dict) and match_filter: 
                    pipeline.append({"$match": match_filter})
        
        sort_stage_val = instruction.get("sort_stage")
        if isinstance(sort_stage_val, dict) and sort_stage_val:
            pipeline.append({"$sort": sort_stage_val})
        else: 
            pipeline.append({"$sort": {"search_score": -1}})

        limit_val = instruction.get("limit", self.limit_fallback)
        limit = 0
        if isinstance(limit_val, int) and limit_val > 0:
            limit = limit_val
        elif isinstance(limit_val, str):
            try:
                limit = int(limit_val.strip())
            except ValueError:
                self.status += f" Alerta: limit inválido, usando fallback {self.limit_fallback} se positivo."
                if self.limit_fallback > 0: limit = self.limit_fallback
        
        if limit > 0 :
            pipeline.append({"$limit": limit})

        projection = instruction.get("projection_stage", {
            "_id": 1, "score": "$search_score", "text": 1, "resumo": 1, "descricao": 1,
            "setores": 1, "status": 1, "classificacao": 1, "tipo": 1, "atualizado_em": 1,
            "participantes_internos": 1, "participantes_externos": 1, "id_reuniao": 1
        })
        if isinstance(projection, dict) and projection:
            pipeline.append({"$project": projection})

        return pipeline

    def search_documents(self) -> Data:
        parsed_instruction = self._parse_search_instruction_from_data()
        if not parsed_instruction: 
            return Data(data={"results": [], "error": self.status or "Invalid search_instruction Data object."})

        user_sectors = self._parse_user_sector()
        doc_status_to_filter = self.doc_status.strip() if self.doc_status else ""

        try:
            pipeline = self._build_search_pipeline(parsed_instruction, user_sectors, doc_status_to_filter)
        except ValueError as e: 
             self.status = str(e)
             return Data(data={"results": [], "error": str(e)})

        if not pipeline: 
            self.status = "Pipeline de busca não pôde ser construída."
            return Data(data={"results": [], "error": self.status})
        
        collection = MongoClient(self.mongodb_uri)[self.db_name][self.collection_name]

        try:
            results = list(collection.aggregate(pipeline))
            for doc in results:
                doc["_id"] = str(doc["_id"])
                if "score" in doc and doc["score"] is not None:
                    try:
                        doc["score"] = float(doc["score"])
                    except (ValueError, TypeError):
                        doc["score"] = 0.0 
                else:
                    doc["score"] = 0.0
            
            self.status = f"Encontrados {len(results)} resultado(s)."
            return Data(data={"results": results, "pipeline_used": pipeline})
        except Exception as e:
            self.status = f"Erro na busca: {str(e)}"
            return Data(data={"results": [], "error": str(e), "pipeline_attempted": pipeline})