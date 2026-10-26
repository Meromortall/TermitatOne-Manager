import shutil
import uuid
from pathlib import Path, PurePosixPath
from utils.backup.restorer import restore_backup
from utils.logs.rise_logger import log

def execute_restoration(game_root, data_root, game_key, files, targets):
    """
    Faz a troca dos arquivos do mod pelos originais com rollback inteligente.
    `files` contém todos os arquivos do mod. `targets` contém apenas os que existiam no disco.
    """
    
    # 1. Staging (Apenas dos arquivos que existiam)
    staging_root = data_root / "uninstall_staging" / str(game_key) / uuid.uuid4().hex
    log.debug(f"[Restorer] Iniciando Staging em: {staging_root}")
    
    try:
        for relative_path, target in targets.items():
            staged_file = staging_root / Path(*PurePosixPath(relative_path).parts)
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, staged_file)
        log.info(f"[Restorer] Staging concluído para {len(targets)} arquivos.")
    except Exception as e:
        log.error(f"[Restorer] Falha crítica ao preparar Staging: {e}", exc_info=True)
        shutil.rmtree(staging_root, ignore_errors=True)
        raise RuntimeError(f"Falha ao preparar a desinstalação: {e}")

    # 2. Restauração (Tentando restaurar TODOS os arquivos originais)
    try:
        log.info(f"[Restorer] Restaurando backups originais para {len(files)} arquivos...")
        for relative_path in reversed(files):
            # Nota: O restore_backup já recria a pasta pai se o arquivo for um "fantasma"
            restore_backup(game_root, relative_path, data_root / "backups", game_key, consume=False)
            log.debug(f"[Restorer] Backup restaurado: {relative_path}")
            
    except Exception as error:
        log.error("[Restorer] 🚨 FALHA AO RESTAURAR BACKUPS. Iniciando Rollback de emergência...", exc_info=True)
        
        # Rollback de emergência
        _rollback_staging(game_root, staging_root, targets, files)
        
        raise RuntimeError(f"A desinstalação falhou e os arquivos originais foram recuperados: {error}")

    # Limpa o staging se deu tudo certo
    log.debug(f"[Restorer] Limpando pasta de staging temporária...")
    shutil.rmtree(staging_root, ignore_errors=True)


def _rollback_staging(game_root, staging_root, targets, all_files):
    """
    Reverte o jogo ao estado exato antes da desinstalação.
    Trata tanto os arquivos que existiam quanto os fantasmas que foram recriados.
    """
    log.warning("[Rollback] Revertendo arquivos do mod a partir do Staging...")
    rollback_errors = []
    
    # 1. Devolve os arquivos que existiam ao seu estado anterior (arquivo do mod)
    for relative_path, target in targets.items():
        staged_file = staging_root / Path(*PurePosixPath(relative_path).parts)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_file, target)
            log.debug(f"[Rollback] Arquivo do mod recuperado: {relative_path}")
        except Exception as e:
            log.critical(f"[Rollback] ERRO CRÍTICO ao recuperar {relative_path}: {e}")
            rollback_errors.append(f"{relative_path}: {e}")
            
    # 2. A MÁGICA: Remove os arquivos "fantasmas" que foram restaurados por engano!
    # Se um arquivo está em all_files, mas NÃO está em targets, ele não existia antes.
    ghost_files = [f for f in all_files if f not in targets]
    
    for relative_path in ghost_files:
        ghost_target = game_root / Path(*PurePosixPath(relative_path).parts)
        try:
            if ghost_target.exists():
                ghost_target.unlink() # Deleta o arquivo original que foi restaurado por engano
                log.debug(f"[Rollback] Fantasma removido com sucesso: {relative_path}")
        except Exception as e:
            log.critical(f"[Rollback] ERRO ao remover fantasma {relative_path}: {e}")
            rollback_errors.append(f"Fantasma {relative_path}: {e}")
    
    if rollback_errors:
        raise RuntimeError(f"FALHA CRÍTICA NO ROLLBACK: {'; '.join(rollback_errors)}")
        
    log.info("[Rollback] Todos os arquivos foram recuperados e o estado original foi restaurado com precisão cirúrgica.")