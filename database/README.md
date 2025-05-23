# Base de Conhecimento

Esta pasta armazena os dados e informações que constituem a base de conhecimento do projeto.

**Fonte dos Dados:**

*   **Banco de Dados:** MongoDB
*   **Nome do Banco de Dados:** `DeepContext`
*   **String de Conexão:** `mongodb+srv://trindade:trindade@clustercocreateai.ykdjn.mongodb.net/?retryWrites=true&w=majority&appName=ClusterCoCreateAI` (Credenciais de exemplo, usar as reais do projeto)

**Coleções Identificadas:**

Atualmente, as seguintes coleções foram identificadas no banco de dados `DeepContext`:

*   `knowledge_nodes`
*   `conversation`
*   `knowledge_edges`
*   `knowledge_context`
*   `title`

**Estrutura das Coleções:**

*   **`knowledge_context`**: A estrutura detalhada de um documento desta coleção pode ser encontrada no arquivo [knowledge_context_structure.txt](knowledge_context_structure.txt).
*   As estruturas das demais coleções (`knowledge_nodes`, `conversation`, `knowledge_edges`, `title`) ainda precisam ser detalhadas.

**Como explorar as coleções:**

Para listar as coleções e inspecionar a estrutura de um documento de uma coleção específica, utilize o script interativo:
`python scripts/list_collections.py`

**Objetivo desta Base de Conhecimento:**

*   [Explique o propósito desta base de conhecimento no contexto do projeto - A SER PREENCHIDO]

**Como utilizar os dados:**

*   [Instruções sobre como acessar, atualizar ou utilizar os dados - A SER PREENCHIDO] 