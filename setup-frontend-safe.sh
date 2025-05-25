#!/bin/bash

# OmniCore AI - Setup Frontend Inteligente (Porta 3001, preserva Grafana)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🛠️ OmniCore AI - Setup Frontend Inteligente${NC}"
echo "=============================================="
echo -e "${YELLOW}📋 Porta 3000: Grafana (preservada)${NC}"
echo -e "${YELLOW}📋 Porta 3001: React Frontend (nova)${NC}"
echo -e "${YELLOW}📋 Porta 8000: API Backend${NC}"
echo ""

# Verificar se pasta frontend existe
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Pasta frontend/ não encontrada!${NC}"
    echo "Certifique-se de estar no diretório correto do projeto."
    exit 1
fi

echo -e "${GREEN}✅ Pasta frontend/ encontrada${NC}"

# Verificar se arquivo TSX existe
if [ ! -f "frontend/omnicore_frontend.tsx" ]; then
    echo -e "${RED}❌ Arquivo omnicore_frontend.tsx não encontrado na pasta frontend/!${NC}"
    echo "Verifique se o arquivo está no local correto."
    exit 1
fi

echo -e "${GREEN}✅ Arquivo omnicore_frontend.tsx encontrado${NC}"

cd frontend

# Verificar se já é um projeto React
if [ -f "package.json" ]; then
    echo -e "${YELLOW}📦 Projeto React existente detectado${NC}"
    
    # Backup do package.json atual
    cp package.json package.json.backup
    echo -e "${GREEN}✅ Backup do package.json criado${NC}"
    
    # Verificar se tem React instalado
    if grep -q '"react"' package.json; then
        echo -e "${GREEN}✅ React já está instalado${NC}"
    else
        echo -e "${BLUE}📦 Instalando React...${NC}"
        npm install react@18.2.0 react-dom@18.2.0 react-scripts@5.0.1
    fi
    
    # Verificar TypeScript
    if grep -q '"typescript"' package.json; then
        echo -e "${GREEN}✅ TypeScript já está instalado${NC}"
    else
        echo -e "${BLUE}📦 Instalando TypeScript...${NC}"
        npm install typescript@4.9.5 @types/react@18.2.0 @types/react-dom@18.2.0 --save-dev
    fi
    
else
    echo -e "${BLUE}📦 Inicializando novo projeto React...${NC}"
    
    # Criar package.json básico
    cat > package.json << 'EOF'
{
  "name": "omnicore-frontend",
  "version": "1.0.0",
  "description": "OmniCore AI Frontend Dashboard",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.5",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0"
  },
  "scripts": {
    "start": "PORT=3001 react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
EOF
    
    echo -e "${GREEN}✅ package.json criado${NC}"
fi

# Instalar dependências específicas do OmniCore
echo -e "${BLUE}📦 Instalando dependências do OmniCore...${NC}"
npm install lucide-react@0.263.1 axios@1.4.0

# Instalar Tailwind CSS
echo -e "${BLUE}🎨 Configurando Tailwind CSS...${NC}"
npm install tailwindcss@3.3.0 postcss@8.4.24 autoprefixer@10.4.14 --save-dev

# Configurar Tailwind
npx tailwindcss init -p

# Configurar tailwind.config.js
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        omnicore: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8'
        }
      }
    },
  },
  plugins: [],
}
EOF

# Criar estrutura src se não existir
mkdir -p src public

# Configurar src/index.css
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f9fafb;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Utilities específicas do OmniCore */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Scrollbar customizada */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
EOF

# Processar arquivo TSX e converter para App.tsx
echo -e "${BLUE}📄 Processando omnicore_frontend.tsx...${NC}"

# Copiar arquivo original para src/App.tsx
cp omnicore_frontend.tsx src/App.tsx

# Ajustar imports para React padrão (se necessário)
sed -i 's/\/\/ OmniCore AI - Interface Web Principal/\/\/ OmniCore AI - Interface Web Principal/' src/App.tsx

echo -e "${GREEN}✅ App.tsx criado a partir do seu arquivo${NC}"

# Configurar src/index.tsx
cat > src/index.tsx << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Configurar public/index.html
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#2563eb" />
    <meta name="description" content="OmniCore AI - Agente de IA Empresarial Inteligente" />
    <meta name="author" content="OmniCore AI Team" />
    <title>OmniCore AI - Dashboard</title>
    <style>
      body { margin: 0; background: #f9fafb; }
      .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        font-family: system-ui, -apple-system, sans-serif;
        color: #6b7280;
        flex-direction: column;
        gap: 1rem;
      }
      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #e5e7eb;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    </style>
  </head>
  <body>
    <noscript>Você precisa habilitar JavaScript para executar esta aplicação.</noscript>
    <div id="root">
      <div class="loading">
        <div class="loading-spinner"></div>
        <div>Carregando OmniCore AI...</div>
      </div>
    </div>
  </body>
</html>
EOF

# Atualizar package.json com configurações específicas
echo -e "${BLUE}🔧 Configurando scripts e proxy...${NC}"

# Configurar para rodar na porta 3001
npm pkg set scripts.start="PORT=3001 react-scripts start"
npm pkg set scripts.dev="PORT=3001 react-scripts start"
npm pkg set scripts.build="react-scripts build"
npm pkg set scripts.test="react-scripts test"

# Configurar proxy para API
npm pkg set proxy="http://localhost:8000"

# Configurar variáveis de ambiente
cat > .env << 'EOF'
PORT=3001
REACT_APP_API_URL=http://localhost:8000
REACT_APP_NAME=OmniCore AI
REACT_APP_VERSION=1.0.0
GENERATE_SOURCEMAP=false
BROWSER=none
EOF

# Criar README específico
cat > README-Frontend.md << 'EOF'
# OmniCore AI - Frontend Dashboard

## 🚀 Execução

```bash
# Iniciar frontend (porta 3001)
npm start

# Build para produção
npm run build
```

## 🌐 URLs

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (preservado)

## 📋 Funcionalidades

- ✅ Dashboard em tempo real
- 📄 Upload e análise de documentos
- 🧪 Testes de decisões automáticas
- 📊 Métricas e analytics
- 🎨 Interface moderna com Tailwind CSS

## 🔧 Configuração

- Porta: 3001 (não conflita com Grafana)
- Proxy: http://localhost:8000 (API Backend)
- Build: React + TypeScript + Tailwind CSS
EOF

echo ""
echo -e "${GREEN}🎉 Setup concluído com sucesso!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📋 Estrutura configurada:${NC}"
echo "  ✅ React + TypeScript + Tailwind CSS"
echo "  ✅ Porta 3001 (não conflita com Grafana)"
echo "  ✅ Proxy configurado para API (porta 8000)"
echo "  ✅ Seu arquivo omnicore_frontend.tsx → src/App.tsx"
echo ""
echo -e "${YELLOW}🚀 Como executar:${NC}"
echo "  1. cd frontend"
echo "  2. npm start"
echo "  3. Acessar: http://localhost:3001"
echo ""
echo -e "${BLUE}🔗 URLs configuradas:${NC}"
echo "  • Frontend OmniCore: http://localhost:3001"
echo "  • Grafana (preservado): http://localhost:3000"
echo "  • API Backend: http://localhost:8000/docs"
echo ""
echo -e "${GREEN}✨ Grafana continua funcionando na porta 3000!${NC}"

# Perguntar se quer iniciar
echo ""
read -p "Deseja iniciar o frontend agora? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 Iniciando frontend na porta 3001...${NC}"
    npm start
fi