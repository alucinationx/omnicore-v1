# OmniCore AI - API REST com FastAPI
# Exposição do agente como serviço empresarial

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import tempfile
import os
from datetime import datetime
from omnicore_ai_agent import AdvancedAIAgent
from fastapi import WebSocket, WebSocketDisconnect
import tempfile
import os
from pathlib import Path

# Instância global do agente IA avançado
advanced_ai_agent = None

def get_advanced_ai_agent():
    """Dependency para obter agente IA avançado"""
    global advanced_ai_agent
    if advanced_ai_agent is None:
        # Configuração avançada
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "model_name": os.getenv("AI_MODEL", "gpt-4-turbo-preview"),
            "memory_path": os.getenv("MEMORY_PATH", "./omnicore_memory"),
            "context_window": 8000,
            "max_history": 50,
            "embedding_model": "all-MiniLM-L6-v2"
        }
        
        # Obter agente principal
        omnicore_agent = get_agent()
        
        # Criar agente IA avançado
        advanced_ai_agent = AdvancedAIAgent(omnicore_agent, config)
    
    return advanced_ai_agent

@app.post("/ai/chat")
async def advanced_chat(
    message: str = Form(...),
    user_id: str = Form(default="user"),
    conversation_id: str = Form(default=""),
    files: List[UploadFile] = File(default=[])
):
    """Endpoint principal para conversa com IA avançada"""
    
    try:
        # Obter agente IA
        ai_agent = get_advanced_ai_agent()
        
        # Processar arquivos anexados
        attachment_paths = []
        if files and files[0].filename:
            for file in files:
                if file.filename:
                    # Salvar arquivo temporariamente
                    suffix = Path(file.filename).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        content = await file.read()
                        temp_file.write(content)
                        attachment_paths.append(temp_file.name)
        
        # Processar conversa
        response = await ai_agent.process_conversation(
            user_id=user_id,
            message=message,
            attachments=attachment_paths
        )
        
        # Limpar arquivos temporários
        for temp_path in attachment_paths:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "advanced_ai",
            "capabilities_used": response.get("function_calls", [])
        }
        
    except Exception as e:
        logger.error(f"Erro na conversa IA: {str(e)}")
        return {
            "success": False,
            "message": f"❌ Erro na IA: {str(e)}",
            "fallback": True,
            "suggestions": ["Tentar novamente", "Usar modo básico"]
        }

