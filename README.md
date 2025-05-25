# 🤖 OmniCore AI

**Agente de IA Empresarial Autônomo e Inteligente**

## 🚀 Instalação Rápida

### Pré-requisitos
- Docker 20.0+
- Docker Compose 2.0+
- 8GB RAM

### Deploy com Docker

```bash
# Clone o projeto
git clone https://github.com/suaempresa/omnicore-ai.git
cd omnicore-ai

# Configure variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Inicie todos os serviços
docker-compose up -d

# Verifique status
curl http://localhost:8000/health
```

### Acesso ao Sistema

- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090

## 🧪 Teste Rápido

```bash
# Criar documento de teste
echo "CONTRATO - Cliente: João Silva - CPF: 123.456.789-01" > teste.txt

# Analisar documento
curl -X POST "http://localhost:8000/documentos/analisar" \
  -F "file=@teste.txt" \
  -F "user_id=teste" \
  -F "company_id=demo"
```

## 📊 Características

- 🤖 **IA Avançada**: Processamento inteligente de documentos
- 🔗 **Integrações**: SAP, Salesforce, ERPs, CRMs
- 🔄 **Workflows**: Automação de processos complexos
- 📊 **Monitoramento**: Métricas em tempo real
- 🔐 **Segurança**: LGPD/GDPR compliance

## 🛠️ Comandos Úteis

```bash
# Ver logs
docker-compose logs -f omnicore-api

# Reiniciar API
docker-compose restart omnicore-api

# Parar tudo
docker-compose down
```

## 📞 Suporte

- Email: suporte@omnicore.ai
- Docs: https://docs.omnicore.ai

**Desenvolvido com ❤️ para revolucionar processos empresariais**
