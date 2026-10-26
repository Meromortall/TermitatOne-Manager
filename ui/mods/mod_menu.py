import tkinter as tk
from tkinter import TclError

try:
    from ui.state.theme_manager import get_theme_colors
except ImportError:
    get_theme_colors = None


class ModMenuMixin:
    """Menu de contexto dos mods, com cores herdadas do tema ativo."""

    def _get_mod_menu_colors(self):
        """Obtém a paleta atual; usa uma paleta escura como fallback."""
        fallback = {
            "bg": "#1E1E1E",
            "fg": "#FFFFFF",
            "active_bg": "#00E676",
            "active_fg": "#000000",
            "disabled_fg": "#777777",
            "danger": "#EF5350",
        }

        # Se o app já passou as cores, usa elas (mais rápido e garante consistência)
        if hasattr(self, "colors") and self.colors:
            return {
                "bg": self.colors.get("bg_panel", fallback["bg"]),
                "fg": self.colors.get("text_main", fallback["fg"]),
                "active_bg": self.colors.get("accent", fallback["active_bg"]),
                "active_fg": self.colors.get("button_text", fallback["active_fg"]),
                "disabled_fg": self.colors.get("text_muted", fallback["disabled_fg"]),
                "danger": self.colors.get("danger", fallback["danger"]),
            }

        if get_theme_colors is None:
            return fallback

        theme_name = getattr(self, "current_theme_name", None)
        supercharge_name = getattr(self, "current_supercharge_name", "Nenhum")

        settings = getattr(self, "settings", {})
        if isinstance(settings, dict):
            theme_name = theme_name or settings.get("theme", "Sistema")
            supercharge_name = settings.get("supercharge", supercharge_name)

        try:
            palette = get_theme_colors(
                theme_name or "Sistema",
                supercharge_name or "Nenhum",
            )
        except (KeyError, TypeError, ValueError, RuntimeError):
            return fallback

        return {
            "bg": palette.get("bg_panel", fallback["bg"]),
            "fg": palette.get("text_main", fallback["fg"]),
            "active_bg": palette.get("accent", fallback["active_bg"]),
            "active_fg": palette.get("button_text", fallback["active_fg"]),
            "disabled_fg": palette.get("text_muted", fallback["disabled_fg"]),
            "danger": palette.get("danger", fallback["danger"]),
        }

    def show_context_menu(self, event, mod):
        """Exibe ações rápidas para o mod clicado com o botão direito."""
        self.select_mod(mod)

        colors = self._get_mod_menu_colors()
        
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=colors["bg"],
            fg=colors["fg"],
            activebackground=colors["active_bg"],
            activeforeground=colors["active_fg"],
            disabledforeground=colors["disabled_fg"],
            selectcolor=colors["active_bg"],
            relief="flat",
            borderwidth=0, # Deluxe: remove a borda branca chata do Windows
            font=("Segoe UI", 10),
        )

        # 1. Ações Seguras
        menu.add_command(
            label="📂 Abrir Pasta do Arquivo",
            command=lambda: self.open_mod_folder(mod),
        )
        menu.add_separator()

        if not mod.get("installed", False):
            menu.add_command(
                label="▶ Instalar Mod",
                command=lambda: self.install_selected(),
            )
            menu.add_separator()
            menu.add_command(
                label="🗑️ Remover do Catálogo",
                command=lambda: self.delete_mod(mod),
            )
        else:
            menu.add_command(
                label="⚠️ Verificar Integridade",
                command=lambda: self.validate_mod(mod),
            )
            menu.add_separator()
            
            # 2. Ações Destrutivas (Destaque em Vermelho)
            menu.add_command(
                label="💀 Remover Completamente (Jogo + ZIP)",
                foreground=colors["danger"], # <-- Fica vermelho na lista
                activeforeground=colors["danger"],
                command=lambda: self.delete_mod_force(mod),
            )

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except TclError:
                pass