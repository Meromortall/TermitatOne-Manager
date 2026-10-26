import os
import json
import time
from pathlib import Path
from utils.logs.rise_logger import log

INVENTORY_SCHEMA_VERSION = 2

def scan_game(game_path: str | Path) -> dict:
    """Analisa a estrutura do jogo usando os.scandir para máxima performance."""
    root = Path(game_path).resolve()

    if not root.exists() or not root.is_dir():
        log.error(f"[GameScanner] Pasta do jogo inválida: {root}")
        raise FileNotFoundError(f"Pasta do jogo não encontrada: {root}")

    log.info(f"[GameScanner] Iniciando escaneamento do jogo em: {root}")
    start_time = time.time()
    
    entries = []
    total_files = 0
    total_dirs = 0
    errors_count = 0

    # Usamos uma PILHA (stack) para evitar estourar a memória em pastas muito profundas
    dirs_to_scan = [("", root)]

    while dirs_to_scan:
        rel_dir, abs_dir = dirs_to_scan.pop()

        try:
            with os.scandir(abs_dir) as it:
                for entry in it:
                    # 1. Ignora QUALQUER atalho (arquivo ou pasta) de forma segura
                    if entry.is_symlink():
                        continue

                    current_rel = f"{rel_dir}/{entry.name}" if rel_dir else entry.name

                    if entry.is_dir(follow_symlinks=False):
                        entries.append({
                            "path": current_rel,
                            "name": entry.name,
                            "type": "directory",
                            "extension": ""
                        })
                        total_dirs += 1
                        dirs_to_scan.append((current_rel, Path(entry.path)))
                        
                    elif entry.is_file(follow_symlinks=False):
                        try:
                            # Lê o stat para garantir que não está corrompido/bloqueado
                            _ = entry.stat() 
                            entries.append({
                                "path": current_rel,
                                "name": entry.name,
                                "type": "file",
                                "extension": Path(entry.name).suffix.lower()
                            })
                            total_files += 1
                        except OSError as e:
                            log.warning(f"[GameScanner] Arquivo bloqueado ignorado: {entry.name} ({e})")
                            errors_count += 1
                            
        except OSError as e:
            log.warning(f"[GameScanner] Pasta inacessível ignorada: {abs_dir} ({e})")
            errors_count += 1

        # Mostra progresso a cada 5000 itens
        if len(entries) % 5000 == 0 and len(entries) > 0:
            log.debug(f"[GameScanner] Progresso: {len(entries)} itens mapeados...")

    # Ordena case-insensitive para busca binária futura
    entries.sort(key=lambda item: item["path"].casefold())
    
    elapsed = round(time.time() - start_time, 2)
    log.info(f"[GameScanner] Escaneamento concluído em {elapsed}s. Arquivos: {total_files} | Pastas: {total_dirs} | Erros: {errors_count}")

    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "root": str(root),
        "total_entries": len(entries),
        "total_files": total_files,
        "total_directories": total_dirs,
        "entries": entries,
    }


def save_inventory(inventory: dict, output_path: str | Path) -> None:
    """Salva o inventário fora da pasta do jogo de forma ultra-rápida e segura."""
    output = Path(output_path).resolve()
    game_root = Path(inventory["root"]).resolve()

    try:
        output.relative_to(game_root)
        log.error("[GameScanner] Tentativa de salvar inventário dentro da pasta do jogo!")
        raise ValueError("O inventário deve ser salvo fora da pasta do jogo.")
    except ValueError:
        pass

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")

    log.info(f"[GameScanner] Salvando inventário em disco: {output.name}")
    
    try:
        # Sem indentação para economizar 80% de espaço em disco
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(inventory, file, separators=(',', ':'), ensure_ascii=False)
            
        temporary.replace(output)
        log.debug("[GameScanner] Inventário salvo com sucesso.")
    except Exception as e:
        log.critical(f"[GameScanner] FALHA AO SALVAR INVENTÁRIO: {e}")
        if temporary.exists():
            temporary.unlink()
        raise


def load_inventory(inventory_path: str | Path) -> dict:
    """Carrega e valida um inventário salvo, protegendo contra JSON corrompido."""
    path = Path(inventory_path)
    log.debug(f"[GameScanner] Carregando inventário de: {path.name}")

    if not path.exists():
        log.error(f"[GameScanner] Arquivo de inventário não existe: {path}")
        raise FileNotFoundError(f"Inventário não encontrado: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            inventory = json.load(file)
    except json.JSONDecodeError as e:
        log.error(f"[GameScanner] O arquivo de inventário está corrompido: {e}")
        raise ValueError("O arquivo JSON do inventário está corrompido.")

    # Validação básica de estrutura
    if not isinstance(inventory, dict) or "entries" not in inventory or "root" not in inventory:
        log.error("[GameScanner] Estrutura do inventário inválida.")
        raise ValueError("O arquivo de inventário tem formato inválido.")

    # Aviso de migração
    schema_ver = inventory.get("schema_version", 1)
    if schema_ver < INVENTORY_SCHEMA_VERSION:
        log.warning(f"[GameScanner] Inventário antigo (v{schema_ver}). Re-escanear o jogo é recomendado.")

    log.info(f"[GameScanner] Inventário carregado. {inventory.get('total_files', 0)} arquivos encontrados.")
    return inventory