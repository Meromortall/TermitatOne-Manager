import customtkinter as ctk
from utils.logs.rise_logger import log

class SystemViewMixin:
    def build_system_screen(self):
        """Cria a tela de ferramentas administrativas."""
        self.system_screen = ctk.CTkFrame(
            self.screen_container, fg_color="transparent", corner_radius=0,
        )
        self.system_screen.grid_columnconfigure(0, weight=1)

        self._build_screen_heading(
            self.system_screen, "Manager System", 
            "Acesso às pastas e às ferramentas do aplicativo."
        )

        # Grupo de Pastas
        folders_group = self._create_settings_group(
            self.system_screen, "Pastas do sistema", "Acesse os diretórios utilizados pelo manager.",
        )
        ctk.CTkButton(
            folders_group, text="📂  Abrir AppData do Termitato",
            fg_color=self.colors["button"], hover_color=self.colors["button_hover"],
            text_color=self.colors["text_main"], anchor="w", command=self.open_manager_folder,
        ).pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkButton(
            folders_group, text="📂  Abrir pasta do jogo",
            fg_color=self.colors["button"], hover_color=self.colors["button_hover"],
            text_color=self.colors["text_main"], anchor="w", command=self.open_game_folder,
        ).pack(fill="x", padx=15, pady=(5, 15))

        # Danger Zone
        danger_group = self._create_settings_group(
            self.system_screen, "Zona de perigo", "Operações potencialmente destrutivas.",
        )
        ctk.CTkLabel(
            danger_group, text="Use o reset apenas se realmente desejar restaurar os dados do manager.",
            text_color=self.colors["text_muted"], wraplength=650, justify="left",
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkButton(
            danger_group, text="Factory Reset — Apagar dados",
            fg_color="transparent", hover_color=self.colors["bg_card"],
            border_width=1, border_color=self.colors["danger"], text_color=self.colors["danger"],
            command=self.factory_reset,
        ).pack(anchor="w", padx=15, pady=(5, 15))