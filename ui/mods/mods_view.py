import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from ui.mods.mod_card import ModCard
from ui.state.game_state import format_size, make_game_key
from utils.logs.rise_logger import log


class ModsViewMixin:
    """Gerencia a lista de mods, a pesquisa e o seletor de jogos."""

    def setup_left_sidebar(self, parent):
        """Cria o painel de pesquisa, seleção de jogo e lista de mods."""
        self.left_panel = ctk.CTkFrame(parent, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Título do Seletor
        ctk.CTkLabel(
            self.left_panel,
            text="JOGO ATIVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_muted"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        # Seletor de jogo.
        self.game_buttons_container = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.game_buttons_container.pack(fill="x", pady=(0, 20))

        self.game_buttons = {}
        self.game_buttons_container.grid_columnconfigure(0, weight=1)

        # Pesquisa
        saved_query = getattr(self, "_saved_mod_query", "")
        self.search_var = tk.StringVar(value=saved_query)
        self.search_var.trace_add("write", lambda *_: self.filter_list())

        self.search_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="🔍 Buscar mod...",
            textvariable=self.search_var,
            fg_color=self.colors["bg_card"],
            border_color=self.colors["border"],
            text_color=self.colors["text_main"],
            placeholder_text_color=self.colors["text_muted"],
            height=40,
            corner_radius=8
        )
        self.search_entry.pack(fill="x", pady=(0, 15))

        # Lista rolável.
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color=self.colors["bg_panel"],
            corner_radius=8,
        )
        self.scroll_frame.pack(fill="both", expand=True)
        self.mod_cards = []

        # Reconstrói os botões se os jogos já estiverem carregados.
        if getattr(self, "games", None):
            self.update_game_buttons()

        self.filter_list()

    def update_game_buttons(self):
        """Atualiza os botões de seleção dos jogos detectados."""
        if not hasattr(self, "game_buttons_container"):
            return

        for widget in self.game_buttons_container.winfo_children():
            widget.destroy()
        self.game_buttons.clear()

        games = getattr(self, "games", None)
        if not games:
            return

        game_names = list(games.keys())

        for column in range(len(game_names)):
            self.game_buttons_container.grid_columnconfigure(column, weight=1)

        ui_dir = Path(__file__).resolve().parent.parent
        icon_dir = ui_dir / "gui_ico"

        for index, game_name in enumerate(game_names):
            is_active = (
                getattr(self, "current_game_key", None) == make_game_key(game_name)
            )

            # Cores temáticas específicas dos jogos
            if "Termina" in game_name:
                game_color, game_hover = "#564037", "#6C5045"
            else:
                game_color, game_hover = "#444340", "#5A5956"

            if is_active:
                button_color = game_color
                text_color = "#FFFFFF"
                border_color = self.colors["accent"]
                border_width = 2
                hover_color = game_hover
            else:
                button_color = self.colors["bg_card"]
                text_color = self.colors["text_muted"]
                border_color = self.colors["bg_card"]
                border_width = 1
                hover_color = self.colors["border"]

            icon_name = "funger2termina.ico" if "Termina" in game_name else "fearandhunger.ico"
            icon_path = icon_dir / icon_name
            image = None

            if icon_path.is_file():
                try:
                    with Image.open(icon_path) as source:
                        icon_image = source.convert("RGBA")
                    image = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(48, 48))
                except (OSError, ValueError) as exc:
                    log.warning(f"Falha ao carregar o ícone '{icon_path}': {exc}")

            # O texto que aparece no botão
            display_text = f"✓ {game_name}" if is_active else game_name

            button = ctk.CTkButton(
                self.game_buttons_container,
                text=display_text, # <-- Texto já está no botão
                image=image,
                compound="top",
                fg_color=button_color,
                border_width=border_width,
                border_color=border_color,
                text_color=text_color,
                hover_color=hover_color,
                font=ctk.CTkFont(weight="bold", size=12),
                height=100,
                corner_radius=8,
                command=lambda name=game_name: self.change_game(name),
            )
            button.grid(
                row=0,
                column=index,
                padx=(0, 10) if index < len(game_names) - 1 else (0, 0),
                sticky="ew",
            )
            self.game_buttons[game_name] = button
            # A chamada do _bind_tooltip foi DELETADA daqui! O bug foi embora.

    def filter_list(self):
        """Filtra os mods pelo nome digitado."""
        if not hasattr(self, "search_var"):
            return

        query = self.search_var.get().strip().casefold()
        self._saved_mod_query = self.search_var.get()
        all_mods = getattr(self, "all_mods", [])

        self.filtered_mods = [
            mod for mod in all_mods
            if query in str(mod.get("name", "")).casefold()
        ]
        self.populate_list()

    def populate_list(self):
        """Reconstrói os cartões correspondentes aos mods filtrados."""
        if not hasattr(self, "scroll_frame"):
            return

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not hasattr(self, "mod_cards"):
            self.mod_cards = []
        else:
            self.mod_cards.clear()

        filtered_mods = getattr(self, "filtered_mods", [])
        
        if not filtered_mods:
            empty_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty_frame.pack(pady=40, fill="x")
            
            ctk.CTkLabel(empty_frame, text="🔍", font=ctk.CTkFont(size=40)).pack()
            ctk.CTkLabel(
                empty_frame, text="Nenhum mod encontrado",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.colors["text_main"],
            ).pack(pady=(5, 2))
            ctk.CTkLabel(
                empty_frame, text="Tente buscar por outro nome.",
                font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"],
            ).pack()
            return

        selected_mod = getattr(self, "selected_mod", None)
        selected_name = selected_mod.get("name") if isinstance(selected_mod, dict) else None

        for mod in filtered_mods:
            card = ModCard(
                master=self.scroll_frame,
                mod_data=mod,
                on_select=self.select_mod,
                on_menu=self.show_context_menu,
                format_size_func=format_size,
                theme_colors=self.colors, 
            )
            is_selected = (selected_name is not None and selected_name == mod.get("name"))
            card.set_selected(is_selected)
            self.mod_cards.append(card)