import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from utils.logs.rise_logger import log

class AnalysisDialogsMixin:
    def _safe_destroy(self, window):
        """Fecha janelas com segurança, esperando o CTk terminar de pintar."""
        try:
            window.grab_release()
            window.withdraw()
            self.after(100, window.destroy) 
        except Exception:
            pass

    def _center_window(self, window, width: int, height: int):
        """Centraliza a janela na tela do usuário."""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_progress_window(self, title: str):
        """Cria uma janela de carregamento elegante e temática."""
        colors = self.colors
        dialog = ctk.CTkToplevel(self)
        dialog.title("Aguarde...")
        self._center_window(dialog, 400, 160)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        dialog.transient(self)
        
        # Aplica a cor de fundo do tema
        dialog.configure(fg_color=colors["bg_panel"])

        # Ícone/Spinner elegante
        ctk.CTkLabel(dialog, text="⚙️", font=ctk.CTkFont(size=30), text_color=colors["text_main"]).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=colors["text_main"]).pack(pady=(0, 15))
        
        pb = ctk.CTkProgressBar(dialog, mode="indeterminate", width=300, progress_color=colors["accent"])
        pb.pack(pady=10)
        pb.start()
        
        return dialog

    def show_file_selection_dialog(self, source_path) -> list | None:
        """Retorna a lista de arquivos que o usuário quer instalar."""
        from core.scanner.mod_scanner import _collect_files
        colors = self.colors
        
        try:
            files = _collect_files(source_path, self.destination_overrides, self.current_inventory)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return None

        if not files:
            messagebox.showwarning("Aviso", "Nenhum arquivo válido encontrado neste mod.")
            return None

        dialog = ctk.CTkToplevel(self)
        dialog.title("Instalação Personalizada")
        self._center_window(dialog, 750, 600)
        dialog.grab_set()
        dialog.lift()
        dialog.transient(self)
        dialog.configure(fg_color=colors["bg_panel"])

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header_frame, text="Selecione os arquivos para instalar", font=ctk.CTkFont(size=18, weight="bold"), text_color=colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(header_frame, text=f"Total: {len(files)} arquivos encontrados", text_color=colors["text_muted"]).pack(anchor="w")

        # Lista de Checkboxes
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=colors["bg_main"], corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        checkboxes = {}
        for item in files:
            var = tk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                scroll, text=item["destination"], variable=var, 
                font=ctk.CTkFont(size=12), text_color=colors["text_main"],
                fg_color=colors["accent"], hover_color=colors["accent_hover"]
            )
            cb.pack(anchor="w", pady=4, padx=10)
            checkboxes[item["destination"]] = var

        result = []
        def confirm():
            result.extend([dest for dest, var in checkboxes.items() if var.get()])
            if not result:
                messagebox.showwarning("Aviso", "Você precisa selecionar pelo menos um arquivo para instalar.", parent=dialog)
                return
            self.file_selection_result = result
            self._safe_destroy(dialog)

        # Footer com botões
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(btn_frame, text="Marcar Todos", fg_color=colors["bg_card"], text_color=colors["text_main"], hover_color=colors["border"], width=100, command=lambda: [var.set(True) for var in checkboxes.values()]).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Desmarcar Todos", fg_color=colors["bg_card"], text_color=colors["text_main"], hover_color=colors["border"], width=120, command=lambda: [var.set(False) for var in checkboxes.values()]).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1, border_color=colors["text_muted"], text_color=colors["text_muted"], hover_color=colors["bg_card"], width=100, command=lambda: self._safe_destroy(dialog)).pack(side="right", padx=(10, 0))
        ctk.CTkButton(btn_frame, text="Confirmar Instalação", fg_color=colors["accent"], text_color=colors["button_text"], hover_color=colors["accent_hover"], font=ctk.CTkFont(weight="bold"), width=160, command=confirm).pack(side="right")

        self.file_selection_result = None
        self.wait_window(dialog)
        return self.file_selection_result

    def show_conflict_dialog(self, conflicts: list) -> dict:
        """Pergunta ao usuário o que fazer com arquivos conflitantes."""
        if not conflicts: return {}
        colors = self.colors

        dialog = ctk.CTkToplevel(self)
        dialog.title("Conflitos Detectados")
        self._center_window(dialog, 650, 500)
        dialog.grab_set()
        dialog.lift()
        dialog.transient(self)
        dialog.configure(fg_color=colors["bg_panel"])

        # Header de Alerta
        header_frame = ctk.CTkFrame(dialog, fg_color=colors["bg_card"], border_width=1, border_color=colors["danger"], corner_radius=8)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text=f"⚠️ {len(conflicts)} Conflitos Encontrados", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors["danger"]).pack(anchor="w", padx=15, pady=(10, 0))
        ctk.CTkLabel(header_frame, text="Estes arquivos já pertencem a outros mods. O que deseja fazer?", text_color=colors["text_main"]).pack(anchor="w", padx=15, pady=(0, 10))

        # Lista de Checkboxes
        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color=colors["bg_main"], corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=5)

        checkboxes = {}
        for item in conflicts:
            var = tk.BooleanVar(value=True)
            
            item_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=5)
            
            cb = ctk.CTkCheckBox(
                item_frame, text="", variable=var, 
                fg_color=colors["accent"], hover_color=colors["accent_hover"], width=24
            )
            cb.pack(side="left", padx=(10, 10))
            
            ctk.CTkLabel(item_frame, text=item['file'], font=ctk.CTkFont(weight="bold"), text_color=colors["text_main"], anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(item_frame, text=f"(Dono: {item['owner']})", text_color=colors["text_muted"], font=ctk.CTkFont(size=11)).pack(side="right", padx=10)
            
            checkboxes[item['file']] = var

        # Funções de confirmação
        def confirm():
            self.conflict_result = {file: "overwrite" if var.get() else "skip" for file, var in checkboxes.items()}
            self._safe_destroy(dialog)

        # Footer de ações
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkButton(btn_frame, text="Sobrescrever Todos (Novo Mod)", fg_color=colors["bg_card"], text_color=colors["text_main"], hover_color=colors["border"], command=lambda: [var.set(True) for var in checkboxes.values()]).pack(side="left")
        ctk.CTkButton(btn_frame, text="Pular Todos (Manter Antigos)", fg_color=colors["bg_card"], text_color=colors["text_main"], hover_color=colors["border"], command=lambda: [var.set(False) for var in checkboxes.values()]).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Confirmar Escolhas", fg_color=colors["accent"], text_color=colors["button_text"], hover_color=colors["accent_hover"], font=ctk.CTkFont(weight="bold"), width=150, command=confirm).pack(side="right")

        self.conflict_result = None
        self.wait_window(dialog)
        return self.conflict_result