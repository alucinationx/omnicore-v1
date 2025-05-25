# OmniCore AI - Sistema de Monitoramento e Métricas Avançado
# Monitoramento em tempo real, alertas e observabilidade

import asyncio
import logging
import json
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import socket
import uuid

# Prometheus e métricas
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server, CollectorRegistry
import prometheus_client

# APM e tracing
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Logging estruturado
import structlog

# Notificações
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import slack_sdk

logger = structlog.get_logger("OmniCore.Monitoring")

class AlertSeverity(Enum):
    """Severidade dos alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Tipos de métricas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Alert:
    """Definição de alerta"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    metric_name: str
    condition: str  # e.g., "> 0.8", "< 100", "== 0"
    threshold: float
    duration: timedelta  # Tempo que deve permanecer no estado para disparar
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    triggered_count: int = 0

@dataclass
class MetricSnapshot:
    """Snapshot de métrica"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealth:
    """Status de saúde do sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_connections: int
    uptime: float
    error_rate: float
    response_time_avg: float

@dataclass
class BusinessMetrics:
    """Métricas de negócio"""
    timestamp: datetime
    documents_processed_total: int
    documents_processed_hour: int
    decisions_made_total: int
    decisions_accuracy: float
    processes_running: int
    processes_completed_today: int
    integration_success_rate: float
    user_satisfaction_score: float

