import shutil
from pathlib import Path
from core.operations.uninstall.validator import validate_uninstallation
from core.operations.uninstall.restorer import execute_restoration
from core.mod_manager.registry_ops import update_mod_files
from core.mod_manager.registry_io import get_registry_path
from utils.backup.restorer import forget_backup_entries
from utils.logs.rise_logger import log

def uninstall_mod(game_path, data_root, game_key, mod_id, selected_files=None, force=False):
    """Orquestra a desinstalação completa de um mod de forma transacional."""
    log.info(f"=== INICIANDO DESINSTALAÇÃO: ID {mod_id} (Forçar: {force}) ===")
    
    game_root = Path(game_path).resolve()
    data_root = Path(data_root).resolve()
    
    # Trava 1: Segurança de caminhos
    try:
        data_root.relative_to(game_root)
        log.critical("[Manager] 🚨 Tentativa de desinstalar o gerenciador dentro do jogo! Abortando.")
        raise ValueError("Os dados do gerenciador devem ficar fora da pasta do jogo.")
    except ValueError:
        pass

    # 1. Validar (Agora com suporte a force)
    log.debug("[Manager] Etapa 1: Validando arquivos...")
    files, targets = validate_uninstallation(game_root, data_root, game_key, mod_id, selected_files, force)
    if not files:
        log.warning("[Manager] Nenhum arquivo selecionado ou válido para desinstalar. Abortando.")
        return []

    # TRAVA 2: Backup do Banco de Dados (Transação Atômica)
    registry_path = get_registry_path(data_root, game_key)
    registry_backup_path = registry_path.with_suffix(".json.bak_uninstall")
    if registry_path.exists():
        shutil.copy2(registry_path, registry_backup_path)
        log.debug("[Manager] Backup transacional do mods.json criado.")

    try:
        # 2. Restaurar backups (com rollback automático no disco)
        log.debug("[Manager] Etapa 2: Executando restauração de backups...")
        execute_restoration(game_root, data_root, game_key, files, targets)

        # 3. Atualizar Registro
        log.debug("[Manager] Etapa 3: Atualizando o banco de dados (Registro)...")
        update_mod_files(data_root, game_key, mod_id, files)

    except Exception as error:
        log.critical(f"[Manager] 🚨 FALHA NA DESINSTALAÇÃO: {error}. Revertendo banco de dados...")
        
        # Se o banco de dados já tinha sido mexido (ou estava prestes a ser), restaura o backup
        if registry_backup_path.exists():
            shutil.copy2(registry_backup_path, registry_path)
            log.info("[Manager] Banco de dados (mods.json) revertido ao estado original.")
            
        registry_backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"A desinstalação falhou. O jogo e o banco de dados foram preservados no estado anterior: {error}")

    # 4. Limpar backups do manifesto (NÃO-CRÍTICO: se falhar, apenas avisa)
    log.debug("[Manager] Etapa 4: Limpando manifesto de backups...")
    try:
        forget_backup_entries(data_root / "backups", game_key, files)
    except Exception as e:
        # Aqui nós não damos raise! A desinstalação já foi um sucesso.
        log.error(f"[Manager] AVISO: Falha ao limpar o manifesto de backups. O jogo foi desinstalado, mas os backups podem ocupar espaço extra: {e}")

    # Limpa o backup do banco de dados
    if registry_backup_path.exists():
        registry_backup_path.unlink()

    log.info(f"=== SUCESSO: {len(files)} arquivos restaurados/desinstalados. ===")
    return files