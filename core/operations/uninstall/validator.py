from pathlib import Path
from core.paths.resolver import resolve_safe_target
from core.mod_manager.registry_query import list_installed_mods
from utils.hash_utils import calculate_file_hash
from utils.logs.rise_logger import log

def validate_uninstallation(game_root, data_root, game_key, mod_id, selected_files=None, force=False):
    """
    Valida se os arquivos existem e não foram alterados. 
    Retorna a lista de arquivos encontrados (para restaurar) e um dicionário de caminhos.
    """
    log.info(f"[Validator] Iniciando validação de desinstalação para o mod ID: {mod_id}")
    
    mods = list_installed_mods(data_root, game_key)
    mod = next((item for item in mods if item["id"] == mod_id), None)
    
    if mod is None:
        log.error(f"[Validator] Mod ID {mod_id} não foi encontrado no registro!")
        raise ValueError("Mod não encontrado no registro.")

    all_files = mod["files"]
    expected_hashes = mod.get("file_hashes", {})

    files = selected_files if selected_files is not None else all_files
    if not files:
        log.warning("[Validator] Nenhum arquivo selecionado para desinstalar.")
        return [], {}

    log.debug(f"[Validator] Validando {len(files)} arquivos contra alterações externas...")
    
    targets = {}
    missing_files = []
    
    for relative_path in files:
        try:
            target = resolve_safe_target(game_root, relative_path)
        except Exception as e:
            log.error(f"[Validator] Caminho inválido no registro: {relative_path} ({e})")
            missing_files.append(relative_path)
            continue
        
        # O arquivo existe no disco?
        if not target.is_file():
            log.warning(f"[Validator] Arquivo não encontrado no jogo (pulando): {relative_path}")
            missing_files.append(relative_path)
            continue

        # Checagem de integridade (se existir hash)
        if expected_hashes and relative_path in expected_hashes and not force:
            try:
                current_hash = calculate_file_hash(target)
            except PermissionError:
                log.critical(f"[Validator] 🚨 PERMISSÃO NEGADA: O arquivo '{relative_path}' está bloqueado pelo Windows (jogo aberto?).")
                raise PermissionError(f"Não foi possível ler o arquivo '{relative_path}'. Feche o jogo e tente novamente.")
            except Exception as e:
                log.error(f"[Validator] Erro ao ler arquivo '{relative_path}': {e}")
                raise RuntimeError(f"Erro ao validar o arquivo '{relative_path}': {e}")
                
            if current_hash != expected_hashes[relative_path]:
                if force:
                    log.warning(f"[Validator] ⚠️ ALTERAÇÃO IGNORADA: '{relative_path}' foi modificado, mas o usuário forçou a desinstalação.")
                else:
                    log.error(f"[Validator] ALERTA: O arquivo '{relative_path}' foi alterado por fora! Hash não bate.")
                    raise ValueError(f"O arquivo foi alterado externamente: {relative_path}. Use a opção 'Forçar Desinstalação' se deseja continuar.")
            else:
                log.debug(f"[Validator] Hash OK para: {relative_path}")
        
        targets[relative_path] = target

    # Retornamos a lista de arquivos que EXISTEM (para o restorer) e os fantasmas
    # O manager.py precisará saber de todos eles para limpar o banco corretamente.
    files_to_restore = [path for path in files if path in targets]
    
    if missing_files:
        log.info(f"[Validator] {len(missing_files)} arquivos já não existem no disco e serão apenas removidos do registro.")

    log.info(f"[Validator] Validação concluída. {len(files_to_restore)} arquivos prontos para restauração.")
    return files, targets # Retornamos a lista original para o registro limpar tudo