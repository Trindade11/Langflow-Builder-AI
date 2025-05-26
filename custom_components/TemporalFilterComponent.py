from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from langflow.custom import Component
from langflow.io import HandleInput, StrInput, Output
from langflow.schema import Data

class TemporalFilterComponent(Component):
    display_name = "Filtro Temporal Inteligente"
    description = "Analisa chunks do MongoDB e aplica filtragem temporal baseada em constraints."
    icon = "clock"
    name = "TemporalFilter"

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
            display_name="Restrições Temporais",
            info="Texto descritivo das restrições temporais (Data object ou string)",
            input_types=["Data", "str"],
            required=True,
        ),
        StrInput(
            name="current_date",
            display_name="Data Atual",
            info="Data atual no formato YYYY-MM-DD",
            required=True,
        )
    ]

    outputs = [
        Output(name="filtered_chunks", display_name="Chunks Filtrados", method="filter_chunks"),
    ]

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

    def filter_chunks(self) -> Data:
        try:
            # Obtém os chunks de entrada
            input_data = self.input_chunks
            if not isinstance(input_data, Data) or not isinstance(input_data.data, dict):
                raise ValueError("Input chunks deve ser um objeto Data contendo um dicionário")
            
            chunks = input_data.data.get("results", [])
            if not chunks:
                return Data(data={"results": [], "message": "Nenhum chunk para filtrar"})

            # Obtém as restrições temporais
            constraints = self.temporal_constraints
            if isinstance(constraints, Data):
                constraints = constraints.data.get("temporal_constraints", "") if isinstance(constraints.data, dict) else ""
            constraints = str(constraints)

            # Converte a data atual
            try:
                current_date = datetime.strptime(self.current_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Data atual deve estar no formato YYYY-MM-DD")

            # Analisa as restrições temporais
            date_range = self._parse_date_expression(constraints, current_date)
            
            # Agrupa chunks por evento/documento
            grouped_chunks = self._group_by_event_id(chunks)
            
            filtered_chunks = []
            
            if "última" in constraints.lower():
                # Para "última X", ordena por data e pega o mais recente
                events_with_dates = []
                for event_id, event_chunks in grouped_chunks.items():
                    latest_date = max(
                        datetime.fromisoformat(str(chunk.get("atualizado_em", "1900-01-01")))
                        for chunk in event_chunks
                    )
                    events_with_dates.append((latest_date, event_chunks))
                
                if events_with_dates:
                    # Pega o evento mais recente
                    latest_event = max(events_with_dates, key=lambda x: x[0])[1]
                    filtered_chunks.extend(latest_event)
            
            elif date_range:
                # Para ranges de data específicos
                for event_chunks in grouped_chunks.values():
                    event_date = datetime.fromisoformat(
                        str(event_chunks[0].get("atualizado_em", "1900-01-01"))
                    )
                    if date_range["start"] <= event_date <= date_range["end"]:
                        filtered_chunks.extend(event_chunks)
            
            else:
                # Se não houver restrição temporal clara, retorna todos os chunks
                filtered_chunks = chunks

            result = {
                "results": filtered_chunks,
                "message": f"Filtrado para {len(filtered_chunks)} chunks baseado nas restrições temporais",
                "applied_constraints": constraints,
                "date_range": str(date_range) if date_range else "Última ocorrência ou sem range específico"
            }

            self.status = result["message"]
            return Data(data=result)

        except Exception as e:
            self.status = f"Erro ao filtrar chunks: {str(e)}"
            return Data(data={"error": str(e), "results": []}) 