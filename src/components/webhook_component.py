import json
import tempfile
from datetime import datetime

from langflow.custom import Component
from langflow.io import MultilineInput, Output
from langflow.schema import Data

class WebhookComponent(Component):
    display_name = "Webhook"
    description = "Receives a JSON payload and emits a Data object."
    name = "Webhook"
    icon = "webhook"

    inputs = [
        MultilineInput(
            name="payload",
            display_name="Payload",
            info="Raw JSON text received via HTTP POST.",
        )
    ]

    outputs = [
        Output(
            display_name="Data",
            name="data",
            method="build_data",
            type="data",      # emite Data, não Message
        ),
    ]

    def build_data(self) -> Data:
        raw = self.payload or ""
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"text": raw}

        # garante campo text para embeddings
        if not payload.get("text"):
            nome = payload.get("nome", "")
            desc = payload.get("descricao", "")
            payload["text"] = (f"{nome} - {desc}".strip() or raw)

        self.status = f"Data built with ID: {payload.get('id', 'N/A')}"
        return Data(data=payload) 