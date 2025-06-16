from langflow.custom import Component
from langflow.io import DataInput, MessageInput, Output
from langflow.schema import Data, Message


class CombineJSONComponent(Component):
    display_name = "Combine JSON + Message"
    description = "Combina os dados de um JSON com duas mensagens e uma lista de textos em um único JSON de saída."
    icon = "plus-square"
    name = "CombineJSON"
    legacy = True

    inputs = [
        DataInput(
            name="json_data",
            display_name="JSON Data",
            info="Dados JSON originais do componente Load JSON.",
            is_list=False,
            required=True,
        ),
        MessageInput(
            name="message1",
            display_name="Message 1",
            info="Primeira mensagem a ser incorporada no JSON.",
            required=False,
        ),
        MessageInput(
            name="message2",
            display_name="Message 2",
            info="Segunda mensagem a ser incorporada no JSON.",
            required=False,
        ),
        DataInput(
            name="data_list",
            display_name="Data List",
            info="Lista de Data formatada a ser incorporada no JSON.",
            is_list=True,
            required=False,
        ),
    ]

    outputs = [
        Output(
            name="combined_data",
            display_name="Combined JSON",
            method="combine",
            info="JSON unificado contendo dados originais + mensagens/lista.",
        )
    ]

    def combine(self) -> Data:
        combined = self.json_data.data.copy()

        if self.message1:
            combined["message1_text"] = self.message1.text

        if self.message2:
            combined["message2_text"] = self.message2.text

        if self.data_list:
            combined["message_list"] = [d.text for d in self.data_list if hasattr(d, "text") and d.text]

        self.status = combined
        return Data(data=combined)