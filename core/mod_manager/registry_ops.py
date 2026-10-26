import uuid
from datetime import datetime, timezone
from pathlib import Path
from core.mod_manager.registry_io import get_registry_path, load_registry, save_registry
from core.mod_manager.registry_query import _normalize_file_path, clear_registry_cache
from utils.logs.rise_logger import log

def register_mod(data_root: str | Path, game_key: str, mod_name: str, files: list, file_hashes: dict = None) -> dict:
    mod_name = str(mod_name).strip()
    if not mod_name:
        raise ValueError("O mod precisa ter um nome.")

    # Normaliza e remove duplicatas
    normalized_files = sorted({_normalize_file_path(f) for f in files})
    if not normalized_files:
        raise ValueError("O mod não contém arquivos para registrar.")

    # TRAVA DE SEGURANÇA 1: Sanitiza os hashes para garantir que só existam hashes de arquivos reais
    safe_hashes = {}
    if file_hashes:
        for f in normalized_files:
            if f in file_hashes:
                safe_hashes[f] = file_hashes[f]

    path = get_registry_path(data_root, game_key)
    registry = load_registry(path)

    # TRAVA DE SEGURANÇA 2: Verifica conflito de posse usando Sets (O(1) em vez de O(N))
    normalized_set = set(normalized_files)
    for mod in registry["mods"]:
        overlap = normalized_set & set(mod["files"])
        if overlap:
            log.warning(f"[RegistryOps] Conflito detectado ao registrar '{mod_name}'. Arquivos: {overlap}")
            raise ValueError(f"Conflito com o mod '{mod['name']}': {', '.join(sorted(overlap))}")

    mod_entry = {
        "id": uuid.uuid4().hex,
        "name": mod_name,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": normalized_files,
        "file_hashes": safe_hashes, # Usa os hashes sanitizados
    }

    registry["mods"].append(mod_entry)
    save_registry(path, registry)
    
    # LIMPA O CACHE para garantir que a próxima leitura veja o novo mod
    clear_registry_cache(data_root, game_key)
    
    log.info(f"[RegistryOps] Mod '{mod_name}' registrado com sucesso ({len(normalized_files)} arquivos).")
    return mod_entry

def remove_mod_record(data_root: str | Path, game_key: str, mod_id: str) -> None:
    log.info(f"[RegistryOps] Removendo registro do mod ID: {mod_id}")
    path = get_registry_path(data_root, game_key)
    registry = load_registry(path)

    remaining_mods = [m for m in registry["mods"] if m["id"] != mod_id]
    if len(remaining_mods) == len(registry["mods"]):
        log.error(f"[RegistryOps] Tentativa de remover mod inexistente: {mod_id}")
        raise ValueError("Mod não encontrado no registro.")

    registry["mods"] = remaining_mods
    save_registry(path, registry)
    
    clear_registry_cache(data_root, game_key)
    log.info(f"[RegistryOps] Registro do mod ID {mod_id} removido.")

def remove_file_ownership(data_root: str | Path, game_key: str, file_paths: list) -> None:
    log.info(f"[RegistryOps] Removendo posse de {len(file_paths)} arquivos de seus donos antigos.")
    path = get_registry_path(data_root, game_key)
    registry = load_registry(path)
    modified = False
    
    # O Segredo da Performance: Converter a lista para Set (Busca O(1))
    paths_to_remove = set(file_paths)

    for mod in registry["mods"]:
        # Interseção rápida de conjuntos
        overlap = paths_to_remove & set(mod["files"])
        if overlap:
            # Remove os arquivos encontrados
            mod["files"] = [f for f in mod["files"] if f not in overlap]
            
            # Remove os hashes desses arquivos
            for f in overlap:
                mod.get("file_hashes", {}).pop(f, None)
            modified = True

    mods_antes = len(registry["mods"])
    registry["mods"] = [m for m in registry["mods"] if len(m.get("files", [])) > 0]
    if len(registry["mods"]) < mods_antes:
        log.info("[RegistryOps] Mods que ficaram com 0 arquivos foram removidos do registro.")
        modified = True

    if modified:
        save_registry(path, registry)
        clear_registry_cache(data_root, game_key)

def update_mod_files(data_root: str | Path, game_key: str, mod_id: str, files_to_remove: list) -> None:
    """Atualiza o registro removendo arquivos desinstalados. Se zerar, apaga o mod."""
    log.debug(f"[RegistryOps] Atualizando arquivos do mod {mod_id}. Removendo {len(files_to_remove)}.")
    path = get_registry_path(data_root, game_key)
    registry = load_registry(path)
    
    paths_to_remove = set(files_to_remove)
    
    for mod in registry["mods"]:
        if mod["id"] == mod_id:
            mod["files"] = [f for f in mod["files"] if f not in paths_to_remove]
            
            for f in paths_to_remove:
                mod.get("file_hashes", {}).pop(f, None)
            
            if not mod["files"]:
                registry["mods"].remove(mod)
                log.info(f"[RegistryOps] Mod '{mod['name']}' ficou com 0 arquivos e foi removido do registro.")
            else:
                log.debug(f"[RegistryOps] Mod '{mod['name']}' atualizado. Restam {len(mod['files'])} arquivos.")
            break
            
    save_registry(path, registry)
    clear_registry_cache(data_root, game_key)