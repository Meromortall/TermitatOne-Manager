import shutil
import uuid
from pathlib import Path, PurePosixPath
from core.paths.resolver import resolve_safe_target
from utils.backup.manifest_io import get_manifest_path, load_manifest, save_manifest
from utils.logs.rise_logger import log

def _get_safe_backup_file(backup_root: Path, game_key: str, relative: str) -> Path:
    """Garante que o caminho do arquivo de backup não escape da pasta de backups."""
    # Reconstrói o caminho usando apenas as partes seguras
    safe_parts = PurePosixPath(relative).parts
    
    # Se o caminho tiver '..' ou começar com '/', a gente barra
    if ".." in safe_parts or relative.startswith("/") or ":" in relative:
        raise ValueError(f"Caminho de backup inseguro bloqueado: {relative}")
        
    backup_file = backup_root / game_key / "files" / Path(*safe_parts)
    
    # Defesa em profundidade: verifica se o caminho resolvido está dentro de backup_root
    try:
        backup_file.resolve().relative_to(backup_root.resolve())
    except ValueError:
        raise ValueError(f"Tentativa de Path Traversal no backup bloqueada: {relative}")
        
    return backup_file

def restore_backup(game_path: str | Path, relative_path: str | Path, backup_root: str | Path, game_key: str, consume: bool = True) -> bool:
    """Restaura o estado anterior à instalação com segurança e rollback em disco."""
    log.debug(f"[BackupRestorer] Iniciando restauração: {relative_path}")
    
    game_root = Path(game_path).resolve()
    backup_root = Path(backup_root).resolve()
    target = resolve_safe_target(game_root, relative_path)
    relative = str(relative_path).replace("\\", "/")

    manifest_path = get_manifest_path(backup_root, game_key)
    manifest = load_manifest(manifest_path)

    if relative not in manifest:
        log.error(f"[BackupRestorer] Tentativa de restaurar arquivo sem backup registrado: {relative}")
        raise ValueError(f"Não existe backup registrado para: {relative}")

    entry = manifest[relative]

    if entry.get("original_exists"):
        # TRAVA 1: Segurança do caminho de backup
        try:
            backup_file = _get_safe_backup_file(backup_root, game_key, relative)
        except ValueError as e:
            log.critical(f"[BackupRestorer] 🚨 {e}")
            raise
            
        if not backup_file.is_file():
            log.error(f"[BackupRestorer] O arquivo de backup original sumiu do cofre: {relative}")
            raise FileNotFoundError(f"Backup original ausente: {relative}")

        target.parent.mkdir(parents=True, exist_ok=True)
        
        # TRAVA 2: Nome de arquivo temporário único (evita lixo na pasta)
        temp_name = f"{target.name}.{uuid.uuid4().hex[:8]}.restore_tmp"
        temporary_target = target.with_name(temp_name)

        try:
            log.debug(f"[BackupRestorer] Restaurando arquivo original: {backup_file.name} -> {target.name}")
            shutil.copy2(backup_file, temporary_target)
            
            try:
                temporary_target.replace(target)
            except PermissionError:
                log.critical(f"[BackupRestorer] 🚨 Arquivo bloqueado na substituição: {relative} (jogo aberto?)")
                raise PermissionError(f"Não foi possível substituir '{relative}'. Feche o jogo e tente novamente.")
                
            log.info(f"[BackupRestorer] Arquivo restaurado com sucesso: {relative}")
        finally:
            if temporary_target.exists():
                try:
                    temporary_target.unlink()
                except Exception as e:
                    log.warning(f"[BackupRestorer] Não foi possível limpar o temporário {temp_name}: {e}")

    else:
        log.debug(f"[BackupRestorer] O arquivo não existia originalmente. Deletando do jogo: {relative}")
        if target.is_file():
            try:
                target.unlink()
                log.info(f"[BackupRestorer] Arquivo criado por mod removido: {relative}")
            except PermissionError:
                log.critical(f"[BackupRestorer] 🚨 Arquivo bloqueado ao tentar deletar: {relative}")
                raise PermissionError(f"Não foi possível deletar '{relative}'. Feche o jogo e tente novamente.")
        elif target.exists():
            log.error(f"[BackupRestorer] O destino é uma pasta, não um arquivo: {relative}")
            raise ValueError(f"O destino não é um arquivo: {relative}")

    if consume:
        log.debug(f"[BackupRestorer] Removendo registro do manifesto após restauração: {relative}")
        del manifest[relative]
        save_manifest(manifest_path, manifest)

    return True

def forget_backup_entries(backup_root: str | Path, game_key: str, relative_paths: list) -> None:
    """Remove do registro os backups de uma operação concluída, limpando o lixo físico."""
    log.debug(f"[BackupRestorer] Esquecendo {len(relative_paths)} entradas de backup concluídas.")
    backup_root = Path(backup_root).resolve()
    manifest_path = get_manifest_path(backup_root, game_key)
    manifest = load_manifest(manifest_path)

    removed_count = 0
    for relative_path in relative_paths:
        relative = str(relative_path).replace("\\", "/")
        if relative in manifest:
            # Limpa o arquivo físico de backup para não acumular lixo no HD
            try:
                backup_file = _get_safe_backup_file(backup_root, game_key, relative)
                if backup_file.is_file():
                    backup_file.unlink()
                    log.debug(f"[BackupRestorer] Arquivo físico de backup deletado: {relative}")
            except Exception as e:
                log.warning(f"[BackupRestorer] Falha ao deletar arquivo físico de backup {relative}: {e}")
                
            # Remove a entrada do manifesto
            del manifest[relative]
            removed_count += 1

    save_manifest(manifest_path, manifest)
    log.info(f"[BackupRestorer] {removed_count} entradas limpas do manifesto de backups.")