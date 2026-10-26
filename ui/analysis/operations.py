import threading
from tkinter import messagebox
from pathlib import Path

from core.operations.install.manager import install_mod
from core.operations.uninstall.manager import uninstall_mod
from core.mod_manager.registry_query import find_file_owner
from core.scanner.mod_scanner import _collect_files
from ui.state.game_state import DATA_ROOT
from utils.logs.rise_logger import log


class AnalysisOperationsMixin:
    def _run_async(self, title: str, task_func, on_success, on_error):
        """Executa uma tarefa pesada em thread separada com barra de progresso."""
        progress_win = self.show_progress_window(title)
        self.update_status(f"⚙️ Processando... Não feche a janela.")
        
        def wrapper():
            try:
                result = task_func()
                self.after(0, lambda: on_success(result, progress_win))
            except Exception as e:
                log.error(f"[UI] Erro em tarefa assíncrona: {e}", exc_info=True)
                self.after(0, lambda: on_error(e, progress_win))

        threading.Thread(target=wrapper, daemon=True).start()

    def install_selected(self):
        if not self.selected_mod or self.selected_mod["installed"]: 
            return
        
        # TRAVA DELUXE 1: Salva o contexto no início da operação
        target_game_key = self.current_game_key
        game_path = self._get_current_game_path()
        if not game_path:
            self.update_status("Erro: Caminho do jogo não encontrado.", is_error=True)
            return

        source_path = Path(self.selected_mod["source_path"])
        mod_name = self.selected_mod["name"]

        if not source_path.exists():
            self.update_status("Erro: O arquivo original do mod sumiu.", is_error=True)
            messagebox.showerror("Erro", "O arquivo original do mod sumiu do seu PC. Adicione-o novamente.")
            return

        # 2. Seleção de arquivos
        selected_files = self.show_file_selection_dialog(source_path)
        if not selected_files: 
            return 

        # 3. Checagem de conflitos
        try:
            files = _collect_files(source_path, self.destination_overrides, self.current_inventory)
            conflicts = []
            for f in files:
                if f["destination"] in selected_files:
                    owner = find_file_owner(DATA_ROOT, target_game_key, f["destination"])
                    if owner:
                        conflicts.append({"file": f["destination"], "owner": owner["name"]})
        except Exception as e:
            log.error(f"[UI] Falha ao ler arquivos do mod para instalar: {e}")
            self.update_status("Erro ao ler arquivos do mod.", is_error=True)
            messagebox.showerror("Erro na Leitura", f"Não foi possível ler os arquivos do mod:\n{e}")
            return

        conflict_actions = self.show_conflict_dialog(conflicts) if conflicts else {}
        if conflict_actions is None: 
            return 

        # 4. Execução assíncrona
        def task():
            return install_mod(
                game_path, source_path, DATA_ROOT, target_game_key, mod_name,
                destination_overrides=self.destination_overrides, inventory=self.current_inventory,
                conflict_actions=conflict_actions, selected_files=selected_files
            )

        def success(installed_files, win):
            self._safe_destroy(win)
            
            # TRAVA DELUXE 2: Só atualiza a UI se o usuário não trocou de jogo
            if self.current_game_key == target_game_key:
                self.load_real_mods()
                try:
                    self.select_mod(next(m for m in self.all_mods if m["name"] == mod_name))
                except StopIteration:
                    pass
                self.update_status(f"✅ Instalação concluída: {mod_name} ({len(installed_files)} arquivos).")
            else:
                self.update_status(f"✅ Mod '{mod_name}' instalado em outro jogo.")
                
            messagebox.showinfo("Sucesso", f"Mod '{mod_name}' instalado!\n{len(installed_files)} arquivos copiados.")

        def error(e, win):
            self._safe_destroy(win)
            self.update_status("❌ Falha na instalação. Verifique o log.", is_error=True)
            messagebox.showerror("Falha na Instalação", str(e))

        self._run_async(f"Instalando {mod_name}...", task, success, error)

    def uninstall_selected(self):
        if not self.selected_mod or not self.selected_mod["installed"]: 
            return
        
        target_game_key = self.current_game_key
        game_path = self._get_current_game_path()
        if not game_path: 
            return
        
        mod = self.selected_mod
        mod_name = mod["name"]
        mod_id = mod["id"]

        if not messagebox.askyesno("Confirmar Desinstalação", f"Tem certeza que deseja desinstalar '{mod_name}'?\n\nOs arquivos originais do jogo serão restaurados."): 
            return

        def task():
            return uninstall_mod(game_path, DATA_ROOT, target_game_key, mod_id)

        def success(removed, win):
            self._safe_destroy(win)
            
            # TRAVA DELUXE 3: Atualiza a UI e limpa a seleção
            if self.current_game_key == target_game_key:
                self.load_real_mods()
                
                # Como o mod foi desinstalado, ele não está mais na lista.
                # Então limpamos o painel da direita (árvore e botões).
                if hasattr(self, '_clear_ui_selection'):
                    self._clear_ui_selection()
                    
                self.update_status(f"✅ Desinstalação concluída: {mod_name} ({len(removed)} arquivos restaurados).")
            else:
                self.update_status(f"✅ Mod '{mod_name}' desinstalado em outro jogo.")
                
            messagebox.showinfo("Sucesso", f"O mod '{mod_name}' foi desinstalado e o jogo restaurado!")

        def error(e, win):
            self._safe_destroy(win)
            self.update_status("❌ Falha na desinstalação. Verifique o log.", is_error=True)
            messagebox.showerror("Falha na Desinstalação", str(e))

        self._run_async(f"Desinstalando {mod_name}...", task, success, error)