# Regra de Rastreamento de Fluxos

## Objetivo
Garantir a rastreabilidade completa e precisa de todos os componentes e suas conexões em cada fluxo do projeto.

## Ferramentas
1. **Flow Analyzer** (`flows/utils/flow_analyzer.py`)
   - Script automático de análise
   - Validação de conexões
   - Geração de mapeamento

## Processo

### 1. Análise Automática
```bash
# Ao adicionar ou modificar um fluxo
python flow_analyzer.py flows/[flow-name]/flow.json flows/[flow-name]/mapping.json
```

### 2. Estrutura de Arquivos
```
flows/
└── [flow-name]/
    ├── flow.json           # Fluxo original do Langflow
    ├── mapping.json        # Mapeamento gerado automaticamente
    └── components/         # Componentes organizados por ID
        └── [component-id]/ # Nome da pasta = ID do componente
```

### 3. Validações Obrigatórias
- Todas as conexões devem ser bidirecionais
- Tipos de dados devem ser compatíveis
- IDs devem ser únicos no fluxo
- Componentes devem existir fisicamente

### 4. Metadados Necessários
- Versão do fluxo
- Timestamp da última atualização
- Total de componentes
- Total de conexões
- Erros de validação (se houver)

### 5. Manutenção
- Executar análise após cada modificação
- Verificar erros de validação
- Atualizar documentação dos componentes

## Uso com LLMs
1. O LLM deve sempre consultar `mapping.json`
2. Usar os IDs como referência primária
3. Validar conexões antes de sugerir modificações
4. Reportar inconsistências encontradas

## Exemplo de Consulta
```python
# Antes de analisar um fluxo
mapping = load_mapping("flows/chat-flow-1/mapping.json")
component = mapping["components"]["CustomComponent-DDTxa"]
connections = component["connections"]["outputs"]
```

## Garantia de Qualidade
1. **Validação Automática**
   - Executada pelo Flow Analyzer
   - Verifica integridade do fluxo
   - Identifica inconsistências

2. **Documentação**
   - Mapeamento sempre atualizado
   - Conexões documentadas
   - Histórico de alterações

3. **Rastreabilidade**
   - IDs únicos preservados
   - Conexões bidirecionais
   - Tipos de dados validados 