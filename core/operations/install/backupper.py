from utils.backup.creator import create_backup
from utils.backup.restorer import restore_backup
from utils.logs.rise_logger import log

def create_backups(game_root, backup_root, game_key, files):
    """Cria o backup de todos os arquivos que serão modificados, com rollback em caso de falha."""
    log.debug(f"[Backupper] Iniciando criação de backups para {len(files)} arquivos...")
    backed_up = []
    
    for item in files:
        dest = item["destination"]
        try:
            created = create_backup(game_root, dest, backup_root, game_key)
            if not created:
                log.debug(f"[Backupper] Backup já existente para '{dest}'. Reutilizando.")
            else:
                log.info(f"[Backupper] Backup criado com sucesso: {dest}")
            backed_up.append(dest)
            
        except Exception as e:
            log.critical(f"[Backupper] 🚨 FALHA AO CRIAR BACKUP para '{dest}': {e}")
            log.error(f"[Backupper] Abortando criação de backups. Os arquivos que já tinham backup serão mantidos, mas a instalação será cancelada.")
            
            # Rollback de emergência: Como o jogo ainda não foi modificado, 
            # apenas limpamos os arquivos de backup que criamos nesta iteração
            # (Isso evita "lixo" no cofre se o disco encheu no meio)
            _clean_orphaned_backups(game_root, backup_root, game_key, backed_up)
            raise RuntimeError(f"Falha crítica ao criar backup do arquivo '{dest}'. Verifique o espaço em disco e permissões.")

    log.info(f"[Backupper] Todos os {len(backed_up)} backups foram criados com sucesso.")
    return backed_up

def _clean_orphaned_backups(game_root, backup_root, game_key, backed_up):
    """Limpa backups órfãos em caso de falha na criação."""
    from utils.backup.restorer import forget_backup_entries
    log.debug("[Backupper] Limpando backups órfãos no manifesto...")
    try:
        forget_backup_entries(backup_root, game_key, backed_up)
        log.info(f"[Backupper] {len(backed_up)} entradas de backup removidas do manifesto.")
    except Exception as e:
        log.error(f"[Backupper] Falha ao limpar backups órfãos: {e}")

def rollback_installation(game_root, backup_root, game_key, backed_up):
    """Reverte o jogo para o estado original se a instalação falhar, tentando o máximo possível."""
    if not backed_up:
        log.debug("[Backupper] Nenhum backup para reverter. Instalação não modificou o jogo.")
        return

    log.critical(f"[Backupper] INICIANDO ROLLBACK DE EMERGÊNCIA para {len(backed_up)} arquivos...")
    rollback_errors = []
    restored_count = 0
    
    # Itera na ordem reversa para restaurar o que foi modificado por último primeiro
    for relative_path in reversed(backed_up):
        try:
            restore_backup(game_root, relative_path, backup_root, game_key)
            log.debug(f"[Backupper] Rollback OK: {relative_path}")
            restored_count += 1
        except Exception as e:
            log.critical(f"[Backupper] ERRO NO ROLLBACK DE '{relative_path}': {e}")
            rollback_errors.append(f"{relative_path}: {e}")
            
    if rollback_errors:
        error_msg = (
            f"FALHA CRÍTICA NO ROLLBACK: {len(rollback_errors)} arquivos não puderam ser restaurados. "
            f"O jogo pode estar em um estado misto. Erros: {'; '.join(rollback_errors)}"
        )
        log.critical(error_msg)
        raise RuntimeError(error_msg)
    
    log.info(f"[Backupper] Rollback concluído com sucesso. {restored_count} arquivos restaurados ao estado original.")