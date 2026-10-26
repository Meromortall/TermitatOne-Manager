import json
import os
from datetime import datetime
from pathlib import Path
from utils.logs.rise_logger import log

def get_preset_path(data_root: str | Path, game_key: str) -> Path:
    if not game_key or any(char in str(game_key) for char in '\\/:*?"<>|'):
        log.error(f"[PresetIO] Identificador de jogo inválido para presets: {game_key}")
        raise ValueError("Identificador de jogo inválido.")
    return Path(data_root) / str(game_key) / "presets.json"

def load_presets_from_disk(path: Path) -> dict:
    log.debug(f"[PresetIO] Lendo arquivo de presets: {path.name}")
    if not path.exists():
        return {}
        
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not isinstance(data, dict):
            raise ValueError("O JSON raiz não é um dicionário.")
            
        # TRAVA DE SEGURANÇA: Sanitiza a estrutura interna
        # Garante que todo preset é uma LISTA de strings
        safe_data = {}
        for key, value in data.items():
            if isinstance(value, list):
                # Filtra apenas strings válidas
                safe_list = [str(m) for m in value if isinstance(m, str)]
                safe_data[str(key)] = safe_list
            else:
                log.warning(f"[PresetIO] Preset '{key}' ignorado: valor não é uma lista.")
                
        log.debug(f"[PresetIO] {len(safe_data)} presets carregados e validados.")
        return safe_data
        
    except json.JSONDecodeError as e:
        log.critical(f"[PresetIO] 🚨 Arquivo de presets '{path.name}' CORROMPIDO: {e}")
        
        # Preserva o arquivo corrompido para recuperação manual
        corrupt_backup = path.with_name(f"presets_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            path.rename(corrupt_backup)
            log.info(f"[PresetIO] Arquivo corrompido movido para: {corrupt_backup.name}")
        except Exception as rename_err:
            log.error(f"[PresetIO] Falha ao salvar arquivo corrompido: {rename_err}")
            
        return {}
        
    except Exception as e:
        log.error(f"[PresetIO] Erro ao ler presets de {path}: {e}")
        return {}

def save_presets_to_disk(path: Path, presets: dict) -> None:
    log.debug(f"[PresetIO] Salvando {len(presets)} presets em: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    
    try:
        with temp.open("w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4, ensure_ascii=False)
            # Força a gravação física no disco (durabilidade)
            f.flush()
            os.fsync(f.fileno())
            
        temp.replace(path)
        log.debug("[PresetIO] Presets salvos e sincronizados no disco.")
        
    except Exception as e:
        log.critical(f"[PresetIO] FALHA CRÍTICA ao salvar presets: {e}")
        if temp.exists():
            temp.unlink()
        raise