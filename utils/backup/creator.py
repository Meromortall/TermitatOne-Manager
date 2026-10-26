import shutil
import uuid
from pathlib import Path, PurePosixPath
from core.paths.resolver import resolve_safe_target
from utils.backup.manifest_io import get_manifest_path, load_manifest, save_manifest
from utils.logs.rise_logger import log

def _get_safe_backup_file(backup_root: Path, game_key: str, relative: str) -> Path:
    """Garante que o caminho do arquivo de backup não escape da pasta de backups."""
    safe_parts = PurePosixPath(relative).parts
    
    if ".." in safe_parts or relative.startswith("/") or ":" in relative:
        raise ValueError(f"Caminho de backup inseguro bloqueado: {relative}")
        
    backup_file = backup_root / game_key / "files" / Path(*safe_parts)
    
    try:
        backup_file.resolve().relative_to(backup_root.resolve())
    except ValueError:
        raise ValueError(f"Tentativa de Path Traversal no backup bloqueada: {relative}")
        
    return backup_file

def create_backup(game_path: str | Path, relative_path: str | Path, backup_root: str | Path, game_key: str) -> bool:
    """Guarda o estado original de um arquivo antes da instalação de forma atômica."""
    log.debug(f"[BackupCreator] Iniciando backup para: {relative_path}")
    
    game_root = Path(game_path).resolve()
    backup_root = Path(backup_root).resolve()
    target = resolve_safe_target(game_root, relative_path)
    relative = str(relative_path).replace("\\", "/")

    try:
        backup_root.relative_to(game_root)
        log.critical("[BackupCreator] 🚨 Os backups estão tentando ser salvos DENTRO do jogo! Abortando.")
        raise ValueError("Os backups devem ficar fora da pasta do jogo.")
    except ValueError:
        pass # O erro esperado: significa que está fora.

    manifest_path = get_manifest_path(backup_root, game_key)
    manifest = load_manifest(manifest_path)

    # Se já tem backup, não sobrescreve
    if relative in manifest:
        entry = manifest[relative]
        if entry.get("original_exists"):
            try:
                backup_file = _get_safe_backup_file(backup_root, game_key, relative)
                if not backup_file.is_file():
                    log.error(f"[BackupCreator] Alerta: Backup original sumiu do cofre: {relative}")
                    raise FileNotFoundError(f"Backup original ausente no cofre: {relative}")
            except ValueError as e:
                log.critical(f"[BackupCreator] 🚨 {e}")
                raise
                
        log.debug(f"[BackupCreator] Backup já existente. Reutilizando original: {relative}")
        return False

    if target.exists() and not target.is_file():
        log.error(f"[BackupCreator] O destino existe, mas não é um arquivo: {relative}")
        raise ValueError(f"O destino existe, mas não é um arquivo: {relative}")

    existed = target.is_file()
    entry = {"original_exists": existed}
    
    backup_file = None
    temp_backup_file = None

    if existed:
        log.debug(f"[BackupCreator] Copiando arquivo original para o cofre: {relative}")
        
        try:
            backup_file = _get_safe_backup_file(backup_root, game_key, relative)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # TRAVA: Cópia Atômica para evitar arquivos corrompidos no cofre
            temp_name = f"{backup_file.name}.{uuid.uuid4().hex[:8]}.tmp"
            temp_backup_file = backup_file.with_name(temp_name)
            
            stat_antes = target.stat()
            shutil.copy2(target, temp_backup_file)
            stat_depois = target.stat()
            
            if stat_antes.st_size != stat_depois.st_size or stat_antes.st_mtime != stat_depois.st_mtime:
                log.warning(f"[BackupCreator] ⚠️ O arquivo '{relative}' mudou durante o backup. O backup pode estar inconsistente.")
                
            temp_backup_file.replace(backup_file)
            
        except PermissionError:
            log.critical(f"[BackupCreator] 🚨 Arquivo bloqueado para leitura: {relative} (O jogo está aberto?)")
            raise PermissionError(f"Não foi possível ler '{relative}' para fazer backup. Feche o jogo e tente novamente.")
        except Exception as e:
            log.error(f"[BackupCreator] Falha ao copiar para o cofre: {e}")
            if temp_backup_file and temp_backup_file.exists():
                temp_backup_file.unlink()
            raise
    else:
        log.info(f"[BackupCreator] Arquivo novo detectado (não existia no jogo): {relative}")

    # TRAVA: Transacionalidade do Manifesto
    try:
        manifest[relative] = entry
        save_manifest(manifest_path, manifest)
    except Exception as e:
        log.critical(f"[BackupCreator] 🚨 Falha ao salvar o manifesto. Desfazendo o backup físico para manter a consistência: {e}")
        if backup_file and backup_file.is_file():
            backup_file.unlink()
        raise

    return True