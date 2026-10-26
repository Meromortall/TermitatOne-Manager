import customtkinter as ctk
import webbrowser
from utils.logs.rise_logger import log

class CreditsViewMixin:
    def build_credits_screen(self):
        """Cria a tela de créditos e agradecimentos."""
        self.credits_screen = ctk.CTkScrollableFrame(
            self.screen_container, fg_color="transparent", corner_radius=0,
        )
        self.credits_screen.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        self._build_screen_heading(
            self.credits_screen, "Créditos", 
            "Conheça o projeto, a comunidade e os agradecimentos especiais."
        )

        # --- GRUPO 1: SOBRE O PROJETO ---
        group_about = self._create_settings_group(
            self.credits_screen, "Termitat One Manager", 
            "Um gerenciador de mods feito por fãs, para fãs."
        )
        
        ctk.CTkLabel(
            group_about, 
            text="Versão 3.2 (Build Final)", 
            font=ctk.CTkFont(size=14, weight="bold"), 
            text_color=self.colors["accent"]
        ).pack(anchor="w", padx=15, pady=(5, 5))
        
        ctk.CTkLabel(
            group_about, 
            text=(
                "Este software foi desenvolvido de forma independente para facilitar "
                "a vida dos modders de Fear & Hunger. Ele conta com um motor de "
                "backup seguro, resolução inteligente de arquivos e suporte a "
                "múltiplos formatos (ZIP, RAR, 7z)."
            ),
            text_color=self.colors["text_muted"], wraplength=700, justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            group_about, 
            text="⚠️ Este produto foi feito com auxílio de Inteligência Artificial e não possui fins lucrativos.",
            font=ctk.CTkFont(weight="bold"), text_color=self.colors["warning"], wraplength=700, justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # --- GRUPO 2: COMUNIDADE E LINKS ---
        group_links = self._create_settings_group(
            self.credits_screen, "Comunidade e Suporte", 
            "Acesse o código-fonte ou junte-se à conversa."
        )
        
        # Funções para abrir links
        def open_github():
            webbrowser.open("https://github.com/Meromortall/TermitatOne-Manager")
        def open_discord():
            webbrowser.open("https://discord.gg/g73ndKfUMk")

        ctk.CTkButton(
            group_links, text="🐙 Repositório no GitHub", 
            fg_color=self.colors["button"], hover_color=self.colors["button_hover"],
            text_color=self.colors["text_main"], anchor="w", command=open_github
        ).pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(
            group_links, text="💬 Servidor do Discord", 
            fg_color=self.colors["button"], hover_color=self.colors["button_hover"],
            text_color=self.colors["text_main"], anchor="w", command=open_discord
        ).pack(fill="x", padx=15, pady=(5, 15))

        # --- GRUPO 3: AGRADECIMENTOS ESPECIAIS ---
        group_thanks = self._create_settings_group(
            self.credits_screen, "Agradecimentos Especiais", 
            "Sem estas pessoas e projetos, nada disso seria possível."
        )
        
        thanks_text = (
            "• Miro Haverinen — Criador de Fear & Hunger 1 e 2: Termina.\n"
            "• A comunidade de modders do Fear & Hunger.\n"
            "• Desenvolvedores do CustomTkinter, Pillow, py7zr e rarfile.\n"
            "• A todos os fãs que mantêm o jogo vivo até hoje."
        )
        ctk.CTkLabel(
            group_thanks, text=thanks_text, text_color=self.colors["text_main"], 
            justify="left", wraplength=700
        ).pack(anchor="w", padx=15, pady=(0, 5))

        # --- GRUPO 4: DIREITOS AUTORAIS ---
        group_legal = self._create_settings_group(
            self.credits_screen, "Aviso Legal", 
            "Direitos autorais e propriedade intelectual."
        )
        
        legal_text = (
            "Fear & Hunger e Fear & Hunger 2: Termina são marcas registradas e "
            "todos os direitos reservados a Miro Haverinen. Este gerenciador não "
            "possui vínculo oficial com o criador do jogo. Todos os mods instalados "
            "são de responsabilidade de seus respectivos autores."
        )
        ctk.CTkLabel(
            group_legal, text=legal_text, text_color=self.colors["text_muted"], 
            justify="left", wraplength=700
        ).pack(anchor="w", padx=15, pady=(0, 15))