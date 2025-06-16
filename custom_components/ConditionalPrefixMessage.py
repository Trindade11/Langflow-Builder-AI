from langflow.custom import Component
from langflow.io import MessageInput, Output, MultilineInput
from langflow.schema.message import Message


class ConditionalPrefixMessage(Component):
    """
    Adiciona um prefixo multilinha à mensagem se ela não estiver vazia
    e gera uma segunda saída com informações de debug.
    """

    display_name = "Prefixo Condicional"
    description = "Adiciona um prefixo (com suporte a múltiplas linhas) à mensagem, e envia debug como segunda saída."
    icon = "message-square"
    name = "ConditionalPrefix"

    inputs = [
        MessageInput(
            name="input_message",
            display_name="Mensagem",
            info="Mensagem de entrada que será processada.",
            required=True,
        ),
        MultilineInput(
            name="prefix",
            display_name="Prefixo",
            info="Texto a ser adicionado antes da mensagem. Suporta múltiplas linhas.",
            value="",
            required=False,
        ),
    ]

    outputs = [
        Output(
            display_name="Mensagem Final",
            name="output_message",
            info="Mensagem final com o prefixo aplicado (se aplicável).",
            method="process_message",
        ),
        Output(
            display_name="Debug",
            name="debug_output",
            info="Informações de depuração do processamento.",
            method="debug_info",
        ),
    ]

    def process_message(self) -> Message:
        input_message: Message = self.input_message
        prefix: str = self.prefix or ""

        self._debug_log = f"Mensagem recebida: '{input_message.text.strip()}'\n"
        self._debug_log += f"Prefixo recebido:\n{prefix}\n"

        message_text = input_message.text.strip() if hasattr(input_message, 'text') and input_message.text else ""

        if not message_text:
            self.status = "Mensagem vazia recebida"
            self._debug_log += "Mensagem está vazia. Retornando texto vazio.\n"
            return Message(text="")

        final_text = f"{prefix}{message_text}"
        self.status = "Mensagem processada com prefixo"
        self._debug_log += f"Resultado final:\n{final_text}"

        return Message(text=final_text)

    def debug_info(self) -> Message:
        return Message(text=self._debug_log.strip() if hasattr(self, "_debug_log") else "Nenhum log disponível.") 