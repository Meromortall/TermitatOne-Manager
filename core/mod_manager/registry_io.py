import json
import os
from datetime import datetime
from pathlib import Path
from utils.logs.rise_logger import log

def get_registry_path(data_root: str | Path, game_key: str) -> Path:
    if not game_key or any(char in str(game_key) for char in '\\/:*?"<>|'):
        log.error(f"[RegistryIO] Identificador de jogo inválido para registro: {game_key}")
        raise ValueError("Identificador de jogo inválido.")
    return Path(data_root) / str(game_key) / "mods.json"

def load_registry(path: Path) -> dict:
    if not path.exists():
        log.debug(f"[RegistryIO] Registro não existe ainda, criando estrutura vazia: {path.name}")
        return {"mods": []}
        
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            
        if not isinstance(data, dict) or not isinstance(data.get("mods"), list):
            raise ValueError("Estrutura inválida (não é um dicionário com lista 'mods').")
            
        log.debug(f"[RegistryIO] Registro carregado com sucesso: {len(data['mods'])} mods.")
        return data
        
    except json.JSONDecodeError as e:
        log.critical(f"[RegistryIO] 🚨 O banco de dados '{path.name}' está CORROMPIDO! Erro de sintaxe: {e}")
        
        # TRAVA DE SEGURANÇA: Preserva o arquivo corrompido para diagnóstico e recuperação manual
        corrupt_backup = path.with_name(f"mods_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            path.rename(corrupt_backup)
            log.info(f"[RegistryIO] O arquivo corrompido foi movido para: {corrupt_backup.name}")
        except Exception as rename_err:
            log.error(f"[RegistryIO] Falha ao tentar salvar o arquivo corrompido: {rename_err}")
            
        return {"mods": []} # Retorna vazio APÓS salvar o original
        
    except Exception as e:
        log.error(f"[RegistryIO] Erro desconhecido ao ler o registro de mods ({path}): {e}")
        return {"mods": []}

def save_registry(path: Path, data: dict) -> None:
    """Salva o registro de mods com gravação atômica e durabilidade no disco."""
    log.debug(f"[RegistryIO] Salvando registro com {len(data.get('mods', []))} mods no disco.")
    
    # Garante que a pasta pai exista
    path.parent.mkdir(parents=True, exist_ok=True)
    
    temporary_path = path.with_suffix(".tmp")
    
    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            # 1. Grava o JSON no arquivo temporário
            json.dump(data, file, indent=4, ensure_ascii=False)
            
            # 2. Força a gravação física no HD (impede perda de dados em queda de energia)
            file.flush()
            os.fsync(file.fileno())
            
        # 3. Substituição atômica
        temporary_path.replace(path)
        log.debug("[RegistryIO] Registro salvo e sincronizado fisicamente no disco.")
        
    except Exception as e:
        log.critical(f"[RegistryIO] 🚨 FALHA CRÍTICA AO SALVAR O BANCO DE DADOS: {e}")
        if temporary_path.exists():
            temporary_path.unlink() # Remove o lixo temporário
        raise