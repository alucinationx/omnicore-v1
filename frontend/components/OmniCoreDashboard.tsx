// OmniCore AI - Interface Web Principal
// Dashboard e interface de usuário para interação com o sistema

import React, { useState, useEffect, useCallback } from 'react';
import AdvancedChatInterface from '@/components/AdvancedChatInterface';
import axios from 'axios';
import { 
  Upload, 
  FileText, 
  Settings, 
  Activity, 
  BarChart3, 
  Users, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Download,
  RefreshCw,
  Play,
  Pause,
  Moon,
  Sun
} from 'lucide-react';

// Configuração da API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Interfaces TypeScript
interface ProcessStatus {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  estimatedTime?: number;
}

interface DocumentAnalysis {
  id: string;
  filename: string;
  classification: string;
  confidence: number;
  entities: Array<{
    type: string;
    value: string;
    confidence: number;
  }>;
  summary: string;
  processingTime: number;
}

interface Decision {
  id: string;
  decision: string;
  confidence: string;
  reasoning: string;
  timestamp: string;
  feedbackScore?: number;
}

interface WorkflowTask {
  id: string;
  workflowName: string;
  taskName: string;
  assignee: string;
  priority: number;
  dueDate: string;
  formFields: Array<{
    name: string;
    type: string;
    required: boolean;
    value?: any;
  }>;
}

interface SystemStatus {
  status: string;
  agent_id: string;
  active_processes: number;
  decisions_made: number;
  uptime: string;
  components: Record<string, string>;
}

