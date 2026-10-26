import shutil
from pathlib import Path
from core.operations.install.validator import prepare_and_validate_files
from core.operations.install.backupper import create_backups, rollback_installation
from core.operations.install.copier import copy_files_to_game
from core.mod_manager.registry_ops import register_mod, remove_file_ownership
from core.mod_manager.registry_io import get_registry_path
from core.scanner.mod_scanner import _collect_files
from utils.logs.rise_logger import log

def install_mod(game_path, source, data_root, game_key, mod_name, destination_overrides=None, inventory=None, conflict_actions=None, selected_files=None):
    """Orquestra a instalação completa de um mod de forma segura e atômica."""
    log.info(f"=== INICIANDO INSTALAÇÃO: '{mod_name}' ===")
    game_root = Path(game_path).resolve()
    data_root = Path(data_root).resolve()
    backup_root = data_root / "backups"

    # Trava de segurança 1: Data Root não pode estar dentro do jogo
    try:
        data_root.relative_to(game_root)
        log.critical("[Manager] 🚨 Tentativa de instalar o gerenciador dentro do jogo! Abortando.")
        raise ValueError("Os dados do gerenciador devem ficar fora da pasta do jogo.")
    except ValueError:
        pass

    # Trava de segurança 2: O arquivo original existe?
    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Arquivo original do mod não encontrado: {source_path}")

    # 1. Coleta e Filtra
    log.debug("[Manager] Etapa 1: Coletando e filtrando arquivos...")
    files = _collect_files(source_path, destination_overrides, inventory)
    
    if selected_files is not None:
        files = [f for f in files if f["destination"] in selected_files]
        log.debug(f"[Manager] Filtro do usuário aplicado. Restaram {len(files)} arquivos.")
        
    if conflict_actions:
        files = [f for f in files if conflict_actions.get(f["destination"]) != "skip"]
        for f in files:
            if f["destination"] in conflict_actions:
                f["conflict_action"] = conflict_actions[f["destination"]]
        log.debug(f"[Manager] Filtro de conflitos aplicado. Restaram {len(files)} arquivos.")

    if not files:
        log.warning("[Manager] Nenhum arquivo restou para instalar após os filtros. Abortando.")
        return []

    # 2. Valida
    log.debug("[Manager] Etapa 2: Validando arquivos e conflitos...")
    valid_files = prepare_and_validate_files(game_root, data_root, game_key, files)

    backed_up = []
    
    # TRAVA DE SEGURANÇA 3: Backup do Banco de Dados antes de mexer no registro
    registry_path = get_registry_path(data_root, game_key)
    registry_backup_path = registry_path.with_suffix(".json.bak")
    if registry_path.exists():
        shutil.copy2(registry_path, registry_backup_path)
        log.debug("[Manager] Backup do banco de dados (mods.json) criado.")

    try:
        # 3. Backup dos arquivos
        log.debug("[Manager] Etapa 3: Criando backups dos arquivos do jogo...")
        backed_up = create_backups(game_root, backup_root, game_key, valid_files)

        # 4. Cópia
        log.debug("[Manager] Etapa 4: Copiando arquivos para o jogo...")
        installed, installed_hashes = copy_files_to_game(game_root, source_path, valid_files)

        # 5. Atualiza Registros
        log.debug("[Manager] Etapa 5: Atualizando banco de dados (Registro)...")
        if conflict_actions:
            overwrites = [f["destination"] for f in valid_files if conflict_actions.get(f["destination"]) == "overwrite"]
            if overwrites:
                log.info(f"[Manager] Removendo posse antiga de {len(overwrites)} arquivos sobrescritos.")
                remove_file_ownership(data_root, game_key, overwrites)

        # O register_mod verifica se há conflito (mas já limpamos os conflitos acima se o usuário autorizou)
        register_mod(data_root, game_key, mod_name, installed, file_hashes=installed_hashes)
        log.info(f"=== SUCESSO: '{mod_name}' instalado ({len(installed)} arquivos). ===")
        
        # Limpa o backup do banco de dados se tudo deu certo
        if registry_backup_path.exists():
            registry_backup_path.unlink()
            
        return installed

    except Exception as error:
        log.error(f"[Manager] FALHA NA INSTALAÇÃO: {error}. Iniciando rollback...", exc_info=True)
        
        # ROLLBACK 1: Restaurar os arquivos do jogo
        if backed_up:
            rollback_installation(game_root, backup_root, game_key, backed_up)
            
        # ROLLBACK 2: Restaurar o banco de dados
        if registry_backup_path.exists():
            log.warning("[Manager] Restaurando o banco de dados (mods.json) do backup devido a falha...")
            shutil.copy2(registry_backup_path, registry_path)
            registry_backup_path.unlink()
            
        raise