class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registry = CollectorRegistry()
        
        # Métricas Prometheus
        self.request_count = Counter(
            'omnicore_requests_total',
            'Total requests processed',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'omnicore_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_processes = Gauge(
            'omnicore_active_processes',
            'Number of active processes',
            registry=self.registry
        )
        
        self.document_processing_time = Histogram(
            'omnicore_document_processing_seconds',
            'Document processing time',
            ['document_type'],
            registry=self.registry
        )
        
        self.decision_accuracy = Gauge(
            'omnicore_decision_accuracy',
            'Decision accuracy score',
            ['decision_type'],
            registry=self.registry
        )
        
        self.system_cpu = Gauge(
            'omnicore_system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory = Gauge(
            'omnicore_system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.integration_status = Gauge(
            'omnicore_integration_status',
            'Integration system status (1=up, 0=down)',
            ['system_name'],
            registry=self.registry
        )
        
        # Métricas de negócio
        self.business_metrics = {
            'documents_processed': Counter(
                'omnicore_documents_processed_total',
                'Total documents processed',
                ['classification'],
                registry=self.registry
            ),
            'decisions_made': Counter(
                'omnicore_decisions_made_total',
                'Total decisions made',
                ['decision_type', 'confidence'],
                registry=self.registry
            ),
            'user_sessions': Gauge(
                'omnicore_active_user_sessions',
                'Number of active user sessions',
                registry=self.registry
            ),
            'error_rate': Gauge(
                'omnicore_error_rate',
                'Application error rate',
                ['component'],
                registry=self.registry
            )
        }
        
        # Histórico de métricas
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.system_health_history = deque(maxlen=100)
        self.business_metrics_history = deque(maxlen=100)
        
        # Thread para coleta contínua
        self.collecting = False
        self.collection_thread = None
    
    def start_collection(self):
        """Inicia coleta contínua de métricas"""
        if self.collecting:
            return
        
        self.collecting = True
        self.collection_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self.collection_thread.start()
        
        # Iniciar servidor Prometheus
        prometheus_port = self.config.get('prometheus_port', 8001)
        start_http_server(prometheus_port, registry=self.registry)
        
        logger.info(f"Coleta de métricas iniciada na porta {prometheus_port}")
    
    def stop_collection(self):
        """Para coleta de métricas"""
        self.collecting = False
        if self.collection_thread:
            self.collection_thread.join()
    
    def _collect_metrics_loop(self):
        """Loop principal de coleta de métricas"""
        while self.collecting:
            try:
                # Coletar métricas do sistema
                self._collect_system_metrics()
                
                # Coletar métricas de negócio
                self._collect_business_metrics()
                
                # Dormir até próxima coleta
                time.sleep(self.config.get('collection_interval', 30))
                
            except Exception as e:
                logger.error(f"Erro na coleta de métricas: {str(e)}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu.set(cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            self.system_memory.set(memory.percent)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Rede
            network = psutil.net_io_counters()
            
            # Conexões ativas
            connections = len(psutil.net_connections())
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Criar snapshot de saúde do sistema
            health = SystemHealth(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk_percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                active_connections=connections,
                uptime=uptime,
                error_rate=0.0,  # Será calculado separadamente
                response_time_avg=0.0  # Será calculado separadamente
            )
            
            self.system_health_history.append(health)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {str(e)}")
    
    def _collect_business_metrics(self):
        """Coleta métricas de negócio"""
        try:
            # Simular coleta de métricas de negócio
            # Em produção, isso seria integrado com o banco de dados
            
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            # Criar snapshot de métricas de negócio
            business = BusinessMetrics(
                timestamp=now,
                documents_processed_total=1250,  # Exemplo
                documents_processed_hour=45,
                decisions_made_total=890,
                decisions_accuracy=0.92,
                processes_running=12,
                processes_completed_today=156,
                integration_success_rate=0.98,
                user_satisfaction_score=4.2
            )
            
            self.business_metrics_history.append(business)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas de negócio: {str(e)}")
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Registra métrica de requisição HTTP"""
        self.request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_document_processing(self, document_type: str, processing_time: float):
        """Registra processamento de documento"""
        self.document_processing_time.labels(document_type=document_type).observe(processing_time)
        self.business_metrics['documents_processed'].labels(classification=document_type).inc()
    
    def record_decision(self, decision_type: str, confidence: str, accuracy: float):
        """Registra decisão tomada"""
        self.business_metrics['decisions_made'].labels(
            decision_type=decision_type, 
            confidence=confidence
        ).inc()
        self.decision_accuracy.labels(decision_type=decision_type).set(accuracy)
    
    def set_integration_status(self, system_name: str, is_up: bool):
        """Define status de integração"""
        self.integration_status.labels(system_name=system_name).set(1 if is_up else 0)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Retorna métricas atuais"""
        current_health = self.system_health_history[-1] if self.system_health_history else None
        current_business = self.business_metrics_history[-1] if self.business_metrics_history else None
        
        return {
            "system_health": current_health.__dict__ if current_health else None,
            "business_metrics": current_business.__dict__ if current_business else None,
            "collection_active": self.collecting,
            "metrics_count": len(self.metrics_history)
        }

class AlertManager:
    """Gerenciador de alertas"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alerts: Dict[str, Alert] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}
        self.notification_channels = []
        
        # Configurar canais de notificação
        self._setup_notification_channels()
        
        # Alertas padrão
        self._setup_default_alerts()
    
    def _setup_notification_channels(self):
        """Configura canais de notificação"""
        # Email
        if self.config.get('email_notifications', {}).get('enabled'):
            self.notification_channels.append(EmailNotifier(
                self.config['email_notifications']
            ))
        
        # Slack
        if self.config.get('slack_notifications', {}).get('enabled'):
            self.notification_channels.append(SlackNotifier(
                self.config['slack_notifications']
            ))
        
        # Webhook
        if self.config.get('webhook_notifications', {}).get('enabled'):
            self.notification_channels.append(WebhookNotifier(
                self.config['webhook_notifications']
            ))
    
    def _setup_default_alerts(self):
        """Configura alertas padrão"""
        default_alerts = [
            Alert(
                alert_id="high_cpu",
                name="CPU Alta",
                description="Uso de CPU acima de 80%",
                severity=AlertSeverity.WARNING,
                metric_name="system_cpu_percent",
                condition="> 80",
                threshold=80.0,
                duration=timedelta(minutes=5)
            ),
            Alert(
                alert_id="high_memory",
                name="Memória Alta",
                description="Uso de memória acima de 85%",
                severity=AlertSeverity.ERROR,
                metric_name="system_memory_percent",
                condition="> 85",
                threshold=85.0,
                duration=timedelta(minutes=3)
            ),
            Alert(
                alert_id="low_decision_accuracy",
                name="Baixa Precisão de Decisões",
                description="Precisão das decisões abaixo de 70%",
                severity=AlertSeverity.ERROR,
                metric_name="decision_accuracy",
                condition="< 0.7",
                threshold=0.7,
                duration=timedelta(minutes=10)
            ),
            Alert(
                alert_id="integration_down",
                name="Integração Indisponível",
                description="Sistema de integração fora do ar",
                severity=AlertSeverity.CRITICAL,
                metric_name="integration_status",
                condition="== 0",
                threshold=0.0,
                duration=timedelta(minutes=1)
            ),
            Alert(
                alert_id="high_error_rate",
                name="Taxa de Erro Alta",
                description="Taxa de erro acima de 5%",
                severity=AlertSeverity.WARNING,
                metric_name="error_rate",
                condition="> 0.05",
                threshold=0.05,
                duration=timedelta(minutes=5)
            )
        ]
        
        for alert in default_alerts:
            self.add_alert(alert)
    
    def add_alert(self, alert: Alert):
        """Adiciona novo alerta"""
        self.alerts[alert.alert_id] = alert
        self.alert_states[alert.alert_id] = {
            'triggered': False,
            'trigger_time': None,
            'last_check': None
        }
        logger.info(f"Alerta adicionado: {alert.name}")
    
    def remove_alert(self, alert_id: str):
        """Remove alerta"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            del self.alert_states[alert_id]
            logger.info(f"Alerta removido: {alert_id}")
    
    async def check_alerts(self, metrics: Dict[str, float]):  # ✅ AGORA É ASYNC
        """Verifica alertas baseado nas métricas"""
        current_time = datetime.now()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            metric_value = metrics.get(alert.metric_name)
            if metric_value is None:
                continue
            
            # Avaliar condição
            triggered = self._evaluate_condition(metric_value, alert.condition, alert.threshold)
            state = self.alert_states[alert_id]
            
            if triggered:
                if not state['triggered']:
                    # Primeiro trigger - iniciar contagem
                    state['trigger_time'] = current_time
                    state['triggered'] = True
                elif current_time - state['trigger_time'] >= alert.duration:
                    # Condição satisfeita por tempo suficiente - disparar alerta
                    await self._fire_alert(alert, metric_value)  # ✅ CORRIGIDO: removido asyncio.run()
                    alert.last_triggered = current_time
                    alert.triggered_count += 1
            else:
                # Condição não satisfeita - resetar estado
                state['triggered'] = False
                state['trigger_time'] = None
            
            state['last_check'] = current_time
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Avalia condição do alerta"""
        try:
            if "> " in condition:
                return value > threshold
            elif "< " in condition:
                return value < threshold
            elif "== " in condition:
                return abs(value - threshold) < 0.001
            elif ">= " in condition:
                return value >= threshold
            elif "<= " in condition:
                return value <= threshold
            else:
                return False
        except:
            return False
    
    async def _fire_alert(self, alert: Alert, current_value: float):
        """Dispara alerta"""
        logger.warning(f"Alerta disparado: {alert.name} - Valor atual: {current_value}")
        
        alert_data = {
            "alert_id": alert.alert_id,
            "name": alert.name,
            "description": alert.description,
            "severity": alert.severity.value,
            "current_value": current_value,
            "threshold": alert.threshold,
            "timestamp": datetime.now().isoformat(),
            "triggered_count": alert.triggered_count + 1
        }
        
        # Enviar notificações
        for channel in self.notification_channels:
            try:
                await channel.send_alert(alert_data)
            except Exception as e:
                logger.error(f"Erro ao enviar notificação via {type(channel).__name__}: {str(e)}")
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Retorna status dos alertas"""
        return {
            "total_alerts": len(self.alerts),
            "enabled_alerts": len([a for a in self.alerts.values() if a.enabled]),
            "triggered_alerts": len([s for s in self.alert_states.values() if s['triggered']]),
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "enabled": alert.enabled,
                    "triggered": self.alert_states[alert_id]['triggered'],
                    "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None,
                    "triggered_count": alert.triggered_count
                }
                for alert_id, alert in self.alerts.items()
            ]
        }

