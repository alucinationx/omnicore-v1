// components/AdvancedChatInterface.tsx
// Interface Avançada para Agente IA Conversacional

import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { 
  Send, 
  Paperclip, 
  Bot, 
  User, 
  Loader2, 
  AlertCircle,
  CheckCircle,
  FileText,
  Minimize2,
  Maximize2,
  X,
  Brain,
  Zap,
  Database,
  BarChart3,
  Settings,
  History,
  Lightbulb,
  Workflow,
  FileImage,
  MessageSquare,
  Star,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

// Tipos avançados
interface AIMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  attachments?: Array<{
    name: string;
    url: string;
    type: string;
  }>;
  function_calls?: Array<{
    function: string;
    arguments: any;
    result: any;
  }>;
  data?: any;
  suggestions?: string[];
  confidence?: number;
  processing_time?: number;
}

interface AICapability {
  name: string;
  description: string;
  category: string;
  examples: string[];
  icon: React.ComponentType<any>;
}

interface UserContext {
  user_id: string;
  preferences: any;
  conversation_id: string;
  session_data: any;
}

const AdvancedChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [aiCapabilities, setAiCapabilities] = useState<AICapability[]>([]);
  const [userContext, setUserContext] = useState<UserContext>({
    user_id: 'advanced_user',
    preferences: {},
    conversation_id: '',
    session_data: {}
  });
  const [isMinimized, setIsMinimized] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [showCapabilities, setShowCapabilities] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Scroll automático
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Inicialização
  useEffect(() => {
    initializeAIChat();
  }, []);

  const initializeAIChat = async () => {
    try {
      setConnectionStatus('connecting');
      
      // Carregar capacidades da IA
      const capabilitiesResponse = await axios.get(`${API_BASE_URL}/ai/capabilities`);
      
      if (capabilitiesResponse.data.success) {
        const caps = Object.values(capabilitiesResponse.data.capabilities).map((cap: any) => ({
          ...cap,
          icon: getCapabilityIcon(cap.category)
        }));
        setAiCapabilities(caps);
      }

      // Carregar histórico do usuário
      const historyResponse = await axios.get(`${API_BASE_URL}/ai/memory/${userContext.user_id}`);
      
      if (historyResponse.data.success && historyResponse.data.messages) {
        const historicalMessages = historyResponse.data.messages.map((msg: any) => ({
          ...msg,
          id: msg.id || `hist_${Date.now()}_${Math.random()}`,
          timestamp: new Date(msg.timestamp),
          type: msg.role === 'user' ? 'user' : 'assistant'
        }));
        setMessages(historicalMessages);
        setUserContext(prev => ({
          ...prev,
          conversation_id: historyResponse.data.conversation_id || ''
        }));
      }

      // Mensagem de boas-vindas se não há histórico
      if (messages.length === 0) {
        const welcomeMessage: AIMessage = {
          id: 'welcome_advanced',
          type: 'assistant',
          content: '🧠 **OmniCore AI Avançado Ativado!**\n\nSou seu assistente inteligente com IA avançada. Posso:\n\n🔍 **Analisar documentos** com contexto profundo\n🤖 **Automatizar workflows** complexos\n📊 **Consultar dados** em linguagem natural\n📈 **Gerar insights** inteligentes\n🧠 **Lembrar contexto** de nossas conversas\n\nTenho memória persistente e aprendo com nossas interações. Como posso ajudar?',
          timestamp: new Date(),
          suggestions: [
            'Analise este documento',
            'Consulte dados de vendas',
            'Gere relatório mensal',
            'Inicie processo de aprovação'
          ],
          confidence: 1.0
        };
        setMessages([welcomeMessage]);
      }

      setConnectionStatus('connected');
      
    } catch (error) {
      console.error('Erro na inicialização:', error);
      setConnectionStatus('disconnected');
      
      // Fallback local
      const errorMessage: AIMessage = {
        id: 'error_init',
        type: 'system',
        content: '⚠️ Modo offline ativado. Funcionalidades limitadas disponíveis.',
        timestamp: new Date(),
        suggestions: ['Tentar reconectar', 'Ver capacidades offline']
      };
      setMessages([errorMessage]);
    }
  };

  const getCapabilityIcon = (category: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      'documents': FileText,
      'data': Database,
      'automation': Workflow,
      'reporting': BarChart3,
      'monitoring': Settings,
      'intelligence': Brain
    };
    return iconMap[category] || Zap;
  };

  // Enviar mensagem para IA avançada
  const sendAdvancedMessage = async (content: string, files?: File[]) => {
    if (!content.trim() && !files?.length) return;

    const userMessage: AIMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: content || '📎 Arquivo(s) enviado(s)',
      timestamp: new Date(),
      attachments: files?.map(file => ({
        name: file.name,
        url: URL.createObjectURL(file),
        type: file.type
      }))
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setAttachments([]);
    setIsTyping(true);
    setIsProcessing(true);

    try {
      // Preparar dados para IA avançada
      const formData = new FormData();
      formData.append('message', content);
      formData.append('user_id', userContext.user_id);
      formData.append('conversation_id', userContext.conversation_id);

      // Adicionar arquivos
      if (files) {
        files.forEach((file, index) => {
          formData.append(`files`, file);
        });
      }

      // Chamar IA avançada
      const response = await axios.post(`${API_BASE_URL}/ai/chat`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000 // 60 segundos para IA processar
      });

      if (response.data.success) {
        const aiResponse = response.data.response;
        
        const aiMessage: AIMessage = {
          id: `ai_${Date.now()}`,
          type: 'assistant',
          content: aiResponse.message,
          timestamp: new Date(),
          suggestions: aiResponse.suggestions || [],
          function_calls: aiResponse.function_calls || [],
          data: aiResponse.data,
          processing_time: response.data.response.processing_time,
          confidence: aiResponse.confidence
        };

        setMessages(prev => [...prev, aiMessage]);
        setConnectionStatus('connected');

        // Atualizar contexto se necessário
        if (aiResponse.context_updated) {
          setUserContext(prev => ({
            ...prev,
            session_data: aiResponse.context_updated
          }));
        }

      } else {
        throw new Error(response.data.error || 'Erro na resposta da IA');
      }

    } catch (error: any) {
      console.error('Erro na conversa com IA:', error);
      setConnectionStatus('disconnected');
      
      // Resposta de erro inteligente
      const errorMessage: AIMessage = {
        id: `error_${Date.now()}`,
        type: 'system',
        content: `❌ **Erro na IA Avançada**\n\n${error.response?.status === 429 ? 'Limite de uso atingido. Tente novamente em alguns minutos.' : error.message || 'Erro de conexão'}\n\nModo básico ativado.`,
        timestamp: new Date(),
        suggestions: ['Tentar novamente', 'Usar modo básico', 'Verificar conexão']
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      setIsProcessing(false);
    }
  };

  // Executar sugestão
  const executeSuggestion = (suggestion: string) => {
    sendAdvancedMessage(suggestion);
  };

  // Feedback para IA
  const provideFeedback = async (messageId: string, feedback: 'positive' | 'negative', correction?: string) => {
    try {
      await axios.post(`${API_BASE_URL}/ai/train`, {
        user_id: userContext.user_id,
        message_id: messageId,
        feedback,
        correction: correction || ''
      });

      // Indicação visual de feedback enviado
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, feedback_provided: feedback }
          : msg
      ));

    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
    }
  };

  // Limpar conversa
  const clearConversation = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/ai/memory/${userContext.user_id}`);
      setMessages([]);
      setUserContext(prev => ({ ...prev, conversation_id: '' }));
      
      // Reinicializar
      await initializeAIChat();
    } catch (error) {
      console.error('Erro ao limpar conversa:', error);
    }
  };

  // Manipular upload de arquivos
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  // Remover anexo
  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // Componente de mensagem avançada
  const AdvancedMessageBubble: React.FC<{ message: AIMessage }> = ({ message }) => (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start max-w-[85%]`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            message.type === 'user' 
              ? 'bg-blue-500 text-white' 
              : message.type === 'system'
              ? 'bg-yellow-500 text-white'
              : 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
          }`}>
            {message.type === 'user' ? (
              <User className="w-5 h-5" />
            ) : message.type === 'system' ? (
              <AlertCircle className="w-5 h-5" />
            ) : (
              <Brain className="w-5 h-5" />
            )}
          </div>
        </div>

        {/* Conteúdo da mensagem */}
        <div className={`rounded-2xl px-4 py-3 ${
          message.type === 'user' 
            ? 'bg-blue-500 text-white' 
            : message.type === 'system'
            ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
            : 'bg-white text-gray-800 border border-gray-200 shadow-sm'
        }`}>
          {/* Conteúdo principal */}
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </div>

          {/* Function calls (ações executadas) */}
          {message.function_calls && message.function_calls.length > 0 && (
            <div className="mt-3 p-2 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-xs font-medium text-blue-700 mb-1">🔧 Ações Executadas:</div>
              {message.function_calls.map((call, index) => (
                <div key={index} className="text-xs text-blue-600">
                  • {call.function.replace('_', ' ').toLowerCase()}
                </div>
              ))}
            </div>
          )}

          {/* Dados estruturados */}
          {message.data && (
            <div className="mt-3 p-2 bg-gray-50 rounded-lg">
              <div className="text-xs font-medium text-gray-700 mb-1">📊 Dados:</div>
              <div className="text-xs text-gray-600 max-h-20 overflow-y-auto">
                {JSON.stringify(message.data, null, 2).slice(0, 200)}...
              </div>
            </div>
          )}

          {/* Anexos */}
          {message.attachments && (
            <div className="mt-2 space-y-1">
              {message.attachments.map((attachment, index) => (
                <div key={index} className="flex items-center gap-2 text-xs opacity-75">
                  <FileText className="w-3 h-3" />
                  <span>{attachment.name}</span>
                </div>
              ))}
            </div>
          )}

          {/* Metadados */}
          <div className="flex justify-between items-center mt-2 text-xs opacity-60">
            <span>
              {message.timestamp.toLocaleTimeString('pt-BR', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
            
            {message.processing_time && (
              <span>⚡ {message.processing_time.toFixed(1)}s</span>
            )}
            
            {message.confidence && (
              <span>🎯 {(message.confidence * 100).toFixed(0)}%</span>
            )}
          </div>

          {/* Feedback buttons para mensagens da IA */}
          {message.type === 'assistant' && (
            <div className="flex gap-1 mt-2">
              <button
                onClick={() => provideFeedback(message.id, 'positive')}
                className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                title="Resposta útil"
              >
                <ThumbsUp className="w-3 h-3" />
              </button>
              <button
                onClick={() => provideFeedback(message.id, 'negative')}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Resposta não útil"
              >
                <ThumbsDown className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Componente de sugestões avançadas
  const AdvancedSuggestions: React.FC<{ suggestions: string[] }> = ({ suggestions }) => (
    <div className="flex flex-wrap gap-2 mb-4 px-4">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => executeSuggestion(suggestion)}
          className="bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 text-blue-700 text-xs px-3 py-2 rounded-full border border-blue-200 transition-all duration-200 transform hover:scale-105"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );

  // Indicador de processamento IA
  const AIProcessingIndicator: React.FC = () => (
    <div className="flex justify-start mb-6 px-4">
      <div className="flex items-center space-x-3 text-gray-500 bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl px-4 py-3 border border-purple-200">
        <Brain className="w-5 h-5 text-purple-500" />
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
        </div>
        <span className="text-sm font-medium">IA processando...</span>
      </div>
    </div>
  );

  // Status da conexão
  const ConnectionStatusBadge: React.FC = () => (
    <div className="flex items-center gap-2 text-sm">
      {connectionStatus === 'connected' ? (
        <>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-600 font-medium">IA Avançada</span>
        </>
      ) : connectionStatus === 'connecting' ? (
        <>
          <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
          <span className="text-yellow-600">Conectando...</span>
        </>
      ) : (
        <>
          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
          <span className="text-red-600">Offline</span>
        </>
      )}
    </div>
  );

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsMinimized(false)}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-300 group"
        >
          <Brain className="w-6 h-6 group-hover:scale-110 transition-transform" />
          {connectionStatus === 'connected' && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col z-50">
      {/* Header avançado */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 rounded-t-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Brain className="w-6 h-6" />
            {connectionStatus === 'connected' && (
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            )}
          </div>
          <div>
            <h3 className="font-bold">OmniCore AI</h3>
            <ConnectionStatusBadge />
          </div>
        </div>
        <div className="flex gap-1">
          <button 
            onClick={() => setShowCapabilities(!showCapabilities)}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Ver capacidades"
          >
            <Lightbulb className="w-4 h-4" />
          </button>
          <button 
            onClick={clearConversation}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Nova conversa"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
          <button 
            onClick={() => setIsMinimized(true)}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Capacidades (se visível) */}
      {showCapabilities && (
        <div className="p-3 bg-gray-50 border-b max-h-32 overflow-y-auto">
          <div className="text-xs font-medium text-gray-600 mb-2">🧠 Capacidades IA:</div>
          <div className="grid grid-cols-2 gap-1">
            {aiCapabilities.slice(0, 6).map((cap, index) => (
              <div key={index} className="flex items-center gap-1 text-xs text-gray-600">
                <cap.icon className="w-3 h-3" />
                <span className="truncate">{cap.name.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.map((message, index) => (
          <React.Fragment key={message.id}>
            <AdvancedMessageBubble message={message} />
            {message.suggestions && message.type === 'assistant' && (
              <AdvancedSuggestions suggestions={message.suggestions} />
            )}
          </React.Fragment>
        ))}
        
        {isProcessing && <AIProcessingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="px-4 py-2 border-t bg-gradient-to-r from-purple-50 to-blue-50">
          <div className="flex flex-wrap gap-2">
            {attachments.map((file, index) => (
              <div key={index} className="flex items-center gap-1 bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-lg">
                <FileImage className="w-3 h-3" />
                <span className="max-w-20 truncate">{file.name}</span>
                <button 
                  onClick={() => removeAttachment(index)}
                  className="hover:bg-purple-200 rounded-full p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendAdvancedMessage(inputMessage, attachments);
                }
              }}
              placeholder="Converse com a IA avançada..."
              className="w-full p-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm bg-white"
              rows={2}
              disabled={isProcessing}
            />
          </div>
          
          <div className="flex flex-col gap-1">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-500 hover:text-purple-600 transition-colors"
              title="Anexar arquivo"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => sendAdvancedMessage(inputMessage, attachments)}
              disabled={isProcessing || (!inputMessage.trim() && attachments.length === 0)}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 text-white p-2 rounded-xl transition-all duration-200"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileUpload}
          className="hidden"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xlsx,.xls,.txt"
        />
        
        <div className="text-xs text-gray-500 mt-2 text-center">
          IA com memória persistente e contexto avançado
        </div>
      </div>
    </div>
  );
};

export default AdvancedChatInterface;