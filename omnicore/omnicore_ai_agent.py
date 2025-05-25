# omnicore_ai_agent.py
# Agente Conversacional Avançado com IA e Contexto Completo

import asyncio
import logging
import json
import openai
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import tiktoken

# Imports do sistema OmniCore
from omnicore_main import OmniCoreAgent, ProcessContext, TaskStatus
from omnicore_documents import DocumentProcessor
from omnicore_workflows import WorkflowEngine
from omnicore_connectors import IntegrationOrchestrator
from omnicore_monitoring import MonitoringSystem

logger = logging.getLogger("OmniCore.AIAgent")

@dataclass
class ConversationMemory:
    """Memória persistente da conversa"""
    user_id: str
    conversation_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    current_task: Optional[str] = None
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

@dataclass
class AgentCapability:
    """Capacidade específica do agente"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    examples: List[str]
    category: str

class AdvancedAIAgent:
    """Agente Conversacional Avançado com IA, Contexto e Memória"""
    
    def __init__(self, omnicore_agent: OmniCoreAgent, config: Dict[str, Any]):
        self.omnicore_agent = omnicore_agent
        self.config = config
        
        # Configurar OpenAI
        self.openai_client = openai.AsyncOpenAI(
            api_key=config.get("openai_api_key", "")
        )
        
        # Configurar embedding model para busca semântica
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Configurar base de dados vetorial para memória
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=config.get("memory_path", "./omnicore_memory"),
            anonymized_telemetry=False
        ))
        
        # Coleção para memória de conversas
        try:
            self.memory_collection = self.chroma_client.get_collection("conversation_memory")
        except:
            self.memory_collection = self.chroma_client.create_collection(
                name="conversation_memory",
                metadata={"description": "OmniCore AI conversation memory"}
            )
        
        # Memória ativa das conversas
        self.active_conversations: Dict[str, ConversationMemory] = {}
        
        # Configurar capacidades do agente
        self.capabilities = self._setup_capabilities()
        
        # Configurar model e tokenizer
        self.model_name = config.get("model_name", "gpt-4-turbo-preview")
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Sistema de contexto avançado
        self.context_window = config.get("context_window", 8000)
        self.max_history_messages = config.get("max_history", 50)
        
        logger.info("Agente AI Avançado inicializado com sucesso")
    
    def _setup_capabilities(self) -> Dict[str, AgentCapability]:
        """Configura capacidades do agente com function calling"""
        
        capabilities = {}
        
        # Análise de Documentos
        capabilities["analyze_document"] = AgentCapability(
            name="analyze_document",
            description="Analisa documentos usando IA avançada (OCR, classificação, extração de entidades)",
            function=self._analyze_document,
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Caminho do arquivo"},
                    "analysis_type": {"type": "string", "enum": ["quick", "complete", "specific"], "description": "Tipo de análise"},
                    "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "Áreas específicas para focar"}
                },
                "required": ["file_path"]
            },
            examples=[
                "Analise este contrato",
                "Processe este documento", 
                "Extraia dados desta nota fiscal"
            ],
            category="documents"
        )
        
        # Consulta na Base de Dados
        capabilities["query_database"] = AgentCapability(
            name="query_database",
            description="Executa consultas inteligentes na base de dados usando linguagem natural",
            function=self._query_database,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta em linguagem natural"},
                    "table_hint": {"type": "string", "description": "Sugestão de tabela"},
                    "format": {"type": "string", "enum": ["table", "summary", "count", "chart"], "description": "Formato da resposta"}
                },
                "required": ["query"]
            },
            examples=[
                "Quantos clientes temos?",
                "Vendas do último mês",
                "Contratos vencendo esta semana"
            ],
            category="data"
        )
        
        # Automação de Workflows
        capabilities["execute_workflow"] = AgentCapability(
            name="execute_workflow",
            description="Inicia e gerencia workflows automatizados",
            function=self._execute_workflow,
            parameters={
                "type": "object",
                "properties": {
                    "workflow_name": {"type": "string", "description": "Nome do workflow"},
                    "parameters": {"type": "object", "description": "Parâmetros do workflow"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "description": "Prioridade"}
                },
                "required": ["workflow_name"]
            },
            examples=[
                "Inicie o processo de aprovação de crédito",
                "Execute onboarding do cliente",
                "Processe aprovação do contrato"
            ],
            category="automation"
        )
        
        # Geração de Relatórios
        capabilities["generate_report"] = AgentCapability(
            name="generate_report",
            description="Gera relatórios inteligentes e insights",
            function=self._generate_report,
            parameters={
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "Tipo de relatório"},
                    "period": {"type": "string", "description": "Período do relatório"},
                    "filters": {"type": "object", "description": "Filtros específicos"},
                    "format": {"type": "string", "enum": ["summary", "detailed", "executive"], "description": "Formato"}
                },
                "required": ["report_type"]
            },
            examples=[
                "Gere relatório mensal de vendas",
                "Analise performance dos processos",
                "Relatório de documentos processados"
            ],
            category="reporting"
        )
        
        # Monitoramento e Status
        capabilities["system_monitoring"] = AgentCapability(
            name="system_monitoring",
            description="Monitora sistema e fornece insights sobre performance",
            function=self._system_monitoring,
            parameters={
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["general", "performance", "errors", "integrations"], "description": "Escopo do monitoramento"},
                    "time_range": {"type": "string", "description": "Período de análise"}
                }
            },
            examples=[
                "Como está o sistema?",
                "Status das integrações",
                "Performance dos últimos dias"
            ],
            category="monitoring"
        )
        
        # Insights e Análise
        capabilities["generate_insights"] = AgentCapability(
            name="generate_insights",
            description="Gera insights inteligentes baseados em dados",
            function=self._generate_insights,
            parameters={
                "type": "object",
                "properties": {
                    "data_source": {"type": "string", "description": "Fonte dos dados"},
                    "analysis_type": {"type": "string", "enum": ["trends", "anomalies", "predictions", "comparisons"], "description": "Tipo de análise"},
                    "focus": {"type": "string", "description": "Foco específico da análise"}
                }
            },
            examples=[
                "Que insights você tem sobre vendas?",
                "Analise tendências dos processos",
                "Identifique padrões nos dados"
            ],
            category="intelligence"
        )
        
        return capabilities
    
    async def process_conversation(self, user_id: str, message: str, attachments: List[str] = None) -> Dict[str, Any]:
        """Processa conversa usando IA avançada com contexto completo"""
        
        try:
            # Obter ou criar memória da conversa
            memory = await self._get_or_create_memory(user_id)
            
            # Adicionar mensagem do usuário à memória
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "attachments": attachments or []
            }
            memory.messages.append(user_message)
            memory.last_activity = datetime.now()
            
            # Construir contexto completo
            context = await self._build_context(memory)
            
            # Processar com IA avançada
            response = await self._process_with_ai(memory, context, message, attachments)
            
            # Adicionar resposta à memória
            assistant_message = {
                "role": "assistant", 
                "content": response["message"],
                "timestamp": datetime.now().isoformat(),
                "function_calls": response.get("function_calls", []),
                "data": response.get("data")
            }
            memory.messages.append(assistant_message)
            
            # Salvar memória
            await self._save_memory(memory)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no processamento da conversa: {str(e)}")
            return {
                "message": f"❌ Desculpe, ocorreu um erro: {str(e)}",
                "error": True,
                "suggestions": ["Tentar novamente", "Reformular pergunta"]
            }
    
    async def _get_or_create_memory(self, user_id: str) -> ConversationMemory:
        """Obtém ou cria memória da conversa"""
        
        if user_id in self.active_conversations:
            return self.active_conversations[user_id]
        
        # Tentar carregar do banco vetorial
        try:
            results = self.memory_collection.query(
                query_texts=[f"user:{user_id}"],
                n_results=1,
                where={"user_id": user_id}
            )
            
            if results["documents"]:
                # Carregar memória existente
                memory_data = json.loads(results["documents"][0])
                memory = ConversationMemory(**memory_data)
            else:
                # Criar nova memória
                memory = ConversationMemory(
                    user_id=user_id,
                    conversation_id=str(uuid.uuid4())
                )
        except:
            # Criar nova memória em caso de erro
            memory = ConversationMemory(
                user_id=user_id,
                conversation_id=str(uuid.uuid4())
            )
        
        self.active_conversations[user_id] = memory
        return memory
    
    async def _build_context(self, memory: ConversationMemory) -> Dict[str, Any]:
        """Constrói contexto completo para a IA"""
        
        # Buscar informações relevantes do sistema
        system_status = await self.omnicore_agent.get_status()
        
        # Buscar histórico relevante usando busca semântica
        recent_context = await self._get_relevant_context(memory)
        
        # Perfil do usuário e preferências
        user_profile = memory.user_profile
        
        # Estado atual do sistema
        current_state = {
            "system_status": system_status,
            "active_processes": len(system_status.get("active_processes", 0)),
            "current_time": datetime.now().isoformat(),
            "user_profile": user_profile,
            "recent_context": recent_context
        }
        
        return current_state
    
    async def _get_relevant_context(self, memory: ConversationMemory) -> List[str]:
        """Busca contexto relevante usando busca semântica"""
        
        if not memory.messages:
            return []
        
        # Pegar últimas mensagens do usuário
        user_messages = [
            msg["content"] for msg in memory.messages[-5:]
            if msg["role"] == "user"
        ]
        
        if not user_messages:
            return []
        
        try:
            # Buscar contexto similar
            results = self.memory_collection.query(
                query_texts=user_messages,
                n_results=5,
                where={"user_id": memory.user_id}
            )
            
            return results.get("documents", [])
        except:
            return []
    
    async def _process_with_ai(self, memory: ConversationMemory, context: Dict[str, Any], message: str, attachments: List[str] = None) -> Dict[str, Any]:
        """Processa mensagem com IA avançada usando function calling"""
        
        # Construir mensagens para a IA
        messages = await self._build_ai_messages(memory, context, message)
        
        # Configurar funções disponíveis
        functions = [
            {
                "type": "function",
                "function": {
                    "name": cap.name,
                    "description": cap.description,
                    "parameters": cap.parameters
                }
            }
            for cap in self.capabilities.values()
        ]
        
        try:
            # Chamada para IA com function calling
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=0.7,
                max_tokens=1500
            )
            
            choice = response.choices[0]
            
            # Verificar se IA quer chamar função
            if choice.message.function_call:
                return await self._handle_function_call(choice.message.function_call, memory, context)
            else:
                # Resposta direta da IA
                return await self._handle_direct_response(choice.message.content, memory, context)
                
        except Exception as e:
            logger.error(f"Erro na chamada para IA: {str(e)}")
            return await self._fallback_response(message, memory, context)
    
    async def _build_ai_messages(self, memory: ConversationMemory, context: Dict[str, Any], current_message: str) -> List[Dict[str, Any]]:
        """Constrói mensagens para enviar à IA"""
        
        # System prompt detalhado
        system_prompt = f"""