class NotificationChannel:
    """Interface para canais de notificação"""
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        raise NotImplementedError

class EmailNotifier(NotificationChannel):
    """Notificador por email"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """Envia alerta por email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = ', '.join(self.config['to_emails'])
            msg['Subject'] = f"[OmniCore AI] Alerta: {alert_data['name']}"
            
            body = f"""
            Alerta Disparado: {alert_data['name']}
            
            Descrição: {alert_data['description']}
            Severidade: {alert_data['severity'].upper()}
            Valor Atual: {alert_data['current_value']}
            Limite: {alert_data['threshold']}
            Timestamp: {alert_data['timestamp']}
            
            Sistema: OmniCore AI
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port'])
            if self.config.get('use_tls'):
                server.starttls()
            if self.config.get('username'):
                server.login(self.config['username'], self.config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alerta enviado por email: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")

class SlackNotifier(NotificationChannel):
    """Notificador via Slack"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = slack_sdk.WebClient(token=config['bot_token'])
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """Envia alerta via Slack"""
        try:
            color = {
                'info': '#36a64f',
                'warning': '#ffcc00',
                'error': '#ff6b6b',
                'critical': '#ff0000'
            }.get(alert_data['severity'], '#cccccc')
            
            attachment = {
                "color": color,
                "title": f"🚨 Alerta: {alert_data['name']}",
                "text": alert_data['description'],
                "fields": [
                    {
                        "title": "Severidade",
                        "value": alert_data['severity'].upper(),
                        "short": True
                    },
                    {
                        "title": "Valor Atual",
                        "value": str(alert_data['current_value']),
                        "short": True
                    },
                    {
                        "title": "Limite",
                        "value": str(alert_data['threshold']),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": alert_data['timestamp'],
                        "short": True
                    }
                ],
                "footer": "OmniCore AI Monitoring",
                "ts": time.time()
            }
            
            self.client.chat_postMessage(
                channel=self.config['channel'],
                attachments=[attachment]
            )
            
            logger.info(f"Alerta enviado via Slack: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem Slack: {str(e)}")

