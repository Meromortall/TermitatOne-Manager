import os
import re
import threading
from pathlib import Path
import customtkinter as ctk

from core.game.game_finder import find_installed_games
from core.scanner.game_scanner import load_inventory
from core.mod_manager.catalog_ops import load_catalog
from core.mod_manager.registry_query import list_installed_mods
from ui.state.data_merger import merge_catalog_and_registry
from utils.logs.rise_logger import log

local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
DATA_ROOT = local_app_data / "TermitatoModManager"

INVENTORY_FILES = {
    "fear_hunger": "fear_and_hunger.json",
    "fear_hunger_2_termina": "fear_and_hunger_2_termina.json",
}

def make_game_key(game_name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", game_name.lower()).strip("_")
    if not key: 
        log.error(f"[GameState] Não foi possível criar key para o jogo: {game_name}")
        raise ValueError("Não foi possível identificar este jogo.")
    return key

def format_size(bytes_size: int) -> str:
    if not bytes_size: return "0 KB"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


class BaseStateMixin:
    """Mixin responsável por gerenciar o estado global da aplicação."""
    
    def initialize_games(self):
        log.info("[GameState] Inicializando busca de jogos...")
        self.games = find_installed_games()
        
        if not self.games:
            log.warning("[GameState] Nenhum jogo instalado foi encontrado.")
            self.update_status("Nenhum jogo instalado foi encontrado.", is_error=True)
            return
            
        first_game_key = list(self.games.keys())[0]
        self.change_game(first_game_key)

    def change_game(self, selected_game: str):
        """Chamado quando o usuário clica no botão do jogo."""
        if not selected_game or selected_game not in self.games: 
            return
        
        new_key = make_game_key(selected_game)
        if new_key == self.current_game_key:
            return
            
        log.info(f"[GameState] Alterando jogo ativo para: {selected_game}")
        self.current_game_key = new_key
        self.current_inventory = None
        self.has_inventory = False 
        
        # TRAVA DE UX: Limpa o painel da direita e a árvore imediatamente
        if hasattr(self, '_clear_ui_selection'):
            self._clear_ui_selection()
        else:
            self.selected_mod = None

        # Limpa a lista da esquerda para dar feedback visual imediato
        if hasattr(self, 'all_mods'):
            self.all_mods = []
        if hasattr(self, 'filter_list'):
            self.filter_list()

        self.title(f"Termitato Mod Manager V3.0 - {selected_game}")
        self.update_status(f"Carregando jogo: {selected_game}...")
        
        # 1. Carrega Inventário
        inv_file = INVENTORY_FILES.get(self.current_game_key)
        if inv_file:
            inv_path = DATA_ROOT / "inventories" / inv_file
            if inv_path.exists():
                try:
                    self.current_inventory = load_inventory(inv_path)
                    self.has_inventory = True
                    log.info(f"[GameState] Inventário carregado: {len(self.current_inventory['entries'])} itens.")
                except Exception as e:
                    log.error(f"[GameState] Falha ao carregar inventário: {e}")
            else:
                log.warning(f"[GameState] Arquivo de inventário não encontrado: {inv_path}")

        # 2. Atualiza UI global (Botões de jogo, menu de presets, etc)
        if hasattr(self, 'update_game_buttons'):
            self.update_game_buttons()
        if hasattr(self, 'update_preset_menu'):
            self.update_preset_menu()
        
        # 3. Carrega mods na interface
        self.load_real_mods()
        
        if hasattr(self, "update_inventory_button"):
            self.update_inventory_button()

    def load_real_mods(self):
        """Carrega os mods de forma assíncrona com trava anti-race-condition."""
        if not self.current_game_key: 
            return
            
        self.update_status("Carregando mods...")
        
        # TRAVA DE SEGURANÇA: Congela a key atual para a thread
        target_key = self.current_game_key
        
        def fetch_data():
            try:
                catalog = load_catalog(DATA_ROOT, target_key)
                installed = list_installed_mods(DATA_ROOT, target_key)
                merged = merge_catalog_and_registry(catalog, installed)
                
                # TRAVA DELUXE: Só atualiza a UI se o usuário não mudou de jogo nesse meio tempo
                def update_if_still_current():
                    if self.current_game_key == target_key:
                        self._on_mods_loaded(merged)
                    else:
                        log.debug("[GameState] Carregamento antigo descartado (usuário trocou de jogo).")
                
                self.after(0, update_if_still_current)
                
            except Exception as e:
                log.error(f"[GameState] Erro fatal ao carregar mods: {e}", exc_info=True)
                self.after(0, lambda: self.update_status("Erro ao carregar mods. Verifique o log.", is_error=True))
        
        threading.Thread(target=fetch_data, daemon=True).start()

    def _on_mods_loaded(self, mods):
        self.all_mods = mods
        log.info(f"[GameState] {len(self.all_mods)} mods carregados na interface.")
        self.update_status(f"{len(self.all_mods)} mods carregados.")
        
        if hasattr(self, 'filter_list'):
            self.filter_list()