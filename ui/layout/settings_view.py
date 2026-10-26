import customtkinter as ctk
from pathlib import Path
from PIL import Image

from ui.state.theme_manager import (
    THEMES, BACKGROUNDS, SUPERCHARGES, get_background_config
)
from utils.logs.rise_logger import log

class SettingsViewMixin:
    def build_settings_screen(self):
        """Cria a tela de personalização do Termitato."""
        self.settings_screen = ctk.CTkScrollableFrame(
            self.screen_container, fg_color="transparent", corner_radius=0,
        )
        self.settings_screen.grid_columnconfigure(0, weight=1)

        self._build_screen_heading(
            self.settings_screen, "Configurações", 
            "Personalize a aparência e o comportamento do manager."
        )

        # Tema base.
        theme_group = self._create_settings_group(
            self.settings_screen, "01  •  Themes", "Escolha a paleta visual da aplicação.",
        )
        ctk.CTkLabel(theme_group, text="Tema visual", text_color=self.colors["text_main"]).pack(anchor="w", padx=15, pady=(12, 4))

        self.theme_selector = ctk.CTkOptionMenu(
            theme_group, values=list(THEMES.keys()),
            fg_color=self.colors["accent"], button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            text_color=self.colors.get("button_text", self.colors["text_main"]),
            command=self.change_theme,
        )
        self.theme_selector.set(self.current_theme_name)
        self.theme_selector.pack(anchor="w", padx=15, pady=(0, 15))

        # Fundos.
        background_group = self._create_settings_group(
            self.settings_screen, "02  •  Backgrounds", "Escolha um cenário para visualizar e ambientar o manager.",
        )
        ctk.CTkLabel(background_group, text="Cenário", text_color=self.colors["text_main"]).pack(anchor="w", padx=15, pady=(12, 4))

        self.background_selector = ctk.CTkOptionMenu(
            background_group, values=list(BACKGROUNDS.keys()),
            fg_color=self.colors["accent"], button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            text_color=self.colors.get("button_text", self.colors["text_main"]),
            command=self.change_background,
        )
        self.background_selector.set(self.current_background_name)
        self.background_selector.pack(anchor="w", padx=15, pady=(0, 12))

        self._build_background_preview(background_group)

        # Supercharges.
        supercharge_group = self._create_settings_group(
            self.settings_screen, "03  •  Supercharges", "Experiências especiais que podem complementar o tema.",
        )
        ctk.CTkLabel(supercharge_group, text="Experiência especial", text_color=self.colors["text_main"]).pack(anchor="w", padx=15, pady=(12, 4))

        self.supercharge_selector = ctk.CTkOptionMenu(
            supercharge_group, values=list(SUPERCHARGES.keys()),
            fg_color=self.colors["accent"], button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            text_color=self.colors.get("button_text", self.colors["text_main"]),
            command=self.change_supercharge,
        )
        self.supercharge_selector.set(self.current_supercharge_name)
        self.supercharge_selector.pack(anchor="w", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            supercharge_group,
            text="Os efeitos animados serão adicionados gradualmente. Nesta etapa, o sistema especial fornece uma paleta própria.",
            text_color=self.colors["text_muted"], wraplength=650, justify="left",
        ).pack(anchor="w", padx=15, pady=(0, 15))

    def _build_background_preview(self, parent):
        """Mostra uma prévia do cenário selecionado."""
        config = get_background_config(self.current_background_name)
        image_relative_path = config.get("image")

        if not image_relative_path:
            ctk.CTkLabel(parent, text="Nenhum fundo selecionado.", text_color=self.colors["text_muted"]).pack(anchor="w", padx=15, pady=(0, 15))
            return

        project_root = Path(__file__).resolve().parents[2]
        image_path = project_root / image_relative_path

        if not image_path.is_file():
            log.warning(f"Imagem de fundo não encontrada: {image_path}")
            ctk.CTkLabel(parent, text=f"Não foi possível encontrar a imagem:\n{image_path}", text_color=self.colors["warning"], justify="left", wraplength=650).pack(anchor="w", padx=15, pady=(0, 15))
            return

        try:
            with Image.open(image_path) as source:
                preview_image = source.convert("RGB")
            self._background_preview_image = ctk.CTkImage(light_image=preview_image, dark_image=preview_image, size=(520, 220))
            ctk.CTkLabel(parent, text="", image=self._background_preview_image, fg_color="transparent").pack(anchor="w", padx=15, pady=(0, 15))
        except (OSError, ValueError) as exc:
            log.error(f"Erro ao carregar prévia do fundo: {exc}")
            ctk.CTkLabel(parent, text="Não foi possível carregar a prévia deste cenário.", text_color=self.colors["danger"]).pack(anchor="w", padx=15, pady=(0, 15))