class WebhookNotifier(NotificationChannel):
    """Notificador via webhook"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """Envia alerta via webhook"""
        try:
            payload = {
                "source": "omnicore_ai",
                "alert": alert_data,
                "timestamp": time.time()
            }
            
            response = requests.post(
                self.config['url'],
                json=payload,
                headers=self.config.get('headers', {}),
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(f"Alerta enviado via webhook: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {str(e)}")

class PerformanceProfiler:
    """Profiler de performance do sistema"""
    
    def __init__(self):
        self.function_timings = defaultdict(list)
        self.memory_usage = defaultdict(list)
        self.active_traces = {}
    
    def profile_function(self, func_name: str):
        """Decorator para profiling de funções"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                trace_id = str(uuid.uuid4())
                self.active_traces[trace_id] = {
                    'function': func_name,
                    'start_time': start_time,
                    'start_memory': start_memory
                }
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    
                    duration = end_time - start_time
                    memory_diff = end_memory - start_memory
                    
                    self.function_timings[func_name].append(duration)
                    self.memory_usage[func_name].append(memory_diff)
                    
                    if trace_id in self.active_traces:
                        del self.active_traces[trace_id]
                    
                    # Manter apenas últimas 1000 medições
                    if len(self.function_timings[func_name]) > 1000:
                        self.function_timings[func_name] = self.function_timings[func_name][-1000:]
                    if len(self.memory_usage[func_name]) > 1000:
                        self.memory_usage[func_name] = self.memory_usage[func_name][-1000:]
            
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de performance"""
        report = {
            "function_performance": {},
            "memory_usage": {},
            "active_traces": len(self.active_traces)
        }
        
        for func_name, timings in self.function_timings.items():
            if timings:
                report["function_performance"][func_name] = {
                    "avg_time": statistics.mean(timings),
                    "min_time": min(timings),
                    "max_time": max(timings),
                    "median_time": statistics.median(timings),
                    "call_count": len(timings),
                    "p95_time": statistics.quantiles(timings, n=20)[18] if len(timings) > 20 else max(timings)
                }
        
        for func_name, memory_deltas in self.memory_usage.items():
            if memory_deltas:
                report["memory_usage"][func_name] = {
                    "avg_memory": statistics.mean(memory_deltas),
                    "max_memory": max(memory_deltas),
                    "total_memory": sum(memory_deltas)
                }
        
        return report

class MonitoringSystem:
    """Sistema central de monitoramento"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_collector = MetricsCollector(config.get('metrics', {}))
        self.alert_manager = AlertManager(config.get('alerts', {}))
        self.profiler = PerformanceProfiler()
        
        self.monitoring_active = False
    
    async def start(self):
        """Inicia sistema de monitoramento"""
        logger.info("Iniciando sistema de monitoramento OmniCore AI")
        
        # Iniciar coleta de métricas
        self.metrics_collector.start_collection()
        
        # Iniciar loop de verificação de alertas
        self.monitoring_active = True
        asyncio.create_task(self._alert_check_loop())
        
        logger.info("Sistema de monitoramento iniciado")
    
    async def stop(self):
        """Para sistema de monitoramento"""
        logger.info("Parando sistema de monitoramento")
        
        self.monitoring_active = False
        self.metrics_collector.stop_collection()
        
        logger.info("Sistema de monitoramento parado")
    
    async def _alert_check_loop(self):
        """Loop de verificação de alertas"""
        while self.monitoring_active:
            try:
                # Obter métricas atuais
                current_metrics = self.metrics_collector.get_current_metrics()
                
                # Extrair valores para verificação de alertas
                metrics_values = {}
                if current_metrics['system_health']:
                    metrics_values.update({
                        'system_cpu_percent': current_metrics['system_health']['cpu_percent'],
                        'system_memory_percent': current_metrics['system_health']['memory_percent'],
                        'error_rate': current_metrics['system_health']['error_rate']
                    })
                
                if current_metrics['business_metrics']:
                    metrics_values.update({
                        'decision_accuracy': current_metrics['business_metrics']['decisions_accuracy'],
                        'integration_success_rate': current_metrics['business_metrics']['integration_success_rate']
                    })
                
                # Verificar alertas
                await self.alert_manager.check_alerts(metrics_values)  # ✅ JÁ ESTAVA CORRETO
                
                # Esperar próxima verificação
                await asyncio.sleep(self.config.get('alert_check_interval', 60))
                
            except Exception as e:
                logger.error(f"Erro no loop de alertas: {str(e)}")
                await asyncio.sleep(5)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        return {
            "monitoring_active": self.monitoring_active,
            "metrics": self.metrics_collector.get_current_metrics(),
            "alerts": self.alert_manager.get_alert_status(),
            "performance": self.profiler.get_performance_report(),
            "timestamp": datetime.now().isoformat()
        }

