# 🤖 Projeto Chat Corporativo

<div align="center">
  <img src="public/logo.png" alt="Chat Corporativo Logo" width="200"/>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
  [![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com/cloud/atlas)
</div>

## 📋 Visão Geral

O Projeto Chat Corporativo é uma solução de comunicação inteligente voltada para ambientes empresariais, desenvolvida com tecnologias avançadas de inteligência artificial (IA). Ele permite uma interação ágil e eficiente entre colaboradores, facilitando o acesso rápido a informações críticas e melhorando significativamente a produtividade das equipes.

## 🎯 Recursos Principais

- **Chat com Agentes Inteligentes**: Utilização de agentes conversacionais que empregam técnicas avançadas como RAG (Retrieval-Augmented Generation) para fornecer respostas contextualizadas e precisas.

- **Integração de Dados Corporativos**: Suporte à integração com bases de conhecimento internas, documentos, planilhas e transcrições de reuniões.

- **Filtragem por Perfil de Usuário**: Acesso segmentado por setor e nível estratégico (operacional, tático e estratégico).

- **Extração e Indexação Automática**: Automação na indexação e recuperação de informações estruturadas e não estruturadas.

- **Interação Híbrida**: Combinação de buscas semânticas e lexicais para uma maior precisão nos resultados.

## 🛠️ Tecnologias Utilizadas

- **🐍 Python**: Linguagem principal de desenvolvimento
- **🗃️ MongoDB Atlas**: Gerenciamento de bases de dados com capacidades avançadas de busca (vetorizada e lexical)
- **🧰 Langflow**: Criação e gerenciamento de fluxos de agentes inteligentes
- **🧠 Frameworks de IA**: Embeddings personalizados e integração com modelos de linguagem (LLM)

## 🚀 Como Utilizar

### Pré-requisitos

- Python 3.9+
- MongoDB Atlas
- Node.js 16+ (para interface web)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/chat-corporativo.git

# Entre no diretório
cd chat-corporativo

# Instale as dependências Python
pip install -r requirements.txt

# Instale as dependências Node.js (se necessário)
npm install
```

### Configuração

1. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

2. Configure o MongoDB Atlas:
- Crie uma conta no MongoDB Atlas
- Configure o cluster e obtenha a string de conexão
- Adicione a string de conexão no arquivo .env

### Execução

```bash
python main.py
```

## 📈 Roadmap Futuro

- Implementação de novos agentes especializados por setores
- Expansão das capacidades de filtragem e personalização por perfil
- Melhoria contínua dos modelos via Fine-tuning para domínio específico
- Desenvolvimento de dashboards analíticos para insights operacionais e estratégicos

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga estas etapas:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Contato

- Email: [seu-email@exemplo.com]
- LinkedIn: [seu-linkedin]
- Twitter: [@seu-twitter]

---
Desenvolvido com ❤️ pela equipe Chat Corporativo 