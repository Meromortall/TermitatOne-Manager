from pathlib import Path
from collections import defaultdict
from utils.logs.rise_logger import log

# Constante global para os arquivos base do RPG Maker (Case-Sensitive, como no jogo original)
RPG_MAKER_CORE = {
    "Actors.json", "Classes.json", "Skills.json", "Items.json", 
    "Weapons.json", "Armors.json", "Enemies.json", "Troops.json", 
    "States.json", "Animations.json", "Tilesets.json", 
    "CommonEvents.json", "System.json"
}

class InventoryIndex:
    """Um índice otimizado O(1) para busca de arquivos no inventário do jogo."""
    
    def __init__(self, inventory_data: dict):
        # Chave: nome do arquivo (casefold), Valor: lista de caminhos já ordenada
        self._index_by_name = defaultdict(list)
        self._total_entries = 0
        self._build_index(inventory_data)

    def _build_index(self, inventory_data: dict):
        log.info("[InventoryIndex] Construindo índice em memória para buscas O(1)...")
        
        # Cache temporário para agrupar antes de ordenar
        temp_index = defaultdict(list)
        
        for entry in inventory_data.get("entries", []):
            if entry.get("type") == "file":
                try:
                    nome_limpo = str(entry["name"]).casefold()
                    temp_index[nome_limpo].append(entry["path"])
                    self._total_entries += 1
                except KeyError as e:
                    log.warning(f"[InventoryIndex] Entrada de inventário inválida ignorada: faltando chave {e}")
                    continue

        # TRAVA DE PERFORMANCE: Ordena uma única vez durante a construção
        for name, paths in temp_index.items():
            self._index_by_name[name] = sorted(paths, key=str.casefold)
            
        log.debug(f"[InventoryIndex] Índice construído com {self._total_entries} arquivos mapeados.")

    def find_matches(self, filename: str) -> list[str]:
        """Busca instantânea pelo nome do arquivo. A lista já vem ordenada."""
        if not filename:
            return []
            
        # Garante que estamos lidando com string (evita crash se vier um Path)
        alvo = str(filename).casefold()
        return self._index_by_name.get(alvo, [])

    def resolve_best_match(self, filename: str) -> str | None:
        """Aplica as regras de negócio do RPG Maker para achar o melhor destino."""
        matches = self.find_matches(filename)
        
        if len(matches) == 1:
            return matches[0]
            
        if len(matches) > 1:
            # MÁGICA AQUI: Se houver duplicados, escolhe o caminho MAIS CURTO.
            # Ex: www/data/Weapons.json é mais curto (e mais correto) que www/data/data/Weapons.json
            # Como já ordenamos por alfabeto na criação, usamos min() para pegar o mais curto.
            best_match = min(matches, key=len)
            log.info(f"[InventoryIndex] ✨ Desempate por caminho mais curto: '{filename}' -> '{best_match}'")
            return best_match

        # Fallback para arquivos base do RPG Maker (se não achou nada no inventário)
        # TRAVA DE CASE: Encontra o nome original com a grafia correta (ex: Weapons.json)
        for standard_name in RPG_MAKER_CORE:
            if standard_name.casefold() == str(filename).casefold():
                log.debug(f"[InventoryIndex] Usando fallback heurístico (Case corrigido): {standard_name}")
                return f"www/data/{standard_name}"

        return None