# Exemplo de uso
async def exemplo_monitoramento():
    """Exemplo de uso do sistema de monitoramento"""
    
    config = {
        "metrics": {
            "collection_interval": 30,
            "prometheus_port": 8001
        },
        "alerts": {
            "email_notifications": {
                "enabled": True,
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "from_email": "alerts@empresa.com",
                "to_emails": ["admin@empresa.com"],
                "username": "alerts@empresa.com",
                "password": "senha_app"
            },
            "slack_notifications": {
                "enabled": True,
                "bot_token": "xoxb-seu-token-aqui",
                "channel": "#alerts"
            }
        },
        "alert_check_interval": 60
    }
    
    # Inicializar sistema
    monitoring = MonitoringSystem(config)
    
    # Iniciar monitoramento
    await monitoring.start()
    
    # Simular algumas métricas
    monitoring.metrics_collector.record_request("POST", "/api/documents", 200, 1.5)
    monitoring.metrics_collector.record_document_processing("contract", 5.2)
    monitoring.metrics_collector.record_decision("credit_approval", "high", 0.95)
    monitoring.metrics_collector.set_integration_status("sap", True)
    
    # Aguardar um pouco
    await asyncio.sleep(5)
    
    # Obter status
    status = monitoring.get_system_status()
    print(f"Status do sistema: {json.dumps(status, indent=2, default=str)}")
    
    # Parar monitoramento
    await monitoring.stop()

if __name__ == "__main__":
    asyncio.run(exemplo_monitoramento())