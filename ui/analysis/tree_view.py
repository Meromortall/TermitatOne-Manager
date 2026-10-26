import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ui.state.game_state import format_size, DATA_ROOT
from utils.logs.rise_logger import log

class AnalysisTreeMixin:
    # ==========================================
    # COLUNA CENTRAL: ÁRVORE DE ARQUIVOS
    # ==========================================
    def setup_center_tree(self, parent):
        # Puxa as cores do tema atual
        colors = self.colors
        
        self.center_panel = ctk.CTkFrame(
            parent, 
            fg_color=colors["bg_panel"], 
            border_width=1, 
            border_color=colors["border"],
            corner_radius=8
        )
        self.center_panel.grid(row=0, column=1, padx=5, pady=15, sticky="nsew")

        ctk.CTkLabel(
            self.center_panel, 
            text="Estrutura de Arquivos", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["text_main"]
        ).pack(anchor="w", padx=15, pady=15)

        # Estilização da Árvore (Treeview) Dinâmica
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
            background=colors["bg_main"], 
            foreground=colors["text_main"], 
            fieldbackground=colors["bg_main"], 
            font=("Consolas", 11), 
            borderwidth=0, 
            rowheight=26 # Um pouco mais alto para respirar
        )
        style.configure("Treeview.Heading", 
            background=colors["bg_panel"], 
            foreground=colors["text_main"], 
            font=("Segoe UI", 11, "bold"), 
            borderwidth=0
        )
        style.map("Treeview", 
            background=[("selected", colors["accent"])], 
            foreground=[("selected", colors.get("button_text", "#000000"))] # <-- CORRIGIDO
        )
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        tree_container = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tree = ttk.Treeview(tree_container, selectmode="browse", show="tree")
        self.tree.pack(side="left", fill="both", expand=True)
        
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview, fg_color=colors["bg_main"])
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree_nodes = {}
        self.tree.insert("", "end", text="Nenhum mod selecionado.", tags=("empty",))
        self.tree.tag_configure("empty", foreground=colors["text_muted"], font=("Segoe UI", 12, "italic"))

    def clear_tree_view(self):
        """Limpa a árvore e reseta os painéis quando um mod é deletado."""
        if hasattr(self, "tree"):
            self.tree.delete(*self.tree.get_children())
            self.tree.insert("", "end", text="Nenhum mod selecionado.", tags=("empty",))
            
        if hasattr(self, "lbl_mod_name"):
            self.lbl_mod_name.configure(text="Nenhum selecionado")
        if hasattr(self, "lbl_mod_size"):
            self.lbl_mod_size.configure(text="Arquivos: -")
        if hasattr(self, "btn_install"):
            self.btn_install.configure(state="disabled", fg_color=self.colors["bg_card"])
        if hasattr(self, "btn_uninstall"):
            self.btn_uninstall.configure(state="disabled", border_color=self.colors["border"], text_color=self.colors["text_muted"])

    def on_tree_double_click(self, event):
        """Evento para abrir o comparador JSON."""
        item = self.tree.selection()
        if not item: return
        
        selected_node = item[0]
        path_parts = []
        current = selected_node
        
        while current:
            text = self.tree.item(current, "text")
            clean_text = text.split(" ", 1)[1] if " " in text else text
            path_parts.insert(0, clean_text)
            current = self.tree.parent(current)
            
        full_path = "/".join(path_parts)
        
        if full_path.lower().endswith(".json"):
            if hasattr(self, 'show_json_comparison'):
                self.show_json_comparison(full_path)
        else:
            self.update_status(f"Visualização de {full_path} não suportada ainda.", is_error=False)

    # ==========================================
    # COLUNA DIREITA: AÇÕES HIERÁRQUICAS
    # ==========================================
    def setup_right_sidebar(self, parent):
        colors = self.colors
        
        self.right_panel = ctk.CTkScrollableFrame(parent, fg_color="transparent", width=230)
        self.right_panel.grid(row=0, column=2, padx=(5, 15), pady=15, sticky="nsew")

        # ------------------------------------------
        # GRUPO 1: ADICIONAR MOD (Ação Primária)
        # ------------------------------------------
        add_frame = ctk.CTkFrame(self.right_panel, fg_color=colors["bg_panel"], border_width=1, border_color=colors["border"], corner_radius=8)
        add_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(add_frame, text="Adicionar Novo Mod", font=ctk.CTkFont(weight="bold"), text_color=colors["accent"]).pack(pady=(12, 5))
        
        ctk.CTkButton(add_frame, text="+ Arquivo ZIP/RAR/7z", fg_color=colors["accent"], text_color=colors["button_text"], hover_color=colors["accent_hover"], height=40, font=ctk.CTkFont(weight="bold"), command=self.add_zip).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(add_frame, text="+ Pasta do Mod", fg_color=colors["bg_card"], hover_color=colors["border"], text_color=colors["text_main"], height=40, command=self.add_folder).pack(fill="x", padx=10, pady=(5, 12))

        # ------------------------------------------
        # GRUPO 2: GERENCIAR MOD
        # ------------------------------------------
        manage_frame = ctk.CTkFrame(self.right_panel, fg_color=colors["bg_panel"], border_width=1, border_color=colors["border"], corner_radius=8)
        manage_frame.pack(fill="x", pady=10)
        
        self.lbl_mod_name = ctk.CTkLabel(manage_frame, text="Nenhum selecionado", font=ctk.CTkFont(size=13, weight="bold"), wraplength=180, text_color=colors["text_main"])
        self.lbl_mod_name.pack(pady=(12, 2))
        self.lbl_mod_size = ctk.CTkLabel(manage_frame, text="Arquivos: -", text_color=colors["text_muted"], font=ctk.CTkFont(size=11))
        self.lbl_mod_size.pack(pady=(0, 12))

        self.btn_install = ctk.CTkButton(manage_frame, text="Instalar Mod", height=35, fg_color=colors["accent"], text_color=colors["button_text"], hover_color=colors["accent_hover"], font=ctk.CTkFont(weight="bold"), command=self.install_selected, state="disabled")
        self.btn_install.pack(fill="x", padx=10, pady=(0, 5))
        
        self.btn_uninstall = ctk.CTkButton(manage_frame, text="Desinstalar", height=35, fg_color="transparent", border_width=1, border_color=colors["danger"], text_color=colors["danger"], state="disabled", command=self.uninstall_selected)
        self.btn_uninstall.pack(fill="x", padx=10, pady=(0, 12))

        # ------------------------------------------
        # GRUPO 3: PRESETS
        # ------------------------------------------
        preset_frame = ctk.CTkFrame(self.right_panel, fg_color=colors["bg_panel"], border_width=1, border_color=colors["border"], corner_radius=8)
        preset_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(preset_frame, text="Presets (Perfis)", font=ctk.CTkFont(weight="bold"), text_color=colors["text_main"]).pack(pady=(12, 5))
        
        self.preset_selector = ctk.CTkOptionMenu(preset_frame, values=["Nenhum"], fg_color=colors["bg_card"], button_color=colors["border"], text_color=colors["text_main"], command=self.apply_preset)
        self.preset_selector.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(preset_frame, text="Salvar Novo Preset", fg_color="transparent", border_width=1, border_color=colors["text_muted"], text_color=colors["text_muted"], command=self.save_preset_dialog).pack(fill="x", padx=10, pady=(0, 12))

        # ------------------------------------------
        # GRUPO 4: FERRAMENTAS E UTILS
        # ------------------------------------------
        utils_frame = ctk.CTkFrame(self.right_panel, fg_color=colors["bg_panel"], border_width=1, border_color=colors["border"], corner_radius=8)
        utils_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(utils_frame, text="Ferramentas", font=ctk.CTkFont(weight="bold"), text_color=colors["text_muted"]).pack(pady=(12, 5))
        
        self.btn_gen_inv = ctk.CTkButton(utils_frame, text="⚙️ Gerar Gabarito", height=32, fg_color=colors["warning"], hover_color=colors["accent_hover"], text_color=colors["button_text"], command=self.generate_inventory)
        self.btn_gen_inv.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(utils_frame, text="Validar Tudo (Hashes)", fg_color="transparent", text_color=colors["text_main"], hover_color=colors["bg_card"], anchor="w", command=self.validate_all_mods).pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(utils_frame, text="Limpar Arquivos Faltando", fg_color="transparent", text_color=colors["text_main"], hover_color=colors["bg_card"], anchor="w", command=self.clean_missing_files).pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(utils_frame, text="Re-scan Cache do Jogo", fg_color="transparent", text_color=colors["text_main"], hover_color=colors["bg_card"], anchor="w", command=self.generate_inventory).pack(fill="x", padx=10, pady=(2, 12))

    def update_inventory_button(self):
        """Mostra ou esconde o botão de gerar inventário."""
        if hasattr(self, "btn_gen_inv"):
            if not getattr(self, "has_inventory", False):
                self.btn_gen_inv.pack(fill="x", padx=10, pady=5, before=self.btn_gen_inv.master.winfo_children()[2])
            else:
                self.btn_gen_inv.pack_forget()
                
    # ==========================================
    # LÓGICA DE SELEÇÃO E ÁRVORE
    # ==========================================
    def select_mod(self, mod):
        """Atualiza a interface quando um mod é clicado."""
        colors = self.colors
        self.selected_mod = mod
        self.populate_list() 
        
        self.lbl_mod_name.configure(text=mod["name"])

        size_str = format_size(mod.get("size", 0))
        self.lbl_mod_size.configure(text=f"Arquivos: {len(mod['files'])} • {size_str}")

        if mod["installed"]:
            self.btn_install.configure(state="disabled", fg_color=colors["bg_card"], text_color=colors["text_muted"], text="Já Instalado")
            self.btn_uninstall.configure(state="normal", text_color=colors["danger"], border_color=colors["danger"])
        else:
            self.btn_install.configure(state="normal", fg_color=colors["accent"], text_color=colors["button_text"], text="Instalar Mod")
            self.btn_uninstall.configure(state="disabled", text_color=colors["text_muted"], border_color=colors["border"])

        self.build_tree(mod.get("files", []))

    def build_tree(self, file_list):
        """Constrói a árvore de diretórios visual."""
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes.clear()
        
        if not file_list: 
            self.tree.insert("", "end", text="Nenhum arquivo listado para este mod.", tags=("empty",))
            return

        for filepath in file_list:
            parts = Path(filepath).parts
            current_path = ""
            for i, part in enumerate(parts):
                parent_path = current_path
                current_path = str(Path(current_path) / part) if current_path else part
                
                if current_path not in self.tree_nodes:
                    is_file = (i == len(parts) - 1)
                    ext = Path(part).suffix.lower()
                    
                    if is_file:
                        prefix = "📄 " if ext == ".json" else "🖼️ " if ext in [".png", ".jpg"] else "📜 " if ext == ".js" else "📄 "
                    else:
                        prefix = "📁 "
                        
                    parent_id = self.tree_nodes[parent_path] if parent_path else ""
                    self.tree_nodes[current_path] = self.tree.insert(parent_id, "end", text=f"{prefix}{part}", open=True)

    # ==========================================
    # LÓGICA DE PRESETS
    # ==========================================
    def update_preset_menu(self):
        """Atualiza a lista de presets na tela."""
        from core.mod_manager.preset_ops import load_presets
        
        if hasattr(self, 'preset_selector') and self.current_game_key:
            presets = load_presets(DATA_ROOT, self.current_game_key)
            nomes = list(presets.keys())
            if not nomes:
                nomes = ["Nenhum preset salvo"]
            self.preset_selector.configure(values=nomes)
            self.preset_selector.set(nomes[0])

    def save_preset_dialog(self):
        """Pede o nome do preset e salva os mods atuais."""
        from tkinter import simpledialog
        from core.mod_manager.preset_ops import add_preset
        
        if not self.current_game_key:
            return
            
        nome = simpledialog.askstring("Salvar Preset", "Dê um nome para este perfil (ex: 'Modo Hardcore'):", parent=self)
        if not nome: return
        
        mods_instalados = [m["name"] for m in self.all_mods if m["installed"]]
        if not mods_instalados:
            messagebox.showwarning("Aviso", "Não há mods instalados para salvar neste preset.")
            return
            
        try:
            add_preset(DATA_ROOT, self.current_game_key, nome, mods_instalados)
            self.update_preset_menu()
            self.update_status(f"Preset '{nome}' salvo com sucesso.")
            messagebox.showinfo("Sucesso", f"Preset '{nome}' salvo com {len(mods_instalados)} mods!")
        except Exception as e:
            log.error(f"[Presets] Falha ao salvar preset: {e}")
            self.update_status("Erro ao salvar preset.", is_error=True)

    def apply_preset(self, preset_nome: str):
        """Desinstala tudo e instala os mods do preset na ordem."""
        from core.mod_manager.preset_ops import load_presets
        from core.operations.install.manager import install_mod
        from core.operations.uninstall.manager import uninstall_mod
        
        if preset_nome == "Nenhum preset salvo" or not self.current_game_key: 
            return
        
        presets = load_presets(DATA_ROOT, self.current_game_key)
        mods_alvo = presets.get(preset_nome, [])
        
        game_path = self._get_current_game_path()
        if not game_path: return
        
        if not messagebox.askyesno("Aplicar Preset", f"Isso vai desinstalar os mods atuais e instalar o perfil '{preset_nome}'.\n\nContinuar?"):
            return

        def task():
            for mod in list(self.all_mods):
                if mod["installed"]:
                    uninstall_mod(game_path, DATA_ROOT, self.current_game_key, mod["id"])

            for nome_mod in mods_alvo:
                mod_alvo = next((m for m in self.all_mods if m["name"] == nome_mod), None)
                if not mod_alvo: continue
                
                source_path = Path(mod_alvo["source_path"])
                if source_path.exists():
                    install_mod(
                        game_path=game_path, source=source_path, data_root=DATA_ROOT,
                        game_key=self.current_game_key, mod_name=nome_mod,
                        inventory=self.current_inventory, force_overwrite=True
                    )
            return True

        def success(result, win):
            self._safe_destroy(win)
            self.load_real_mods()
            self.update_preset_menu()
            self.update_status(f"✅ Preset '{preset_nome}' aplicado com sucesso.")
            messagebox.showinfo("Sucesso", f"Preset '{preset_nome}' aplicado!")

        self._run_async(f"Aplicando preset '{preset_nome}'...", task, success, self._handle_error)