@app.get("/ai/capabilities")
async def get_ai_capabilities():
    """Lista capacidades do agente IA"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        capabilities = {}
        for name, cap in ai_agent.capabilities.items():
            capabilities[name] = {
                "name": cap.name,
                "description": cap.description,
                "category": cap.category,
                "examples": cap.examples
            }
        
        return {
            "success": True,
            "capabilities": capabilities,
            "model": ai_agent.model_name,
            "features": {
                "function_calling": True,
                "context_memory": True,
                "semantic_search": True,
                "document_analysis": True,
                "workflow_automation": True,
                "database_queries": True,
                "report_generation": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/ai/memory/{user_id}")
async def get_user_memory(user_id: str, limit: int = 20):
    """Obtém memória da conversa do usuário"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Buscar memória ativa
        if user_id in ai_agent.active_conversations:
            memory = ai_agent.active_conversations[user_id]
            
            recent_messages = memory.messages[-limit:] if len(memory.messages) > limit else memory.messages
            
            return {
                "success": True,
                "user_id": user_id,
                "conversation_id": memory.conversation_id,
                "messages": recent_messages,
                "context": memory.context,
                "user_profile": memory.user_profile,
                "last_activity": memory.last_activity.isoformat()
            }
        else:
            return {
                "success": True,
                "user_id": user_id,
                "messages": [],
                "message": "Nenhuma conversa ativa encontrada"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/ai/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Limpa memória da conversa do usuário"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Limpar memória ativa
        if user_id in ai_agent.active_conversations:
            del ai_agent.active_conversations[user_id]
        
        return {
            "success": True,
            "message": f"Memória do usuário {user_id} limpa com sucesso"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/ai/context")
async def set_user_context(
    user_id: str = Form(...),
    context_data: str = Form(...)
):
    """Define contexto específico para usuário"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        context = json.loads(context_data)
        
        # Obter ou criar memória
        memory = await ai_agent._get_or_create_memory(user_id)
        
        # Atualizar contexto
        memory.context.update(context)
        memory.user_profile.update(context.get("user_profile", {}))
        
        # Salvar
        await ai_agent._save_memory(memory)
        
        return {
            "success": True,
            "message": "Contexto atualizado com sucesso",
            "context": memory.context
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/ai/train")
async def train_from_feedback(
    user_id: str = Form(...),
    message_id: str = Form(...),
    feedback: str = Form(...),  # "positive", "negative", "correction"
    correction: str = Form(default="")
):
    """Treina agente baseado em feedback do usuário"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Buscar conversa
        if user_id in ai_agent.active_conversations:
            memory = ai_agent.active_conversations[user_id]
            
            # Encontrar mensagem específica
            target_message = None
            for msg in memory.messages:
                if msg.get("id") == message_id:
                    target_message = msg
                    break
            
            if target_message:
                # Adicionar feedback à memória
                feedback_data = {
                    "message_id": message_id,
                    "feedback": feedback,
                    "correction": correction,
                    "timestamp": datetime.now().isoformat()
                }
                
                if "feedback" not in memory.context:
                    memory.context["feedback"] = []
                memory.context["feedback"].append(feedback_data)
                
                # Salvar memória atualizada
                await ai_agent._save_memory(memory)
                
                return {
                    "success": True,
                    "message": "Feedback registrado com sucesso",
                    "learning": "Agente irá considerar este feedback em futuras interações"
                }
            else:
                return {
                    "success": False,
                    "error": "Mensagem não encontrada"
                }
        else:
            return {
                "success": False,
                "error": "Conversa não encontrada"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/ai/analytics")
async def get_ai_analytics():
    """Retorna analytics do uso da IA"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Calcular estatísticas
        total_conversations = len(ai_agent.active_conversations)
        total_messages = sum(
            len(memory.messages) 
            for memory in ai_agent.active_conversations.values()
        )
        
        # Estatísticas por capability
        capability_usage = {}
        for user_id, memory in ai_agent.active_conversations.items():
            for message in memory.messages:
                if message.get("function_calls"):
                    for call in message["function_calls"]:
                        func_name = call.get("function", "unknown")
                        capability_usage[func_name] = capability_usage.get(func_name, 0) + 1
        
        # Atividade por usuário
        user_activity = {}
        for user_id, memory in ai_agent.active_conversations.items():
            user_activity[user_id] = {
                "messages": len(memory.messages),
                "last_activity": memory.last_activity.isoformat(),
                "conversation_id": memory.conversation_id
            }
        
        return {
            "success": True,
            "analytics": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "capability_usage": capability_usage,
                "user_activity": user_activity,
                "model_info": {
                    "model": ai_agent.model_name,
                    "context_window": ai_agent.context_window,
                    "max_history": ai_agent.max_history_messages
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.websocket("/ws/ai/{user_id}")
async def websocket_ai_chat(websocket: WebSocket, user_id: str):
    """WebSocket para chat IA em tempo real"""
    
    await websocket.accept()
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Enviar mensagem de boas-vindas
        await websocket.send_text(json.dumps({
            "type": "system",
            "message": "🤖 Conectado ao OmniCore AI avançado!",
            "capabilities": list(ai_agent.capabilities.keys()),
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Receber mensagem
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message = message_data.get("message", "")
            attachments = message_data.get("attachments", [])
            
            # Processar com IA avançada
            response = await ai_agent.process_conversation(
                user_id=user_id,
                message=message,
                attachments=attachments
            )
            
            # Enviar resposta
            await websocket.send_text(json.dumps({
                "type": "message",
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket AI disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket AI error: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Erro na conexão: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }))

@app.post("/ai/bulk-analyze")
async def bulk_document_analysis(
    files: List[UploadFile] = File(...),
    user_id: str = Form(default="bulk_user"),
    analysis_type: str = Form(default="complete")
):
    """Análise em lote de múltiplos documentos"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        results = []
        
        for file in files:
            if file.filename:
                # Salvar arquivo temporariamente
                suffix = Path(file.filename).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                try:
                    # Analisar com IA
                    response = await ai_agent.process_conversation(
                        user_id=f"{user_id}_bulk",
                        message=f"Analise este documento: {file.filename}",
                        attachments=[temp_path]
                    )
                    
                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "analysis": response.get("data", {}),
                        "insights": response.get("message", "")
                    })
                    
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    })
                finally:
                    # Limpar arquivo temporário
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
        
        # Gerar insights consolidados
        consolidated_insights = await ai_agent.process_conversation(
            user_id=f"{user_id}_consolidate",
            message=f"Gere insights consolidados sobre {len(results)} documentos analisados em lote. Resultados: {json.dumps(results, default=str)}"
        )
        
        return {
            "success": True,
            "total_documents": len(files),
            "results": results,
            "consolidated_insights": consolidated_insights.get("message", ""),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise em lote: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/ai/smart-query")
async def smart_database_query(
    query: str = Form(...),
    user_id: str = Form(default="query_user"),
    context: str = Form(default="{}")
):
    """Consulta inteligente na base de dados usando linguagem natural"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Processar consulta com contexto
        context_data = json.loads(context) if context != "{}" else {}
        
        full_message = f"Consulte na base de dados: {query}"
        if context_data:
            full_message += f" Contexto adicional: {json.dumps(context_data)}"
        
        # Processar com IA
        response = await ai_agent.process_conversation(
            user_id=user_id,
            message=full_message
        )
        
        return {
            "success": True,
            "query": query,
            "response": response,
            "data": response.get("data", {}),
            "insights": response.get("message", ""),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na consulta inteligente: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/ai/health")
async def ai_health_check():
    """Verifica saúde do sistema de IA"""
    
    try:
        ai_agent = get_advanced_ai_agent()
        
        # Testar conectividade com OpenAI
        test_response = await ai_agent.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        
        openai_status = "healthy" if test_response else "error"
        
        # Verificar memória
        memory_status = "healthy" if ai_agent.chroma_client else "error"
        
        # Verificar embedding model
        embedding_status = "healthy" if ai_agent.embedding_model else "error"
        
        return {
            "success": True,
            "ai_health": {
                "openai_api": openai_status,
                "memory_system": memory_status,
                "embedding_model": embedding_status,
                "active_conversations": len(ai_agent.active_conversations),
                "capabilities_loaded": len(ai_agent.capabilities),
                "model": ai_agent.model_name
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "ai_health": {
                "status": "error",
                "error": str(e)
            }
        }
# Importar o agente principal
from .omnicore_main import OmniCoreAgent, ProcessContext, TaskStatus

# Configuração da aplicação
app = FastAPI(
    title="OmniCore AI",
    description="Agente de IA Empresarial - Automação Inteligente de Processos Corporativos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do agente
omnicore_agent = None

# Modelos Pydantic para requisições
class ProcessRequest(BaseModel):
    processo_nome: str = Field(..., description="Nome do processo a ser executado")
    parametros: Dict[str, Any] = Field(default_factory=dict)
    user_id: str = Field(..., description="ID do usuário")
    company_id: str = Field(..., description="ID da empresa")
    department: str = Field(default="geral", description="Departamento")

class DecisionRequest(BaseModel):
    dados_entrada: Dict[str, Any] = Field(..., description="Dados para tomada de decisão")
    user_id: str = Field(..., description="ID do usuário")
    company_id: str = Field(..., description="ID da empresa")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    logs: List[str] = []

async def get_agent():
    """Dependency para obter instância do agente"""
    global omnicore_agent
    if omnicore_agent is None:
        config = {
            "integrations": {
                "sap": {"endpoint": os.getenv("SAP_ENDPOINT", "")},
                "salesforce": {"endpoint": os.getenv("SALESFORCE_ENDPOINT", "")}
            },
            "security": {
                "encryption_key": os.getenv("ENCRYPTION_KEY", "default-key"),
                "audit_logs": True
            }
        }
        omnicore_agent = OmniCoreAgent(config)
    return omnicore_agent

@app.get("/")
async def root():
    """Endpoint de status básico"""
    return {"message": "OmniCore AI - Sistema Ativo", "version": "1.0.0"}

@app.get("/health")
async def health_check(agent: OmniCoreAgent = Depends(get_agent)):
    """Verificação de saúde do sistema"""
    try:
        status = await agent.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no health check: {str(e)}")

@app.post("/documentos/analisar", response_model=TaskResponse)
async def analisar_documento(
    file: UploadFile = File(...),
    tipo_analise: str = "completa",
    user_id: str = "default",
    company_id: str = "default",
    agent: OmniCoreAgent = Depends(get_agent)
):
    """Analisa documento enviado"""
    try:
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        context = ProcessContext(
            process_id=f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=user_id,
            company_id=company_id,
            department="documentos"
        )
        
        resultado = await agent.analisar_documento(
            temp_path,
            context,
            tipo_analise
        )
        
        # Limpar arquivo temporário
        os.unlink(temp_path)
        
        return TaskResponse(
            task_id=resultado.task_id,
            status=resultado.status.value,
            result=resultado.result,
            error=resultado.error,
            execution_time=resultado.execution_time,
            logs=resultado.logs
        )
        
    except Exception as e:
        if 'temp_path' in locals():
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Erro na análise do documento: {str(e)}")

@app.post("/decisoes/tomar")
async def tomar_decisao(
    request: DecisionRequest,
    agent: OmniCoreAgent = Depends(get_agent)
):
    """Toma decisão baseada em dados fornecidos"""
    try:
        context = ProcessContext(
            process_id=f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=request.user_id,
            company_id=request.company_id,
            department="decisoes"
        )
        
        decisao = await agent.decidir(request.dados_entrada, context)
        
        return {
            "decision_id": decisao.decision_id,
            "decision": decisao.decision,
            "confidence": decisao.confidence.value,
            "reasoning": decisao.reasoning,
            "timestamp": decisao.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na tomada de decisão: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
