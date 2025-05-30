import json
import re
from pydantic import BaseModel
from langchain_core.messages import AIMessage

from langflow.base.models.chat_result import get_chat_result
from langflow.custom import Component
from langflow.helpers.base_model import build_model_from_schema
from langflow.io import (
    HandleInput,
    MessageTextInput,
    MultilineInput,
    Output,
)
from langflow.schema.data import Data
from langflow.schema.dataframe import DataFrame


class StructuredOutputComponent(Component):
    display_name = "Classificador de Regras"
    description = (
        "Analisa mensagens e gera o JSON estruturado do classificador de regras "
        "conforme especificado no arquivo classificador_regras.txt."
    )
    name = "StructuredOutput"
    icon = "braces"

    inputs = [
        HandleInput(
            name="llm",
            display_name="Language Model",
            info="O modelo de linguagem para gerar o JSON do classificador.",
            input_types=["LanguageModel"],
            required=True,
        ),
        MessageTextInput(
            name="input_value",
            display_name="Mensagem de Entrada",
            info="A mensagem do usuário para ser analisada.",
            tool_mode=True,
            required=True,
        ),
        MultilineInput(
            name="system_prompt",
            display_name="Instruções Básicas",
            info="Instruções básicas para o LLM - as instruções detalhadas vêm via input_value.",
            value=(
                "Você é um assistente especializado em classificação de perguntas e geração de JSON estruturado. "
                "Analise cuidadosamente todas as informações fornecidas na mensagem do usuário e retorne "
                "exatamente o JSON solicitado, sem texto adicional."
            ),
            required=True,
        ),
    ]

    outputs = [
        Output(
            name="structured_output_dataframe",
            display_name="DataFrame",
            method="as_dataframe",
        ),
        Output(
            name="structured_output_json",
            display_name="JSON Estruturado",
            method="as_json_data",
        ),
    ]

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extrai JSON válido de um texto, mesmo se houver texto adicional.
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Primeiro, tenta o texto completo como JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Se falhar, procura por um bloco JSON no texto
        # Procura por padrões como ```json ou ```
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*?\})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # Se ainda não encontrou, tenta encontrar entre chaves balanceadas
        start_idx = text.find('{')
        if start_idx != -1:
            brace_count = 0
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(text[start_idx:i+1])
                        except json.JSONDecodeError:
                            continue
        
        raise ValueError("Nenhum JSON válido encontrado no texto")

    def _validate_classificador_json(self, data: dict) -> dict:
        """
        Valida e garante que o JSON tem a estrutura correta do classificador.
        """
        required_fields = [
            "message", "classificador_pergunta", "foco_analise", 
            "dynamic_agent_prompt", "rerank_pesos", "search_instruction", 
            "temporal_constraints"
        ]
        
        # Verifica se todos os campos obrigatórios estão presentes
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado no JSON")
        
        # Valida tipos específicos
        if not isinstance(data["classificador_pergunta"], list):
            raise ValueError("classificador_pergunta deve ser uma lista")
        
        if not isinstance(data["rerank_pesos"], dict):
            raise ValueError("rerank_pesos deve ser um objeto")
        
        if "lexical" not in data["rerank_pesos"] or "semantic" not in data["rerank_pesos"]:
            raise ValueError("rerank_pesos deve conter 'lexical' e 'semantic'")
        
        if not isinstance(data["search_instruction"], dict):
            raise ValueError("search_instruction deve ser um objeto")
        
        return data

    def _get_llm_response(self) -> str:
        """
        Chama o LLM diretamente e retorna a resposta como string.
        O input_value já contém todas as instruções e dados necessários.
        """
        # Cria uma mensagem simples para o LLM
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self.input_value)  # input_value já contém tudo estruturado
        ]
        
        # Chama o LLM diretamente
        response = self.llm.invoke(messages)
        
        # Extrai o conteúdo da resposta
        if isinstance(response, AIMessage):
            return response.content
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)

    def as_dataframe(self) -> DataFrame:
        try:
            # Obter resposta do LLM
            llm_response = self._get_llm_response()
            
            # Extrair JSON da resposta
            json_data = self._extract_json_from_text(llm_response)
            
            # Validar estrutura do JSON
            validated_json = self._validate_classificador_json(json_data)
            
            # Retornar DataFrame com o JSON válido
            return DataFrame(data=[validated_json])
            
        except Exception as e:
            # Em caso de erro, retorna DataFrame com informações de debug
            error_data = {
                "error": str(e),
                "error_type": type(e).__name__,
                "raw_response": getattr(self, '_last_llm_response', 'N/A')[:500],
                "input_message": self.input_value[:200] if self.input_value else 'N/A'
            }
            return DataFrame(data=[error_data])

    def as_json_data(self) -> Data:
        """
        Retorna o JSON validado como um objeto Data estruturado.
        """
        try:
            # Obter resposta do LLM
            llm_response = self._get_llm_response()
            
            # Extrair JSON da resposta
            json_data = self._extract_json_from_text(llm_response)
            
            # Validar estrutura do JSON
            validated_json = self._validate_classificador_json(json_data)
            
            # Retornar Data com o JSON válido
            return Data(data=validated_json)
            
        except Exception as e:
            # Em caso de erro, retorna Data com informações de debug
            error_data = {
                "error": str(e),
                "error_type": type(e).__name__,
                "raw_response": getattr(self, '_last_llm_response', 'N/A')[:500],
                "input_message": self.input_value[:200] if self.input_value else 'N/A'
            }
            return Data(data=error_data)
