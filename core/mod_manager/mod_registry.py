from core.mod_manager.registry_io import get_registry_path, load_registry, save_registry
from core.mod_manager.registry_query import clear_registry_cache
from utils.logs.rise_logger import log

def update_mod_files(data_root: str | Path, game_key: str, mod_id: str, files_to_remove: list) -> None:
    """Atualiza o registro removendo arquivos desinstalados. Se zerar, apaga o mod."""
    
    # TRAVA 1: Validação de entrada
    if not files_to_remove:
        log.debug(f"[RegistryOps] Nenhum arquivo para remover do mod {mod_id}. Ignorando.")
        return

    log.debug(f"[RegistryOps] Atualizando arquivos do mod {mod_id}. Removendo {len(files_to_remove)}.")
    path = get_registry_path(data_root, game_key)
    registry = load_registry(path)
    
    # TRAVA 2: Performance O(1) com Sets
    paths_to_remove = set(files_to_remove)
    mod_found = False
    
    for mod in registry["mods"]:
        if mod["id"] == mod_id:
            mod_found = True
            
            # Usa set para remover rapidamente os arquivos da lista
            mod["files"] = [f for f in mod["files"] if f not in paths_to_remove]
            
            # Remove os hashes desses arquivos
            file_hashes = mod.get("file_hashes", {})
            for f in paths_to_remove:
                file_hashes.pop(f, None)
            
            # Se o mod ficou com 0 arquivos, remove ele do registro
            if not mod["files"]:
                registry["mods"].remove(mod)
                log.info(f"[RegistryOps] Mod '{mod['name']}' ficou com 0 arquivos e foi removido do registro.")
            else:
                log.debug(f"[RegistryOps] Mod '{mod['name']}' atualizado. Restam {len(mod['files'])} arquivos.")
            break
            
    if not mod_found:
        log.warning(f"[RegistryOps] Tentativa de atualizar um mod que não existe no registro: {mod_id}")
        return

    # TRAVA 3: Salvamento seguro e invalidação do cache
    try:
        save_registry(path, registry)
        clear_registry_cache(data_root, game_key) # O SEGREDO AQUI
        log.debug("[RegistryOps] Registro salvo e cache limpo com sucesso.")
    except Exception as e:
        log.critical(f"[RegistryOps] 🚨 FALHA CRÍTICA ao salvar o registro após atualização: {e}")
        raise