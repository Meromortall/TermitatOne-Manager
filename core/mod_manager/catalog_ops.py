import uuid
from datetime import datetime, timezone
from pathlib import Path
from core.mod_manager.catalog_io import get_catalog_path, load_catalog_from_disk, save_catalog_to_disk
from utils.logs.rise_logger import log

def load_catalog(data_root: str | Path, game_key: str) -> list:
    path = get_catalog_path(data_root, game_key)
    return load_catalog_from_disk(path)

def add_to_catalog(data_root: str | Path, game_key: str, name: str, source_path: str | Path, files: list) -> dict:
    # TRAVA DE SEGURANÇA 1: Sanitiza o nome do mod
    safe_name = str(name).strip() if name else ""
    if not safe_name:
        log.error("[CatalogOps] Tentativa de adicionar mod sem nome. Abortando.")
        raise ValueError("O mod precisa ter um nome válido.")

    # TRAVA DE SEGURANÇA 2: Garante que o caminho seja absoluto
    safe_path = Path(source_path).resolve()
    
    # TRAVA DE SEGURANÇA 3: Garante que a lista de arquivos seja válida
    if not isinstance(files, list) or not files:
        log.error(f"[CatalogOps] O mod '{safe_name}' não contém arquivos válidos para o catálogo.")
        raise ValueError("O mod não contém arquivos para serem catalogados.")

    path = get_catalog_path(data_root, game_key)
    catalog = load_catalog_from_disk(path)
    
    # TRAVA DE SEGURANÇA 4: Busca Case-Insensitive (O Fim dos Duplicados)
    for mod in catalog:
        if mod["name"].casefold() == safe_name.casefold():
            log.info(f"[CatalogOps] Mod '{safe_name}' já existe. Atualizando dados no catálogo.")
            mod["name"] = safe_name # Atualiza para o novo case, se o usuário mudou
            mod["source_path"] = str(safe_path)
            mod["files"] = files
            mod["added_at"] = datetime.now(timezone.utc).isoformat()
            save_catalog_to_disk(path, catalog)
            return mod

    log.info(f"[CatalogOps] Adicionando novo mod '{safe_name}' ao catálogo.")
    new_mod = {
        "id": uuid.uuid4().hex,
        "name": safe_name,
        "source_path": str(safe_path),
        "files": files,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    catalog.append(new_mod)
    save_catalog_to_disk(path, catalog)
    return new_mod

def remove_from_catalog(data_root: str | Path, game_key: str, mod_name: str) -> bool:
    safe_name = str(mod_name).strip()
    if not safe_name:
        return False

    path = get_catalog_path(data_root, game_key)
    catalog = load_catalog_from_disk(path)
    
    # TRAVA DE SEGURANÇA 5: Remoção Case-Insensitive
    new_catalog = [m for m in catalog if m["name"].casefold() != safe_name.casefold()]
    
    if len(new_catalog) != len(catalog):
        log.info(f"[CatalogOps] Mod '{safe_name}' removido do catálogo.")
        save_catalog_to_disk(path, new_catalog)
        return True
        
    log.warning(f"[CatalogOps] Tentativa de remover mod inexistente do catálogo: {safe_name}")
    return False