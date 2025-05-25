# OmniCore AI - Sistema de Backup e Recuperação
# Backup automatizado, recuperação de desastres e migração de dados

import asyncio
import logging
import json
import os
import shutil
import tarfile
import gzip
import subprocess
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import psycopg2
import redis
import tempfile
from concurrent.futures import ThreadPoolExecutor
import schedule
import time
import threading

# Configuração de logging
logger = logging.getLogger("OmniCore.Backup")

class BackupType:
    """Tipos de backup"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus:
    """Status do backup"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BackupConfig:
    """Configuração de backup"""
    name: str
    backup_type: str
    schedule: str  # cron format
    retention_days: int
    compression: bool = True
    encryption: bool = True
    storage_backends: List[str] = field(default_factory=lambda: ["local"])
    exclude_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackupResult:
    """Resultado de backup"""
    backup_id: str
    config_name: str
    backup_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    size_bytes: int = 0
    file_count: int = 0
    checksum: Optional[str] = None
    storage_locations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class DatabaseBackup:
    """Backup de banco de dados PostgreSQL"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection_params = self._parse_connection_string(
            config.get("database_url", "")
        )
    
    def _parse_connection_string(self, connection_string: str) -> Dict[str, str]:
        """Parse da string de conexão PostgreSQL"""
        # postgresql://user:password@host:port/database
        import urllib.parse as urlparse
        
        parsed = urlparse.urlparse(connection_string)
        return {
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port or 5432),
            "database": parsed.path.lstrip('/') or "omnicore_db",
            "username": parsed.username or "omnicore",
            "password": parsed.password or ""
        }
    
    def create_backup(self, output_path: str, backup_type: str = BackupType.FULL) -> bool:
        """Cria backup do banco de dados"""
        try:
            logger.info(f"Iniciando backup do banco de dados: {backup_type}")
            
            # Configurar variáveis de ambiente para pg_dump
            env = os.environ.copy()
            if self.connection_params["password"]:
                env["PGPASSWORD"] = self.connection_params["password"]
            
            # Comandos pg_dump
            cmd = [
                "pg_dump",
                "-h", self.connection_params["host"],
                "-p", self.connection_params["port"],
                "-U", self.connection_params["username"],
                "-d", self.connection_params["database"],
                "--verbose",
                "--no-owner",
                "--no-privileges"
            ]
            
            if backup_type == BackupType.FULL:
                cmd.extend(["--create", "--clean"])
            
            # Executar backup
            with open(output_path, "w") as output_file:
                result = subprocess.run(
                    cmd,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
            
            if result.returncode == 0:
                logger.info(f"Backup do banco criado: {output_path}")
                return True
            else:
                logger.error(f"Erro no backup do banco: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao criar backup do banco: {str(e)}")
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restaura backup do banco de dados"""
        try:
            logger.info(f"Restaurando backup do banco: {backup_path}")
            
            # Configurar variáveis de ambiente
            env = os.environ.copy()
            if self.connection_params["password"]:
                env["PGPASSWORD"] = self.connection_params["password"]
            
            # Comando psql para restauração
            cmd = [
                "psql",
                "-h", self.connection_params["host"],
                "-p", self.connection_params["port"],
                "-U", self.connection_params["username"],
                "-d", self.connection_params["database"],
                "-f", backup_path
            ]
            
            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Backup do banco restaurado com sucesso")
                return True
            else:
                logger.error(f"Erro na restauração: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Testa conexão com o banco"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                database=self.connection_params["database"],
                user=self.connection_params["username"],
                password=self.connection_params["password"]
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro de conexão com banco: {str(e)}")
            return False

class RedisBackup:
    """Backup de dados Redis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.from_url(
            config.get("redis_url", "redis://localhost:6379/0")
        )
    
    def create_backup(self, output_path: str) -> bool:
        """Cria backup do Redis"""
        try:
            logger.info("Iniciando backup do Redis")
            
            # Forçar save no Redis
            self.redis_client.bgsave()
            
            # Aguardar conclusão do save
            while True:
                if self.redis_client.lastsave():
                    break
                time.sleep(1)
            
            # Copiar arquivo RDB
            redis_data_dir = self.config.get("redis_data_dir", "/var/lib/redis")
            rdb_file = os.path.join(redis_data_dir, "dump.rdb")
            
            if os.path.exists(rdb_file):
                shutil.copy2(rdb_file, output_path)
                logger.info(f"Backup do Redis criado: {output_path}")
                return True
            else:
                logger.error("Arquivo RDB não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao criar backup do Redis: {str(e)}")
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restaura backup do Redis"""
        try:
            logger.info(f"Restaurando backup do Redis: {backup_path}")
            
            # Parar Redis (seria necessário em produção)
            # subprocess.run(["redis-cli", "SHUTDOWN", "NOSAVE"])
            
            # Copiar arquivo de backup
            redis_data_dir = self.config.get("redis_data_dir", "/var/lib/redis")
            rdb_file = os.path.join(redis_data_dir, "dump.rdb")
            
            shutil.copy2(backup_path, rdb_file)
            
            # Reiniciar Redis (seria necessário em produção)
            # subprocess.run(["redis-server"])
            
            logger.info("Backup do Redis restaurado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar backup do Redis: {str(e)}")
            return False

class FileBackup:
    """Backup de arquivos e diretórios"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_paths = config.get("backup_paths", [])
        self.exclude_patterns = config.get("exclude_patterns", [])
    
    def create_backup(self, output_path: str, backup_type: str = BackupType.FULL) -> bool:
        """Cria backup de arquivos"""
        try:
            logger.info(f"Iniciando backup de arquivos: {backup_type}")
            
            # Criar arquivo tar
            with tarfile.open(output_path, "w:gz") as tar:
                for base_path in self.base_paths:
                    if os.path.exists(base_path):
                        logger.info(f"Adicionando ao backup: {base_path}")
                        
                        if os.path.isfile(base_path):
                            tar.add(base_path, arcname=os.path.basename(base_path))
                        else:
                            # Adicionar diretório com filtros
                            self._add_directory_to_tar(tar, base_path, base_path)
                    else:
                        logger.warning(f"Caminho não encontrado: {base_path}")
            
            logger.info(f"Backup de arquivos criado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de arquivos: {str(e)}")
            return False
    
    def _add_directory_to_tar(self, tar: tarfile.TarFile, directory: str, base_path: str):
        """Adiciona diretório ao arquivo tar com filtros"""
        for root, dirs, files in os.walk(directory):
            # Filtrar diretórios excluídos
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if not self._should_exclude(file_path):
                    # Calcular caminho relativo
                    arcname = os.path.relpath(file_path, base_path)
                    tar.add(file_path, arcname=arcname)
    
    def _should_exclude(self, file_path: str) -> bool:
        """Verifica se arquivo deve ser excluído"""
        import fnmatch
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def restore_backup(self, backup_path: str, restore_path: str) -> bool:
        """Restaura backup de arquivos"""
        try:
            logger.info(f"Restaurando backup de arquivos: {backup_path}")
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=restore_path)
            
            logger.info(f"Backup restaurado em: {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {str(e)}")
            return False

class StorageBackend:
    """Interface para backends de armazenamento"""
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        raise NotImplementedError
    
    def download(self, remote_path: str, local_path: str) -> bool:
        raise NotImplementedError
    
    def delete(self, remote_path: str) -> bool:
        raise NotImplementedError
    
    def list_backups(self) -> List[str]:
        raise NotImplementedError

class LocalStorageBackend(StorageBackend):
    """Backend de armazenamento local"""
    
    def __init__(self, config: Dict[str, Any]):
        self.backup_dir = Path(config.get("backup_directory", "/var/backups/omnicore"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        try:
            dest_path = self.backup_dir / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest_path)
            return True
        except Exception as e:
            logger.error(f"Erro no upload local: {str(e)}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        try:
            source_path = self.backup_dir / remote_path
            shutil.copy2(source_path, local_path)
            return True
        except Exception as e:
            logger.error(f"Erro no download local: {str(e)}")
            return False
    
    def delete(self, remote_path: str) -> bool:
        try:
            file_path = self.backup_dir / remote_path
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo local: {str(e)}")
            return False
    
    def list_backups(self) -> List[str]:
        try:
            return [str(f.relative_to(self.backup_dir)) for f in self.backup_dir.rglob("*") if f.is_file()]
        except Exception:
            return []

class S3StorageBackend(StorageBackend):
    """Backend de armazenamento AWS S3"""
    
    def __init__(self, config: Dict[str, Any]):
        self.bucket_name = config["bucket_name"]
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=config.get("access_key_id"),
            aws_secret_access_key=config.get("secret_access_key"),
            region_name=config.get("region", "us-east-1")
        )
        self.prefix = config.get("prefix", "omnicore-backups/")
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        try:
            key = f"{self.prefix}{remote_path}"
            self.s3_client.upload_file(local_path, self.bucket_name, key)
            logger.info(f"Backup enviado para S3: s3://{self.bucket_name}/{key}")
            return True
        except Exception as e:
            logger.error(f"Erro no upload S3: {str(e)}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        try:
            key = f"{self.prefix}{remote_path}"
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return True
        except Exception as e:
            logger.error(f"Erro no download S3: {str(e)}")
            return False
    
    def delete(self, remote_path: str) -> bool:
        try:
            key = f"{self.prefix}{remote_path}"
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar do S3: {str(e)}")
            return False
    
    def list_backups(self) -> List[str]:
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            backups = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key.startswith(self.prefix):
                    backups.append(key[len(self.prefix):])
            
            return backups
        except Exception as e:
            logger.error(f"Erro ao listar backups S3: {str(e)}")
            return []

class BackupManager:
    """Gerenciador principal de backups"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backup_configs: Dict[str, BackupConfig] = {}
        self.storage_backends: Dict[str, StorageBackend] = {}
        self.backup_history: List[BackupResult] = []
        
        # Inicializar componentes de backup
        self.db_backup = DatabaseBackup(config)
        self.redis_backup = RedisBackup(config)
        self.file_backup = FileBackup(config)
        
        # Configurar backends de armazenamento
        self._setup_storage_backends()
        
        # Scheduler para backups automáticos
        self.scheduler_thread = None
        self.scheduler_running = False
    
    def _setup_storage_backends(self):
        """Configura backends de armazenamento"""
        storage_config = self.config.get("storage", {})
        
        # Local storage
        if "local" in storage_config:
            self.storage_backends["local"] = LocalStorageBackend(
                storage_config["local"]
            )
        
        # AWS S3
        if "s3" in storage_config:
            self.storage_backends["s3"] = S3StorageBackend(
                storage_config["s3"]
            )
    
    def add_backup_config(self, config: BackupConfig):
        """Adiciona configuração de backup"""
        self.backup_configs[config.name] = config
        logger.info(f"Configuração de backup adicionada: {config.name}")
    
    def create_backup(self, config_name: str, backup_type: str = BackupType.FULL) -> BackupResult:
        """Cria backup baseado na configuração"""
        if config_name not in self.backup_configs:
            raise ValueError(f"Configuração de backup não encontrada: {config_name}")
        
        config = self.backup_configs[config_name]
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = BackupResult(
            backup_id=backup_id,
            config_name=config_name,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Iniciando backup: {backup_id}")
            
            # Criar diretório temporário
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Backup do banco de dados
                db_backup_file = temp_path / f"{backup_id}_database.sql"
                if self.db_backup.create_backup(str(db_backup_file), backup_type):
                    result.file_count += 1
                    result.size_bytes += db_backup_file.stat().st_size
                
                # Backup do Redis
                redis_backup_file = temp_path / f"{backup_id}_redis.rdb"
                if self.redis_backup.create_backup(str(redis_backup_file)):
                    result.file_count += 1
                    result.size_bytes += redis_backup_file.stat().st_size
                
                # Backup de arquivos
                files_backup_file = temp_path / f"{backup_id}_files.tar.gz"
                if self.file_backup.create_backup(str(files_backup_file), backup_type):
                    result.file_count += 1
                    result.size_bytes += files_backup_file.stat().st_size
                
                # Criar arquivo de metadados
                metadata = {
                    "backup_id": backup_id,
                    "config_name": config_name,
                    "backup_type": backup_type,
                    "created_at": result.start_time.isoformat(),
                    "omnicore_version": "1.0.0",
                    "files": [
                        {"name": "database.sql", "type": "database"},
                        {"name": "redis.rdb", "type": "redis"},
                        {"name": "files.tar.gz", "type": "files"}
                    ]
                }
                
                metadata_file = temp_path / f"{backup_id}_metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # Criar arquivo final compactado
                final_backup_file = temp_path / f"{backup_id}.tar.gz"
                with tarfile.open(final_backup_file, "w:gz") as tar:
                    for file in temp_path.glob(f"{backup_id}_*"):
                        tar.add(file, arcname=file.name)
                
                # Calcular checksum
                import hashlib
                with open(final_backup_file, "rb") as f:
                    result.checksum = hashlib.sha256(f.read()).hexdigest()
                
                # Enviar para backends de armazenamento
                for backend_name in config.storage_backends:
                    if backend_name in self.storage_backends:
                        backend = self.storage_backends[backend_name]
                        remote_path = f"{config_name}/{backup_id}.tar.gz"
                        
                        if backend.upload(str(final_backup_file), remote_path):
                            result.storage_locations.append(f"{backend_name}:{remote_path}")
                            logger.info(f"Backup enviado para {backend_name}")
                        else:
                            logger.error(f"Falha ao enviar backup para {backend_name}")
            
            result.status = BackupStatus.COMPLETED
            result.end_time = datetime.now()
            
            logger.info(f"Backup concluído: {backup_id}")
            
        except Exception as e:
            result.status = BackupStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            logger.error(f"Erro no backup {backup_id}: {str(e)}")
        
        self.backup_history.append(result)
        return result
    
    def restore_backup(self, backup_id: str, restore_path: Optional[str] = None) -> bool:
        """Restaura backup"""
        try:
            logger.info(f"Iniciando restauração do backup: {backup_id}")
            
            # Encontrar backup nos backends
            backup_file = None
            for backend_name, backend in self.storage_backends.items():
                for config_name in self.backup_configs:
                    remote_path = f"{config_name}/{backup_id}.tar.gz"
                    
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
                            if backend.download(remote_path, temp_file.name):
                                backup_file = temp_file.name
                                break
                    except:
                        continue
                
                if backup_file:
                    break
            
            if not backup_file:
                logger.error(f"Backup não encontrado: {backup_id}")
                return False
            
            # Extrair backup
            with tempfile.TemporaryDirectory() as temp_dir:
                with tarfile.open(backup_file, "r:gz") as tar:
                    tar.extractall(temp_dir)
                
                temp_path = Path(temp_dir)
                
                # Restaurar banco de dados
                db_backup_file = temp_path / f"{backup_id}_database.sql"
                if db_backup_file.exists():
                    self.db_backup.restore_backup(str(db_backup_file))
                
                # Restaurar Redis
                redis_backup_file = temp_path / f"{backup_id}_redis.rdb"
                if redis_backup_file.exists():
                    self.redis_backup.restore_backup(str(redis_backup_file))
                
                # Restaurar arquivos
                files_backup_file = temp_path / f"{backup_id}_files.tar.gz"
                if files_backup_file.exists() and restore_path:
                    self.file_backup.restore_backup(str(files_backup_file), restore_path)
            
            # Cleanup
            os.unlink(backup_file)
            
            logger.info(f"Restauração concluída: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na restauração: {str(e)}")
            return False
    
    def list_backups(self) -> List[BackupResult]:
        """Lista todos os backups"""
        return self.backup_history
    
    def cleanup_old_backups(self):
        """Remove backups antigos baseado na política de retenção"""
        logger.info("Iniciando limpeza de backups antigos")
        
        for config_name, config in self.backup_configs.items():
            cutoff_date = datetime.now() - timedelta(days=config.retention_days)
            
            # Buscar backups para remover
            backups_to_remove = []
            for backend_name, backend in self.storage_backends.items():
                for backup_path in backend.list_backups():
                    if backup_path.startswith(config_name):
                        # Extrair data do nome do backup
                        try:
                            date_part = backup_path.split("_")[1:3]  # backup_YYYYMMDD_HHMMSS
                            backup_date = datetime.strptime(
                                f"{date_part[0]}_{date_part[1]}", 
                                "%Y%m%d_%H%M%S"
                            )
                            
                            if backup_date < cutoff_date:
                                backups_to_remove.append((backend_name, backup_path))
                        except:
                            continue
            
            # Remover backups antigos
            for backend_name, backup_path in backups_to_remove:
                backend = self.storage_backends[backend_name]
                if backend.delete(backup_path):
                    logger.info(f"Backup antigo removido: {backup_path}")
                else:
                    logger.error(f"Erro ao remover backup: {backup_path}")
    
    def start_scheduler(self):
        """Inicia scheduler de backups automáticos"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Configurar schedules
        for config_name, config in self.backup_configs.items():
            if config.schedule:
                # Exemplo: "0 2 * * *" (todo dia às 2h)
                schedule.every().day.at("02:00").do(
                    self._scheduled_backup, config_name
                )
        
        logger.info("Scheduler de backups iniciado")
    
    def stop_scheduler(self):
        """Para scheduler de backups"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Scheduler de backups parado")
    
    def _scheduler_loop(self):
        """Loop principal do scheduler"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    
    def _scheduled_backup(self, config_name: str):
        """Executa backup agendado"""
        try:
            logger.info(f"Executando backup agendado: {config_name}")
            result = self.create_backup(config_name)
            
            if result.status == BackupStatus.COMPLETED:
                logger.info(f"Backup agendado concluído: {config_name}")
            else:
                logger.error(f"Backup agendado falhou: {config_name}")
        
        except Exception as e:
            logger.error(f"Erro no backup agendado {config_name}: {str(e)}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Retorna status do sistema de backup"""
        total_backups = len(self.backup_history)
        completed_backups = len([b for b in self.backup_history if b.status == BackupStatus.COMPLETED])
        failed_backups = len([b for b in self.backup_history if b.status == BackupStatus.FAILED])
        
        last_backup = self.backup_history[-1] if self.backup_history else None
        
        return {
            "total_backups": total_backups,
            "completed_backups": completed_backups,
            "failed_backups": failed_backups,
            "success_rate": completed_backups / total_backups if total_backups > 0 else 0,
            "last_backup": {
                "backup_id": last_backup.backup_id,
                "status": last_backup.status,
                "created_at": last_backup.start_time.isoformat(),
                "size_mb": last_backup.size_bytes / 1024 / 1024
            } if last_backup else None,
            "scheduler_running": self.scheduler_running,
            "storage_backends": list(self.storage_backends.keys()),
            "configurations": list(self.backup_configs.keys())
        }

# Exemplo de uso
async def exemplo_backup_system():
    """Exemplo de uso do sistema de backup"""
    
    config = {
        "database_url": "postgresql://omnicore:password@localhost:5432/omnicore_db",
        "redis_url": "redis://localhost:6379/0",
        "backup_paths": [
            "/app/data",
            "/app/uploads",
            "/app/logs"
        ],
        "exclude_patterns": [
            "*.tmp",
            "*.log",
            "__pycache__/*"
        ],
        "storage": {
            "local": {
                "backup_directory": "/var/backups/omnicore"
            },
            "s3": {
                "bucket_name": "omnicore-backups",
                "access_key_id": "AWS_ACCESS_KEY",
                "secret_access_key": "AWS_SECRET_KEY",
                "region": "us-east-1",
                "prefix": "prod/"
            }
        }
    }
    
    # Criar gerenciador de backup
    backup_manager = BackupManager(config)
    
    # Configurar backup diário
    daily_config = BackupConfig(
        name="daily_backup",
        backup_type=BackupType.FULL,
        schedule="0 2 * * *",  # Todo dia às 2h
        retention_days=30,
        compression=True,
        encryption=True,
        storage_backends=["local", "s3"]
    )
    
    backup_manager.add_backup_config(daily_config)
    
    # Configurar backup incremental
    incremental_config = BackupConfig(
        name="incremental_backup",
        backup_type=BackupType.INCREMENTAL,
        schedule="0 */6 * * *",  # A cada 6 horas
        retention_days=7,
        compression=True,
        storage_backends=["local"]
    )
    
    backup_manager.add_backup_config(incremental_config)
    
    # Criar backup manual
    print("Criando backup manual...")
    result = backup_manager.create_backup("daily_backup", BackupType.FULL)
    
    print(f"Backup ID: {result.backup_id}")
    print(f"Status: {result.status}")
    print(f"Tamanho: {result.size_bytes / 1024 / 1024:.2f} MB")
    print(f"Arquivos: {result.file_count}")
    print(f"Locais: {result.storage_locations}")
    
    # Iniciar scheduler automático
    backup_manager.start_scheduler()
    
    # Status do sistema
    status = backup_manager.get_backup_status()
    print(f"\nStatus do sistema de backup:")
    print(json.dumps(status, indent=2, default=str))
    
    # Simular restauração
    print("\nSimulando restauração...")
    if backup_manager.restore_backup(result.backup_id, "/tmp/restore"):
        print("Restauração bem-sucedida!")
    else:
        print("Falha na restauração")
    
    # Parar scheduler
    backup_manager.stop_scheduler()

if __name__ == "__main__":
    asyncio.run(exemplo_backup_system())