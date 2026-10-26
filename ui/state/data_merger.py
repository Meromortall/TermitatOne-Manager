from pathlib import Path
from utils.logs.rise_logger import log

def merge_catalog_and_registry(catalog: list, installed: list) -> list:
    """Junta os mods do catálogo e do registro, garantindo que mods instalados nunca sumam."""
    log.debug(f"[DataMerger] Mesclando {len(catalog)} do catálogo com {len(installed)} do registro.")
    
    catalog_dict = {m["name"].casefold(): m for m in catalog}
    installed_dict = {m["name"].casefold(): m for m in installed}
    
    all_mod_names = set(catalog_dict.keys()) | set(installed_dict.keys())
    merged_mods = []

    for name_key in all_mod_names:
        cat_mod = catalog_dict.get(name_key)
        reg_mod = installed_dict.get(name_key)
        
        display_name = reg_mod["name"] if reg_mod else cat_mod["name"]
        is_installed = reg_mod is not None
        actual_id = reg_mod["id"] if reg_mod else cat_mod.get("id")
        files = reg_mod["files"] if reg_mod else cat_mod.get("files", [])
        
        source_path = cat_mod.get("source_path", "") if cat_mod else ""
        file_size = 0
        
        if source_path:
            path_obj = Path(source_path)
            try:
                if path_obj.is_file():
                    file_size = path_obj.stat().st_size
            except OSError as e:
                log.warning(f"[DataMerger] Falha ao ler tamanho de {path_obj.name}: {e}")

        merged_mods.append({
            "name": display_name,
            "installed": is_installed,
            "files": files,
            "source_path": source_path,
            "id": actual_id,
            "size": file_size,
            "in_catalog": cat_mod is not None 
        })
        
    return sorted(merged_mods, key=lambda x: x["name"].casefold())