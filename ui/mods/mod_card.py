import customtkinter as ctk

class ModCard(ctk.CTkFrame):
    def __init__(self, master, mod_data, on_select, on_menu, format_size_func, theme_colors, **kwargs):
        # A MÁGICA AQUI: height=60 limita o tamanho do card
        super().__init__(master, height=60, **kwargs)
        self.mod_data = mod_data
        self.theme_colors = theme_colors # Guarda as cores para o set_selected
        
        # Puxa as cores do tema atual
        accent = theme_colors.get("accent", "#00E676")
        danger = theme_colors.get("danger", "#D32F2F")
        text_muted = theme_colors.get("text_muted", "#A0A0A0")
        text_main = theme_colors.get("text_main", "#FFFFFF")
        
        self.configure(fg_color="transparent", corner_radius=5)
        # O pack para preencher a largura da lista fica aqui
        self.pack(fill="x", pady=2, padx=2)
        
        # Impede que o frame mude de tamanho para preencher o vazio
        self.pack_propagate(False) 

        # --- BARRA LATERAL DE SELEÇÃO ---
        self.selection_bar = ctk.CTkFrame(self, width=4, corner_radius=2, fg_color="transparent")
        self.selection_bar.pack(side="left", fill="y", padx=(0, 5))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # --- FUNÇÃO AUXILIAR DE CLIQUE ---
        def bind_click(widget):
            widget.bind("<Button-1>", lambda e: on_select(mod_data))
            widget.bind("<Button-3>", lambda e: on_menu(e, mod_data))

        bind_click(self)
        bind_click(content)

        # Checkbox (Apenas visual de status)
        cb = ctk.CTkCheckBox(content, text="", width=20, fg_color=accent, hover_color=accent, state="disabled")
        if mod_data["installed"]: 
            cb.select()
        cb.pack(side="left")
        bind_click(cb)

        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        bind_click(text_frame)

        # Nome do Mod (Agora com cor dinâmica!)
        lbl_name = ctk.CTkLabel(
            text_frame, 
            text=mod_data["name"], 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color=text_main, 
            anchor="w"
        )
        lbl_name.pack(fill="x")
        bind_click(lbl_name)

        # --- STATUS E TAMANHO ---
        size_str = format_size_func(mod_data.get("size", 0))
        file_count = len(mod_data.get('files', []))
        
        in_catalog = mod_data.get("in_catalog", True)
        
        if mod_data["installed"]:
            status_txt = f"Instalado • {file_count} arq • {size_str}"
            status_color = accent
        else:
            if not in_catalog:
                status_txt = f"⚠️ ZIP Ausente • {file_count} arq"
                status_color = danger
            else:
                status_txt = f"Não Instalado • {file_count} arq • {size_str}"
                status_color = text_muted
        
        lbl_status = ctk.CTkLabel(text_frame, text=status_txt, font=ctk.CTkFont(size=11), text_color=status_color, anchor="w")
        lbl_status.pack(fill="x")
        bind_click(lbl_status)

    def set_selected(self, is_selected):
        """Muda a cor de fundo e a barra lateral quando o mod é selecionado."""
        if is_selected:
            # Usa a cor do card do tema para o fundo e a cor de destaque para a barra
            self.configure(fg_color=self.theme_colors.get("bg_card", "#2A2A2A"))
            self.selection_bar.configure(fg_color=self.theme_colors.get("accent", "#00E676"))
        else:
            self.configure(fg_color="transparent")
            self.selection_bar.configure(fg_color="transparent")