#!/bin/bash

# OmniCore AI - Verificar Estrutura Existente

echo "🔍 Verificando estrutura atual do projeto..."
echo "============================================"

# Verificar diretório atual
echo "📁 Diretório atual: $(pwd)"
echo ""

# Verificar se pasta frontend existe
if [ -d "frontend" ]; then
    echo "✅ Pasta frontend/ encontrada"
    
    # Listar conteúdo da pasta frontend
    echo "📋 Conteúdo da pasta frontend/:"
    ls -la frontend/
    echo ""
    
    # Verificar se é projeto React existente
    if [ -f "frontend/package.json" ]; then
        echo "✅ package.json encontrado - É um projeto React/Node existente"
        echo "📄 Dependências atuais:"
        cat frontend/package.json | grep -A 10 '"dependencies"' || echo "Nenhuma dependência encontrada"
    else
        echo "❌ package.json NÃO encontrado - Pasta frontend não é projeto React"
    fi
    
    # Verificar se arquivo frontend existe
    if [ -f "frontend/omnicore_frontend.tsx" ]; then
        echo "✅ omnicore_frontend.tsx encontrado!"
    else
        echo "❌ omnicore_frontend.tsx NÃO encontrado na pasta frontend/"
    fi
    
else
    echo "❌ Pasta frontend/ NÃO encontrada"
fi

echo ""
echo "🌐 Verificando portas em uso:"
# Verificar porta 3000 (Grafana)
if lsof -i :3000 >/dev/null 2>&1; then
    echo "🔴 Porta 3000 - EM USO (Grafana)"
else
    echo "🟢 Porta 3000 - LIVRE"
fi

# Verificar porta 3001 (React alternativa)
if lsof -i :3001 >/dev/null 2>&1; then
    echo "🔴 Porta 3001 - EM USO"
else
    echo "🟢 Porta 3001 - LIVRE (IDEAL para React)"
fi

# Verificar porta 8000 (Backend)
if lsof -i :8000 >/dev/null 2>&1; then
    echo "🟢 Porta 8000 - EM USO (Backend OmniCore)"
else
    echo "🔴 Porta 8000 - LIVRE (Backend precisa estar rodando)"
fi

echo ""
echo "🐳 Verificando Docker:"
docker-compose ps 2>/dev/null || echo "Docker Compose não está rodando ou não existe"

echo ""
echo "📋 RESUMO DA ANÁLISE:"
echo "===================="
if [ -d "frontend" ] && [ -f "frontend/omnicore_frontend.tsx" ]; then
    if [ -f "frontend/package.json" ]; then
        echo "✅ Cenário: Projeto React EXISTENTE com arquivo frontend"
        echo "📋 Ação: Configurar React na porta 3001"
    else
        echo "✅ Cenário: Pasta frontend com arquivo TSX, mas SEM projeto React"
        echo "📋 Ação: Inicializar projeto React na pasta existente"
    fi
else
    echo "❌ Cenário: Estrutura incompleta"
    echo "📋 Ação: Verificar localização dos arquivos"
fi