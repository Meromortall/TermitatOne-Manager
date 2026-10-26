import customtkinter as ctk
from utils.logs.rise_logger import log


class HeaderComponent:
    def __init__(self, master, app_instance):
        self.app = app_instance
        colors = self.app.colors

        accent = colors.get("accent", "#00E676")
        accent_hover = colors.get("accent_hover", "#00B248")
        button_text = colors.get("button_text", "#000000")

        # Container principal do Cabeçalho
        self.frame = ctk.CTkFrame(
            master,
            height=60,
            corner_radius=0,
            fg_color="transparent"
        )
        self.frame.pack_propagate(False) # Impede que os botões mudem a altura

        self.bottom_border = ctk.CTkFrame(
            self.frame,
            height=1,
            corner_radius=0,
            fg_color=colors["border"]
        )
        self.bottom_border.pack(side="bottom", fill="x")

        # Título da tela atual (alinhado verticalmente)
        self.lbl_current_screen = ctk.CTkLabel(
            self.frame,
            text="Mod Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=colors["text_main"]
        )
        self.lbl_current_screen.pack(
            side="left",
            padx=25,
            pady=15
        )

        # Container para agrupar os botões da direita
        self.actions_frame = ctk.CTkFrame(
            self.frame, 
            fg_color="transparent"
        )
        self.actions_frame.pack(side="right", padx=15, pady=12)

        # Botão para abrir a pasta do jogo (Ação secundária)
        self.btn_open_folder = ctk.CTkButton(
            self.actions_frame,
            text="📂 Abrir Pasta",
            fg_color="transparent",
            border_width=1,
            border_color=colors["border"],
            text_color=colors["text_muted"],
            hover_color=colors["bg_card"],
            height=32,
            command=self.app.open_game_folder
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))

        # Botão para iniciar o jogo (Ação primária - Destaque)
        self.btn_play = ctk.CTkButton(
            self.actions_frame,
            text="▶ Iniciar Jogo",
            fg_color=accent,
            text_color=button_text,
            hover_color=accent_hover,
            height=32,
            font=ctk.CTkFont(weight="bold"),
            command=self.app.launch_game
        )
        self.btn_play.pack(side="left")