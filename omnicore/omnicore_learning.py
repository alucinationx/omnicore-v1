// OmniCore AI - Interface Web Principal
// Dashboard e interface de usuário para interação com o sistema

import React, { useState, useEffect, useCallback } from 'react';
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
  Pause
} from 'lucide-react';

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

// Componente principal do dashboard
const OmniCoreDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [processes, setProcesses] = useState<ProcessStatus[]>([]);
  const [documents, setDocuments] = useState<DocumentAnalysis[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [systemStatus, setSystemStatus] = useState({
    status: 'active',
    processesRunning: 0,
    decisionsToday: 0,
    documentsProcessed: 0,
    tasksWaiting: 0
  });

  // Simulação de dados para demonstração
  useEffect(() => {
    // Simular carregamento de dados
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

      setSystemStatus({
        status: 'active',
        processesRunning: 3,
        decisionsToday: 27,
        documentsProcessed: 145,
        tasksWaiting: 5
      });
    };

    loadMockData();
  }, []);

  const StatusCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
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
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium">{process.name}</h3>
          <div className={`flex items-center gap-1 ${getStatusColor(process.status)}`}>
            {getStatusIcon(process.status)}
            <span className="text-sm capitalize">{process.status}</span>
          </div>
        </div>
        
        <div className="mb-2">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progresso</span>
            <span>{process.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${process.progress}%` }}
            />
          </div>
        </div>
        
        <div className="text-xs text-gray-500">
          Iniciado: {new Date(process.startTime).toLocaleString()}
          {process.estimatedTime && (
            <div>Tempo estimado: {Math.round(process.estimatedTime / 60)} min</div>
          )}
        </div>
      </div>
    );
  };

  const DocumentCard: React.FC<{ document: DocumentAnalysis }> = ({ document }) => (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="font-medium">{document.filename}</h3>
        </div>
        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
          {(document.confidence * 100).toFixed(0)}% confiança
        </span>
      </div>
      
      <div className="mb-3">
        <span className="text-sm font-medium text-gray-700">Classificação: </span>
        <span className="text-sm text-blue-600 capitalize">{document.classification}</span>
      </div>
      
      <div className="mb-3">
        <p className="text-sm text-gray-600 line-clamp-2">{document.summary}</p>
      </div>
      
      <div className="flex flex-wrap gap-1 mb-3">
        {document.entities.slice(0, 3).map((entity, index) => (
          <span 
            key={index}
            className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
          >
            {entity.type}: {entity.value}
          </span>
        ))}
        {document.entities.length > 3 && (
          <span className="text-xs text-gray-500">
            +{document.entities.length - 3} mais
          </span>
        )}
      </div>
      
      <div className="text-xs text-gray-500">
        Processado em {document.processingTime}s
      </div>
    </div>
  );

  const DecisionCard: React.FC<{ decision: Decision }> = ({ decision }) => (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            decision.decision === 'aprovar' ? 'bg-green-500' :
            decision.decision === 'rejeitar' ? 'bg-red-500' : 'bg-yellow-500'
          }`} />
          <h3 className="font-medium capitalize">{decision.decision}</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${
          decision.confidence === 'high' ? 'bg-green-100 text-green-800' :
          decision.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {decision.confidence} confiança
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{decision.reasoning}</p>
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{new Date(decision.timestamp).toLocaleString()}</span>
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
      
      // Simular chamada à API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Remover tarefa da lista
      setTasks(prev => prev.filter(t => t.id !== task.id));
      setIsCompleting(false);
    };

    return (
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-medium">{task.taskName}</h3>
            <p className="text-sm text-gray-600">{task.workflowName}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              task.priority >= 7 ? 'bg-red-500' :
              task.priority >= 5 ? 'bg-yellow-500' : 'bg-green-500'
            }`} />
            <span className="text-xs text-gray-500">
              Prioridade {task.priority}
            </span>
          </div>
        </div>
        
        <div className="mb-3">
          <p className="text-sm text-gray-600">Responsável: {task.assignee}</p>
          <p className="text-sm text-gray-600">
            Vencimento: {new Date(task.dueDate).toLocaleString()}
          </p>
        </div>
        
        <div className="space-y-2 mb-4">
          {task.formFields.map((field, index) => (
            <div key={index}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.name} {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.type === 'boolean' ? (
                <select 
                  className="w-full p-2 border rounded-md text-sm"
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
                  className="w-full p-2 border rounded-md text-sm"
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
          className="w-full bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
      
      // Simular upload e análise
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Adicionar documento simulado à lista
      const newDoc: DocumentAnalysis = {
        id: String(documents.length + 1),
        filename: files[0].name,
        classification: 'documento_generico',
        confidence: 0.87,
        entities: [
          { type: 'data', value: '15/01/2024', confidence: 0.9 }
        ],
        summary: 'Documento analisado automaticamente...',
        processingTime: 3.1
      };
      
      setDocuments(prev => [newDoc, ...prev]);
      setIsUploading(false);
    };

    return (
      <div 
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
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
            <p className="text-sm text-gray-600">Analisando documento...</p>
          </div>
        ) : (
          <>
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Arraste documentos aqui ou clique para selecionar
            </p>
            <p className="text-sm text-gray-500">
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
              className="inline-block mt-4 bg-blue-600 text-white px-4 py-2 rounded-md cursor-pointer hover:bg-blue-700"
            >
              Selecionar Arquivos
            </label>
          </>
        )}
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
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
              <h2 className="text-lg font-medium mb-4">Processos em Andamento</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {processes.map(process => (
                  <ProcessCard key={process.id} process={process} />
                ))}
              </div>
            </div>

            {/* Decisões Recentes */}
            <div>
              <h2 className="text-lg font-medium mb-4">Decisões Recentes</h2>
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
              <h2 className="text-lg font-medium mb-4">Documentos Analisados</h2>
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
              <h2 className="text-lg font-medium">Tarefas Pendentes</h2>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700">
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
            <h2 className="text-lg font-medium">Analytics e Relatórios</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="font-medium mb-4">Performance dos Processos</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">Gráfico de Performance</p>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="font-medium mb-4">Precisão das Decisões</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">Gráfico de Precisão</p>
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">OmniCore AI</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Sistema Ativo
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
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
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
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
    </div>
  );
};

export default OmniCoreDashboard;