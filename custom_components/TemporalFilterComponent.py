from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from langflow.custom import Component
from langflow.io import HandleInput, StrInput, Output, MessageTextInput
from langflow.schema import Data
from langflow.schema.message import Message
from langflow.field_typing import LanguageModel

class TemporalFilterComponent(Component):
    display_name = "Filtro Temporal Inteligente com LLM"
    description = "Aplica filtragem temporal em chunks do MongoDB usando um LLM para interpretar restrições."
    icon = "clock-play"
    name = "TemporalFilterLLM"

    inputs = [
        HandleInput(
            name="input_chunks",
            display_name="Chunks de Entrada",
            info="Lista de chunks retornados pela busca lexical (Data object)",
            input_types=["Data"],
            required=True,
        ),
        HandleInput(
            name="temporal_constraints",
            display_name="Restrições Temporais (Prompt para LLM)",
            info="Texto descritivo das restrições temporais, usado como prompt para o LLM (Data object ou string)",
            input_types=["Data", "str"],
            required=True,
        ),
        MessageTextInput(
            name="current_date",
            display_name="Data Atual",
            info="Data atual no formato YYYY-MM-DD. Pode ser uma variável como {{current_date_component.current_date}}.",
            required=True,
        ),
        HandleInput(
            name="llm_model",
            display_name="Modelo LLM para Filtragem",
            info="LLM configurado para realizar a filtragem temporal baseada nas constraints.",
            input_types=["LanguageModel"],
            required=True,
        )
    ]

    outputs = [
        Output(name="filtered_chunks", display_name="Chunks Filtrados pelo LLM", method="filter_chunks_with_llm"),
        Output(name="debug_output", display_name="Saída de Debug", method="get_debug_info"),
    ]

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._debug_info: Dict[str, Any] = {}

    def _parse_date_expression(self, expr: str, current_date: datetime) -> Optional[Dict[str, datetime]]:
        """Interpreta expressões temporais relativas."""
        try:
            if "semana passada" in expr.lower():
                end = current_date - timedelta(days=current_date.weekday())
                start = end - timedelta(days=7)
                return {"start": start, "end": end}
            
            if "últimos 2 meses" in expr.lower():
                end = current_date
                start = current_date - timedelta(days=60)
                return {"start": start, "end": end}
            
            if "última" in expr.lower():
                # Para "última reunião", "última ata", etc., retornamos None
                # pois precisaremos ordenar por data e pegar o mais recente
                return None
            
            # Adicionar mais padrões conforme necessário
            return None
            
        except Exception as e:
            self.status = f"Erro ao interpretar expressão temporal: {str(e)}"
            return None

    def _group_by_event_id(self, chunks: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa chunks pelo ID do evento/documento."""
        grouped = {}
        for chunk in chunks:
            event_id = chunk.get('id_reuniao') or chunk.get('id')  # Tenta ambos os campos
            if event_id:
                if event_id not in grouped:
                    grouped[event_id] = []
                grouped[event_id].append(chunk)
        return grouped

    def _call_llm(self, llm: LanguageModel, prompt: str) -> str:
        """Chama o modelo LLM com o prompt fornecido."""
        # Tenta diferentes métodos de chamada comuns em componentes Langflow LLM
        try:
            if hasattr(llm, 'invoke') and callable(llm.invoke):
                response = llm.invoke(prompt)
            elif hasattr(llm, 'predict') and callable(llm.predict):
                response = llm.predict(prompt)
            elif callable(llm):
                response = llm(prompt)
            else:
                raise ValueError("Modelo LLM não possui um método de chamada reconhecido (invoke, predict ou __call__).")
            
            if hasattr(response, 'content'): # Comum em modelos de chat (ex: AIMessage)
                return str(response.content)
            return str(response)
            
        except Exception as e:
            self._debug_info["llm_call_error"] = str(e)
            self.status = f"Erro ao chamar LLM: {str(e)}"
            # Retorna uma string vazia ou lança exceção para ser capturada acima
            raise # Re-levanta a exceção para ser tratada no método principal

    def _prepare_llm_input(self, chunks: List[Dict], constraints: str, current_date_str: str) -> str:
        """
        Prepara o prompt para o LLM, combinando as restrições, a data atual e metadados dos chunks.
        """
        
        chunks_for_llm = []
        for chunk in chunks:
            resumo_text = chunk.get('resumo', '') 
            metadata_chunk = {
                "_id": chunk.get('_id'),
                "atualizado_em": chunk.get('atualizado_em'),
                "id_reuniao": chunk.get('id_reuniao'),
                "id_documento": chunk.get('id'),
                "classificacao": chunk.get('classificacao'),
                "resumo": resumo_text
            }
            chunks_for_llm.append({k: v for k, v in metadata_chunk.items() if v is not None})

        chunks_json_for_llm = json.dumps(chunks_for_llm, indent=2, ensure_ascii=False)
        
        prompt = f"""Você é um especialista em análise temporal de documentos.
Sua tarefa é filtrar uma lista de METADADOS de 'chunks' de documentos com base em 'restrições temporais' e uma 'data atual de referência'.

Data Atual de Referência: {current_date_str}

Restrições Temporais a serem aplicadas:
{constraints}

Lista de METADADOS dos Chunks (em formato JSON) para análise:
Cada objeto na lista representa um chunk e contém os seguintes campos (alguns podem ser omitidos se não aplicáveis ao chunk):
- _id: Identificador único do chunk (gerado pelo sistema).
- atualizado_em: Data/hora da última atualização do chunk/documento (formato ISO).
- id_reuniao: Identificador do evento de reunião ao qual o chunk pertence (se aplicável).
- id_documento: Identificador principal do documento/evento ao qual o chunk pertence.
- classificacao: Classificação do tipo de documento/evento (ex: 'ata', 'relatorio', 'documento').
- resumo: O resumo completo do documento ao qual o chunk pertence. (Campo chave: 'resumo')

{chunks_json_for_llm}

Instruções:
1. Analise CUIDADOSAMENTE as 'Restrições Temporais'.
2. Utilize a 'Data Atual de Referência' para resolver quaisquer referências relativas (ex: "semana passada", "últimos 3 meses") e aplique-as ao campo 'atualizado_em' dos metadados dos chunks.
3. Considere os campos 'id_documento' (ou 'id_reuniao') e 'classificacao' dos metadados para identificar e agrupar chunks que pertencem ao mesmo evento/documento, conforme as 'Restrições Temporais' (ex: "última reunião com classificação 'ata'").
4. Se as restrições mencionam "último evento" ou similar, você deve identificar o evento (usando 'id_documento' ou 'id_reuniao', agrupando por características e 'atualizado_em') que é o mais recente e, então, selecionar TODOS os metadados de chunks que pertencem a ESSE evento específico.
5. Sua saída deve ser EXCLUSIVAMENTE uma string JSON contendo a lista dos OBJETOS DE METADADOS (exatamente como fornecidos na entrada, mas apenas os selecionados) que satisfazem as restrições. Mantenha a estrutura dos objetos de metadados selecionados.
   - Se nenhum chunk atender aos critérios, retorne uma lista JSON vazia: [].
   - Não adicione nenhuma explicação, introdução, conclusão ou qualquer texto fora do JSON da lista de metadados.

Exemplo de Saída Esperada (somente a string JSON da lista de METADADOS de chunks filtrados):
[
  {{ "_id": "chunk_xyz123", "atualizado_em": "2024-08-20T10:00:00Z", "id_documento": "doc_evento_A", "resumo": "Este é o resumo do documento A..." }},
  {{ "_id": "chunk_abc789", "atualizado_em": "2024-08-20T10:00:00Z", "id_documento": "doc_evento_A", "resumo": "Este é o resumo do documento A..." }}
]
"""
        return prompt

    def filter_chunks_with_llm(self) -> Data:
        self._debug_info = {}
        original_chunks_map: Dict[str, Dict[str, Any]] = {} # Para mapear IDs de volta para chunks completos

        try:
            input_data = self.input_chunks
            if not isinstance(input_data, Data) or not isinstance(input_data.data, dict):
                self.status = "Erro: Input chunks deve ser um objeto Data contendo um dicionário."
                self._debug_info["error"] = self.status
                return Data(data={"results": [], "error": self.status})
            
            raw_chunks: List[Dict[str, Any]] = input_data.data.get("results", [])
            if not raw_chunks:
                self.status = "Nenhum chunk para filtrar."
                self._debug_info["message"] = self.status
                return Data(data={"results": [], "message": self.status})
            
            # Criar mapa dos chunks originais para fácil recuperação e garantir que _id seja string
            for chunk_item in raw_chunks:
                chunk_id = chunk_item.get('_id')
                if chunk_id is not None:
                    original_chunks_map[str(chunk_id)] = chunk_item 
                else:
                    # Se não houver _id, não poderemos mapear de volta. Poderíamos gerar um ID temporário
                    # ou alertar. Por ora, vamos pular chunks sem ID para a filtragem LLM.
                    self._debug_info.setdefault("warnings", []).append(f"Chunk sem _id encontrado: {str(chunk_item)[:100]}...")
            
            # Usar apenas os chunks que têm _id para a preparação do prompt
            chunks_with_ids_for_prompt = [ch for ch in raw_chunks if ch.get('_id') is not None]
            if not chunks_with_ids_for_prompt:
                self.status = "Nenhum chunk com _id encontrado para processamento."
                return Data(data={"results": [], "message": self.status})

            self._debug_info["original_chunk_count"] = len(raw_chunks)
            self._debug_info["chunks_sent_to_llm_preparation_count"] = len(chunks_with_ids_for_prompt)

            constraints_input = self.temporal_constraints
            if isinstance(constraints_input, Data) and isinstance(constraints_input.data, dict):
                constraints_text: str = constraints_input.data.get("temporal_constraints", "")
            elif isinstance(constraints_input, str):
                constraints_text: str = constraints_input
            else:
                constraints_text: str = str(constraints_input.data if isinstance(constraints_input, Data) else constraints_input)

            if not constraints_text or constraints_text.strip().lower() == "nenhuma restrição temporal específica identificada":
                self.status = "Nenhuma restrição temporal aplicável. Retornando todos os chunks originais."
                self._debug_info["message"] = self.status
                return Data(data={"results": raw_chunks, "message": self.status})
            self._debug_info["temporal_constraints_received"] = constraints_text
            
            current_date_str: str = self.current_date 
            try:
                datetime.strptime(current_date_str, "%Y-%m-%d")
            except ValueError:
                self.status = "Erro: Data atual deve estar no formato YYYY-MM-DD."
                self._debug_info["error"] = self.status
                return Data(data={"results": [], "error": self.status})
            self._debug_info["current_date_received"] = current_date_str

            llm_prompt = self._prepare_llm_input(chunks_with_ids_for_prompt, constraints_text, current_date_str)
            self._debug_info["llm_prompt"] = llm_prompt
            
            # Chamar o LLM conectado
            # self.llm_model é agora uma instância de LanguageModel
            if not hasattr(self, 'llm_model') or self.llm_model is None:
                self.status = "Erro: Modelo LLM para Filtragem não foi fornecido ou não está conectado."
                self._debug_info["error"] = self.status
                return Data(data={"results": [], "error": self.status})

            llm_response_text = self._call_llm(self.llm_model, llm_prompt)
            self._debug_info["llm_response_raw"] = llm_response_text
            
            filtered_metadata_from_llm: List[Dict[str,Any]]
            try:
                raw_json_response = llm_response_text
                if "```json" in raw_json_response:
                    raw_json_response = raw_json_response.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_json_response: # Genérico para ``` .... ```
                    raw_json_response = raw_json_response.split("```")[1].strip()
                
                parsed_response = json.loads(raw_json_response)
                if not isinstance(parsed_response, list):
                    raise ValueError("LLM não retornou uma lista JSON.")
                filtered_metadata_from_llm = parsed_response

            except json.JSONDecodeError as jde:
                self.status = f"Erro: LLM retornou uma resposta que não é JSON válido. Detalhes: {str(jde)}"
                self._debug_info["error"] = self.status
                self._debug_info["llm_response_error_details"] = llm_response_text
                return Data(data={"results": [], "error": self.status})
            except ValueError as ve:
                self.status = f"Erro ao processar resposta do LLM: {str(ve)}"
                self._debug_info["error"] = self.status
                self._debug_info["llm_response_error_details"] = llm_response_text
                return Data(data={"results": [], "error": self.status})
            
            # Mapear os metadados filtrados de volta para os chunks originais completos
            final_filtered_chunks: List[Dict[str, Any]] = []
            processed_ids_from_llm = set()

            for item_meta in filtered_metadata_from_llm:
                if not isinstance(item_meta, dict):
                    self._debug_info.setdefault("warnings", []).append(f"Item não-dicionário na resposta do LLM: {item_meta}")
                    continue
                
                llm_item_id = item_meta.get('_id')
                if llm_item_id is not None:
                    # Garantir que o ID seja string para correspondência com as chaves do mapa
                    llm_item_id_str = str(llm_item_id)
                    if llm_item_id_str in original_chunks_map and llm_item_id_str not in processed_ids_from_llm:
                        final_filtered_chunks.append(original_chunks_map[llm_item_id_str])
                        processed_ids_from_llm.add(llm_item_id_str)
                    else:
                        self._debug_info.setdefault("warnings", []).append(f"ID {llm_item_id_str} da resposta do LLM não encontrado nos chunks originais ou já processado.")
                else:
                    self._debug_info.setdefault("warnings", []).append(f"Item da resposta do LLM sem _id: {item_meta}")

            self._debug_info["filtered_chunk_count_from_llm_metadata"] = len(filtered_metadata_from_llm)
            self._debug_info["final_mapped_chunk_count"] = len(final_filtered_chunks)
            
            result_message = f"Filtragem com LLM resultou em {len(final_filtered_chunks)} chunks."
            self.status = result_message
            self._debug_info["final_message"] = result_message
            
            return Data(data={
                "results": final_filtered_chunks, 
                "message": result_message,
                "applied_constraints_summary": constraints_text[:200] + "..." if len(constraints_text) > 200 else constraints_text
            })

        except Exception as e:
            error_msg = f"Erro crítico no TemporalFilterComponent: {str(e)}"
            self.status = error_msg
            self._debug_info["critical_error"] = error_msg
            import traceback
            self._debug_info["traceback"] = traceback.format_exc()
            return Data(data={"results": [], "error": error_msg})

    def get_debug_info(self) -> Data:
        """Retorna informações de debug da última execução."""
        return Data(data=self._debug_info, display="Debug Info") 