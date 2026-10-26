from pathlib import Path
from core.scanner.source_reader import get_raw_files
from core.scanner.destination_resolver import resolve_destination
from utils.inventory_index import InventoryIndex
from utils.logs.rise_logger import log

MAX_MOD_FILES = 10000

def _build_index(inventory) -> InventoryIndex | None:
    if not inventory: return None
    try:
        if isinstance(inventory, dict): return InventoryIndex(inventory)
        return inventory
    except Exception as e:
        log.error(f"[ModScanner] Falha ao construir o Índice: {e}")
        return None

def _collect_files(source, destination_overrides=None, inventory=None) -> list:
    log.debug(f"[ModScanner] Iniciando coleta para instalação. Origem: {source}")
    files = []
    skipped_count = 0
    seen_destinations = set() 
    index = _build_index(inventory)

    # DICIONÁRIO DE CONTEXTO: Mapeia "pasta_no_mod" -> "pasta_no_jogo"
    dir_context = {}

    for relative, file_source, kind in get_raw_files(source):
        if len(files) >= MAX_MOD_FILES:
            raise ValueError(f"Mod rejeitado: excede o limite de {MAX_MOD_FILES} arquivos.")

        destination, auto_resolved = resolve_destination(relative, index, destination_overrides, dir_context)
        
        if destination:
            dest_lower = destination.lower()
            if dest_lower in seen_destinations:
                raise ValueError(f"Mod corrompido: contém arquivos duplicados para o mesmo destino ({destination}).")
                
            seen_destinations.add(dest_lower)
            
            # Salva o contexto para os próximos arquivos da mesma pasta
            parent_dir_mod = str(Path(relative).parent).replace("\\", "/")
            parent_dir_game = str(Path(destination).parent).replace("\\", "/")
            if parent_dir_mod not in dir_context and parent_dir_mod != ".":
                dir_context[parent_dir_mod] = parent_dir_game

            files.append({
                "destination": str(destination).replace("\\", "/"),
                "source": str(file_source),
                "kind": kind,
                "auto_resolved": auto_resolved
            })
        else:
            skipped_count += 1

    log.info(f"[ModScanner] Coleta concluída. {len(files)} válidos. {skipped_count} ignorados.")
    if not files:
        raise ValueError("Nenhum arquivo com destino reconhecido foi encontrado no mod.")
    return files

def inspect_source(source, inventory=None) -> list:
    log.debug(f"[ModScanner] Iniciando inspeção para a UI. Origem: {source}")
    entries = []
    unknown_count = 0
    index = _build_index(inventory)
    
    # DICIONÁRIO DE CONTEXTO: Para a UI também mostrarmos a resolução inteligente!
    dir_context = {}

    for relative, _, kind in get_raw_files(source):
        if len(entries) >= MAX_MOD_FILES:
            break

        destination, auto_resolved = resolve_destination(relative, index, None, dir_context)
        
        status = "Destino reconhecido" if destination else "Destino desconhecido"
        if auto_resolved:
            status = "Destino auto-resolvido"
        elif not destination:
            unknown_count += 1

        if destination:
            parent_dir_mod = str(Path(relative).parent).replace("\\", "/")
            parent_dir_game = str(Path(destination).parent).replace("\\", "/")
            if parent_dir_mod not in dir_context and parent_dir_mod != ".":
                dir_context[parent_dir_mod] = parent_dir_game

        entries.append({
            "source": str(relative),
            "kind": kind,
            "destination": destination,
            "auto_resolved": auto_resolved,
            "status": status,
        })

    log.info(f"[ModScanner] Inspeção concluída. {len(entries)} arquivos. {unknown_count} sem destino.")
    return entries