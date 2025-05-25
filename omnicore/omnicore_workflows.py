# OmniCore AI - Sistema de Workflows e BPMN
# Orquestração de processos empresariais complexos com execução automática

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import networkx as nx
from collections import defaultdict, deque

# Para visualização de workflows
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch

logger = logging.getLogger("OmniCore.WorkflowEngine")

class NodeType(Enum):
    """Tipos de nós em um workflow"""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL_GATEWAY = "parallel_gateway"
    EXCLUSIVE_GATEWAY = "exclusive_gateway"
    TIMER = "timer"
    HUMAN_TASK = "human_task"
    SERVICE_TASK = "service_task"
    SCRIPT_TASK = "script_task"
    SUBPROCESS = "subprocess"

class ExecutionStatus(Enum):
    """Status de execução"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    SKIPPED = "skipped"

class TaskPriority(Enum):
    """Prioridades de tarefas"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    CRITICAL = 7
    URGENT = 9

@dataclass
class WorkflowVariable:
    """Variável de workflow"""
    name: str
    value: Any
    type: str = "string"  # string, number, boolean, object, array
    required: bool = False
    description: str = ""

@dataclass
class ExecutionContext:
    """Contexto de execução de workflow"""
    workflow_id: str
    execution_id: str
    user_id: str
    company_id: str
    variables: Dict[str, WorkflowVariable] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    current_nodes: List[str] = field(default_factory=list)

@dataclass
class NodeExecution:
    """Registro de execução de nó"""
    node_id: str
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None

class WorkflowNode(ABC):
    """Classe base para nós de workflow"""
    
    def __init__(self, node_id: str, name: str, node_type: NodeType):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.incoming = []
        self.outgoing = []
        self.properties = {}
        self.conditions = {}
    
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """Executa o nó"""
        pass
    
    def add_incoming(self, node_id: str, condition: str = None):
        """Adiciona conexão de entrada"""
        self.incoming.append({"node_id": node_id, "condition": condition})
    
    def add_outgoing(self, node_id: str, condition: str = None):
        """Adiciona conexão de saída"""
        self.outgoing.append({"node_id": node_id, "condition": condition})

class StartNode(WorkflowNode):
    """Nó de início do workflow"""
    
    def __init__(self, node_id: str = "start"):
        super().__init__(node_id, "Start", NodeType.START)
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        logger.info(f"Iniciando workflow {context.workflow_id}")
        return {"status": "started", "next_nodes": [conn["node_id"] for conn in self.outgoing]}

class EndNode(WorkflowNode):
    """Nó de fim do workflow"""
    
    def __init__(self, node_id: str = "end"):
        super().__init__(node_id, "End", NodeType.END)
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        logger.info(f"Finalizando workflow {context.workflow_id}")
        return {"status": "completed", "result": context.variables}

