"""
Exemplo básico de uso do Langflow Builder AI.
"""

from src.core.builder import LangflowBuilder, ComponentMetadata
from src.core.ai_agent import AIAgent

def main():
    # Inicializa o builder e o agente de IA
    builder = LangflowBuilder()
    agent = AIAgent()
    
    # Exemplo de requisitos para um componente
    requirements = """
    Crie um componente que receba um texto e retorne a contagem de palavras.
    O componente deve ter:
    - Input: texto (str)
    - Output: contagem (int)
    - Parâmetros: nenhum
    """
    
    # Interpreta os requisitos
    specification = agent.interpret_requirements(requirements)
    
    # Gera o componente
    component_code = agent.generate_component(specification)
    
    # Cria os metadados do componente
    metadata = ComponentMetadata(
        name="WordCounter",
        description="Conta o número de palavras em um texto",
        category="Text Processing",
        inputs=[{"name": "text", "type": "str"}],
        outputs=[{"name": "count", "type": "int"}],
        parameters=[]
    )
    
    # Cria o componente no builder
    component_id = builder.create_component(metadata)
    
    print(f"Componente criado com ID: {component_id}")
    print("\nMetadados do componente:")
    print(builder.get_component(component_id))

if __name__ == "__main__":
    main() 