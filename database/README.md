# Base de Conhecimento

Esta pasta armazena os dados e informações que constituem a base de conhecimento do projeto.

# Configuração do Banco de Dados

## Informações do Banco:
*   **Banco de Dados:** MongoDB
*   **Nome do Banco:** DeepContext
*   **String de Conexão:** Configure a variável `MONGODB_URI` no arquivo `.env` com sua string de conexão do MongoDB Atlas
*   **Exemplo:** `mongodb+srv://seu-usuario:sua-senha@seu-cluster.mongodb.net/?retryWrites=true&w=majority&appName=SeuApp`

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