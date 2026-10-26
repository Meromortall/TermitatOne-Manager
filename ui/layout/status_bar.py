import customtkinter as ctk
from utils.logs.rise_logger import log


class StatusBarComponent:
    def __init__(self, master, app_instance):
        self.app = app_instance
        colors = self.app.colors

        # Container principal (um pouco mais alto para respirar)
        self.frame = ctk.CTkFrame(
            master,
            height=28,
            corner_radius=0,
            fg_color=colors["bg_panel"]
        )
        self.frame.pack_propagate(False)

        # Borda superior sutil (separador de layout)
        self.top_border = ctk.CTkFrame(
            self.frame,
            height=1,
            corner_radius=0,
            fg_color=colors["border"]
        )
        self.top_border.pack(fill="x", side="top")

        # Container do conteúdo (para alinhar a bolinha e o texto)
        self.content = ctk.CTkFrame(self.frame, fg_color="transparent", height=27)
        self.content.pack(fill="both", expand=True, padx=10)

        # Indicador de status (A bolinha)
        self.dot = ctk.CTkFrame(
            self.content,
            width=8,
            height=8,
            corner_radius=4,
            fg_color=colors["text_muted"]
        )
        self.dot.pack(side="left", padx=(0, 8))

        # Texto de status
        self.label = ctk.CTkLabel(
            self.content,
            text="Pronto.",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=colors["text_muted"]
        )
        self.label.pack(side="left", fill="x", expand=True)

        # Disponibiliza a atualização de status para o app
        self.app.update_status = self.update_status

    def update_status(self, message: str, is_error: bool = False):
        """Atualiza o texto, a cor e o indicador da barra de status."""
        colors = self.app.colors

        # Define as cores baseadas no estado
        if is_error:
            text_color = colors.get("danger", "#EF5350")
            dot_color = colors.get("danger", "#EF5350")
        else:
            text_color = colors["text_muted"]
            dot_color = colors.get("success", "#00E676") # Verde se for sucesso/aviso

        # TRAVA DELUXE: Se a mensagem for gigante, corta para não quebrar o layout
        safe_message = message
        if len(safe_message) > 100:
            safe_message = safe_message[:97] + "..."

        # Aplica os novos valores
        self.label.configure(text=f" {safe_message}", text_color=text_color)
        self.dot.configure(fg_color=dot_color)

        # Loga se for erro
        if is_error:
            log.error("[STATUS ERROR] %s", message)