# OmniCore AI - Sistema de Testes Automatizados
# Testes unitários, integração, end-to-end e performance

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
import aiofiles
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

# Imports dos módulos do OmniCore
from omnicore_main import OmniCoreAgent, ProcessContext, TaskStatus, DecisionConfidence
from omnicore_api import app
from omnicore_connectors import SAPConnector, SalesforceConnector, ConnectionConfig
from omnicore_documents import DocumentProcessor, DocumentAnalysisResult
from omnicore_learning import AdvancedLearningSystem, ModelManager
from omnicore_workflows import WorkflowEngine, WorkflowBuilder
from omnicore_monitoring import MonitoringSystem, MetricsCollector

# Configurações de teste
TEST_CONFIG = {
    "integrations": {
        "sap": {
            "endpoint": "https://sap-test.example.com",
            "username": "test_user",
            "password": "test_pass"
        },
        "salesforce": {
            "endpoint": "https://test.salesforce.com",
            "client_id": "test_client",
            "client_secret": "test_secret"
        }
    },
    "security": {
        "encryption_key": "test_key_32_characters_long!!!",
        "audit_logs": True
    },
    "llm": {
        "api_key": "test_openai_key",
        "model": "gpt-3.5-turbo"
    }
}

# Fixtures para testes

@pytest.fixture
def test_config():
    """Configuração de teste"""
    return TEST_CONFIG.copy()

@pytest.fixture
def process_context():
    """Contexto de processo para testes"""
    return ProcessContext(
        process_id="test_proc_001",
        user_id="test_user_123",
        company_id="test_company_456",
        department="testing"
    )

@pytest.fixture
async def omnicore_agent(test_config):
    """Agente OmniCore para testes"""
    agent = OmniCoreAgent(test_config)
    yield agent
    # Cleanup se necessário

