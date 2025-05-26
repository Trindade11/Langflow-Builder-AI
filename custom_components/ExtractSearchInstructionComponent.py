import json
from langflow.custom import Component
from langflow.io import HandleInput, Output
from langflow.schema import Data # Certifique-se que Data está corretamente importado

class ExtractSearchInstructionComponent(Component):
    display_name = "Extrair Search Instruction"
    description = "Extrai o dicionário 'search_instruction' de um objeto Data de entrada que contém o JSON completo do LLM."
    icon = "filter" # Ícone sugerido, pode ser alterado
    name = "ExtractSearchInstruction"

    inputs = [
        HandleInput(
            name="input_data_object", # Nome da entrada
            display_name="Input Data Object",
            info="Objeto Data contendo o JSON completo do LLM (espera-se que input_data_object.data seja um dict).",
            input_types=["Data"], # Aceita objetos do tipo Data
            required=True,
        ),
    ]

    outputs = [
        Output(name="search_instruction_output", display_name="Search Instruction (Data)", method="extract_instruction"),
    ]

    def extract_instruction(self) -> Data:
        input_data = self.input_data_object # Usar o nome da entrada definido nos inputs

        if not input_data or not isinstance(input_data, Data):
            self.status = "Objeto Data de entrada não recebido ou inválido."
            # É importante retornar um objeto Data para compatibilidade com o fluxo
            return Data(data={"error": self.status, "results": []}) 

        if not isinstance(input_data.data, dict):
            self.status = f"O atributo 'data' do objeto Data de entrada não é um dicionário. Tipo recebido: {type(input_data.data)}"
            return Data(data={"error": self.status, "results": []})

        llm_output_dict = input_data.data
        
        if "search_instruction" not in llm_output_dict:
            self.status = "Chave 'search_instruction' não encontrada no dicionário de entrada (Data.data)."
            return Data(data={"error": self.status, "results": []})
            
        search_instruction_payload = llm_output_dict["search_instruction"]
        
        if not isinstance(search_instruction_payload, dict):
            self.status = "O valor de 'search_instruction' não é um dicionário."
            return Data(data={"error": self.status, "results": []})

        self.status = "Search instruction extraída com sucesso."
        # Retorna um novo objeto Data contendo apenas o dicionário da search_instruction
        return Data(data=search_instruction_payload) 