// Componente principal do dashboard
const OmniCoreDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [processes, setProcesses] = useState<ProcessStatus[]>([]);
  const [documents, setDocuments] = useState<DocumentAnalysis[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [systemStatus, setSystemStatus] = useState({
    status: 'loading',
    processesRunning: 0,
    decisionsToday: 0,
    documentsProcessed: 0,
    tasksWaiting: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Função para alternar tema
  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  // Função para buscar status do sistema
  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      const healthData: SystemStatus = response.data;
      
      setSystemStatus({
        status: healthData.status,
        processesRunning: healthData.active_processes,
        decisionsToday: healthData.decisions_made,
        documentsProcessed: 0, // Seria implementado no backend
        tasksWaiting: 0 // Seria implementado no backend
      });
      
      setError(null);
    } catch (err) {
      console.error('Erro ao buscar status do sistema:', err);
      setError('Não foi possível conectar com o backend');
    }
  }, []);

  // Carregar dados iniciais
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      
      // Buscar status do sistema
      await fetchSystemStatus();
      
      // Carregar dados simulados (em produção viria do backend)
      loadMockData();
      
      setIsLoading(false);
    };

    loadData();
    
    // Atualizar status a cada 30 segundos
    const interval = setInterval(fetchSystemStatus, 30000);
    
    return () => clearInterval(interval);
  }, [fetchSystemStatus]);

  // Simulação de dados para demonstração
  const loadMockData = () => {
    setProcesses([
      {
        id: '1',
        name: 'Onboarding Cliente',
        status: 'running',
        progress: 65,
        startTime: '2024-01-15T10:30:00',
        estimatedTime: 300
      },
      {
        id: '2',
        name: 'Conciliação Financeira',
        status: 'completed',
        progress: 100,
        startTime: '2024-01-15T09:15:00'
      },
      {
        id: '3',
        name: 'Análise de Risco',
        status: 'pending',
        progress: 0,
        startTime: '2024-01-15T11:00:00'
      }
    ]);

    setDocuments([
      {
        id: '1',
        filename: 'contrato_cliente_001.pdf',
        classification: 'contrato',
        confidence: 0.95,
        entities: [
          { type: 'cpf', value: '123.456.789-01', confidence: 0.98 },
          { type: 'valor_monetario', value: 'R$ 150.000,00', confidence: 0.92 },
          { type: 'data', value: '15/01/2024', confidence: 0.85 }
        ],
        summary: 'Contrato de prestação de serviços com valor de R$ 150.000,00...',
        processingTime: 5.2
      }
    ]);

    setDecisions([
      {
        id: '1',
        decision: 'aprovar',
        confidence: 'high',
        reasoning: 'Score de crédito alto (850) e documentação completa.',
        timestamp: '2024-01-15T10:45:00',
        feedbackScore: 0.9
      }
    ]);

    setTasks([
      {
        id: '1',
        workflowName: 'Aprovação de Crédito',
        taskName: 'Revisão Manual',
        assignee: 'manager@empresa.com',
        priority: 5,
        dueDate: '2024-01-16T17:00:00',
        formFields: [
          { name: 'approved', type: 'boolean', required: true },
          { name: 'comments', type: 'text', required: false }
        ]
      }
    ]);
  };

  const StatusCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-6 animate-fadeIn transition-colors`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', isDarkMode ? '-900' : '-100')}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const ProcessCard: React.FC<{ process: ProcessStatus }> = ({ process }) => {
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'running': return 'text-blue-600';
        case 'completed': return 'text-green-600';
        case 'failed': return 'text-red-600';
        default: return 'text-yellow-600';
      }
    };

    const getStatusIcon = (status: string) => {
      switch (status) {
        case 'running': return <RefreshCw className="w-4 h-4 animate-spin" />;
        case 'completed': return <CheckCircle className="w-4 h-4" />;
        case 'failed': return <XCircle className="w-4 h-4" />;
        default: return <Clock className="w-4 h-4" />;
      }
    };

    return (
      <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-4 animate-fadeIn transition-colors`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{process.name}</h3>
          <div className={`flex items-center gap-1 ${getStatusColor(process.status)}`}>
            {getStatusIcon(process.status)}
            <span className="text-sm capitalize">{process.status}</span>
          </div>
        </div>
        
        <div className="mb-2">
          <div className={`flex justify-between text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-1`}>
            <span>Progresso</span>
            <span>{process.progress}%</span>
          </div>
          <div className={`w-full ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-full h-2`}>
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${process.progress}%` }}
            />
          </div>
        </div>
        
        <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          Iniciado: {new Date(process.startTime).toLocaleString('pt-BR')}
          {process.estimatedTime && (
            <div>Tempo estimado: {Math.round(process.estimatedTime / 60)} min</div>
          )}
        </div>
      </div>
    );
  };

  const DocumentCard: React.FC<{ document: DocumentAnalysis }> = ({ document }) => (
    <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-4 animate-fadeIn transition-colors`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{document.filename}</h3>
        </div>
        <span className={`text-xs ${isDarkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'} px-2 py-1 rounded`}>
          {(document.confidence * 100).toFixed(0)}% confiança
        </span>
      </div>
      
      <div className="mb-3">
        <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Classificação: </span>
        <span className="text-sm text-blue-600 capitalize">{document.classification}</span>
      </div>
      
      <div className="mb-3">
        <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'} line-clamp-2`}>{document.summary}</p>
      </div>
      
      <div className="flex flex-wrap gap-1 mb-3">
        {document.entities.slice(0, 3).map((entity, index) => (
          <span 
            key={index}
            className={`text-xs ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'} px-2 py-1 rounded`}
          >
            {entity.type}: {entity.value}
          </span>
        ))}
        {document.entities.length > 3 && (
          <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            +{document.entities.length - 3} mais
          </span>
        )}
      </div>
      
      <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        Processado em {document.processingTime}s
      </div>
    </div>
  );

  const DecisionCard: React.FC<{ decision: Decision }> = ({ decision }) => (
    <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-4 animate-fadeIn transition-colors`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            decision.decision === 'aprovar' ? 'bg-green-500' :
            decision.decision === 'rejeitar' ? 'bg-red-500' : 'bg-yellow-500'
          }`} />
          <h3 className={`font-medium capitalize ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{decision.decision}</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${
          decision.confidence === 'high' ? (isDarkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800') :
          decision.confidence === 'medium' ? (isDarkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800') :
          (isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800')
        }`}>
          {decision.confidence} confiança
        </span>
      </div>
      
      <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-3`}>{decision.reasoning}</p>
      
      <div className={`flex justify-between items-center text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        <span>{new Date(decision.timestamp).toLocaleString('pt-BR')}</span>
        {decision.feedbackScore && (
          <span className="text-green-600">
            ⭐ {(decision.feedbackScore * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );

  const TaskCard: React.FC<{ task: WorkflowTask }> = ({ task }) => {
    const [formData, setFormData] = useState<Record<string, any>>({});
    const [isCompleting, setIsCompleting] = useState(false);

    const handleCompleteTask = async () => {
      setIsCompleting(true);
      
      try {
        // Aqui seria a chamada real para a API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Remover tarefa da lista
        setTasks(prev => prev.filter(t => t.id !== task.id));
      } catch (error) {
        console.error('Erro ao completar tarefa:', error);
      } finally {
        setIsCompleting(false);
      }
    };

    return (
      <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-4 animate-fadeIn transition-colors`}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{task.taskName}</h3>
            <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{task.workflowName}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              task.priority >= 7 ? 'bg-red-500' :
              task.priority >= 5 ? 'bg-yellow-500' : 'bg-green-500'
            }`} />
            <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Prioridade {task.priority}
            </span>
          </div>
        </div>
        
        <div className="mb-3">
          <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Responsável: {task.assignee}</p>
          <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            Vencimento: {new Date(task.dueDate).toLocaleString('pt-BR')}
          </p>
        </div>
        
        <div className="space-y-2 mb-4">
          {task.formFields.map((field, index) => (
            <div key={index}>
              <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'} mb-1`}>
                {field.name} {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.type === 'boolean' ? (
                <select 
                  className={`w-full p-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    isDarkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
                  }`}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    [field.name]: e.target.value === 'true'
                  }))}
                >
                  <option value="">Selecione...</option>
                  <option value="true">Sim</option>
                  <option value="false">Não</option>
                </select>
              ) : (
                <textarea
                  className={`w-full p-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  }`}
                  rows={2}
                  placeholder={`Digite ${field.name}...`}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    [field.name]: e.target.value
                  }))}
                />
              )}
            </div>
          ))}
        </div>
        
        <button
          onClick={handleCompleteTask}
          disabled={isCompleting}
          className="w-full bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
        >
          {isCompleting ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Completando...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Completar Tarefa
            </>
          )}
        </button>
      </div>
    );
  };

  const FileUploadArea: React.FC = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const handleFileUpload = async (files: FileList) => {
      setIsUploading(true);
      
      try {
        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('tipo_analise', 'completa');
        formData.append('user_id', 'frontend_user');
        formData.append('company_id', 'demo_company');

        const response = await axios.post(`${API_BASE_URL}/documentos/analisar`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        const result = response.data;
        
        // Adicionar documento analisado à lista
        const newDoc: DocumentAnalysis = {
          id: result.task_id,
          filename: files[0].name,
          classification: result.result?.classification || 'documento_generico',
          confidence: result.result?.confidence || 0.5,
          entities: result.result?.entities || [],
          summary: result.result?.summary || 'Documento processado automaticamente',
          processingTime: result.execution_time || 0
        };
        
        setDocuments(prev => [newDoc, ...prev]);
        
      } catch (error) {
        console.error('Erro ao fazer upload:', error);
        setError('Erro ao processar documento');
      } finally {
        setIsUploading(false);
      }
    };

    return (
      <div 
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : isDarkMode 
              ? 'border-gray-600 bg-gray-800' 
              : 'border-gray-300 bg-white'
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const files = e.dataTransfer.files;
          if (files.length > 0) {
            handleFileUpload(files);
          }
        }}
      >
        {isUploading ? (
          <div className="flex flex-col items-center gap-2">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
            <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Analisando documento...</p>
          </div>
        ) : (
          <>
            <Upload className={`w-12 h-12 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'} mx-auto mb-4`} />
            <p className={`text-lg font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-700'} mb-2`}>
              Arraste documentos aqui ou clique para selecionar
            </p>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Suporte a PDF, DOCX, imagens e planilhas
            </p>
            <input
              type="file"
              multiple
              className="hidden"
              id="file-upload"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileUpload(e.target.files);
                }
              }}
            />
            <label 
              htmlFor="file-upload"
              className="inline-block mt-4 bg-blue-600 text-white px-4 py-2 rounded-md cursor-pointer hover:bg-blue-700 transition-colors"
            >
              Selecionar Arquivos
            </label>
          </>
        )}
      </div>
    );
  };

  const renderTabContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
          <span className={`ml-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Carregando dados...</span>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {error && (
              <div className={`${isDarkMode ? 'bg-red-900/50 border-red-700' : 'bg-red-50 border-red-200'} border rounded-lg p-4`}>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className={`${isDarkMode ? 'text-red-200' : 'text-red-700'}`}>{error}</span>
                </div>
              </div>
            )}
            
            {/* Cards de Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatusCard
                title="Processos Ativos"
                value={systemStatus.processesRunning}
                icon={<Activity className="w-6 h-6" />}
                color="text-blue-600"
              />
              <StatusCard
                title="Decisões Hoje"
                value={systemStatus.decisionsToday}
                icon={<BarChart3 className="w-6 h-6" />}
                color="text-green-600"
              />
              <StatusCard
                title="Documentos Processados"
                value={systemStatus.documentsProcessed}
                icon={<FileText className="w-6 h-6" />}
                color="text-purple-600"
              />
              <StatusCard
                title="Tarefas Pendentes"
                value={systemStatus.tasksWaiting}
                icon={<Users className="w-6 h-6" />}
                color="text-orange-600"
              />
            </div>

            {/* Processos em Andamento */}
            <div>
              <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Processos em Andamento</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {processes.map(process => (
                  <ProcessCard key={process.id} process={process} />
                ))}
              </div>
            </div>

            {/* Decisões Recentes */}
            <div>
              <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Decisões Recentes</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {decisions.map(decision => (
                  <DecisionCard key={decision.id} decision={decision} />
                ))}
              </div>
            </div>
          </div>
        );

      case 'documents':
        return (
          <div className="space-y-6">
            <FileUploadArea />
            
            <div>
              <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Documentos Analisados</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {documents.map(document => (
                  <DocumentCard key={document.id} document={document} />
                ))}
              </div>
            </div>
          </div>
        );

      case 'tasks':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className={`text-lg font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Tarefas Pendentes</h2>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors">
                Filtrar Tarefas
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tasks.map(task => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <h2 className={`text-lg font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Analytics e Relatórios</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-6 transition-colors`}>
                <h3 className={`font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Performance dos Processos</h3>
                <div className={`h-64 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'} rounded flex items-center justify-center`}>
                  <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Gráfico de Performance</p>
                </div>
              </div>
              
              <div className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow-sm border p-6 transition-colors`}>
                <h3 className={`font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Precisão das Decisões</h3>
                <div className={`h-64 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'} rounded flex items-center justify-center`}>
                  <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Gráfico de Precisão</p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`min-h-screen transition-colors ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} shadow-sm border-b transition-colors`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>OmniCore AI</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.status === 'active' ? 'bg-green-500' : 
                  systemStatus.status === 'loading' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                {systemStatus.status === 'active' ? 'Sistema Ativo' : 
                 systemStatus.status === 'loading' ? 'Carregando...' : 'Sistema Inativo'}
              </div>
              
              {/* Botão de Tema */}
              <button 
                onClick={toggleTheme}
                className={`p-2 rounded-md transition-colors ${
                  isDarkMode 
                    ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
                title={isDarkMode ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
              >
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              
              <button 
                onClick={fetchSystemStatus}
                className={`p-2 rounded-md transition-colors ${
                  isDarkMode 
                    ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              <button className={`p-2 rounded-md transition-colors ${
                isDarkMode 
                  ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}>
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className={`${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b transition-colors`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'overview', name: 'Visão Geral', icon: BarChart3 },
              { id: 'documents', name: 'Documentos', icon: FileText },
              { id: 'tasks', name: 'Tarefas', icon: Users },
              { id: 'analytics', name: 'Analytics', icon: Activity }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : isDarkMode
                      ? 'border-transparent text-gray-400 hover:text-gray-200'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </main>
      <AdvancedChatInterface />
    </div>
  );
};

export default OmniCoreDashboard;