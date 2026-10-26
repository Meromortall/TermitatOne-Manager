from pathlib import Path
from core.paths.validator import extract_www_path
from utils.inventory_index import InventoryIndex
from utils.logs.rise_logger import log

def resolve_destination(relative_path: str, inventory_index: InventoryIndex | None = None, overrides: dict | None = None, dir_context: dict | None = None) -> tuple[str | None, bool]:
    """Descobre o destino final de um arquivo baseado no www, inventário, contexto de pasta e overrides."""
    overrides = overrides or {}
    dir_context = dir_context if dir_context is not None else {}
    relative_path = str(relative_path).replace("\\", "/")
    
    # 1. Tenta o caminho base (www/)
    destination = extract_www_path(relative_path)
    auto_resolved = False

    if destination:
        log.debug(f"[DestinationResolver] Destino resolvido via 'www/': {destination}")

    # 2. Se falhou, tenta a Mágica do Inventário O(1)
    if not destination and inventory_index:
        filename = Path(relative_path).name
        destination = inventory_index.resolve_best_match(filename)
        if destination:
            auto_resolved = True
            log.info(f"[DestinationResolver] ✨ Auto-resolução O(1): '{relative_path}' -> '{destination}'")

    # 3. NOVO: Se falhou, tenta o Contexto de Diretório (Pasta irmã)
    if not destination and dir_context:
        parent_dir = str(Path(relative_path).parent)
        # Se já vimos um arquivo dessa mesma pasta indo para um lugar, usamos esse lugar
        if parent_dir in dir_context:
            resolved_parent = dir_context[parent_dir]
            filename = Path(relative_path).name
            destination = f"{resolved_parent}/{filename}" if resolved_parent else filename
            auto_resolved = True
            log.info(f"[DestinationResolver] 🧠 Contexto de Pasta: '{relative_path}' -> '{destination}'")

    # 4. Overrides do usuário têm a palavra final
    if relative_path in overrides:
        destination = overrides[relative_path]
        auto_resolved = False
        log.info(f"[DestinationResolver] Forçando destino via override manual: {destination}")

    if not destination:
        log.warning(f"[DestinationResolver] ❌ Falha ao resolver destino para: {relative_path}")
        
    return destination, auto_resolved