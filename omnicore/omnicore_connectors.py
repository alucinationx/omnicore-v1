# OmniCore AI - Conectores de Integração Empresarial
# Sistema modular de conectores para ERP, CRM e outros sistemas

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import base64
import hashlib
import hmac
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Configuração de logging
logger = logging.getLogger("OmniCore.Connectors")

@dataclass
class ConnectionConfig:
    """Configuração de conexão para sistemas externos"""
    system_name: str
    endpoint: str
    auth_type: str  # "oauth2", "basic", "api_key", "certificate"
    credentials: Dict[str, str]
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit: int = 100  # requests per minute

@dataclass
class IntegrationResult:
    """Resultado de operação de integração"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    metadata: Dict[str, Any] = None

class BaseConnector(ABC):
    """Classe base para todos os conectores"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.session = None
        self.logger = logging.getLogger(f"OmniCore.Connectors.{config.system_name}")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Autentica no sistema externo"""
        pass
    
    @abstractmethod
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> IntegrationResult:
        """Executa operação específica do sistema"""
        pass
    
    async def test_connection(self) -> bool:
        """Testa conectividade com o sistema"""
        try:
            result = await self.execute_operation("health_check", {})
            return result.success
        except Exception as e:
            self.logger.error(f"Teste de conexão falhou: {str(e)}")
            return False

class SAPConnector(BaseConnector):
    """Conector para SAP S/4HANA via OData API"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.csrf_token = None
        self.cookies = None
    
    async def authenticate(self) -> bool:
        """Autenticação SAP com CSRF token"""
        try:
            # Primeiro, obter CSRF token
            headers = {
                "X-CSRF-Token": "Fetch",
                "Authorization": self._get_auth_header()
            }
            
            async with self.session.get(
                f"{self.config.endpoint}/sap/opu/odata/sap/API_BUSINESS_PARTNER/",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.csrf_token = response.headers.get("X-CSRF-Token")
                    self.cookies = response.cookies
                    self.logger.info("Autenticação SAP realizada com sucesso")
                    return True
                else:
                    self.logger.error(f"Falha na autenticação SAP: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Erro na autenticação SAP: {str(e)}")
            return False
    
    def _get_auth_header(self) -> str:
        """Gera header de autenticação básica"""
        credentials = f"{self.config.credentials['username']}:{self.config.credentials['password']}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> IntegrationResult:
        """Executa operações SAP"""
        start_time = datetime.now()
        
        try:
            if operation == "get_business_partners":
                return await self._get_business_partners(data)
            elif operation == "create_sales_order":
                return await self._create_sales_order(data)
            elif operation == "get_financial_data":
                return await self._get_financial_data(data)
            elif operation == "health_check":
                return await self._health_check()
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Operação não suportada: {operation}"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _get_business_partners(self, params: Dict[str, Any]) -> IntegrationResult:
        """Busca parceiros de negócio"""
        filter_params = params.get("filters", {})
        
        # Construir filtro OData
        odata_filter = self._build_odata_filter(filter_params)
        url = f"{self.config.endpoint}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner"
        
        if odata_filter:
            url += f"?$filter={odata_filter}"
        
        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json"
        }
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return IntegrationResult(
                    success=True,
                    data=data.get("d", {}).get("results", []),
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return IntegrationResult(
                    success=False,
                    error=f"Erro SAP: {error_text}",
                    status_code=response.status
                )
    
    async def _create_sales_order(self, order_data: Dict[str, Any]) -> IntegrationResult:
        """Cria pedido de venda"""
        headers = {
            "Authorization": self._get_auth_header(),
            "X-CSRF-Token": self.csrf_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        url = f"{self.config.endpoint}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"
        
        async with self.session.post(url, headers=headers, json=order_data) as response:
            if response.status in [200, 201]:
                data = await response.json()
                return IntegrationResult(
                    success=True,
                    data=data,
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return IntegrationResult(
                    success=False,
                    error=f"Erro ao criar pedido: {error_text}",
                    status_code=response.status
                )
    
    async def _health_check(self) -> IntegrationResult:
        """Verifica status do sistema SAP"""
        url = f"{self.config.endpoint}/sap/bc/rest/system/info"
        headers = {"Authorization": self._get_auth_header()}
        
        async with self.session.get(url, headers=headers) as response:
            return IntegrationResult(
                success=response.status == 200,
                status_code=response.status
            )
    
    def _build_odata_filter(self, filters: Dict[str, Any]) -> str:
        """Constrói filtro OData"""
        filter_parts = []
        for field, value in filters.items():
            if isinstance(value, str):
                filter_parts.append(f"{field} eq '{value}'")
            else:
                filter_parts.append(f"{field} eq {value}")
        return " and ".join(filter_parts)

class SalesforceConnector(BaseConnector):
    """Conector para Salesforce via REST API"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.access_token = None
        self.instance_url = None
    
    async def authenticate(self) -> bool:
        """Autenticação OAuth2 no Salesforce"""
        try:
            auth_data = {
                "grant_type": "password",
                "client_id": self.config.credentials["client_id"],
                "client_secret": self.config.credentials["client_secret"],
                "username": self.config.credentials["username"],
                "password": self.config.credentials["password"]
            }
            
            url = f"{self.config.endpoint}/services/oauth2/token"
            
            async with self.session.post(url, data=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["access_token"]
                    self.instance_url = data["instance_url"]
                    self.logger.info("Autenticação Salesforce realizada com sucesso")
                    return True
                else:
                    self.logger.error(f"Falha na autenticação Salesforce: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Erro na autenticação Salesforce: {str(e)}")
            return False
    
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> IntegrationResult:
        """Executa operações Salesforce"""
        start_time = datetime.now()
        
        try:
            if operation == "query":
                return await self._execute_soql(data.get("soql", ""))
            elif operation == "create_record":
                return await self._create_record(data.get("object"), data.get("fields"))
            elif operation == "update_record":
                return await self._update_record(data.get("object"), data.get("id"), data.get("fields"))
            elif operation == "get_opportunities":
                return await self._get_opportunities(data)
            elif operation == "health_check":
                return await self._health_check()
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Operação não suportada: {operation}"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_soql(self, soql: str) -> IntegrationResult:
        """Executa query SOQL"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.instance_url}/services/data/v58.0/query"
        params = {"q": soql}
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return IntegrationResult(
                    success=True,
                    data=data.get("records", []),
                    status_code=response.status,
                    metadata={"totalSize": data.get("totalSize")}
                )
            else:
                error_text = await response.text()
                return IntegrationResult(
                    success=False,
                    error=f"Erro SOQL: {error_text}",
                    status_code=response.status
                )
    
    async def _create_record(self, sobject: str, fields: Dict[str, Any]) -> IntegrationResult:
        """Cria registro no Salesforce"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.instance_url}/services/data/v58.0/sobjects/{sobject}"
        
        async with self.session.post(url, headers=headers, json=fields) as response:
            if response.status in [200, 201]:
                data = await response.json()
                return IntegrationResult(
                    success=True,
                    data=data,
                    status_code=response.status
                )
            else:
                error_text = await response.text()
                return IntegrationResult(
                    success=False,
                    error=f"Erro ao criar registro: {error_text}",
                    status_code=response.status
                )
    
    async def _health_check(self) -> IntegrationResult:
        """Verifica status do Salesforce"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.instance_url}/services/data/v58.0/limits"
        
        async with self.session.get(url, headers=headers) as response:
            return IntegrationResult(
                success=response.status == 200,
                status_code=response.status
            )

class DatabaseConnector(BaseConnector):
    """Conector para bancos de dados SQL/NoSQL"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.engine = None
    
    async def authenticate(self) -> bool:
        """Estabelece conexão com banco de dados"""
        try:
            connection_string = self._build_connection_string()
            self.engine = create_async_engine(connection_string)
            
            # Testar conexão
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.logger.info("Conexão com banco de dados estabelecida")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na conexão com banco: {str(e)}")
            return False
    
    def _build_connection_string(self) -> str:
        """Constrói string de conexão"""
        creds = self.config.credentials
        db_type = creds.get("type", "postgresql")
        
        if db_type == "postgresql":
            return f"postgresql+asyncpg://{creds['username']}:{creds['password']}@{creds['host']}:{creds.get('port', 5432)}/{creds['database']}"
        elif db_type == "mysql":
            return f"mysql+aiomysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds.get('port', 3306)}/{creds['database']}"
        elif db_type == "sqlserver":
            return f"mssql+aiodbc://{creds['username']}:{creds['password']}@{creds['host']}:{creds.get('port', 1433)}/{creds['database']}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Tipo de banco não suportado: {db_type}")
    
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> IntegrationResult:
        """Executa operações no banco de dados"""
        start_time = datetime.now()
        
        try:
            if operation == "query":
                return await self._execute_query(data.get("sql", ""))
            elif operation == "insert":
                return await self._execute_insert(data.get("table"), data.get("data"))
            elif operation == "update":
                return await self._execute_update(data.get("table"), data.get("data"), data.get("where"))
            elif operation == "health_check":
                return await self._health_check()
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Operação não suportada: {operation}"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_query(self, sql: str) -> IntegrationResult:
        """Executa query SQL"""
        async with self.engine.connect() as conn:
            result = await conn.execute(text(sql))
            rows = result.fetchall()
            
            # Converter para lista de dicionários
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            
            return IntegrationResult(
                success=True,
                data=data,
                metadata={"row_count": len(data)}
            )
    
    async def _health_check(self) -> IntegrationResult:
        """Verifica status do banco"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return IntegrationResult(success=True)
        except Exception:
            return IntegrationResult(success=False)

class EmailConnector(BaseConnector):
    """Conector para sistemas de email (Outlook, Gmail)"""
    
    async def authenticate(self) -> bool:
        """Autenticação email"""
        # Implementar OAuth2 para Gmail/Outlook
        return True
    
    async def execute_operation(self, operation: str, data: Dict[str, Any]) -> IntegrationResult:
        """Operações de email"""
        if operation == "send_email":
            return await self._send_email(data)
        elif operation == "read_emails":
            return await self._read_emails(data)
        else:
            return IntegrationResult(success=False, error="Operação não suportada")
    
    async def _send_email(self, email_data: Dict[str, Any]) -> IntegrationResult:
        """Envia email"""
        # Implementar envio via SMTP ou API
        return IntegrationResult(
            success=True,
            data={"message_id": "email_123", "status": "sent"}
        )
    
    async def _read_emails(self, params: Dict[str, Any]) -> IntegrationResult:
        """Lê emails"""
        # Implementar leitura via IMAP ou API
        return IntegrationResult(
            success=True,
            data=[{"id": "1", "subject": "Test", "body": "Email content"}]
        )

class ConnectorFactory:
    """Factory para criação de conectores"""
    
    _connectors = {
        "sap": SAPConnector,
        "salesforce": SalesforceConnector,
        "database": DatabaseConnector,
        "email": EmailConnector
    }
    
    @classmethod
    def create_connector(cls, config: ConnectionConfig) -> BaseConnector:
        """Cria conector baseado na configuração"""
        system_type = config.system_name.lower()
        
        if system_type not in cls._connectors:
            raise ValueError(f"Conector não suportado: {system_type}")
        
        return cls._connectors[system_type](config)
    
    @classmethod
    def register_connector(cls, name: str, connector_class: type):
        """Registra novo tipo de conector"""
        cls._connectors[name] = connector_class

class IntegrationOrchestrator:
    """Orquestrador de integrações"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.logger = logging.getLogger("OmniCore.IntegrationOrchestrator")
    
    async def add_connector(self, name: str, config: ConnectionConfig):
        """Adiciona novo conector"""
        try:
            connector = ConnectorFactory.create_connector(config)
            async with connector as conn:
                if await conn.test_connection():
                    self.connectors[name] = connector
                    self.logger.info(f"Conector {name} adicionado com sucesso")
                    return True
                else:
                    self.logger.error(f"Falha no teste de conexão para {name}")
                    return False
        except Exception as e:
            self.logger.error(f"Erro ao adicionar conector {name}: {str(e)}")
            return False
    
    async def execute_integration(self, 
                                connector_name: str, 
                                operation: str, 
                                data: Dict[str, Any]) -> IntegrationResult:
        """Executa integração específica"""
        if connector_name not in self.connectors:
            return IntegrationResult(
                success=False,
                error=f"Conector {connector_name} não encontrado"
            )
        
        connector = self.connectors[connector_name]
        
        try:
            async with connector:
                return await connector.execute_operation(operation, data)
        except Exception as e:
            self.logger.error(f"Erro na integração {connector_name}: {str(e)}")
            return IntegrationResult(
                success=False,
                error=str(e)
            )
    
    async def get_connector_status(self) -> Dict[str, bool]:
        """Verifica status de todos os conectores"""
        status = {}
        
        for name, connector in self.connectors.items():
            try:
                async with connector:
                    status[name] = await connector.test_connection()
            except Exception:
                status[name] = False
        
        return status

# Exemplo de uso
async def exemplo_uso_conectores():
    """Exemplo de uso do sistema de conectores"""
    
    # Configuração SAP
    sap_config = ConnectionConfig(
        system_name="sap",
        endpoint="https://sap.empresa.com",
        auth_type="basic",
        credentials={
            "username": "usuario_sap",
            "password": "senha_sap"
        }
    )
    
    # Configuração Salesforce
    sf_config = ConnectionConfig(
        system_name="salesforce",
        endpoint="https://login.salesforce.com",
        auth_type="oauth2",
        credentials={
            "client_id": "client_id_sf",
            "client_secret": "client_secret_sf",
            "username": "usuario@empresa.com",
            "password": "senha_sf"
        }
    )
    
    # Inicializar orquestrador
    orchestrator = IntegrationOrchestrator()
    
    # Adicionar conectores
    await orchestrator.add_connector("sap_prod", sap_config)
    await orchestrator.add_connector("salesforce_prod", sf_config)
    
    # Executar integrações
    # Buscar parceiros no SAP
    sap_result = await orchestrator.execute_integration(
        "sap_prod",
        "get_business_partners",
        {"filters": {"Country": "BR"}}
    )
    
    # Consultar oportunidades no Salesforce
    sf_result = await orchestrator.execute_integration(
        "salesforce_prod",
        "query",
        {"soql": "SELECT Id, Name, Amount FROM Opportunity WHERE StageName = 'Closed Won'"}
    )
    
    print(f"SAP Result: {sap_result.success}")
    print(f"Salesforce Result: {sf_result.success}")
    
    # Verificar status
    status = await orchestrator.get_connector_status()
    print(f"Connector Status: {status}")

if __name__ == "__main__":
    asyncio.run(exemplo_uso_conectores())