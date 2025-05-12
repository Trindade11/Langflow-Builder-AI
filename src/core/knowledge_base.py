"""
Gerenciador da base de conhecimento do Langflow Builder AI.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class KnowledgeBase:
    """Gerencia a base de conhecimento do sistema."""
    
    def __init__(self, knowledge_file: str = "src/core/data/knowledge_base.json"):
        """
        Inicializa a base de conhecimento.
        
        Args:
            knowledge_file: Caminho para o arquivo JSON da base de conhecimento
        """
        self.knowledge_file = Path(knowledge_file)
        self.knowledge: Dict[str, Any] = self._load_knowledge()
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """
        Carrega a base de conhecimento do arquivo JSON.
        
        Returns:
            Dict[str, Any]: Dados da base de conhecimento
        """
        if not self.knowledge_file.exists():
            raise FileNotFoundError(f"Arquivo de conhecimento não encontrado: {self.knowledge_file}")
        
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_component_categories(self) -> Dict[str, Dict]:
        """
        Retorna as categorias de componentes disponíveis.
        
        Returns:
            Dict[str, Dict]: Categorias de componentes
        """
        return self.knowledge["component_categories"]
    
    def get_component_structure(self) -> Dict[str, Any]:
        """
        Retorna a estrutura padrão de componentes.
        
        Returns:
            Dict[str, Any]: Estrutura de componentes
        """
        return self.knowledge["component_structure"]
    
    def get_implementation_patterns(self) -> Dict[str, Dict]:
        """
        Retorna os padrões de implementação.
        
        Returns:
            Dict[str, Dict]: Padrões de implementação
        """
        return self.knowledge["implementation_patterns"]
    
    def get_best_practices(self) -> Dict[str, Dict]:
        """
        Retorna as melhores práticas.
        
        Returns:
            Dict[str, Dict]: Melhores práticas
        """
        return self.knowledge["best_practices"]
    
    def get_examples(self) -> Dict[str, Dict]:
        """
        Retorna os exemplos de componentes.
        
        Returns:
            Dict[str, Dict]: Exemplos de componentes
        """
        return self.knowledge["examples"]
    
    def get_category_examples(self, category: str) -> List[Dict]:
        """
        Retorna exemplos de uma categoria específica.
        
        Args:
            category: Nome da categoria
            
        Returns:
            List[Dict]: Exemplos da categoria
        """
        return self.knowledge["component_categories"][category]["examples"]
    
    def get_category_base_class(self, category: str) -> str:
        """
        Retorna a classe base de uma categoria.
        
        Args:
            category: Nome da categoria
            
        Returns:
            str: Nome da classe base
        """
        return self.knowledge["component_categories"][category]["base_class"]
    
    def get_category_attributes(self, category: str) -> List[str]:
        """
        Retorna os atributos comuns de uma categoria.
        
        Args:
            category: Nome da categoria
            
        Returns:
            List[str]: Atributos comuns
        """
        return self.knowledge["component_categories"][category]["common_attributes"] 