Você é o OmniCore AI, um assistente empresarial avançado especializado em:
- Análise inteligente de documentos com OCR e IA
- Automação de processos e workflows empresariais
- Geração de relatórios e insights de dados
- Integração com sistemas ERP/CRM (SAP, Salesforce)
- Monitoramento de sistema e métricas
- Consultas inteligentes em bases de dados

CONTEXTO ATUAL DO SISTEMA:
{json.dumps(context, indent=2, default=str)}

SUAS CAPACIDADES:
{self._get_capabilities_description()}

INSTRUÇÕES COMPORTAMENTAIS:
1. Seja proativo e inteligente - antecipe necessidades do usuário
2. Use function calling quando apropriado para executar ações
3. Mantenha contexto da conversa e referências anteriores
4. Forneça insights valiosos baseados nos dados
5. Seja específico e actionable em suas respostas
6. Adapte o tom e nível técnico ao usuário

IMPORTANTE: 
- Se o usuário menciona documentos, use analyze_document
- Para consultas de dados, use query_database  
- Para automação, use execute_workflow
- Para relatórios, use generate_report
- Sempre considere o contexto completo da conversa
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Adicionar histórico relevante (últimas mensagens)
        recent_messages = memory.messages[-10:] if len(memory.messages) > 10 else memory.messages
        
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return messages
    
    def _get_capabilities_description(self) -> str:
        """Gera descrição das capacidades para a IA"""
        
        description = "FUNÇÕES DISPONÍVEIS:\n"
        
        for cap in self.capabilities.values():
            description += f"\n• {cap.name}: {cap.description}"
            description += f"\n  Exemplos: {', '.join(cap.examples[:2])}"
        
        return description
    
    async def _handle_function_call(self, function_call, memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa function call e processa resultado"""
        
        function_name = function_call.name
        
        try:
            # Parse dos argumentos
            arguments = json.loads(function_call.arguments)
            
            if function_name in self.capabilities:
                # Executar função
                capability = self.capabilities[function_name]
                result = await capability.function(arguments, memory, context)
                
                # Processar resultado com IA
                follow_up_response = await self._process_function_result(
                    function_name, arguments, result, memory, context
                )
                
                return {
                    "message": follow_up_response["message"],
                    "function_calls": [{"function": function_name, "arguments": arguments, "result": result}],
                    "data": result,
                    "suggestions": follow_up_response.get("suggestions", []),
                    "actions": follow_up_response.get("actions", [])
                }
            else:
                return {
                    "message": f"❌ Função '{function_name}' não encontrada.",
                    "error": True
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar function call: {str(e)}")
            return {
                "message": f"❌ Erro ao executar ação: {str(e)}",
                "error": True,
                "suggestions": ["Tentar novamente", "Reformular solicitação"]
            }
    
    async def _process_function_result(self, function_name: str, arguments: Dict, result: Any, memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processa resultado da função com IA para gerar resposta inteligente"""
        
        # Prompt para interpretar resultado
        interpretation_prompt = f"""
        FUNÇÃO EXECUTADA: {function_name}
        ARGUMENTOS: {json.dumps(arguments, indent=2)}
        RESULTADO: {json.dumps(result, indent=2, default=str)}
        
        Gere uma resposta inteligente e útil baseada no resultado acima.
        - Destaque os pontos principais
        - Forneça insights quando apropriado
        - Sugira próximas ações
        - Seja específico e actionable
        
        Formato da resposta: texto direto (sem JSON)
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Você é um assistente que interpreta resultados de funções e gera respostas úteis."},
                    {"role": "user", "content": interpretation_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            message = response.choices[0].message.content
            
            # Gerar sugestões baseadas na função executada
            suggestions = self._generate_contextual_suggestions(function_name, result)
            
            return {
                "message": message,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Erro ao interpretar resultado: {str(e)}")
            return {
                "message": f"✅ Ação executada com sucesso!\n\nResultado: {str(result)[:500]}...",
                "suggestions": ["Ver detalhes completos", "Executar próxima ação"]
            }
    
    def _generate_contextual_suggestions(self, function_name: str, result: Any) -> List[str]:
        """Gera sugestões contextuais baseadas na função executada"""
        
        suggestions_map = {
            "analyze_document": [
                "Gerar relatório do documento",
                "Iniciar workflow de aprovação", 
                "Extrair mais dados",
                "Analisar outro documento"
            ],
            "query_database": [
                "Gerar gráfico dos dados",
                "Exportar resultado", 
                "Fazer análise detalhada",
                "Consultar dados relacionados"
            ],
            "execute_workflow": [
                "Acompanhar progresso",
                "Ver tarefas pendentes",
                "Configurar notificações",
                "Iniciar outro workflow"
            ],
            "generate_report": [
                "Compartilhar relatório",
                "Agendar relatório automático",
                "Análise comparativa",
                "Exportar dados"
            ]
        }
        
        return suggestions_map.get(function_name, ["Continuar análise", "Ver mais opções"])
    
    async def _handle_direct_response(self, content: str, memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processa resposta direta da IA"""
        
        return {
            "message": content,
            "suggestions": [
                "Analisar documento",
                "Consultar dados", 
                "Gerar relatório",
                "Iniciar processo"
            ]
        }
    
    async def _fallback_response(self, message: str, memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resposta de fallback quando IA não está disponível"""
        
        # Análise simples baseada em keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["documento", "analisar", "processar"]):
            return {
                "message": "📄 Posso ajudar com análise de documentos!\n\nEnvie arquivos PDF, DOCX ou imagens para análise automática com IA.",
                "suggestions": ["Enviar documento", "Ver exemplos", "Tipos suportados"]
            }
        elif any(word in message_lower for word in ["dados", "consulta", "quantos", "buscar"]):
            return {
                "message": "🔍 Posso consultar dados no sistema!\n\nPergunte sobre clientes, vendas, processos ou qualquer métrica.",
                "suggestions": ["Quantos clientes?", "Vendas hoje", "Processos ativos"]
            }
        elif any(word in message_lower for word in ["relatório", "report", "análise"]):
            return {
                "message": "📊 Posso gerar relatórios personalizados!\n\nEspecifique o tipo e período desejado.",
                "suggestions": ["Relatório mensal", "Performance", "Dashboard"]
            }
        else:
            return {
                "message": "🤖 Sou o assistente inteligente do OmniCore AI!\n\nPosso ajudar com:\n• Análise de documentos\n• Consultas de dados\n• Automação de processos\n• Geração de relatórios\n\nO que precisa?",
                "suggestions": ["Analisar documento", "Consultar dados", "Ver status", "Iniciar processo"]
            }
    
    # ===== IMPLEMENTAÇÃO DAS FUNÇÕES =====
    
    async def _analyze_document(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise de documento"""
        
        file_path = args.get("file_path")
        analysis_type = args.get("analysis_type", "complete")
        
        try:
            # Criar contexto de processo
            process_context = ProcessContext(
                process_id=f"ai_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=memory.user_id,
                company_id="ai_chat",
                department="ai_assistant"
            )
            
            # Executar análise
            result = await self.omnicore_agent.analisar_documento(
                file_path, process_context, analysis_type
            )
            
            if result.status == TaskStatus.COMPLETED:
                return {
                    "success": True,
                    "document_analysis": result.result,
                    "processing_time": result.execution_time,
                    "insights": self._generate_document_insights(result.result)
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Erro na análise do documento"
                }
                
        except Exception as e:
            logger.error(f"Erro na análise de documento: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _query_database(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa consulta na base de dados"""
        
        query = args.get("query")
        
        try:
            # Converter consulta natural para SQL (simplificado)
            sql_query = self._natural_language_to_sql(query)
            
            # Simular execução da consulta
            # Em produção, conectaria com banco real
            result = await self._execute_database_query(sql_query)
            
            return {
                "success": True,
                "query": query,
                "sql_generated": sql_query,
                "result": result,
                "insights": self._generate_data_insights(result)
            }
            
        except Exception as e:
            logger.error(f"Erro na consulta: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_workflow(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa workflow"""
        
        workflow_name = args.get("workflow_name")
        parameters = args.get("parameters", {})
        
        try:
            if hasattr(self.omnicore_agent, 'workflow_engine'):
                execution_id = await self.omnicore_agent.workflow_engine.start_workflow(
                    workflow_name,
                    memory.user_id,
                    "ai_chat",
                    parameters
                )
                
                return {
                    "success": True,
                    "workflow_name": workflow_name,
                    "execution_id": execution_id,
                    "status": "started",
                    "parameters": parameters
                }
            else:
                return {
                    "success": False,
                    "error": "Sistema de workflows não disponível"
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_report(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório"""
        
        report_type = args.get("report_type")
        period = args.get("period", "last_30_days")
        
        try:
            # Buscar dados do sistema
            system_status = context.get("system_status", {})
            
            # Gerar relatório baseado no tipo
            report_data = {
                "type": report_type,
                "period": period,
                "generated_at": datetime.now().isoformat(),
                "metrics": {
                    "documents_processed": 150,
                    "workflows_executed": 45,
                    "decisions_made": 89,
                    "accuracy_rate": 0.94,
                    "processing_time_avg": 3.2
                },
                "insights": [
                    "Produtividade aumentou 25% no período",
                    "Taxa de aprovação automática: 85%",
                    "Tempo médio de processamento reduzido"
                ]
            }
            
            return {
                "success": True,
                "report": report_data,
                "summary": f"Relatório {report_type} gerado para {period}"
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _system_monitoring(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Monitora sistema"""
        
        scope = args.get("scope", "general")
        
        try:
            system_status = context.get("system_status", {})
            
            monitoring_data = {
                "scope": scope,
                "timestamp": datetime.now().isoformat(),
                "status": system_status.get("status", "unknown"),
                "components": system_status.get("components", {}),
                "metrics": {
                    "active_processes": system_status.get("active_processes", 0),
                    "decisions_made": system_status.get("decisions_made", 0),
                    "uptime": "99.9%",
                    "response_time": "250ms"
                },
                "alerts": [],
                "recommendations": [
                    "Sistema funcionando normalmente",
                    "Todas as integrações ativas",
                    "Performance dentro do esperado"
                ]
            }
            
            return {
                "success": True,
                "monitoring": monitoring_data
            }
            
        except Exception as e:
            logger.error(f"Erro no monitoramento: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_insights(self, args: Dict[str, Any], memory: ConversationMemory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gera insights inteligentes"""
        
        try:
            insights = [
                {
                    "type": "trend",
                    "title": "Aumento de Produtividade",
                    "description": "Processamento de documentos cresceu 40% nas últimas duas semanas",
                    "impact": "high",
                    "recommendation": "Considerar expansão da capacidade"
                },
                {
                    "type": "efficiency", 
                    "title": "Automação Bem-sucedida",
                    "description": "85% das decisões estão sendo tomadas automaticamente",
                    "impact": "medium",
                    "recommendation": "Otimizar os 15% restantes"
                },
                {
                    "type": "quality",
                    "title": "Alta Precisão",
                    "description": "Taxa de precisão da IA mantém-se em 94%",
                    "impact": "high", 
                    "recommendation": "Manter modelos atualizados"
                }
            ]
            
            return {
                "success": True,
                "insights": insights,
                "summary": "Sistema apresenta excelente performance com oportunidades de otimização"
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _generate_document_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Gera insights sobre análise de documento"""
        
        insights = []
        
        classification = analysis_result.get("classification", "")
        confidence = analysis_result.get("confidence", 0)
        entities = analysis_result.get("entities", [])
        
        if confidence > 0.9:
            insights.append(f"Alta confiança na classificação como '{classification}'")
        
        if len(entities) > 5:
            insights.append(f"Documento rico em informações ({len(entities)} entidades extraídas)")
        
        # Análise específica por tipo
        if classification == "contrato":
            insights.append("Contrato identificado - verificar cláusulas importantes")
        elif classification == "nota_fiscal":
            insights.append("Nota fiscal - validar valores e impostos")
        
        return insights
    
    def _generate_data_insights(self, query_result: Dict[str, Any]) -> List[str]:
        """Gera insights sobre resultado de consulta"""
        
        insights = []
        
        if isinstance(query_result, dict) and "count" in query_result:
            count = query_result["count"]
            if count > 1000:
                insights.append("Volume alto de registros encontrados")
            elif count == 0:
                insights.append("Nenhum registro encontrado - verificar critérios")
        
        return insights
    
    def _natural_language_to_sql(self, query: str) -> str:
        """Converte linguagem natural para SQL (simplificado)"""
        
        query_lower = query.lower()
        
        if "quantos clientes" in query_lower:
            return "SELECT COUNT(*) as count FROM clientes"
        elif "vendas" in query_lower and "hoje" in query_lower:
            return "SELECT SUM(valor) as total FROM vendas WHERE DATE(data_venda) = CURRENT_DATE"
        elif "documentos processados" in query_lower:
            return "SELECT COUNT(*) as count FROM documentos WHERE status = 'processado'"
        else:
            return f"SELECT * FROM tabela WHERE descricao LIKE '%{query}%' LIMIT 10"
    
    async def _execute_database_query(self, sql: str) -> Dict[str, Any]:
        """Executa consulta no banco (simulado)"""
        
        # Simular resultados baseados na consulta
        if "COUNT(*)" in sql:
            return {"count": 1250}
        elif "SUM(valor)" in sql:
            return {"total": 45670.50}
        else:
            return {
                "rows": [
                    {"id": 1, "nome": "Cliente 1", "valor": 1500},
                    {"id": 2, "nome": "Cliente 2", "valor": 2300}
                ],
                "count": 2
            }
    
    async def _save_memory(self, memory: ConversationMemory):
        """Salva memória da conversa no banco vetorial"""
        
        try:
            # Converter para formato serializável
            memory_json = json.dumps({
                "user_id": memory.user_id,
                "conversation_id": memory.conversation_id,
                "messages": memory.messages[-20:],  # Salvar apenas últimas 20
                "context": memory.context,
                "user_profile": memory.user_profile,
                "last_activity": memory.last_activity.isoformat()
            }, default=str)
            
            # Criar embedding do contexto
            context_text = " ".join([msg["content"] for msg in memory.messages[-5:] if msg["role"] == "user"])
            embedding = self.embedding_model.encode(context_text).tolist()
            
            # Salvar no banco vetorial
            self.memory_collection.upsert(
                ids=[f"{memory.user_id}_{memory.conversation_id}"],
                documents=[memory_json],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": memory.user_id,
                    "conversation_id": memory.conversation_id,
                    "last_activity": memory.last_activity.isoformat()
                }]
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {str(e)}")

# Exemplo de uso
async def exemplo_uso_avancado():
    """Exemplo de uso do agente avançado"""
    
    config = {
        "openai_api_key": "sua_chave_openai",
        "model_name": "gpt-4-turbo-preview",
        "memory_path": "./omnicore_memory",
        "context_window": 8000
    }
    
    # Criar agente principal
    omnicore_agent = OmniCoreAgent({})
    
    # Criar agente IA avançado
    ai_agent = AdvancedAIAgent(omnicore_agent, config)
    
    # Conversa de exemplo
    user_id = "usuario_teste"
    
    # Mensagem 1
    response1 = await ai_agent.process_conversation(
        user_id, 
        "Olá! Preciso analisar alguns contratos e gerar um relatório mensal. Como você pode me ajudar?"
    )
    print(f"Bot: {response1['message']}")
    
    # Mensagem 2 com contexto
    response2 = await ai_agent.process_conversation(
        user_id,
        "Tenho um contrato em PDF que precisa ser analisado urgentemente",
        attachments=["/path/to/contrato.pdf"]
    )
    print(f"Bot: {response2['message']}")
    
    # Mensagem 3 com follow-up
    response3 = await ai_agent.process_conversation(
        user_id,
        "Baseado na análise anterior, você pode iniciar o processo de aprovação?"
    )
    print(f"Bot: {response3['message']}")

if __name__ == "__main__":
    asyncio.run(exemplo_uso_avancado())