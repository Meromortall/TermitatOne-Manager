import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from utils.logs.rise_logger import log

def get_manifest_path(backup_root: str | Path, game_key: str) -> Path:
    if not game_key or any(char in str(game_key) for char in '\\/:*?"<>|'):
        log.error(f"[ManifestIO] Identificador de jogo inválido para manifesto: {game_key}")
        raise ValueError("Identificador de jogo inválido.")
    return Path(backup_root) / str(game_key) / "backup_manifest.json"

def load_manifest(manifest_path: Path) -> dict:
    log.debug(f"[ManifestIO] Carregando manifesto de backups: {manifest_path.name}")
    if not manifest_path.exists():
        return {}
        
    try:
        # utf-8-sig ignora o BOM do Windows
        with manifest_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
            
        if not isinstance(data, dict):
            raise ValueError("O JSON raiz não é um dicionário.")
            
        # TRAVA DE SEGURANÇA: Valida a estrutura de cada entrada do cofre
        safe_data = {}
        for path_key, entry in data.items():
            if isinstance(entry, dict) and "original_exists" in entry:
                if isinstance(entry["original_exists"], bool):
                    safe_data[str(path_key)] = entry
                else:
                    log.warning(f"[ManifestIO] Entrada de manifesto inválida para '{path_key}': 'original_exists' não é booleano.")
            else:
                log.warning(f"[ManifestIO] Entrada corrompida ignorada no manifesto: {path_key}")
                
        log.debug(f"[ManifestIO] Manifesto carregado e validado. {len(safe_data)} registros de backup.")
        return safe_data
        
    except json.JSONDecodeError as e:
        log.critical(f"[ManifestIO] 🚨 O manifesto '{manifest_path.name}' está CORROMPIDO: {e}")
        
        # Preserva o arquivo corrompido para não perder o histórico de backups
        corrupt_backup = manifest_path.with_name(f"manifest_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            manifest_path.rename(corrupt_backup)
            log.info(f"[ManifestIO] O manifesto corrompido foi movido para: {corrupt_backup.name}")
        except Exception as rename_err:
            log.error(f"[ManifestIO] Falha ao salvar o manifesto corrompido: {rename_err}")
            
        return {} # Retorna vazio APÓS salvar a cópia de segurança
        
    except Exception as e:
        log.error(f"[ManifestIO] Erro desconhecido ao ler manifesto {manifest_path.name}: {e}")
        return {}

def save_manifest(manifest_path: Path, manifest: dict) -> None:
    log.debug(f"[ManifestIO] Salvando manifesto com {len(manifest)} entradas...")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Usa um nome de temporário único para evitar conflitos
    temp_name = f"{manifest_path.name}.{uuid.uuid4().hex[:8]}.tmp"
    temporary_path = manifest_path.with_name(temp_name)
    
    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=4, ensure_ascii=False)
            # Garante que os dados foram fisicamente para o HD
            file.flush()
            os.fsync(file.fileno())
            
        temporary_path.replace(manifest_path)
        log.debug("[ManifestIO] Manifesto salvo e sincronizado no disco.")
        
    except Exception as e:
        log.critical(f"[ManifestIO] FALHA CRÍTICA ao salvar o manifesto: {e}")
        if temporary_path.exists():
            temporary_path.unlink()
        raise