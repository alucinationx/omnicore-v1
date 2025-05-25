#!/usr/bin/env python3
"""
OmniCore AI CLI - Ferramenta de linha de comando
"""

import click
import requests
import json
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    """🤖 OmniCore AI - Interface de Linha de Comando"""
    pass

@cli.command()
def status():
    """Verifica status do sistema"""
    try:
        response = requests.get("http://localhost:8000/health")
        data = response.json()
        
        table = Table(title="Status do OmniCore AI")
        table.add_column("Componente", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("API", "🟢 Ativo" if data.get("status") == "active" else "🔴 Inativo")
        table.add_row("Agent ID", data.get("agent_id", "N/A")[:8] + "...")
        table.add_row("Processos Ativos", str(data.get("active_processes", 0)))
        
        console.print(table)
        
    except requests.exceptions.ConnectionError:
        console.print("❌ Não foi possível conectar à API", style="bold red")
        console.print("Verifique se o sistema está rodando: docker-compose up -d")

@cli.command()
@click.argument("file_path")
def analyze(file_path):
    """Analisa um documento"""
    try:
        console.print(f"📄 Analisando: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"user_id": "cli", "company_id": "demo"}
            
            response = requests.post(
                "http://localhost:8000/documentos/analisar",
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            console.print("✅ Análise concluída!", style="bold green")
            console.print(f"Classificação: {result.get('result', {}).get('classification', 'N/A')}")
            console.print(f"Confiança: {result.get('result', {}).get('confidence', 0):.2%}")
        else:
            console.print("❌ Erro na análise", style="bold red")
            
    except FileNotFoundError:
        console.print(f"❌ Arquivo não encontrado: {file_path}", style="bold red")
    except Exception as e:
        console.print(f"❌ Erro: {str(e)}", style="bold red")

if __name__ == "__main__":
    cli()
