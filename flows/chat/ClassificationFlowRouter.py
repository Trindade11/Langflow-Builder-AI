import json
from typing import List, Dict, Any, Union

from langflow.custom import Component
from langflow.inputs import HandleInput # type: ignore
from langflow.schema import Data, Message # type: ignore
from langflow.template import Output # type: ignore


class ClassificationFlowRouter(Component):
    display_name = "Roteador de Fluxo por Classificação (com Stop)"
    description = (
        "Recebe o JSON do classificador e um array de setores, "
        "roteando os dados para saídas específicas e parando fluxos inativos."
    )
    icon = "git-merge"

    inputs = [
        HandleInput(
            name="classifier_output_json",
            display_name="JSON de Saída do Classificador",
            input_types=["Data", "str", "dict"],
            required=True,
            info="O JSON gerado pelo StructuredOutputComponent contendo a análise da pergunta."
        ),
        HandleInput(
            name="input_setores_array",
            display_name="Array de Setores de Entrada",
            input_types=["Data", "str", "list"],
            required=True,
            info='Array de strings com os setores. Ex: ["Apoio", "Sistemas"] ou como string JSON \'["Apoio", "Sistemas"]\''
        )
    ]

    outputs = [
        # Saídas para "corporativo_global"
        Output(name="message_global", display_name="[Global] Message", method="get_message_global_output"),
        Output(name="foco_analise_global", display_name="[Global] Foco Análise", method="get_foco_analise_global_output"),
        Output(name="rerank_pesos_global", display_name="[Global] Rerank Pesos", method="get_rerank_pesos_global_output"),
        Output(name="restricoes_temporais_global", display_name="[Global] Restrições Temporais", method="get_restricoes_temporais_global_output"),
        Output(name="setores_global", display_name="[Global] Setores (JSON Array)", method="get_setores_global_output"),

        # Saídas para "corporativo_local"
        Output(name="message_local", display_name="[Local] Message", method="get_message_local_output"),
        Output(name="foco_analise_local", display_name="[Local] Foco Análise", method="get_foco_analise_local_output"),
        Output(name="rerank_pesos_local", display_name="[Local] Rerank Pesos", method="get_rerank_pesos_local_output"),
        Output(name="restricoes_temporais_local", display_name="[Local] Restrições Temporais", method="get_restricoes_temporais_local_output"),
        Output(name="setores_local", display_name="[Local] Setores (JSON Array)", method="get_setores_local_output"),

        # Saídas para "casual"
        Output(name="message_casual", display_name="[Casual] Message", method="get_message_casual_output"),

        # Saídas para "internet"
        Output(name="message_internet", display_name="[Internet] Message", method="get_message_internet_output"),
        Output(name="foco_analise_internet", display_name="[Internet] Foco Análise", method="get_foco_analise_internet_output"),
    ]

    _processed_once: bool = False
    _classifier_data_parsed: Dict[str, Any] = {}
    _input_setores_json_str_parsed: str = "[]"
    _is_global_active: bool = False
    _is_local_active: bool = False
    _is_casual_active: bool = False
    _is_internet_active: bool = False

    def _parse_input_json(self, input_val: Union[Data, str, dict]) -> Dict[str, Any]:
        raw_parsed_dict = {}
        source_for_error_log = ""

        if isinstance(input_val, Data):
            source_data = input_val.data if hasattr(input_val, 'data') and input_val.data else input_val.text
            source_for_error_log = str(source_data)[:200] # Aumentar um pouco para logs mais úteis
            if isinstance(source_data, str):
                try:
                    raw_parsed_dict = json.loads(source_data)
                except json.JSONDecodeError:
                    pass # Error logged outside if raw_parsed_dict remains empty
            elif isinstance(source_data, dict):
                raw_parsed_dict = source_data
        elif isinstance(input_val, str):
            source_for_error_log = input_val[:200] # Aumentar um pouco para logs mais úteis
            try:
                raw_parsed_dict = json.loads(input_val)
            except json.JSONDecodeError:
                pass # Error logged outside if raw_parsed_dict remains empty
        elif isinstance(input_val, dict):
            raw_parsed_dict = input_val
        
        # Navegar para a estrutura aninhada correta
        parsed_dict = {}
        if raw_parsed_dict:
            try:
                parsed_dict = raw_parsed_dict.get("results", {}).get("messages", [{}])[0].get("content", {})
                if not parsed_dict and raw_parsed_dict: # Se content estiver vazio, mas o JSON original não.
                    self.status = f"Estrutura JSON recebida, mas 'results.messages[0].content' está vazia ou ausente. JSON recebido (início): {source_for_error_log}..."
            except (AttributeError, IndexError, TypeError) as e:
                 self.status = f"Erro ao acessar 'results.messages[0].content' no JSON. Verifique a estrutura. Erro: {e}. JSON (início): {source_for_error_log}..."
                 parsed_dict = {} # Garante que parsed_dict seja um dict para os setdefault abaixo
        
        if not parsed_dict and not self.status and source_for_error_log: # Log error if parsing failed and no specific error was set
             self.status = f"Erro ao decodificar JSON de entrada ou estrutura inesperada: {source_for_error_log}..."
        
        # Garantir campos default para evitar KeyErrors no dicionário 'content'
        parsed_dict.setdefault("message", "")
        parsed_dict.setdefault("classificador_pergunta", [])
        parsed_dict.setdefault("foco_analise", "")
        parsed_dict.setdefault("restricoes_temporais", {})
        parsed_dict.setdefault("rerank_pesos", {})
        return parsed_dict

    def _parse_setores_list_to_json_str(self, input_val: Union[Data, str, list]) -> str:
        setores_list: List[str] = []
        if isinstance(input_val, Data):
            source_data = input_val.data if hasattr(input_val, 'data') and input_val.data else input_val.text
            if isinstance(source_data, list):
                setores_list = [str(item).strip() for item in source_data]
            elif isinstance(source_data, str):
                try:
                    parsed = json.loads(source_data)
                    setores_list = [str(item).strip() for item in parsed] if isinstance(parsed, list) else ([str(parsed).strip()] if str(parsed).strip() else [])
                except json.JSONDecodeError:
                    setores_list = [s.strip() for s in source_data.split(",")] if "," in source_data else ([source_data.strip()] if source_data.strip() else [])
        elif isinstance(input_val, str):
            input_val = input_val.strip()
            if not input_val: return "[]"
            try:
                parsed = json.loads(input_val)
                setores_list = [str(item).strip() for item in parsed] if isinstance(parsed, list) else ([str(parsed).strip()] if str(parsed).strip() else [])
            except json.JSONDecodeError:
                setores_list = [s.strip() for s in input_val.split(",")] if "," in input_val else ([input_val] if input_val else [])
        elif isinstance(input_val, list):
            setores_list = [str(item).strip() for item in input_val]
        
        return json.dumps([s for s in setores_list if s])

    def _create_message(self, content: Any) -> Message:
        if isinstance(content, Message):
            return content
        text_content = json.dumps(content, ensure_ascii=False) if isinstance(content, (dict, list)) else str(content)
        return Message(text=text_content)

    def _ensure_processed(self):
        if self._processed_once:
            return

        self._classifier_data_parsed = self._parse_input_json(self.classifier_output_json)
        self._input_setores_json_str_parsed = self._parse_setores_list_to_json_str(self.input_setores_array)

        classificador_list = self._classifier_data_parsed.get("classificador_pergunta", [])
        
        self._is_global_active = "corporativo_global" in classificador_list
        self._is_local_active = "corporativo_local" in classificador_list
        self._is_casual_active = "casual" in classificador_list
        self._is_internet_active = "internet" in classificador_list
        
        active_paths_names = []
        if self._is_global_active: active_paths_names.append("Global")
        if self._is_local_active: active_paths_names.append("Local")
        if self._is_casual_active: active_paths_names.append("Casual")
        if self._is_internet_active: active_paths_names.append("Internet")

        if not self._classifier_data_parsed and not self.status: # Se _parse_input_json já não setou um erro
             self.status = "JSON do classificador inválido ou vazio. Todos os fluxos parados."
        elif active_paths_names:
            self.status = f"Roteando para: {', '.join(active_paths_names)}."
        else:
            self.status = "Nenhuma classificação ativa. Todos os fluxos parados."
            
        self._processed_once = True

    # --- Getters para "corporativo_global" ---
    def get_message_global_output(self) -> Message:
        self._ensure_processed()
        if self._is_global_active: return self._create_message(self._classifier_data_parsed.get("message"))
        self.stop("message_global"); return Message(text="")
    
    def get_foco_analise_global_output(self) -> Message:
        self._ensure_processed()
        if self._is_global_active: return self._create_message(self._classifier_data_parsed.get("foco_analise"))
        self.stop("foco_analise_global"); return Message(text="")

    def get_rerank_pesos_global_output(self) -> Message:
        self._ensure_processed()
        if self._is_global_active: return self._create_message(self._classifier_data_parsed.get("rerank_pesos"))
        self.stop("rerank_pesos_global"); return Message(text="")

    def get_restricoes_temporais_global_output(self) -> Message:
        self._ensure_processed()
        if self._is_global_active: return self._create_message(self._classifier_data_parsed.get("restricoes_temporais"))
        self.stop("restricoes_temporais_global"); return Message(text="")

    def get_setores_global_output(self) -> Message:
        self._ensure_processed()
        if self._is_global_active: return self._create_message(self._input_setores_json_str_parsed)
        self.stop("setores_global"); return Message(text="")

    # --- Getters para "corporativo_local" ---
    def get_message_local_output(self) -> Message:
        self._ensure_processed()
        if self._is_local_active: return self._create_message(self._classifier_data_parsed.get("message"))
        self.stop("message_local"); return Message(text="")

    def get_foco_analise_local_output(self) -> Message:
        self._ensure_processed()
        if self._is_local_active: return self._create_message(self._classifier_data_parsed.get("foco_analise"))
        self.stop("foco_analise_local"); return Message(text="")

    def get_rerank_pesos_local_output(self) -> Message:
        self._ensure_processed()
        if self._is_local_active: return self._create_message(self._classifier_data_parsed.get("rerank_pesos"))
        self.stop("rerank_pesos_local"); return Message(text="")

    def get_restricoes_temporais_local_output(self) -> Message:
        self._ensure_processed()
        if self._is_local_active: return self._create_message(self._classifier_data_parsed.get("restricoes_temporais"))
        self.stop("restricoes_temporais_local"); return Message(text="")

    def get_setores_local_output(self) -> Message:
        self._ensure_processed()
        if self._is_local_active: return self._create_message(self._input_setores_json_str_parsed)
        self.stop("setores_local"); return Message(text="")

    # --- Getters para "casual" ---
    def get_message_casual_output(self) -> Message:
        self._ensure_processed()
        if self._is_casual_active: return self._create_message(self._classifier_data_parsed.get("message"))
        self.stop("message_casual"); return Message(text="")

    # --- Getters para "internet" ---
    def get_message_internet_output(self) -> Message:
        self._ensure_processed()
        if self._is_internet_active: return self._create_message(self._classifier_data_parsed.get("message"))
        self.stop("message_internet"); return Message(text="")

    def get_foco_analise_internet_output(self) -> Message:
        self._ensure_processed()
        if self._is_internet_active: return self._create_message(self._classifier_data_parsed.get("foco_analise"))
        self.stop("foco_analise_internet"); return Message(text="")