@pytest.fixture
def sample_document():
    """Documento de exemplo para testes"""
    content = """
    CONTRATO DE PRESTAÇÃO DE SERVIÇOS
    
    Contratante: João Silva
    CPF: 123.456.789-01
    
    Contratada: Empresa XYZ LTDA
    CNPJ: 12.345.678/0001-99
    
    Valor: R$ 15.000,00
    Data: 15/01/2024
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def test_client():
    """Cliente de teste para API"""
    return TestClient(app)

# Testes Unitários - Agente Principal

class TestOmniCoreAgent:
    """Testes do agente principal"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_config):
        """Testa inicialização do agente"""
        agent = OmniCoreAgent(test_config)
        
        assert agent.config == test_config
        assert agent.agent_id is not None
        assert len(agent.active_processes) == 0
        assert len(agent.decision_history) == 0
    
    @pytest.mark.asyncio
    async def test_document_analysis(self, omnicore_agent, sample_document, process_context):
        """Testa análise de documento"""
        result = await omnicore_agent.analisar_documento(
            sample_document,
            process_context,
            "completa"
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.result is not None
        assert "extracted_text" in result.result
        assert "entities" in result.result
        assert "classification" in result.result
    
    @pytest.mark.asyncio
    async def test_process_execution(self, omnicore_agent, process_context):
        """Testa execução de processo"""
        parametros = {
            "cliente_id": "test_cliente_001",
            "documentos": ["doc1.pdf", "doc2.pdf"]
        }
        
        result = await omnicore_agent.executar_processo(
            "onboarding_cliente",
            parametros,
            process_context
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.execution_time is not None
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_decision_making(self, omnicore_agent, process_context):
        """Testa tomada de decisão"""
        dados_entrada = {
            "tipo": "aprovacao_credito",
            "valor": 50000,
            "score": 750,
            "renda": 8000
        }
        
        decisao = await omnicore_agent.decidir(dados_entrada, process_context)
        
        assert decisao.decision_id is not None
        assert decisao.decision in ["aprovar", "rejeitar", "escalar"]
        assert isinstance(decisao.confidence, DecisionConfidence)
        assert decisao.reasoning is not None
    
    @pytest.mark.asyncio
    async def test_learning_system(self, omnicore_agent):
        """Testa sistema de aprendizado"""
        feedback = {
            "score": 0.8,
            "outcome": "success",
            "comments": "Decisão correta"
        }
        
        result = await omnicore_agent.aprender(feedback)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_report_generation(self, omnicore_agent, process_context):
        """Testa geração de relatórios"""
        parametros = {
            "periodo": "mensal",
            "departamento": "vendas"
        }
        
        result = await omnicore_agent.gerar_relatorio(
            "performance",
            parametros,
            process_context
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.result is not None
    
    @pytest.mark.asyncio
    async def test_api_integration(self, omnicore_agent, process_context):
        """Testa integração com APIs"""
        dados = {
            "operation": "get_customer",
            "customer_id": "123"
        }
        
        result = await omnicore_agent.conectar_api(
            "salesforce",
            "query",
            dados,
            process_context
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.result is not None

# Testes Unitários - Processamento de Documentos

class TestDocumentProcessor:
    """Testes do processador de documentos"""
    
    @pytest.fixture
    def document_processor(self):
        """Processador de documentos para testes"""
        config = {
            "ocr_engine": "tesseract",
            "tesseract_path": "/usr/bin/tesseract"
        }
        return DocumentProcessor(config)
    
    def test_metadata_extraction(self, document_processor, sample_document):
        """Testa extração de metadados"""
        metadata = document_processor._extract_metadata(sample_document)
        
        assert metadata.filename is not None
        assert metadata.file_type == ".txt"
        assert metadata.file_size > 0
        assert metadata.creation_date is not None
    
    @pytest.mark.asyncio
    async def test_text_extraction_txt(self, document_processor, sample_document):
        """Testa extração de texto de arquivo TXT"""
        text = await document_processor._extract_text(sample_document, ".txt")
        
        assert "CONTRATO" in text
        assert "123.456.789-01" in text
        assert "R$ 15.000,00" in text
    
    def test_brazilian_entity_extraction(self, document_processor):
        """Testa extração de entidades brasileiras"""
        text = """
        Cliente: João Silva
        CPF: 123.456.789-01
        CNPJ: 12.345.678/0001-99
        Telefone: (11) 99999-9999
        Email: joao@email.com
        Valor: R$ 1.500,00
        """
        
        entities = document_processor._extract_brazilian_entities(text)
        
        # Verificar se entidades foram extraídas
        entity_types = [e.type for e in entities]
        assert "cpf" in entity_types
        assert "cnpj" in entity_types
        assert "telefone" in entity_types
        assert "email" in entity_types
        assert "valor_monetario" in entity_types
    
    @pytest.mark.asyncio
    async def test_document_classification(self, document_processor):
        """Testa classificação de documentos"""
        text = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS entre as partes..."
        entities = [
            {"type": "cpf", "value": "123.456.789-01"},
            {"type": "cnpj", "value": "12.345.678/0001-99"}
        ]
        
        classification, confidence = await document_processor._classify_document(text, entities)
        
        assert classification in ["contrato", "documento_generico"]
        assert 0 <= confidence <= 1

# Testes Unitários - Conectores

class TestConnectors:
    """Testes dos conectores de integração"""
    
    def test_sap_connector_initialization(self):
        """Testa inicialização do conector SAP"""
        config = ConnectionConfig(
            system_name="sap",
            endpoint="https://sap.test.com",
            auth_type="basic",
            credentials={"username": "test", "password": "test"}
        )
        
        connector = SAPConnector(config)
        assert connector.config == config
        assert connector.csrf_token is None
    
    def test_salesforce_connector_initialization(self):
        """Testa inicialização do conector Salesforce"""
        config = ConnectionConfig(
            system_name="salesforce",
            endpoint="https://test.salesforce.com",
            auth_type="oauth2",
            credentials={
                "client_id": "test_id",
                "client_secret": "test_secret"
            }
        )
        
        connector = SalesforceConnector(config)
        assert connector.config == config
        assert connector.access_token is None

# Testes Unitários - Sistema de Aprendizado

class TestLearningSystem:
    """Testes do sistema de aprendizado"""
    
    @pytest.fixture
    def model_manager(self):
        """Gerenciador de modelos para testes"""
        return ModelManager("test_models")
    
    @pytest.fixture
    def learning_system(self):
        """Sistema de aprendizado para testes"""
        config = {"models_path": "test_models"}
        return AdvancedLearningSystem(config)
    
    def test_model_manager_initialization(self, model_manager):
        """Testa inicialização do gerenciador de modelos"""
        assert len(model_manager.models) == 0
        assert len(model_manager.scalers) == 0
        assert len(model_manager.encoders) == 0
    
    def test_training_data_preparation(self, model_manager):
        """Testa preparação de dados de treinamento"""
        training_data = [
            {"score": 0.8, "amount": 5000, "risk_level": 2, "decision": "approve", "user_feedback": 0.9},
            {"score": 0.3, "amount": 50000, "risk_level": 8, "decision": "reject", "user_feedback": 0.8},
            {"score": 0.7, "amount": 15000, "risk_level": 4, "decision": "approve", "user_feedback": 0.7}
        ]
        
        # Teste simples de validação de dados
        assert len(training_data) >= 3
        assert all("decision" in item for item in training_data)
    
    @pytest.mark.asyncio
    async def test_feedback_processing(self, learning_system):
        """Testa processamento de feedback"""
        feedback = {
            "score": 0.8,
            "outcome": "success",
            "decision_data": {"score": 0.7, "amount": 10000}
        }
        
        update = await learning_system.process_feedback(feedback)
        
        assert update.update_id is not None
        assert update.source == "feedback"

# Testes Unitários - Workflows

class TestWorkflowEngine:
    """Testes do motor de workflows"""
    
    @pytest.fixture
    def workflow_engine(self):
        """Motor de workflows para testes"""
        return WorkflowEngine()
    
    def test_workflow_builder(self):
        """Testa construção de workflow"""
        builder = WorkflowBuilder("test_workflow", "Workflow de Teste")
        
        workflow = (builder
                   .start()
                   .service_task("task1", "Tarefa 1", "service1", "operation1")
                   .human_task("task2", "Tarefa Humana", "user@test.com")
                   .end()
                   .build())
        
        assert workflow.workflow_id == "test_workflow"
        assert workflow.name == "Workflow de Teste"
        assert len(workflow.nodes) == 4  # start, task1, task2, end
        
        # Verificar validação
        errors = workflow.validate()
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, workflow_engine):
        """Testa execução de workflow"""
        # Criar workflow simples
        builder = WorkflowBuilder("simple_workflow", "Workflow Simples")
        workflow = (builder
                   .start()
                   .service_task("process", "Processar", "test_service", "process")
                   .end()
                   .build())
        
        workflow_engine.register_workflow(workflow)
        
        # Executar
        execution_id = await workflow_engine.start_workflow(
            "simple_workflow",
            "test_user",
            "test_company",
            {"input": "test_data"}
        )
        
        assert execution_id is not None
        
        # Verificar status
        status = workflow_engine.get_execution_status(execution_id)
        assert status["execution_id"] == execution_id

# Testes de Integração - API

class TestAPI:
    """Testes de integração da API"""
    
    def test_health_endpoint(self, test_client):
        """Testa endpoint de health check"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agent_id" in data
    
    def test_document_analysis_endpoint(self, test_client):
        """Testa endpoint de análise de documentos"""
        # Criar arquivo de teste
        test_content = b"Contrato de teste com CPF 123.456.789-01"
        
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {
            "tipo_analise": "completa",
            "user_id": "test_user",
            "company_id": "test_company"
        }
        
        with patch('omnicore_api.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.analisar_documento.return_value = Mock(
                status=TaskStatus.COMPLETED,
                result={"classification": "contrato", "entities": []},
                execution_time=1.5,
                logs=["Documento processado"]
            )
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/documentos/analisar",
                files=files,
                data=data
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "completed"
    
    def test_process_execution_endpoint(self, test_client):
        """Testa endpoint de execução de processos"""
        data = {
            "processo_nome": "test_process",
            "parametros": {"param1": "value1"},
            "user_id": "test_user",
            "company_id": "test_company"
        }
        
        with patch('omnicore_api.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.executar_processo.return_value = Mock(
                task_id="task_123",
                status=TaskStatus.COMPLETED,
                result={"success": True},
                execution_time=2.0,
                logs=["Processo executado"]
            )
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/processos/executar", json=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "completed"
    
    def test_decision_endpoint(self, test_client):
        """Testa endpoint de tomada de decisão"""
        data = {
            "dados_entrada": {"score": 0.8, "amount": 10000},
            "user_id": "test_user",
            "company_id": "test_company"
        }
        
        with patch('omnicore_api.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.decidir.return_value = Mock(
                decision_id="decision_123",
                decision="approve",
                confidence=DecisionConfidence.HIGH,
                reasoning="Score alto",
                timestamp=datetime.now()
            )
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/decisoes/tomar", json=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["decision"] == "approve"

# Testes de Performance

class TestPerformance:
    """Testes de performance do sistema"""
    
    @pytest.mark.asyncio
    async def test_document_processing_performance(self, omnicore_agent, process_context):
        """Testa performance do processamento de documentos"""
        # Criar múltiplos documentos de teste
        documents = []
        for i in range(10):
            content = f"Documento de teste {i} com CPF 123.456.789-0{i}"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                documents.append(f.name)
        
        try:
            start_time = datetime.now()
            
            # Processar documentos em paralelo
            tasks = [
                omnicore_agent.analisar_documento(doc, process_context, "completa")
                for doc in documents
            ]
            
            results = await asyncio.gather(*tasks)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Verificações de performance
            assert total_time < 30  # Menos de 30 segundos para 10 documentos
            assert all(r.status == TaskStatus.COMPLETED for r in results)
            
            avg_time = total_time / len(documents)
            assert avg_time < 5  # Menos de 5 segundos por documento em média
            
        finally:
            # Cleanup
            for doc in documents:
                os.unlink(doc)
    
    @pytest.mark.asyncio
    async def test_concurrent_decisions(self, omnicore_agent, process_context):
        """Testa decisões concorrentes"""
        # Criar múltiplas decisões
        decision_data = [
            {"tipo": "credit", "score": 0.8, "amount": 5000 + i * 1000}
            for i in range(20)
        ]
        
        start_time = datetime.now()
        
        # Executar decisões em paralelo
        tasks = [
            omnicore_agent.decidir(data, process_context)
            for data in decision_data
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Verificações
        assert total_time < 10  # Menos de 10 segundos para 20 decisões
        assert len(results) == 20
        assert all(r.decision_id is not None for r in results)

# Testes End-to-End

class TestEndToEnd:
    """Testes end-to-end do sistema completo"""
    
    @pytest.mark.asyncio
    async def test_complete_document_workflow(self, test_client):
        """Testa workflow completo de processamento de documento"""
        # 1. Upload e análise de documento
        test_content = b"""
        CONTRATO DE PRESTACAO DE SERVICOS
        Cliente: Joao Silva
        CPF: 123.456.789-01
        Valor: R$ 25.000,00
        """
        
        files = {"file": ("contrato.txt", test_content, "text/plain")}
        data = {
            "tipo_analise": "completa",
            "user_id": "test_user",
            "company_id": "test_company"
        }
        
        with patch('omnicore_api.get_agent') as mock_get_agent:
            # Mock do agente para análise de documento
            mock_agent = AsyncMock()
            mock_agent.analisar_documento.return_value = Mock(
                task_id="doc_task_123",
                status=TaskStatus.COMPLETED,
                result={
                    "classification": "contrato",
                    "entities": [
                        {"type": "cpf", "value": "123.456.789-01"},
                        {"type": "valor_monetario", "value": "R$ 25.000,00"}
                    ],
                    "confidence": 0.92
                },
                execution_time=3.2,
                logs=["Documento analisado com sucesso"]
            )
            
            # Mock para tomada de decisão
            mock_agent.decidir.return_value = Mock(
                decision_id="decision_123",
                decision="aprovar",
                confidence=DecisionConfidence.HIGH,
                reasoning="Documento válido com alta confiança",
                timestamp=datetime.now()
            )
            
            # Mock para execução de processo
            mock_agent.executar_processo.return_value = Mock(
                task_id="process_123",
                status=TaskStatus.COMPLETED,
                result={"contract_processed": True, "status": "approved"},
                execution_time=5.1,
                logs=["Processo de contrato executado"]
            )
            
            mock_get_agent.return_value = mock_agent
            
            # 1. Analisar documento
            response = test_client.post(
                "/documentos/analisar",
                files=files,
                data=data
            )
            
            assert response.status_code == 200
            doc_result = response.json()
            assert doc_result["status"] == "completed"
            assert doc_result["result"]["classification"] == "contrato"
            
            # 2. Tomar decisão baseada na análise
            decision_data = {
                "dados_entrada": {
                    "document_classification": "contrato",
                    "confidence": 0.92,
                    "value": 25000
                },
                "user_id": "test_user",
                "company_id": "test_company"
            }
            
            response = test_client.post("/decisoes/tomar", json=decision_data)
            
            assert response.status_code == 200
            decision_result = response.json()
            assert decision_result["decision"] == "aprovar"
            
            # 3. Executar processo baseado na decisão
            process_data = {
                "processo_nome": "processar_contrato",
                "parametros": {
                    "document_id": doc_result["task_id"],
                    "decision": decision_result["decision"]
                },
                "user_id": "test_user",
                "company_id": "test_company"
            }
            
            response = test_client.post("/processos/executar", json=process_data)
            
            assert response.status_code == 200
            process_result = response.json()
            assert process_result["status"] == "completed"
            assert process_result["result"]["contract_processed"] is True
    
    @pytest.mark.asyncio
    async def test_integration_workflow(self, test_client):
        """Testa workflow de integração com sistemas externos"""
        # Simular integração SAP -> Decisão -> Salesforce
        
        with patch('omnicore_api.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            
            # Mock para integração SAP
            mock_agent.conectar_api.return_value = Mock(
                task_id="sap_integration_123",
                status=TaskStatus.COMPLETED,
                result={
                    "system": "sap",
                    "operation": "get_customer",
                    "data": {"customer_id": "123", "status": "active", "credit_score": 750}
                },
                execution_time=2.1,
                logs=["Integração SAP realizada"]
            )
            
            mock_get_agent.return_value = mock_agent
            
            # 1. Buscar dados no SAP
            sap_data = {
                "sistema": "sap",
                "operacao": "get_customer",
                "dados": {"customer_id": "123"},
                "user_id": "test_user",
                "company_id": "test_company"
            }
            
            response = test_client.post("/integracoes/executar", json=sap_data)
            
            assert response.status_code == 200
            sap_result = response.json()
            assert sap_result["status"] == "completed"
            
            customer_data = sap_result["result"]["data"]
            
            # Mock para decisão baseada nos dados do SAP
            mock_agent.decidir.return_value = Mock(
                decision_id="credit_decision_123",
                decision="aprovar_credito",
                confidence=DecisionConfidence.HIGH,
                reasoning=f"Score de crédito alto: {customer_data['credit_score']}",
                timestamp=datetime.now()
            )
            
            # 2. Tomar decisão baseada nos dados
            decision_data = {
                "dados_entrada": {
                    "customer_data": customer_data,
                    "credit_score": customer_data["credit_score"]
                },
                "user_id": "test_user",
                "company_id": "test_company"
            }
            
            response = test_client.post("/decisoes/tomar", json=decision_data)
            
            assert response.status_code == 200
            decision_result = response.json()
            assert "aprovar" in decision_result["decision"]
            
            # Mock para atualização no Salesforce
            mock_agent.conectar_api.return_value = Mock(
                task_id="sf_integration_123",
                status=TaskStatus.COMPLETED,
                result={
                    "system": "salesforce",
                    "operation": "update_opportunity",
                    "record_id": "opp_123"
                },
                execution_time=1.8,
                logs=["Oportunidade atualizada no Salesforce"]
            )
            
            # 3. Atualizar Salesforce com decisão
            sf_data = {
                "sistema": "salesforce",
                "operacao": "update_opportunity",
                "dados": {
                    "customer_id": "123",
                    "decision": decision_result["decision"],
                    "credit_approved": True
                },
                "user_id": "test_user",
                "company_id": "test_company"
            }
            
            response = test_client.post("/integracoes/executar", json=sf_data)
            
            assert response.status_code == 200
            sf_result = response.json()
            assert sf_result["status"] == "completed"

# Testes de Monitoramento

class TestMonitoring:
    """Testes do sistema de monitoramento"""
    
    @pytest.fixture
    def monitoring_config(self):
        """Configuração de monitoramento para testes"""
        return {
            "metrics": {
                "collection_interval": 5,
                "prometheus_port": 8002
            },
            "alerts": {
                "email_notifications": {"enabled": False},
                "slack_notifications": {"enabled": False}
            }
        }
    
    def test_metrics_collector_initialization(self, monitoring_config):
        """Testa inicialização do coletor de métricas"""
        collector = MetricsCollector(monitoring_config["metrics"])
        
        assert collector.config == monitoring_config["metrics"]
        assert collector.request_count is not None
        assert collector.request_duration is not None
    
    def test_metrics_recording(self, monitoring_config):
        """Testa gravação de métricas"""
        collector = MetricsCollector(monitoring_config["metrics"])
        
        # Registrar algumas métricas
        collector.record_request("POST", "/api/test", 200, 1.5)
        collector.record_document_processing("contract", 3.2)
        collector.record_decision("credit", "high", 0.92)
        collector.set_integration_status("sap", True)
        
        # Verificar se não há erros
        current_metrics = collector.get_current_metrics()
        assert current_metrics is not None

# Utilitários para testes

class TestUtils:
    """Utilitários para auxiliar nos testes"""
    
    @staticmethod
    def create_test_document(content: str, file_type: str = ".txt") -> str:
        """Cria documento de teste temporário"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=file_type, delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def cleanup_test_files(file_paths: List[str]):
        """Remove arquivos de teste"""
        for path in file_paths:
            try:
                os.unlink(path)
            except:
                pass
    
    @staticmethod
    def generate_test_data(count: int) -> List[Dict[str, Any]]:
        """Gera dados de teste"""
        return [
            {
                "id": f"test_{i}",
                "value": i * 100,
                "category": f"category_{i % 3}",
                "timestamp": datetime.now().isoformat()
            }
            for i in range(count)
        ]

# Configuração de pytest

def pytest_configure(config):
    """Configuração do pytest"""
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

# Markers personalizados
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance

# Exemplo de execução
if __name__ == "__main__":
    # Executar testes específicos
    pytest.main([
        "-v",
        "--tb=short",
        "--cov=omnicore",
        "--cov-report=html",
        "--cov-report=term-missing",
        __file__
    ])