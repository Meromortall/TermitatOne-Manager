import sys
import ctypes
from pathlib import Path

# Garante que a raiz do projeto está no PATH
sys.path.append(str(Path(__file__).resolve().parent))

# [NOVO] Ativa o High DPI no Windows para o app não ficar embaçado
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass # Ignora se não for Windows ou SO antigo

import customtkinter as ctk
from tkinter import messagebox
from utils.logs.rise_logger import setup_rise_logging, log

# Layout e Estado
from ui.layout.main_layout import LayoutMixin
from ui.layout.settings_view import SettingsViewMixin # [NOVO] Importado
from ui.layout.system_view import SystemViewMixin     # [NOVO] Importado
from ui.layout.credits_view import CreditsViewMixin
from ui.state.game_state import BaseStateMixin
from ui.state.theme_manager import load_settings, get_theme_colors

# Mods (Coluna Esquerda e Menu)
from ui.mods.mods_view import ModsViewMixin
from ui.mods.mod_actions import ModsActionsMixin
from ui.mods.mod_menu import ModMenuMixin

# Análise (Coluna Central, Direita e Diálogos)
from ui.analysis.tree_view import AnalysisTreeMixin
from ui.analysis.dialogs import AnalysisDialogsMixin
from ui.analysis.operations import AnalysisOperationsMixin
from ui.analysis.tools import AnalysisToolsMixin

# Configuração visual base (Fallback antes do tema carregar)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class TermitatoApp(
    LayoutMixin, 
    BaseStateMixin, 
    ModsViewMixin, 
    ModsActionsMixin, 
    ModMenuMixin, 
    AnalysisTreeMixin, 
    AnalysisDialogsMixin, 
    AnalysisOperationsMixin, 
    AnalysisToolsMixin, 
    SettingsViewMixin,
    SystemViewMixin,
    ctk.CTk,
    CreditsViewMixin, 
):
    def __init__(self):
        super().__init__()

        # Carrega as preferências salvas
        self.settings = load_settings()
        self.current_theme_name = self.settings.get("theme", "Sistema")
        self.current_supercharge_name = self.settings.get("supercharge", "Nenhum")

        # [NOVO] Resolve a paleta ANTES de criar a janela (evita flash branco)
        self.colors = get_theme_colors(self.current_theme_name, self.current_supercharge_name)
        self.configure(fg_color=self.colors["bg_main"]) 

        # Configuração da janela principal
        self.title("Termitato Mod Manager V3.0")
        self.geometry("1250x800")
        self.minsize(1100, 700)

        # Carrega o ícone do aplicativo
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            log.warning(f"[Bootstrapper] Não foi possível carregar o ícone: {e}")

        # Estado inicial
        self.games = {}
        self.current_game_key = None
        self.current_inventory = None
        self.all_mods = []
        self.filtered_mods = []
        self.selected_mod = None
        self.destination_overrides = {}
        self.has_inventory = False

        # Construção da interface
        log.info("[Bootstrapper] Construindo interface...")
        self.build_interface(self)

        # Busca os jogos instalados
        log.info("[Bootstrapper] Buscando jogos instalados...")
        self.initialize_games()


if __name__ == "__main__":
    # Inicializa o sistema de logs antes de tudo
    setup_rise_logging()
    log.info("============================================================")
    log.info("Iniciando TERMITATO MOD MANAGER V3.0")
    log.info("============================================================")
    
    try:
        app = TermitatoApp()
        app.mainloop()
    except Exception as e:
        log.critical("[Bootstrapper] O aplicativo crashou fatalmente.", exc_info=True)
        
        # [NOVO] Avisa o usuário que deu erro em vez de sumir silenciosamente
        try:
            messagebox.showerror(
                "Erro Fatal", 
                f"O Termitato encontrou um erro inesperado e precisa fechar.\n\n"
                f"Detalhes técnicos foram salvos no arquivo:\n"
                f"{Path.home() / 'AppData/Local/TermitatoModManager/logs/rise_debug.log'}"
            )
        except Exception:
            pass # Se o messagebox falhar (porque o Tkinter morreu), ignora.
            
        raise e
    finally:
        log.info("============================================================")
        log.info("TERMITATO MOD MANAGER encerrado.")
        log.info("============================================================")