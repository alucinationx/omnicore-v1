# OmniCore AI - Documentação Técnica Completa

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Guia de Uso](#guia-de-uso)
5. [API Reference](#api-reference)
6. [Conectores Empresariais](#conectores-empresariais)
7. [Processamento de Documentos](#processamento-de-documentos)
8. [Segurança e Compliance](#segurança-e-compliance)
9. [Monitoramento e Logs](#monitoramento-e-logs)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O **OmniCore AI** é um agente de IA empresarial autônomo, modular e escalável, projetado para automação inteligente de processos corporativos. O sistema oferece capacidades avançadas de:

- **Integração universal** com sistemas empresariais (SAP, Salesforce, ERPs, CRMs)
- **Processamento inteligente de documentos** com OCR e extração de dados
- **Tomada de decisão automatizada** baseada em IA e regras de negócio
- **Aprendizado contínuo** com feedback supervisionado
- **Orquestração de processos** complexos e workflows
- **Geração de relatórios** e insights empresariais

### 🏗️ Características Principais

- **Plug & Play**: Integração rápida em qualquer empresa com configurações mínimas
- **Modular**: Componentes independentes e expansíveis
- **Seguro**: Compliance com LGPD, GDPR e ISO 27001
- **Escalável**: Arquitetura preparada para alta demanda
- **Auditável**: Logs completos e rastreabilidade total

---

## 🏛️ Arquitetura do Sistema

### Componentes Principais

```mermaid
graph TB
    A[Frontend/Dashboard] --> B[API Gateway/FastAPI]
    B --> C[OmniCore Agent]
    C --> D[Document Processor]
    C --> E[Integration Manager]
    C --> F[Decision Engine]
    C --> G[Learning System]
    C --> H[Security Manager]
    C --> I[Report Generator]
    
    B --> J[(PostgreSQL)]
    B --> K[(Redis)]
    B --> L[(Qdrant Vector DB)]
    
    E --> M[SAP Connector]
    E --> N[Salesforce Connector]
    E --> O[Database Connector]
    E --> P[Email Connector]
    
    Q[Prometheus] --> R[Grafana]
    B --> Q
```

### Stack Tecnológico

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Banco de Dados**: PostgreSQL (principal), Redis (cache), Qdrant (vetores)
- **IA/ML**: OpenAI GPT-4, Transformers, spaCy, Sentence Transformers
- **OCR**: Tesseract, EasyOCR
- **Filas**: Celery + Redis
- **Monitoramento**: Prometheus + Grafana
- **Deployment**: Docker, Docker Compose
- **Proxy**: Nginx

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Docker 20.0+
- Docker Compose 2.0+
- 8GB RAM mínimo (16GB recomendado)
- 50GB de espaço em disco

### Instalação Rápida com Docker

1. **Clone o repositório**:
```bash
git clone https://github.com/suaempresa/omnicore-ai.git
cd omnicore-ai
```

2. **Configure as variáveis de ambiente**:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Inicie os serviços**:
```bash
docker-compose up -d
```

4. **Verifique o status**:
```bash
curl http://localhost:8000/health
```

### Configuração Manual

#### 1. Instalação Python

```bash
# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Baixar modelo spaCy
python -m spacy download pt_core_news_sm
```

#### 2. Configuração do Banco

```bash
# PostgreSQL
createdb omnicore_db
psql omnicore_db < init.sql

# Redis
redis-server

# Qdrant
docker run -p 6333:6333 qdrant/qdrant:latest
```

#### 3. Variáveis de Ambiente Essenciais

```bash
# API Keys
export OPENAI_API_KEY="sua_chave_aqui"

# Banco de dados
export DATABASE_URL="postgresql://user:pass@localhost:5432/omnicore_db"
export REDIS_URL="redis://localhost:6379/0"
export QDRANT_URL="http://localhost:6333"

# Segurança
export JWT_SECRET="sua_chave_jwt_super_secreta"
export ENCRYPTION_KEY="sua_chave_criptografia_32_chars"
```

#### 4. Iniciar Aplicação

```bash
# API principal
uvicorn omnicore_api:app --host 0.0.0.0 --port 8000

# Worker Celery
celery -A omnicore.celery worker --loglevel=info

# Scheduler
celery -A omnicore.celery beat --loglevel=info
```

---

## 📚 Guia de Uso

### 1. Primeiro Acesso

Após a instalação, acesse:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana**: http://localhost:3000 (admin/admin123)

### 2. Configuração Inicial

#### Criar Empresa
```python
import requests

response = requests.post("http://localhost:8000/empresas", json={
    "name": "Minha Empresa",
    "cnpj": "12.345.678/0001-99",
    "industry": "Tecnologia"
})
```

#### Configurar Integrações
```python
# Configurar SAP
sap_config = {
    "system_name": "sap",
    "endpoint": "https://sap.suaempresa.com",
    "credentials": {
        "username": "usuario_sap",
        "password": "senha_sap"
    }
}

response = requests.post("http://localhost:8000/integracoes/configurar", json=sap_config)
```

### 3. Casos de Uso Práticos

#### Análise de Documento
```python
# Upload e análise de PDF
files = {"file": open("contrato.pdf", "rb")}
data = {
    "tipo_analise": "completa",
    "user_id": "user_123",
    "company_id": "empresa_456"
}

response = requests.post(
    "http://localhost:8000/documentos/analisar",
    files=files,
    data=data
)

result = response.json()
print(f"Classificação: {result['result']['classification']}")
print(f"Entidades encontradas: {len(result['result']['entities'])}")
```

#### Execução de Processo
```python
# Processo de onboarding de cliente
process_data = {
    "processo_nome": "onboarding_cliente",
    "parametros": {
        "cliente_id": "cli_789",
        "documentos": ["cpf.pdf", "comprovante.pdf"]
    },
    "user_id": "user_123",
    "company_id": "empresa_456"
}

response = requests.post(
    "http://localhost:8000/processos/executar",
    json=process_data
)
```

#### Tomada de Decisão
```python
# Decisão de aprovação de crédito
decision_data = {
    "dados_entrada": {
        "tipo": "aprovacao_credito",
        "valor": 50000,
        "score_credito": 750,
        "renda_mensal": 8000
    },
    "user_id": "user_123",
    "company_id": "empresa_456"
}

response = requests.post(
    "http://localhost:8000/decisoes/tomar",
    json=decision_data
)

decision = response.json()
print(f"Decisão: {decision['decision']}")
print(f"Confiança: {decision['confidence']}")
```

---

## 🔌 API Reference

### Endpoints Principais

#### 1. Documentos

**POST /documentos/analisar**
- Analisa documento com OCR e IA
- Parâmetros: arquivo + configurações
- Retorna: texto extraído, entidades, classificação

**GET /documentos/{document_id}**
- Recupera análise de documento
- Retorna: resultado completo da análise

#### 2. Processos

**POST /processos/executar**
- Executa processo de negócio
- Parâmetros: nome do processo + parâmetros
- Retorna: resultado da execução

**GET /processos/ativos**
- Lista processos em execução
- Retorna: lista de processos ativos

#### 3. Decisões

**POST /decisoes/tomar**
- Toma decisão baseada em dados
- Parâmetros: dados de entrada
- Retorna: decisão + confiança + raciocínio

**POST /aprendizado/feedback**
- Aplica feedback para aprendizado
- Parâmetros: score + resultado
- Retorna: confirmação do aprendizado

#### 4. Integrações

**POST /integracoes/executar**
- Executa integração com sistema externo
- Parâmetros: sistema + operação + dados
- Retorna: resultado da integração

#### 5. Relatórios

**POST /relatorios/gerar**
- Gera relatório empresarial
- Parâmetros: tipo + parâmetros + formato
- Retorna: relatório gerado

### Autenticação

Todas as requisições requerem token JWT no header:
```bash
Authorization: Bearer <seu_token_jwt>
```

### Códigos de Resposta

- **200**: Sucesso
- **201**: Criado com sucesso
- **400**: Erro na requisição
- **401**: Não autorizado
- **403**: Proibido
- **404**: Não encontrado
- **500**: Erro interno do servidor

---

## 🔗 Conectores Empresariais

### SAP S/4HANA

#### Configuração
```python
sap_config = {
    "system_name": "sap",
    "endpoint": "https://sap.empresa.com",
    "auth_type": "basic",
    "credentials": {
        "username": "SAP_USER",
        "password": "SAP_PASS",
        "client": "100"
    }
}
```

#### Operações Disponíveis
- `get_business_partners`: Buscar parceiros de negócio
- `create_sales_order`: Criar pedido de venda
- `get_financial_data`: Obter dados financeiros
- `update_material`: Atualizar dados de material

### Salesforce

#### Configuração
```python
sf_config = {
    "system_name": "salesforce",
    "endpoint": "https://login.salesforce.com",
    "auth_type": "oauth2",
    "credentials": {
        "client_id": "SF_CLIENT_ID",
        "client_secret": "SF_CLIENT_SECRET",
        "username": "usuario@empresa.com",
        "password": "SF_PASSWORD"
    }
}
```

#### Operações Disponíveis
- `query`: Executar SOQL
- `create_record`: Criar registro
- `update_record`: Atualizar registro
- `get_opportunities`: Buscar oportunidades

### Banco de Dados

#### Configuração
```python
db_config = {
    "system_name": "database",
    "credentials": {
        "type": "postgresql",
        "host": "db.empresa.com",
        "port": 5432,
        "database": "empresa_db",
        "username": "db_user",
        "password": "db_pass"
    }
}
```

#### Operações Disponíveis
- `query`: Executar SQL
- `insert`: Inserir dados
- `update`: Atualizar dados
- `bulk_insert`: Inserção em lote

---

## 📄 Processamento de Documentos

### Tipos de Arquivo Suportados

- **PDF**: Extração de texto + OCR
- **Imagens**: JPG, PNG, TIFF com OCR
- **Office**: DOCX, XLSX
- **Texto**: TXT, CSV

### Entidades Extraídas

#### Entidades Brasileiras
- **CPF**: 123.456.789-01
- **CNPJ**: 12.345.678/0001-99
- **CEP**: 12345-678
- **Telefone**: (11) 99999-9999
- **Valores**: R$ 1.234,56
- **Datas**: 01/01/2024

#### Entidades Genéricas
- **Email**: usuario@empresa.com
- **URLs**: https://empresa.com
- **Números de documento**: Códigos de barras, protocolos

### Classificação de Documentos

- **Contratos**: Identificação automática de contratos comerciais
- **Notas Fiscais**: NFe, NFCe, NFSe
- **Boletos**: Títulos de cobrança
- **Relatórios Financeiros**: Balanços, DRE
- **Documentos de Identidade**: RG, CNH, Passaporte

### Configuração de OCR

```python
ocr_config = {
    "engine": "tesseract",  # ou "easyocr"
    "languages": ["por", "eng"],
    "confidence_threshold": 0.8,
    "preprocess": {
        "enhance_contrast": True,
        "remove_noise": True,
        "deskew": True
    }
}
```

---

## 🔒 Segurança e Compliance

### Controle de Acesso (RBAC)

#### Papéis Disponíveis
- **Admin**: Acesso total ao sistema
- **Manager**: Gestão de processos e relatórios
- **User**: Operações básicas
- **Viewer**: Apenas visualização

#### Configuração de Permissões
```python
permissions = {
    "admin": ["*"],
    "manager": [
        "process:execute",
        "document:analyze",
        "report:generate",
        "decision:make"
    ],
    "user": [
        "document:upload",
        "process:view",
        "report:view"
    ]
}
```

### Criptografia

- **Em repouso**: AES-256 para dados sensíveis
- **Em trânsito**: TLS 1.3 para todas as comunicações
- **Dados pessoais**: Criptografia específica para CPF, etc.

### Compliance LGPD/GDPR

#### Funcionalidades Implementadas
- **Consentimento**: Registro de consentimentos
- **Portabilidade**: Exportação de dados pessoais
- **Esquecimento**: Remoção de dados pessoais
- **Auditoria**: Logs completos de acesso

#### Configuração
```python
privacy_settings = {
    "auto_anonymize": True,
    "retention_period": "7y",
    "consent_required": ["document_analysis", "data_export"],
    "sensitive_fields": ["cpf", "email", "phone"]
}
```

### Logs de Auditoria

Todos os eventos são logados:
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": "user_123",
    "action": "document_analyze",
    "resource": "doc_456",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "result": "success"
}
```

---

## 📊 Monitoramento e Logs

### Métricas Principais

#### Performance
- **Tempo de resposta**: Latência das APIs
- **Throughput**: Requisições por segundo
- **Taxa de erro**: Percentual de falhas

#### Negócio
- **Documentos processados**: Volume diário
- **Decisões tomadas**: Quantidade e precisão
- **Integrações ativas**: Status dos conectores

### Dashboards Grafana

#### Dashboard Principal
- **Status Geral**: Saúde do sistema
- **Performance**: Métricas de resposta
- **Volumes**: Documentos e processos

#### Dashboard de Segurança
- **Tentativas de acesso**: Login failures
- **Atividade suspeita**: Padrões anômalos
- **Compliance**: Status LGPD/GDPR

### Alertas

```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    duration: "5m"
    notification: "slack"
  
  - name: "Document Processing Slow"
    condition: "processing_time > 30s"
    duration: "2m"
    notification: "email"
```

### Logs Estruturados

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "document_processor",
    "event": "document_analyzed",
    "document_id": "doc_123",
    "processing_time": 5.2,
    "classification": "contract",
    "confidence": 0.95,
    "user_id": "user_456"
}
```

---

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco
```bash
# Verificar conectividade
docker-compose exec postgres psql -U omnicore -d omnicore_db -c "SELECT 1;"

# Logs do container
docker-compose logs postgres
```

#### 2. OCR não funciona
```bash
# Verificar Tesseract
docker-compose exec omnicore-api tesseract --version

# Instalar idiomas
docker-compose exec omnicore-api apt-get update && apt-get install tesseract-ocr-por
```

#### 3. API lenta
```bash
# Verificar recursos
docker stats

# Logs da aplicação
docker-compose logs omnicore-api | grep "ERROR\|WARNING"
```

#### 4. Integração SAP falha
```bash
# Testar conectividade
curl -X POST http://localhost:8000/integracoes/teste \
  -H "Content-Type: application/json" \
  -d '{"sistema": "sap"}'
```

### Logs de Debug

Para ativar logs detalhados:
```bash
export LOG_LEVEL=DEBUG
docker-compose restart omnicore-api
```

### Performance Tuning

#### Para volumes altos:
```yaml
# docker-compose.override.yml
services:
  omnicore-api:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: '2'
  
  omnicore-worker:
    deploy:
      replicas: 5
```

#### Configuração Redis:
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
```

### Backup e Recuperação

#### Backup diário automatizado:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U omnicore omnicore_db > backup_${DATE}.sql

# Backup arquivos
tar -czf files_${DATE}.tar.gz data/ uploads/

# Upload para S3/storage
aws s3 cp backup_${DATE}.sql s3://omnicore-backups/
```

#### Recuperação:
```bash
# Restaurar banco
docker-compose exec postgres psql -U omnicore omnicore_db < backup_20240115.sql

# Restaurar arquivos
tar -xzf files_20240115.tar.gz
```

---

## 🚀 Deploy em Produção

### Configurações Importantes

#### 1. Variáveis de Ambiente
```bash
ENV=production
DEBUG=false
SECRET_KEY=chave_super_secreta_producao
JWT_SECRET=chave_jwt_producao_complexa
```

#### 2. Configuração SSL
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/omnicore.crt;
    ssl_certificate_key /etc/ssl/private/omnicore.key;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

#### 3. Monitoramento
- Configurar Sentry para errors
- Alertas no Slack/Teams
- Backup automatizado
- Logs centralizados

### Checklist de Deploy

- [ ] Configurações de produção aplicadas
- [ ] SSL configurado
- [ ] Backup configurado
- [ ] Monitoramento ativo
- [ ] Logs estruturados
- [ ] Testes de carga realizados
- [ ] Documentação atualizada
- [ ] Equipe treinada

---

## 📞 Suporte e Contribuição

### Suporte Técnico
- **Email**: suporte@omnicore.ai
- **Documentação**: https://docs.omnicore.ai
- **Issues**: GitHub Issues

### Contribuição
1. Fork o projeto
2. Crie branch feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Abra Pull Request

### Licença
MIT License - veja LICENSE.md para detalhes.

---

**OmniCore AI** - Transformando empresas com IA inteligente e automação de processos.

*Versão: 1.0.0 | Última atualização: Janeiro 2024*