class ServiceTaskNode(WorkflowNode):
    """Nó de tarefa de serviço (integração)"""
    
    def __init__(self, node_id: str, name: str, service_name: str, operation: str):
        super().__init__(node_id, name, NodeType.SERVICE_TASK)
        self.service_name = service_name
        self.operation = operation
        self.input_mapping = {}
        self.output_mapping = {}
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        try:
            logger.info(f"Executando service task {self.name}")
            
            # Preparar dados de entrada
            input_data = {}
            for var_name, mapping in self.input_mapping.items():
                if mapping in context.variables:
                    input_data[var_name] = context.variables[mapping].value
            
            # Simular chamada de serviço (integrar com IntegrationManager)
            result = await self._call_service(input_data)
            
            # Mapear dados de saída
            for var_name, mapping in self.output_mapping.items():
                if var_name in result:
                    context.variables[mapping] = WorkflowVariable(
                        name=mapping,
                        value=result[var_name],
                        type="object"
                    )
            
            return {
                "status": "completed",
                "result": result,
                "next_nodes": [conn["node_id"] for conn in self.outgoing]
            }
            
        except Exception as e:
            logger.error(f"Erro em service task {self.name}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _call_service(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula chamada de serviço"""
        # Aqui seria integração real com sistemas externos
        await asyncio.sleep(0.1)  # Simular latência
        return {"result": f"Service {self.service_name} executed", "data": input_data}

class DecisionNode(WorkflowNode):
    """Nó de decisão (gateway exclusivo)"""
    
    def __init__(self, node_id: str, name: str):
        super().__init__(node_id, name, NodeType.DECISION)
        self.decision_rules = {}
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        try:
            logger.info(f"Avaliando decisão {self.name}")
            
            # Avaliar condições
            for connection in self.outgoing:
                condition = connection.get("condition")
                if condition:
                    if self._evaluate_condition(condition, context):
                        return {
                            "status": "completed",
                            "decision": condition,
                            "next_nodes": [connection["node_id"]]
                        }
            
            # Se nenhuma condição foi atendida, usar rota padrão
            default_route = [conn["node_id"] for conn in self.outgoing if not conn.get("condition")]
            return {
                "status": "completed",
                "decision": "default",
                "next_nodes": default_route
            }
            
        except Exception as e:
            logger.error(f"Erro em decisão {self.name}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Avalia condição de decisão"""
        try:
            # Substituir variáveis na condição
            condition_eval = condition
            for var_name, var in context.variables.items():
                condition_eval = condition_eval.replace(f"{{{var_name}}}", str(var.value))
            
            # Avaliar expressão (em produção, usar parser seguro)
            return eval(condition_eval)
        except:
            return False

class HumanTaskNode(WorkflowNode):
    """Nó de tarefa humana"""
    
    def __init__(self, node_id: str, name: str, assignee: str = None):
        super().__init__(node_id, name, NodeType.HUMAN_TASK)
        self.assignee = assignee
        self.form_fields = []
        self.due_date = None
        self.priority = TaskPriority.NORMAL
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        logger.info(f"Criando tarefa humana {self.name}")
        
        # Criar tarefa para usuário
        task = {
            "task_id": str(uuid.uuid4()),
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "node_id": self.node_id,
            "name": self.name,
            "assignee": self.assignee,
            "form_fields": self.form_fields,
            "due_date": self.due_date,
            "priority": self.priority.value,
            "created_at": datetime.now()
        }
        
        return {
            "status": "waiting",
            "task": task,
            "waiting_for": "human_input"
        }
    
    async def complete_task(self, task_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Completa tarefa humana"""
        logger.info(f"Completando tarefa humana {self.name}")
        
        # Atualizar variáveis do contexto com dados da tarefa
        for field, value in task_data.items():
            context.variables[field] = WorkflowVariable(
                name=field,
                value=value,
                type=type(value).__name__
            )
        
        return {
            "status": "completed",
            "result": task_data,
            "next_nodes": [conn["node_id"] for conn in self.outgoing]
        }

class TimerNode(WorkflowNode):
    """Nó de timer"""
    
    def __init__(self, node_id: str, name: str, duration: timedelta):
        super().__init__(node_id, name, NodeType.TIMER)
        self.duration = duration
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        logger.info(f"Iniciando timer {self.name} por {self.duration}")
        
        await asyncio.sleep(self.duration.total_seconds())
        
        return {
            "status": "completed",
            "duration": self.duration.total_seconds(),
            "next_nodes": [conn["node_id"] for conn in self.outgoing]
        }

class ParallelGatewayNode(WorkflowNode):
    """Gateway paralelo (fork/join)"""
    
    def __init__(self, node_id: str, name: str, gateway_type: str = "fork"):
        super().__init__(node_id, name, NodeType.PARALLEL_GATEWAY)
        self.gateway_type = gateway_type  # "fork" ou "join"
    
    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        if self.gateway_type == "fork":
            logger.info(f"Fork paralelo {self.name}")
            return {
                "status": "completed",
                "type": "fork",
                "next_nodes": [conn["node_id"] for conn in self.outgoing]
            }
        else:  # join
            logger.info(f"Join paralelo {self.name}")
            return {
                "status": "completed",
                "type": "join",
                "next_nodes": [conn["node_id"] for conn in self.outgoing]
            }

class WorkflowDefinition:
    """Definição de workflow"""
    
    def __init__(self, workflow_id: str, name: str, version: str = "1.0"):
        self.workflow_id = workflow_id
        self.name = name
        self.version = version
        self.description = ""
        self.nodes: Dict[str, WorkflowNode] = {}
        self.variables: Dict[str, WorkflowVariable] = {}
        self.created_at = datetime.now()
        self.created_by = ""
    
    def add_node(self, node: WorkflowNode):
        """Adiciona nó ao workflow"""
        self.nodes[node.node_id] = node
    
    def connect_nodes(self, from_node: str, to_node: str, condition: str = None):
        """Conecta dois nós"""
        if from_node in self.nodes and to_node in self.nodes:
            self.nodes[from_node].add_outgoing(to_node, condition)
            self.nodes[to_node].add_incoming(from_node, condition)
    
    def add_variable(self, variable: WorkflowVariable):
        """Adiciona variável ao workflow"""
        self.variables[variable.name] = variable
    
    def validate(self) -> List[str]:
        """Valida definição do workflow"""
        errors = []
        
        # Verificar se há nó de início
        start_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            errors.append("Workflow deve ter um nó de início")
        elif len(start_nodes) > 1:
            errors.append("Workflow deve ter apenas um nó de início")
        
        # Verificar se há nó de fim
        end_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.END]
        if not end_nodes:
            errors.append("Workflow deve ter pelo menos um nó de fim")
        
        # Verificar conectividade
        for node in self.nodes.values():
            if node.node_type not in [NodeType.START, NodeType.END]:
                if not node.incoming:
                    errors.append(f"Nó {node.name} não tem conexões de entrada")
                if not node.outgoing and node.node_type != NodeType.END:
                    errors.append(f"Nó {node.name} não tem conexões de saída")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "name": node.name,
                    "type": node.node_type.value,
                    "incoming": node.incoming,
                    "outgoing": node.outgoing,
                    "properties": node.properties
                }
                for node_id, node in self.nodes.items()
            },
            "variables": {
                var_name: {
                    "name": var.name,
                    "type": var.type,
                    "required": var.required,
                    "description": var.description
                }
                for var_name, var in self.variables.items()
            }
        }

class WorkflowExecution:
    """Execução de workflow"""
    
    def __init__(self, workflow_def: WorkflowDefinition, context: ExecutionContext):
        self.workflow_def = workflow_def
        self.context = context
        self.node_executions: Dict[str, NodeExecution] = {}
        self.current_tokens = []  # Tokens de execução para fluxos paralelos
        self.waiting_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_at: Optional[datetime] = None
        self.status = ExecutionStatus.PENDING
    
    async def start(self) -> Dict[str, Any]:
        """Inicia execução do workflow"""
        logger.info(f"Iniciando execução do workflow {self.workflow_def.name}")
        
        self.status = ExecutionStatus.RUNNING
        
        # Encontrar nó de início
        start_nodes = [n for n in self.workflow_def.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            raise ValueError("Workflow não tem nó de início")
        
        start_node = start_nodes[0]
        
        # Executar nó de início
        result = await self._execute_node(start_node)
        
        # Continuar execução
        if result.get("next_nodes"):
            for next_node_id in result["next_nodes"]:
                await self._continue_execution(next_node_id)
        
        return {"execution_id": self.context.execution_id, "status": self.status.value}
    
    async def _execute_node(self, node: WorkflowNode) -> Dict[str, Any]:
        """Executa um nó específico"""
        execution = NodeExecution(
            node_id=node.node_id,
            execution_id=self.context.execution_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self.node_executions[node.node_id] = execution
        
        try:
            logger.info(f"Executando nó {node.name} ({node.node_type.value})")
            
            result = await node.execute(self.context)
            
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.output_data = result
            
            if result.get("status") == "failed":
                execution.status = ExecutionStatus.FAILED
                execution.error_message = result.get("error")
            elif result.get("status") == "waiting":
                execution.status = ExecutionStatus.WAITING
                # Adicionar tarefa à lista de espera
                if "task" in result:
                    self.waiting_tasks[node.node_id] = result["task"]
            else:
                execution.status = ExecutionStatus.COMPLETED
            
            return result
            
        except Exception as e:
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            
            logger.error(f"Erro na execução do nó {node.name}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _continue_execution(self, node_id: str):
        """Continua execução a partir de um nó"""
        if node_id not in self.workflow_def.nodes:
            logger.error(f"Nó {node_id} não encontrado")
            return
        
        node = self.workflow_def.nodes[node_id]
        
        # Verificar se é nó de fim
        if node.node_type == NodeType.END:
            await self._execute_node(node)
            self.status = ExecutionStatus.COMPLETED
            self.completed_at = datetime.now()
            logger.info(f"Workflow {self.workflow_def.name} completado")
            return
        
        # Executar nó
        result = await self._execute_node(node)
        
        # Verificar resultado
        if result.get("status") == "failed":
            self.status = ExecutionStatus.FAILED
            return
        elif result.get("status") == "waiting":
            # Pausar execução - será retomada quando tarefa for completada
            return
        
        # Continuar para próximos nós
        next_nodes = result.get("next_nodes", [])
        for next_node_id in next_nodes:
            await self._continue_execution(next_node_id)
    
    async def complete_human_task(self, node_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Completa tarefa humana e retoma execução"""
        if node_id not in self.waiting_tasks:
            raise ValueError(f"Tarefa {node_id} não encontrada ou já completada")
        
        node = self.workflow_def.nodes[node_id]
        if not isinstance(node, HumanTaskNode):
            raise ValueError(f"Nó {node_id} não é uma tarefa humana")
        
        # Completar tarefa
        result = await node.complete_task(task_data, self.context)
        
        # Atualizar execução do nó
        execution = self.node_executions[node_id]
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output_data = result
        
        # Remover da lista de espera
        del self.waiting_tasks[node_id]
        
        # Continuar execução
        next_nodes = result.get("next_nodes", [])
        for next_node_id in next_nodes:
            await self._continue_execution(next_node_id)
        
        return {"status": "resumed", "completed_task": node_id}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status da execução"""
        return {
            "execution_id": self.context.execution_id,
            "workflow_id": self.workflow_def.workflow_id,
            "status": self.status.value,
            "started_at": self.context.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "nodes_executed": len(self.node_executions),
            "waiting_tasks": len(self.waiting_tasks),
            "current_variables": {
                name: var.value for name, var in self.context.variables.items()
            }
        }

class WorkflowEngine:
    """Motor de execução de workflows"""
    
    def __init__(self):
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_workflow(self, workflow_def: WorkflowDefinition):
        """Registra definição de workflow"""
        errors = workflow_def.validate()
        if errors:
            raise ValueError(f"Workflow inválido: {', '.join(errors)}")
        
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
        logger.info(f"Workflow {workflow_def.name} registrado")
    
    async def start_workflow(self, 
                           workflow_id: str, 
                           user_id: str, 
                           company_id: str,
                           variables: Dict[str, Any] = None) -> str:
        """Inicia execução de workflow"""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} não encontrado")
        
        workflow_def = self.workflow_definitions[workflow_id]
        
        # Criar contexto de execução
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            user_id=user_id,
            company_id=company_id
        )
        
        # Adicionar variáveis iniciais
        if variables:
            for name, value in variables.items():
                context.variables[name] = WorkflowVariable(
                    name=name,
                    value=value,
                    type=type(value).__name__
                )
        
        # Criar execução
        execution = WorkflowExecution(workflow_def, context)
        self.executions[execution_id] = execution
        
        # Iniciar execução
        await execution.start()
        
        logger.info(f"Workflow {workflow_def.name} iniciado - Execução: {execution_id}")
        return execution_id
    
    async def complete_task(self, 
                          execution_id: str, 
                          node_id: str, 
                          task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Completa tarefa humana"""
        if execution_id not in self.executions:
            raise ValueError(f"Execução {execution_id} não encontrada")
        
        execution = self.executions[execution_id]
        return await execution.complete_human_task(node_id, task_data)
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Retorna status de execução"""
        if execution_id not in self.executions:
            raise ValueError(f"Execução {execution_id} não encontrada")
        
        return self.executions[execution_id].get_status()
    
    def get_waiting_tasks(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Retorna tarefas aguardando ação humana"""
        tasks = []
        
        for execution in self.executions.values():
            for task in execution.waiting_tasks.values():
                if user_id is None or task.get("assignee") == user_id:
                    tasks.append(task)
        
        return tasks
    
    def visualize_workflow(self, workflow_id: str, save_path: str = None) -> str:
        """Gera visualização do workflow"""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} não encontrado")
        
        workflow_def = self.workflow_definitions[workflow_id]
        
        # Criar grafo
        G = nx.DiGraph()
        
        # Adicionar nós
        for node in workflow_def.nodes.values():
            G.add_node(node.node_id, label=node.name, type=node.node_type.value)
        
        # Adicionar arestas
        for node in workflow_def.nodes.values():
            for connection in node.outgoing:
                G.add_edge(node.node_id, connection["node_id"], 
                          condition=connection.get("condition", ""))
        
        # Configurar layout
        pos = nx.spring_layout(G)
        
        # Criar figura
        plt.figure(figsize=(12, 8))
        
        # Definir cores por tipo de nó
        color_map = {
            NodeType.START: 'lightgreen',
            NodeType.END: 'lightcoral',
            NodeType.TASK: 'lightblue',
            NodeType.DECISION: 'yellow',
            NodeType.HUMAN_TASK: 'orange',
            NodeType.SERVICE_TASK: 'lightgray'
        }
        
        # Desenhar nós
        for node_id, data in G.nodes(data=True):
            node_type = NodeType(data['type'])
            color = color_map.get(node_type, 'white')
            
            x, y = pos[node_id]
            
            if node_type == NodeType.DECISION:
                # Diamond para decisões
                plt.scatter(x, y, s=1000, c=color, marker='D', edgecolors='black')
            else:
                # Retângulo para outros tipos
                rect = FancyBboxPatch((x-0.1, y-0.05), 0.2, 0.1, 
                                    boxstyle="round,pad=0.01", 
                                    facecolor=color, edgecolor='black')
                plt.gca().add_patch(rect)
            
            # Label do nó
            plt.text(x, y, data['label'], ha='center', va='center', fontsize=8)
        
        # Desenhar arestas
        nx.draw_networkx_edges(G, pos, edge_color='black', arrows=True, arrowsize=20)
        
        # Título
        plt.title(f"Workflow: {workflow_def.name}")
        plt.axis('off')
        
        # Salvar ou mostrar
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            return save_path
        else:
            plt.show()
            return "displayed"

# Builders para facilitar criação de workflows

class WorkflowBuilder:
    """Builder para facilitar criação de workflows"""
    
    def __init__(self, workflow_id: str, name: str):
        self.workflow = WorkflowDefinition(workflow_id, name)
        self.last_node_id = None
    
    def start(self, node_id: str = "start") -> 'WorkflowBuilder':
        """Adiciona nó de início"""
        start_node = StartNode(node_id)
        self.workflow.add_node(start_node)
        self.last_node_id = node_id
        return self
    
    def end(self, node_id: str = "end") -> 'WorkflowBuilder':
        """Adiciona nó de fim"""
        end_node = EndNode(node_id)
        self.workflow.add_node(end_node)
        if self.last_node_id:
            self.workflow.connect_nodes(self.last_node_id, node_id)
        return self
    
    def service_task(self, node_id: str, name: str, service: str, operation: str) -> 'WorkflowBuilder':
        """Adiciona tarefa de serviço"""
        task_node = ServiceTaskNode(node_id, name, service, operation)
        self.workflow.add_node(task_node)
        if self.last_node_id:
            self.workflow.connect_nodes(self.last_node_id, node_id)
        self.last_node_id = node_id
        return self
    
    def human_task(self, node_id: str, name: str, assignee: str = None) -> 'WorkflowBuilder':
        """Adiciona tarefa humana"""
        task_node = HumanTaskNode(node_id, name, assignee)
        self.workflow.add_node(task_node)
        if self.last_node_id:
            self.workflow.connect_nodes(self.last_node_id, node_id)
        self.last_node_id = node_id
        return self
    
    def decision(self, node_id: str, name: str) -> 'WorkflowBuilder':
        """Adiciona nó de decisão"""
        decision_node = DecisionNode(node_id, name)
        self.workflow.add_node(decision_node)
        if self.last_node_id:
            self.workflow.connect_nodes(self.last_node_id, node_id)
        self.last_node_id = node_id
        return self
    
    def connect_to(self, to_node_id: str, condition: str = None) -> 'WorkflowBuilder':
        """Conecta último nó a outro nó"""
        if self.last_node_id:
            self.workflow.connect_nodes(self.last_node_id, to_node_id, condition)
        return self
    
    def build(self) -> WorkflowDefinition:
        """Constrói workflow"""
        return self.workflow

# Exemplo de uso
async def exemplo_workflow_system():
    """Exemplo de uso do sistema de workflows"""
    
    # Criar engine
    engine = WorkflowEngine()
    
    # Criar workflow de aprovação de crédito
    builder = WorkflowBuilder("credit_approval", "Aprovação de Crédito")
    
    workflow = (builder
                .start()
                .service_task("validate_documents", "Validar Documentos", "document_service", "validate")
                .decision("credit_decision", "Decisão de Crédito")
                .human_task("manual_review", "Revisão Manual", "manager@empresa.com")
                .end()
                .build())
    
    # Configurar decisão
    decision_node = workflow.nodes["credit_decision"]
    decision_node.add_outgoing("manual_review", "{score} < 700")
    decision_node.add_outgoing("end", "{score} >= 700")
    
    # Registrar workflow
    engine.register_workflow(workflow)
    
    # Iniciar execução
    execution_id = await engine.start_workflow(
        "credit_approval",
        "user_123",
        "empresa_456",
        {"customer_id": "cust_789", "amount": 50000, "score": 650}
    )
    
    print(f"Workflow iniciado: {execution_id}")
    
    # Verificar tarefas pendentes
    tasks = engine.get_waiting_tasks("manager@empresa.com")
    print(f"Tarefas pendentes: {len(tasks)}")
    
    # Completar tarefa humana
    if tasks:
        task = tasks[0]
        await engine.complete_task(
            execution_id,
            task["node_id"],
            {"approved": True, "comments": "Aprovado após análise"}
        )
    
    # Status final
    status = engine.get_execution_status(execution_id)
    print(f"Status final: {status['status']}")

if __name__ == "__main__":
    asyncio.run(exemplo_workflow_system())