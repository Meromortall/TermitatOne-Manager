import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from PIL import Image

from ui.state.theme_manager import get_background_config
from ui.layout.header import HeaderComponent
from ui.layout.status_bar import StatusBarComponent
from ui.state.theme_manager import (
    THEMES, BACKGROUNDS, SUPERCHARGES, load_settings, save_settings, get_theme_colors
)
from utils.logs.rise_logger import log


class LayoutMixin:
    """Gerencia a estrutura principal e a navegação do Termitato."""

    def build_interface(self, root):
        """Inicializa a estrutura visual da aplicação."""
        self.root = root
        self.root.title("Termitato Mod Manager V3.0")
        self.root.geometry("1250x800")
        self.root.minsize(1100, 700)

        if not hasattr(self, "settings"):
            self.settings = load_settings()

        self.current_theme_name = self.settings.get("theme", "Sistema")
        self.current_background_name = self.settings.get("background", "Nenhum")
        self.current_supercharge_name = self.settings.get("supercharge", "Nenhum")
        self.current_screen = "mods"
        self._ui_refresh_id = None

        self._render_ui()

    def _render_ui(self):
        """Reconstrói a interface utilizando a paleta atual com fundo real."""
        self.colors = get_theme_colors(
            self.current_theme_name,
            self.current_supercharge_name,
        )
        
        ctk.set_appearance_mode(self.colors["mode"])
        self.root.configure(fg_color=self.colors["bg_main"])

        for widget in self.root.winfo_children():
            widget.destroy()

        # ============================================================
        # FUNDO COM CANVAS
        # ============================================================
        bg_config = get_background_config(self.current_background_name)
        bg_image_path = bg_config.get("image")
        
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=self.colors["bg_main"])
        self.canvas.pack(fill="both", expand=True)

        if bg_image_path:
            project_root = Path(__file__).resolve().parents[2]
            full_path = project_root / bg_image_path
            if full_path.is_file():
                try:
                    with Image.open(full_path) as img:
                        img = img.convert("RGB")
                        img = img.resize((1250, 800), Image.Resampling.LANCZOS)
                        overlay = Image.new("RGBA", img.size, (0, 0, 0, 180))
                        img = Image.alpha_composite(img.convert("RGBA"), overlay)
                        
                        from PIL import ImageTk
                        self._bg_photo = ImageTk.PhotoImage(img)
                        self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")
                except Exception as e:
                    log.error(f"Erro ao carregar imagem de fundo: {e}")

        # ============================================================
        # UI EM CIMA DO CANVAS
        # ============================================================
        
        # Sidebar (colocada diretamente no Canvas)
        self.sidebar = ctk.CTkFrame(self.canvas, width=190, corner_radius=0, fg_color=self.colors["bg_panel"])
        self.canvas.create_window((0, 0), window=self.sidebar, anchor="nw", width=190, height=800)
        self._populate_sidebar()

        # Main Content (colocado ao lado da Sidebar)
        self.main_content = ctk.CTkFrame(self.canvas, fg_color="transparent", corner_radius=0)
        self.canvas.create_window((190, 0), window=self.main_content, anchor="nw", width=1060, height=800)
        
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)

        self.header = HeaderComponent(self.main_content, self)
        self.header.frame.grid(row=0, column=0, sticky="ew")

        self.screen_container = ctk.CTkFrame(self.main_content, fg_color="transparent", corner_radius=0)
        self.screen_container.grid(row=1, column=0, sticky="nsew")
        self.screen_container.grid_columnconfigure(0, weight=1)
        self.screen_container.grid_rowconfigure(0, weight=1)

        self.status_bar = StatusBarComponent(self.main_content, self)
        self.status_bar.frame.grid(row=2, column=0, sticky="ew")

        self.build_mods_screen()
        self.build_settings_screen()
        self.build_system_screen()
        self.build_credits_screen()

        self.show_screen(self.current_screen)

        if hasattr(self, "load_real_mods") and getattr(self, "current_game_key", None):
            self.load_real_mods()

    # ---------------------------------------------------------
    # Conteúdo da Sidebar (Adaptado do setup_sidebar original)
    # ---------------------------------------------------------
    def _populate_sidebar(self):
        """Preenche o sidebar com os botões e labels (sem criar o frame)."""
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="Termitato", 
            font=ctk.CTkFont(size=22, weight="bold"), 
            text_color=self.colors["accent"]
        ).grid(row=0, column=0, pady=(30, 5), padx=20, sticky="w")

        ctk.CTkLabel(
            self.sidebar, text="MOD MANAGER V3.0", 
            font=ctk.CTkFont(size=10), 
            text_color=self.colors["text_muted"]
        ).grid(row=1, column=0, padx=21, pady=(0, 30), sticky="w")

        self.create_nav_button("📦  Mod Manager", 2, lambda: self.show_screen("mods"))
        self.create_nav_button("⚙️  Settings", 3, lambda: self.show_screen("settings"))
        self.create_nav_button("🛠️  Manager System", 4, lambda: self.show_screen("system"))
        self.create_nav_button("👨‍💻  Credits", 5, lambda: self.show_screen("credits"))

        ctk.CTkLabel(
            self.sidebar, text="Personalize sua experiência", 
            font=ctk.CTkFont(size=10), 
            text_color=self.colors["text_muted"], 
            wraplength=150
        ).grid(row=11, column=0, padx=15, pady=15, sticky="sw")

    def create_nav_button(self, text, row, command):
        button = ctk.CTkButton(
            self.sidebar, text=text, fg_color="transparent", 
            text_color=self.colors["text_main"], hover_color=self.colors["bg_card"], 
            anchor="w", height=42, corner_radius=8, 
            font=ctk.CTkFont(size=13), command=command
        )
        button.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        return button

    # ---------------------------------------------------------
    # Personalização
    # ---------------------------------------------------------
    def change_theme(self, new_theme_name):
        if new_theme_name not in THEMES or new_theme_name == self.current_theme_name: return
        self.settings["theme"] = new_theme_name
        self.current_theme_name = new_theme_name
        self._save_personalization()
        self._schedule_ui_refresh(f"Tema alterado para: {new_theme_name}")

    def change_background(self, new_background_name):
        if new_background_name not in BACKGROUNDS or new_background_name == self.current_background_name: return
        self.settings["background"] = new_background_name
        self.current_background_name = new_background_name
        self._save_personalization()
        self._schedule_ui_refresh(f"Fundo selecionado: {new_background_name}")

    def change_supercharge(self, new_supercharge_name):
        if new_supercharge_name not in SUPERCHARGES or new_supercharge_name == self.current_supercharge_name: return
        self.settings["supercharge"] = new_supercharge_name
        self.current_supercharge_name = new_supercharge_name
        self._save_personalization()
        self._schedule_ui_refresh(f"Supercharge alterado para: {new_supercharge_name}")

    def _save_personalization(self):
        try:
            save_settings(self.settings)
        except (OSError, TypeError, ValueError) as exc:
            log.error(f"Não foi possível salvar as configurações: {exc}")
            if hasattr(self, "update_status"):
                self.update_status("Erro ao salvar configurações. Veja o log.", is_error=True)

    # ---------------------------------------------------------
    # Mod Manager
    # ---------------------------------------------------------
    def build_mods_screen(self):
        self.mods_screen = ctk.CTkFrame(self.screen_container, fg_color="transparent", corner_radius=0)
        self.mods_screen.grid_columnconfigure(0, weight=1)
        self.mods_screen.grid_columnconfigure(1, weight=2)
        self.mods_screen.grid_columnconfigure(2, weight=0)
        self.mods_screen.grid_rowconfigure(0, weight=1)

        if hasattr(self, "setup_left_sidebar"): self.setup_left_sidebar(self.mods_screen)
        if hasattr(self, "setup_center_tree"): self.setup_center_tree(self.mods_screen)
        if hasattr(self, "setup_right_sidebar"): self.setup_right_sidebar(self.mods_screen)

    # ---------------------------------------------------------
    # Componentes reutilizáveis (Usados pelo Settings e System)
    # ---------------------------------------------------------
    def _build_screen_heading(self, parent, title, subtitle):
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=25, weight="bold"), text_color=self.colors["text_main"]).pack(anchor="w", padx=20, pady=(22, 4))
        ctk.CTkLabel(parent, text=subtitle, font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"], wraplength=800, justify="left").pack(anchor="w", padx=20, pady=(0, 12))

    def _create_settings_group(self, parent, title, description):
        group = ctk.CTkFrame(parent, fg_color=self.colors["bg_panel"], border_width=1, border_color=self.colors["border"], corner_radius=10)
        group.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(group, text=title, font=ctk.CTkFont(size=15, weight="bold"), text_color=self.colors["text_main"]).pack(anchor="w", padx=15, pady=(12, 3))
        ctk.CTkLabel(group, text=description, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"], wraplength=700, justify="left").pack(anchor="w", padx=15, pady=(0, 5))
        return group

    # ---------------------------------------------------------
    # Navegação e Refresh
    # ---------------------------------------------------------
    def show_screen(self, screen_name):
        screens = {
            "mods": getattr(self, "mods_screen", None), 
            "settings": getattr(self, "settings_screen", None), 
            "system": getattr(self, "system_screen", None),
            "credits": getattr(self, "credits_screen", None) # <-- NOVO
        }
        
        if screen_name not in screens or screens[screen_name] is None: return

        for screen in screens.values():
            if screen is not None: screen.grid_forget()

        screens[screen_name].grid(row=0, column=0, sticky="nsew")
        self.current_screen = screen_name

        titles = {
            "mods": "Mod Manager", 
            "settings": "Settings", 
            "system": "Manager System",
            "credits": "Créditos" # <-- NOVO
        }
        if hasattr(self, "header") and hasattr(self.header, "lbl_current_screen"):
            self.header.lbl_current_screen.configure(text=titles[screen_name])
            
    def _schedule_ui_refresh(self, message):
        pending = getattr(self, "_ui_refresh_id", None)
        if pending is not None:
            try: self.after_cancel(pending)
            except (ValueError, RuntimeError): pass
        self._ui_refresh_id = self.after(350, lambda: self._finish_ui_refresh(message))

    def _finish_ui_refresh(self, message):
        """Reconstrói a interface e retorna à tela de configurações."""
        self._ui_refresh_id = None

        try:
            if not self.winfo_exists():
                return
        except (tk.TclError, AttributeError, NameError):
            return

        if hasattr(self, 'theme_selector'): self.theme_selector.configure(state="disabled")
        if hasattr(self, 'background_selector'): self.background_selector.configure(state="disabled")
        if hasattr(self, 'supercharge_selector'): self.supercharge_selector.configure(state="disabled")

        self._render_ui()
        self.show_screen("settings")

        if hasattr(self, "update_status"):
            self.update_status(message)