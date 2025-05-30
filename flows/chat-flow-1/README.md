# Chat Flow - Assistente AI com Memória Contextual

## Objetivo
Este fluxo implementa um assistente AI com capacidade de memória contextual, integrando Azure OpenAI para processamento de linguagem natural e MongoDB para armazenamento e recuperação de contexto.

## Componentes Principais

### 1. Webhook Receiver (ID: CustomComponent-DDTxa)
- **Função**: Ponto de entrada para recebimento de mensagens
- **Inputs**: Dados do webhook (mensagem, metadados)
- **Outputs**: Dados estruturados para processamento

### 2. Azure OpenAI Processor (ID: AzureOpenAIModel-P8Rf9)
- **Função**: Processamento de linguagem natural
- **Inputs**: Texto processado, configurações do modelo
- **Outputs**: Resposta gerada pelo modelo

### 3. MongoDB Text Search (ID: MongoTextSearch-vLX80)
- **Função**: Busca contextual em histórico de conversas
- **Inputs**: Query de busca, parâmetros de conexão
- **Outputs**: Resultados relevantes do histórico

### 4. Structured Output (ID: StructuredOutput-78c4L)
- **Função**: Formatação final da resposta
- **Inputs**: Dados processados
- **Outputs**: Resposta estruturada para o usuário

## Fluxo de Dados
1. Recebimento da mensagem via webhook
2. Processamento inicial e estruturação
3. Busca de contexto relevante no MongoDB
4. Processamento da mensagem + contexto pelo Azure OpenAI
5. Estruturação e envio da resposta

## Configuração
- Arquivo de configuração: `flow.json`
- Configurações específicas por componente em `/components`
- Documentação detalhada em `/docs`

## Desenvolvimento
- Versão atual: 1.0.0
- Status: Em desenvolvimento
- Próximos passos:
  - Implementação de testes automatizados
  - Otimização de consultas MongoDB
  - Refinamento do prompt do Azure OpenAI 