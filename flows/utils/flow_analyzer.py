import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class FlowAnalyzer:
    def __init__(self, flow_json_path: str):
        self.flow_json_path = flow_json_path
        self.component_connections: Dict = {}
        self.flow_id = Path(flow_json_path).parent.name

    def load_flow(self) -> Dict:
        """Carrega o JSON do fluxo."""
        with open(self.flow_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_edges(self, flow_data: Dict) -> None:
        """Analisa todas as conexões do fluxo."""
        for edge in flow_data.get("data", {}).get("edges", []):
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            if not source_id or not target_id:
                continue

            # Inicializa componente fonte se não existir
            if source_id not in self.component_connections:
                self.component_connections[source_id] = {
                    "path": f"components/{source_id.lower()}",
                    "type": edge["data"]["sourceHandle"]["dataType"],
                    "connections": {"outputs": [], "inputs": []}
                }

            # Inicializa componente alvo se não existir
            if target_id not in self.component_connections:
                self.component_connections[target_id] = {
                    "path": f"components/{target_id.lower()}",
                    "type": edge["data"]["targetHandle"].get("type", "unknown"),
                    "connections": {"outputs": [], "inputs": []}
                }

            # Adiciona conexão de saída ao componente fonte
            self.component_connections[source_id]["connections"]["outputs"].append({
                "target": target_id,
                "type": edge["data"]["sourceHandle"]["output_types"][0],
                "field_name": edge["data"]["sourceHandle"]["name"]
            })

            # Adiciona conexão de entrada ao componente alvo
            self.component_connections[target_id]["connections"]["inputs"].append({
                "source": source_id,
                "type": edge["data"]["targetHandle"]["inputTypes"][0],
                "field_name": edge["data"]["targetHandle"]["fieldName"]
            })

    def generate_mapping(self) -> Dict:
        """Gera o mapeamento final."""
        flow_data = self.load_flow()
        self.analyze_edges(flow_data)

        return {
            "components": self.component_connections,
            "metadata": {
                "flow_id": self.flow_id,
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "total_components": len(self.component_connections),
                "total_connections": sum(
                    len(comp["connections"]["outputs"])
                    for comp in self.component_connections.values()
                )
            }
        }

    def validate_connections(self) -> List[str]:
        """Valida a integridade das conexões."""
        errors = []
        for comp_id, comp_data in self.component_connections.items():
            # Verifica conexões de saída
            for output in comp_data["connections"]["outputs"]:
                target_id = output["target"]
                if target_id not in self.component_connections:
                    errors.append(f"Componente {comp_id} tem conexão com {target_id} inexistente")
                
                # Verifica se o tipo de dados é compatível
                target_comp = self.component_connections.get(target_id)
                if target_comp:
                    matching_input = next(
                        (inp for inp in target_comp["connections"]["inputs"]
                         if inp["source"] == comp_id),
                        None
                    )
                    if matching_input and matching_input["type"] != output["type"]:
                        errors.append(
                            f"Incompatibilidade de tipos entre {comp_id} ({output['type']}) "
                            f"e {target_id} ({matching_input['type']})"
                        )

        return errors

def analyze_flow(flow_path: str, output_path: Optional[str] = None) -> Dict:
    """
    Analisa um fluxo e gera seu mapeamento.
    
    Args:
        flow_path: Caminho para o arquivo JSON do fluxo
        output_path: Caminho opcional para salvar o mapeamento
    
    Returns:
        Dict com o mapeamento do fluxo
    """
    analyzer = FlowAnalyzer(flow_path)
    mapping = analyzer.generate_mapping()
    
    # Valida conexões
    errors = analyzer.validate_connections()
    if errors:
        mapping["metadata"]["validation_errors"] = errors
    
    # Salva o mapeamento se especificado
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    return mapping

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python flow_analyzer.py <caminho_do_flow.json> [caminho_saida.json]")
        sys.exit(1)
    
    flow_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        mapping = analyze_flow(flow_path, output_path)
        if "validation_errors" in mapping["metadata"]:
            print("\nErros encontrados:")
            for error in mapping["metadata"]["validation_errors"]:
                print(f"- {error}")
        else:
            print("\nAnálise concluída com sucesso!")
            print(f"Total de componentes: {mapping['metadata']['total_components']}")
            print(f"Total de conexões: {mapping['metadata']['total_connections']}")
    except Exception as e:
        print(f"Erro ao analisar fluxo: {str(e)}")
        sys.exit(1) 