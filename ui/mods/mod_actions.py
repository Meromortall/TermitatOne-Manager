import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

from core.scanner.mod_scanner import inspect_source
from core.mod_manager.catalog_ops import add_to_catalog, remove_from_catalog
from core.mod_manager.registry_query import list_installed_mods
from core.operations.uninstall.manager import uninstall_mod
from utils.hash_utils import calculate_file_hash
from ui.state.game_state import DATA_ROOT
from utils.logs.rise_logger import log


class ModsActionsMixin:
    
    def add_zip(self):
        if not self.current_game_key: return
        filepaths = filedialog.askopenfilenames(
            title="Escolher Mods (ZIP, RAR, 7z)", 
            filetypes=[("Arquivos Suportados", "*.zip *.rar *.7z")]
        )
        if filepaths: 
            self._process_batch(filepaths)
            
    def add_folder(self):
        if not self.current_game_key: return
        folderpath = filedialog.askdirectory(title="Escolher Pasta do Mod")
        if folderpath: 
            self._process_batch([folderpath])

    def _process_batch(self, paths):
        """Processa múltiplos mods sem congelar a interface."""
        log.info(f"[UI] Iniciando processamento de lote: {len(paths)} mods.")
        self.update_status(f"Lendo 0/{len(paths)}...")
        
        def process_next(index):
            if index >= len(paths):
                self.load_real_mods()
                self.update_status(f"Lote concluído. {len(paths)} mods processados.")
                return

            path = paths[index]
            self.update_status(f"Lendo ({index+1}/{len(paths)}): {Path(path).name}...")
            
            try:
                entries = inspect_source(Path(path), self.current_inventory)
                if not any(entry["destination"] for entry in entries):
                    log.warning(f"[UI] Mod ignorado (sem destino): {path}")
                    self.update_status(f"Mod ignorado (sem destino): {Path(path).name}", is_error=True)
                else:
                    mod_name = Path(path).stem 
                    files = [entry["source"] for entry in entries]
                    add_to_catalog(DATA_ROOT, self.current_game_key, mod_name, path, files)
                    log.info(f"[UI] Mod adicionado ao catálogo: {mod_name}")
            except Exception as e:
                log.error(f"[UI] Erro ao adicionar mod {path}: {e}")
                self.update_status(f"Erro ao adicionar: {Path(path).name}", is_error=True)

            self.after(10, lambda: process_next(index + 1))

        process_next(0)

    def _clear_ui_selection(self):
        """Limpa os painéis da direita e a árvore quando um mod é deletado."""
        self.selected_mod = None
        
        # Limpa a árvore de arquivos (se o método existir)
        if hasattr(self, 'clear_tree_view'):
            self.clear_tree_view()
        elif hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            self.tree.insert("", "end", text="Nenhum mod selecionado.", tags=("empty",))
            
        # Limpa as labels do painel direito (se existirem)
        if hasattr(self, "lbl_mod_name"):
            self.lbl_mod_name.configure(text="Nenhum selecionado")
        if hasattr(self, "lbl_mod_size"):
            self.lbl_mod_size.configure(text="Arquivos: -")
        if hasattr(self, "btn_install"):
            self.btn_install.configure(state="disabled", fg_color=self.colors["bg_card"])
        if hasattr(self, "btn_uninstall"):
            self.btn_uninstall.configure(state="disabled", border_color=self.colors["border"])

    def delete_mod(self, mod):
        """Remove o mod APENAS do catálogo (não toca no jogo)."""
        if mod["installed"]:
            messagebox.showwarning("Aviso", "Desinstale o mod do jogo antes de removê-lo do catálogo.")
            return
            
        if messagebox.askyesno("Remover", f"Remover '{mod['name']}' do gerenciador?\n\nO arquivo ZIP original NÃO será apagado."):
            if remove_from_catalog(DATA_ROOT, self.current_game_key, mod["name"]):
                log.info(f"[UI] Mod removido do catálogo: {mod['name']}")
                self._clear_ui_selection() # <--- CORREÇÃO UX
                self.load_real_mods()
                self.update_status(f"Mod '{mod['name']}' removido do catálogo.")

    def delete_mod_force(self, mod):
        """Desinstala o mod do jogo E o remove do catálogo."""
        if not messagebox.askyesno("CUIDADO", f"Tem certeza que deseja remover COMPLETAMENTE o mod '{mod['name']}'?\n\nEle será desinstalado do jogo e apagado da lista."):
            return
            
        game_path = self._get_current_game_path()
        if not game_path:
            self.update_status("Erro: Caminho do jogo não encontrado.", is_error=True)
            return # <--- CORREÇÃO DE CRASH
            
        self.update_status(f"Desinstalando e apagando: {mod['name']}...")
        try:
            if mod["installed"]:
                log.info(f"[UI] Desinstalando e apagando: {mod['name']}")
                uninstall_mod(game_path, DATA_ROOT, self.current_game_key, mod["id"])
                
            remove_from_catalog(DATA_ROOT, self.current_game_key, mod["name"])
            self._clear_ui_selection() # <--- CORREÇÃO UX
            self.load_real_mods()
                
            messagebox.showinfo("Removido", f"O mod '{mod['name']}' foi completamente removido.")
            self.update_status(f"Mod '{mod['name']}' removido completamente.")
        except Exception as e:
            log.error(f"[UI] Falha ao remover: {e}")
            messagebox.showerror("Falha", f"Erro ao remover: {e}")
            self.update_status(f"Falha ao remover: {mod['name']}", is_error=True)

    def validate_mod(self, mod):
        """Valida a integridade do mod em uma Thread separada."""
        if not mod["installed"]: return
        
        game_path = self._get_current_game_path()
        if not game_path:
            self.update_status("Erro: Caminho do jogo não encontrado.", is_error=True)
            return # <--- CORREÇÃO DE CRASH
            
        self.update_status("⚙️ Validando integridade (em segundo plano)...")
        
        def run_validation():
            try:
                installed = list_installed_mods(DATA_ROOT, self.current_game_key)
                reg_mod = next((m for m in installed if m["name"] == mod["name"]), None)
                
                if not reg_mod or "file_hashes" not in reg_mod:
                    self.after(0, lambda: messagebox.showwarning("Aviso", "Este mod não possui hashes salvos."))
                    return

                errors = []
                for rel_path, expected_hash in reg_mod["file_hashes"].items():
                    full_path = game_path / rel_path
                    if not full_path.exists():
                        errors.append(f"Faltando: {rel_path}")
                    elif calculate_file_hash(full_path) != expected_hash:
                        errors.append(f"Modificado: {rel_path}")

                self.after(0, lambda: self._on_validation_finished(mod['name'], errors))
                
            except Exception as e:
                log.error(f"[UI] Falha na validação de {mod['name']}: {e}")
                self.after(0, lambda: self.update_status(f"Erro na validação: {mod['name']}", is_error=True))

        threading.Thread(target=run_validation, daemon=True).start()

    def _on_validation_finished(self, mod_name, errors):
        """Callback chamado quando a thread de validação termina."""
        if errors:
            log.warning(f"[UI] Validação falhou para {mod_name}: {len(errors)} erros.")
            messagebox.showerror("Validação Falhou", "Os seguintes arquivos estão diferentes do original:\n\n" + "\n".join(errors[:10]))
            self.update_status(f"Validação falhou: {mod_name}", is_error=True)
        else:
            log.info(f"[UI] Validação OK para {mod_name}.")
            messagebox.showinfo("Sucesso", "Todos os arquivos estão íntegros e corretos!")
            self.update_status(f"✅ Validação concluída: {mod_name}")

    def open_mod_folder(self, mod):
        """Abre a pasta onde o ZIP original do mod está guardado."""
        source = mod.get("source_path")
        if source and Path(source).exists():
            try:
                os.startfile(Path(source).parent)
            except OSError as e:
                log.error(f"[UI] Falha ao abrir pasta do mod: {e}")
                self.update_status("Erro ao abrir a pasta do mod.", is_error=True)
        else:
            messagebox.showerror("Erro", "O arquivo original deste mod não existe mais no seu computador.")