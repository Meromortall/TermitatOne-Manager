import os
import shutil
import logging
import threading
from tkinter import messagebox
from pathlib import Path

from core.scanner.game_scanner import scan_game, save_inventory
from core.mod_manager.catalog_ops import remove_from_catalog
from core.mod_manager.registry_query import list_installed_mods
from utils.hash_utils import calculate_file_hash
from ui.state.game_state import DATA_ROOT, INVENTORY_FILES
from utils.logs.rise_logger import log


class AnalysisToolsMixin:
    
    def _get_current_game_path(self) -> Path | None:
        """Helper para descobrir o caminho do jogo atual sem depender do dropdown antigo."""
        if not self.current_game_key or not hasattr(self, 'games'):
            return None
            
        for game_name, path in self.games.items():
            clean_key = "".join(c if c.isalnum() else "_" for c in game_name.lower())
            clean_key = "_".join(filter(None, clean_key.split("_")))
            
            if clean_key == self.current_game_key:
                return Path(path)
        return None

    def launch_game(self):
        """Inicia o executável do jogo atual."""
        game_path = self._get_current_game_path()
        if not game_path:
            self.update_status("Erro: Caminho do jogo não encontrado.", is_error=True)
            return

        exes = list(game_path.glob("*.exe"))
        if not exes:
            self.update_status("Erro: Executável do jogo não encontrado.", is_error=True)
            messagebox.showerror("Erro", "Executável (.exe) do jogo não encontrado na pasta.")
            return
            
        try:
            target_exe = next((e for e in exes if e.name.lower() == "game.exe"), exes[0])
            os.startfile(target_exe)
            self.update_status("🚀 Iniciando o jogo...")
        except Exception as e:
            log.error(f"[Tools] Falha ao abrir o jogo: {e}")
            self.update_status("Falha ao abrir o jogo.", is_error=True)

    def open_game_folder(self):
        """Abre a pasta raiz do jogo no Windows Explorer."""
        game_path = self._get_current_game_path()
        if game_path and game_path.exists():
            try:
                os.startfile(game_path)
                self.update_status("📂 Pasta do jogo aberta.")
            except Exception as e:
                log.error(f"[Tools] Falha ao abrir pasta: {e}")
                self.update_status("Falha ao abrir pasta do jogo.", is_error=True)
        else:
            self.update_status("Erro: Pasta do jogo não encontrada.", is_error=True)

    def open_manager_folder(self):
        """Abre a pasta AppData do Termitato."""
        if DATA_ROOT.exists():
            try:
                os.startfile(DATA_ROOT)
                self.update_status("📂 Pasta do AppData aberta.")
            except Exception as e:
                log.error(f"[Tools] Falha ao abrir AppData: {e}")
                self.update_status("Erro ao abrir pasta do AppData.", is_error=True)
        else:
            messagebox.showerror("Erro", "A pasta do AppData ainda não foi criada pelo Termitato.")

    def generate_inventory(self):
        """Gera o inventário do jogo em segundo plano com barra de progresso."""
        game_path = self._get_current_game_path()
        if not game_path:
            return
            
        game_name = next((name for name, p in self.games.items() if str(p) == str(game_path)), "Jogo")
        inv_path = DATA_ROOT / "inventories" / INVENTORY_FILES.get(self.current_game_key, "unknown.json")

        def task():
            inv = scan_game(game_path)
            save_inventory(inv, inv_path)
            return inv

        def success(inv, win):
            self._safe_destroy(win)
            self.current_inventory = inv
            self.has_inventory = True
            self.update_inventory_button()
            self.update_status(f"✅ Gabarito gerado: {inv['total_files']} arquivos.")
            messagebox.showinfo("Gabarito Gerado", f"Inventário criado com sucesso!\n\n{inv['total_files']} arquivos mapeados.")

        if hasattr(self, '_run_async'):
            self._run_async(f"Lendo {game_name}...", task, success, self._handle_error)
        else:
            self._handle_error("O sistema de execução assíncrona (_run_async) não foi encontrado.")

    def validate_all_mods(self):
        """Verifica a integridade de TODOS os mods instalados de uma vez (em segundo plano)."""
        game_path = self._get_current_game_path()
        if not game_path: 
            return
        
        # TRAVA DELUXE 1: Salva a key atual para não validar o jogo errado se o usuário trocar
        target_key = self.current_game_key
        installed = list_installed_mods(DATA_ROOT, target_key)
        
        if not installed:
            self.update_status("Nenhum mod instalado para validar.", is_error=False)
            messagebox.showinfo("Aviso", "Não há mods instalados para validar.")
            return

        self.update_status("⚙️ Validando todos os mods (em segundo plano)...")

        def run_validation():
            erros_globais = []
            for mod in installed:
                expected_hashes = mod.get("file_hashes", {})
                if not expected_hashes: continue
                
                for rel_path, expected_hash in expected_hashes.items():
                    full_path = game_path / rel_path
                    if not full_path.exists():
                        erros_globais.append(f"[{mod['name']}] Faltando: {rel_path}")
                    elif calculate_file_hash(full_path) != expected_hash:
                        erros_globais.append(f"[{mod['name']}] Modificado: {rel_path}")

            # TRAVA DELUXE 2: Só atualiza a UI se o usuário não trocou de jogo no meio do processo
            def update_if_current():
                if self.current_game_key == target_key:
                    self._on_validate_all_finished(erros_globais)
                else:
                    log.debug("[Tools] Validação antiga descartada (usuário trocou de jogo).")

            self.after(0, update_if_current)

        threading.Thread(target=run_validation, daemon=True).start()

    def _on_validate_all_finished(self, erros_globais):
        if erros_globais:
            log.warning(f"[Tools] Validação em massa encontrou {len(erros_globais)} erros.")
            self.update_status(f"Validação em massa falhou: {len(erros_globais)} arquivos corrompidos.", is_error=True)
            msg = "Problemas encontrados:\n\n" + "\n".join(erros_globais[:10])
            if len(erros_globais) > 10: 
                msg += f"\n... e mais {len(erros_globais)-10} erros."
            messagebox.showerror("Falha na Validação", msg)
        else:
            log.info("[Tools] Validação em massa concluída com sucesso.")
            self.update_status("✅ Todos os mods estão íntegros.")
            messagebox.showinfo("Sucesso", "Todos os arquivos de todos os mods estão corretos!")

    def clean_missing_files(self):
        """Remove do catálogo mods cujo arquivo ZIP original sumiu do PC (em segundo plano)."""
        self.update_status("🧹 Procurando arquivos faltando...")
        
        def run_clean():
            removidos = []
            for mod in list(self.all_mods):
                source = mod.get("source_path")
                if source and not Path(source).exists():
                    remove_from_catalog(DATA_ROOT, self.current_game_key, mod["name"])
                    removidos.append(mod["name"])

            def update_ui():
                if removidos:
                    self.load_real_mods()
                    # Se o mod deletado estava selecionado na árvore, limpa o painel direito
                    if self.selected_mod and self.selected_mod["name"] in removidos:
                        if hasattr(self, '_clear_ui_selection'):
                            self._clear_ui_selection()
                            
                    self.update_status(f"🧹 Limpeza concluída: {len(removidos)} mods removidos.")
                    messagebox.showinfo("Limpeza", f"{len(removidos)} mods foram removidos do catálogo pois o ZIP sumiu.")
                else:
                    self.update_status("Nenhum arquivo faltando encontrado.")
                    messagebox.showinfo("Limpeza", "Nenhum arquivo sumido foi encontrado. Tudo limpo!")

            self.after(0, update_ui)

        # Executa a checagem de disco em uma thread separada
        threading.Thread(target=run_clean, daemon=True).start()

    def _handle_error(self, error, window=None):
        """Tratamento de erro padrão para tarefas assíncronas."""
        if window: 
            self._safe_destroy(window)
        log.error(f"[Tools] Erro em ferramenta: {error}")
        self.update_status(f"Erro: {error}", is_error=True)
        messagebox.showerror("Erro", str(error))

    def factory_reset(self):
        """Apaga TODOS os dados do gerenciador."""
        if not messagebox.askyesno("CUIDADO EXTREMO", "Isso apagará TODOS os seus mods, catálogos, backups e configurações do Termitato.\n\nO jogo original não será afetado.\n\nTem certeza absoluta?"):
            return
        
        try:
            # Fecha os arquivos de log antes de apagar para evitar WinError 32
            logger = logging.getLogger("Rise")
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()
            
            # Agora o Windows libera a pasta para ser apagada
            if DATA_ROOT.exists():
                shutil.rmtree(DATA_ROOT)
                
            messagebox.showinfo("Resetado", "O Termitato foi resetado com sucesso.\nO programa será fechado.")
            self.quit() # Fecha o app
            
        except Exception as e:
            log.error(f"[Tools] Falha no Factory Reset: {e}")
            messagebox.showerror("Erro", f"Falha ao resetar o sistema: {e}\n\nTente fechar o programa e apagar a pasta manualmente.")