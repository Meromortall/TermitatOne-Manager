from pathlib import Path
from core.mod_manager.preset_io import get_preset_path, load_presets_from_disk, save_presets_to_disk
from utils.logs.rise_logger import log

def load_presets(data_root: str | Path, game_key: str) -> dict:
    """Carrega todos os presets do jogo."""
    path = get_preset_path(data_root, game_key)
    return load_presets_from_disk(path)

def add_preset(data_root: str | Path, game_key: str, preset_name: str, mod_names: list) -> None:
    """Cria ou atualiza um preset, sanitizando os nomes dos mods."""
    if not preset_name:
        raise ValueError("O nome do preset não pode ser vazio.")
        
    clean_name = str(preset_name).strip()
    if not clean_name:
        raise ValueError("O nome do preset não pode conter apenas espaços.")

    # TRAVA DE SEGURANÇA 1: Sanitiza a lista de mods
    # Remove duplicatas, ignora valores nulos e remove espaços extras
    safe_mods = []
    for m in mod_names:
        if isinstance(m, str) and m.strip():
            safe_mods.append(m.strip())
            
    # Remove duplicatas mantendo a ordem (importante para presets)
    safe_mods = list(dict.fromkeys(safe_mods))
    
    if not safe_mods:
        raise ValueError("O preset precisa ter pelo menos um mod válido para ser salvo.")
        
    path = get_preset_path(data_root, game_key)
    presets = load_presets_from_disk(path)
    
    presets[clean_name] = safe_mods
    save_presets_to_disk(path, presets)
    log.info(f"[PresetOps] Preset '{clean_name}' salvo com {len(safe_mods)} mods.")

def delete_preset(data_root: str | Path, game_key: str, preset_name: str) -> bool:
    """Remove um preset existente, corrigindo o bug do espaço invisível."""
    clean_name = str(preset_name).strip()
    if not clean_name:
        return False
        
    path = get_preset_path(data_root, game_key)
    presets = load_presets_from_disk(path)
    
    if clean_name in presets:
        del presets[clean_name]
        save_presets_to_disk(path, presets)
        log.info(f"[PresetOps] Preset '{clean_name}' deletado.")
        return True
    
    log.warning(f"[PresetOps] Tentativa de deletar preset inexistente: '{clean_name}'")
    return False