import json
import ast
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class ProcessEscapedJsonStringComponent(Component):
    display_name = "Processar String JSON Escapada (Seguro)"
    description = "Converte uma string JSON com escapes literais (ex: \\n, \\\") para um objeto Data, preservando UTF-8."
    icon = "JSON"
    name = "ProcessEscapedJsonSafe"

    inputs = [
        MessageTextInput(
            name="input_message",
            display_name="Mensagem de Entrada com String JSON",
            info="String JSON com escapes literais (ex: de AIMessage.content via Regex Extractor).",
            required=True,
        ),
    ]

    outputs = [
        Output(name="data_output", display_name="Saída de Dados (Data)", method="process_string_to_data"),
    ]

    def process_string_to_data(self) -> Data | list[Data]:
        raw_json_string = self.input_message
        
        if not raw_json_string:
            self.status = "String JSON de entrada está vazia."
            raise ValueError("String JSON de entrada está vazia.")

        processed_string = raw_json_string

        try:
            processed_for_structure = bytes(raw_json_string, "utf-8").decode("unicode-escape")
            parsed_data_struct = json.loads(processed_for_structure)

            def fix_utf8_issues_in_obj(obj):
                if isinstance(obj, dict):
                    return {k: fix_utf8_issues_in_obj(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [fix_utf8_issues_in_obj(elem) for elem in obj]
                elif isinstance(obj, str):
                    try:
                        return obj.encode('latin-1').decode('utf-8')
                    except UnicodeEncodeError:
                        return obj
                    except UnicodeDecodeError:
                        return obj 
                else:
                    return obj

            parsed_data = fix_utf8_issues_in_obj(parsed_data_struct)

            if isinstance(parsed_data, list):
                result = [Data(data=item) for item in parsed_data]
            else:
                result = Data(data=parsed_data)
            
            self.status = "JSON processado e encoding corrigido (tentativa)."
            return result

        except json.JSONDecodeError as e_json:
            error_msg = f"Erro ao decodificar JSON estrutural: {str(e_json)}. String após unicode-escape era: >>>{processed_for_structure if 'processed_for_structure' in locals() else 'N/A'}<<<"
            self.status = error_msg
            raise ValueError(error_msg) from e_json
        
        except Exception as e_general: 
            error_msg = f"Erro inesperado: {str(e_general)}. String original era: >>>{raw_json_string}<<<"
            self.status = error_msg
            raise ValueError(error_msg) from e_general