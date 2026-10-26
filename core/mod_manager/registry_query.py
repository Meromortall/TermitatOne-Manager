import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from core.mod_manager.registry_io import get_registry_path, load_registry
from utils.logs.rise_logger import log

# Cache global para evitar ler o HD 500 vezes no mesmo segundo
_registry_cache = {}
_cache_mtime = {}

def _normalize_file_path(file_path: str | Path) -> str:
    normalized = str(file_path).replace("\\", "/")
    path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(normalized)

    if (not normalized or path.is_absolute() or windows_path.is_absolute() or 
        windows_path.drive or ".." in path.parts or "." in path.parts):
        log.error(f"[RegistryQuery] Caminho inválido bloqueado na normalização: {file_path}")
        raise ValueError(f"Caminho de arquivo inválido: {file_path}")
    return path.as_posix()

def list_installed_mods(data_root: str | Path, game_key: str) -> list:
    log.debug(f"[RegistryQuery] Listando mods instalados para o jogo: {game_key}")
    return load_registry(get_registry_path(data_root, game_key))["mods"]

def get_file_owner_index(data_root: str | Path, game_key: str) -> dict:
    """
    Cria um índice O(1) mapeando cada arquivo para o mod que é dono dele.
    Ex: {"www/data/Weapons.json": "Weapons Fix Mod V1"}
    """
    registry_path = get_registry_path(data_root, game_key)
    
    # Verifica se o arquivo existe e se o cache está atualizado
    current_mtime = os.path.getmtime(registry_path) if registry_path.exists() else 0
    cache_key = f"{data_root}_{game_key}"
    
    if cache_key in _registry_cache and _cache_mtime.get(cache_key) == current_mtime:
        return _registry_cache[cache_key]
    
    # Se chegou aqui, o cache expirou ou não existe. Vamos construir.
    mods = list_installed_mods(data_root, game_key)
    index = {}
    
    for mod in mods:
        for file_path in mod["files"]:
            index[file_path] = mod
            
    # Atualiza o cache
    _registry_cache[cache_key] = index
    _cache_mtime[cache_key] = current_mtime
    
    return index

def find_file_owner(data_root: str | Path, game_key: str, file_path: str | Path) -> dict | None:
    relative_path = _normalize_file_path(file_path)
    
    index = get_file_owner_index(data_root, game_key)
    owner = index.get(relative_path)
    
    if owner:
        log.debug(f"[RegistryQuery] Dono encontrado: '{owner['name']}' para o arquivo {relative_path}")
    return owner

def clear_registry_cache(data_root: str | Path, game_key: str) -> None:
    """Força a invalidação do cache de leitura do registro."""
    cache_key = f"{data_root}_{game_key}"
    if cache_key in _registry_cache:
        del _registry_cache[cache_key]
    if cache_key in _cache_mtime:
        del _cache_mtime[cache_key]