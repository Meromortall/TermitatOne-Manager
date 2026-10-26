import json
import os
from datetime import datetime
from pathlib import Path
from utils.logs.rise_logger import log

def get_catalog_path(data_root: str | Path, game_key: str) -> Path:
    if not game_key or any(char in str(game_key) for char in '\\/:*?"<>|'):
        log.error(f"[CatalogIO] Identificador de jogo inválido para catálogo: {game_key}")
        raise ValueError("Identificador de jogo inválido.")
    return Path(data_root) / str(game_key) / "catalog.json"

def load_catalog_from_disk(path: Path) -> list:
    log.debug(f"[CatalogIO] Lendo catálogo do disco: {path.name}")
    if not path.exists():
        return []
        
    try:
        # utf-8-sig ignora o BOM invisível que o Bloco de Notas do Windows adiciona
        with path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
            
        if not isinstance(data, dict) or "mods" not in data:
            raise ValueError("Estrutura raiz inválida.")
            
        raw_mods = data.get("mods")
        if not isinstance(raw_mods, list):
            raise ValueError("A chave 'mods' não é uma lista.")
            
        # TRAVA DE SEGURANÇA: Valida cada mod individualmente
        # Garante que a UI nunca receba um mod quebrado que cause KeyError
        safe_mods = []
        required_keys = {"id", "name", "source_path", "files"}
        
        for mod in raw_mods:
            if isinstance(mod, dict) and required_keys.issubset(mod.keys()):
                # Garante que 'files' é uma lista
                if isinstance(mod["files"], list):
                    safe_mods.append(mod)
                else:
                    log.warning(f"[CatalogIO] Mod '{mod.get('name', 'Desconhecido')}' ignorado: 'files' não é uma lista.")
            else:
                log.warning(f"[CatalogIO] Entrada de mod inválida ignorada no catálogo: {mod}")
                
        if len(safe_mods) < len(raw_mods):
            log.warning(f"[CatalogIO] {len(raw_mods) - len(safe_mods)} mods inválidos foram removidos da memória para proteger a UI.")
            
        log.debug(f"[CatalogIO] {len(safe_mods)} mods carregados e validados do catálogo.")
        return safe_mods
        
    except json.JSONDecodeError as e:
        log.critical(f"[CatalogIO] 🚨 O catálogo '{path.name}' está CORROMPIDO: {e}")
        
        # Preserva o arquivo corrompido para diagnóstico
        corrupt_backup = path.with_name(f"catalog_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            path.rename(corrupt_backup)
            log.info(f"[CatalogIO] O arquivo corrompido foi movido para: {corrupt_backup.name}")
        except Exception as rename_err:
            log.error(f"[CatalogIO] Falha ao salvar o arquivo corrompido: {rename_err}")
            
        return []
        
    except Exception as e:
        log.error(f"[CatalogIO] Erro ao ler catálogo ({path}): {e}")
        return []

def save_catalog_to_disk(path: Path, mods: list) -> None:
    log.debug(f"[CatalogIO] Salvando {len(mods)} mods no catálogo.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    
    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump({"mods": mods}, f, indent=4, ensure_ascii=False)
            # Durabilidade no disco (evita arquivo em branco em queda de energia)
            f.flush()
            os.fsync(f.fileno())
            
        temp_path.replace(path)
        log.debug("[CatalogIO] Catálogo salvo e sincronizado no disco.")
        
    except Exception as e:
        log.critical(f"[CatalogIO] FALHA CRÍTICA ao salvar catálogo: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise