import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Configuração de diretório
local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
LOG_DIR = local_app_data / "TermitatoModManager" / "logs"

def _add_console_handler(logger: logging.Logger, level: int) -> None:
    """Handler de console com proteção contra caracteres não suportados pelo Windows."""
    # Garante que o console suporte UTF-8, ou usa errors='replace' como fallback
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass # Se falhar (ex: redirecionamento de IO), segue o jogo
        
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)

# TRAVA DE SEGURANÇA 1: Garante que o logger sempre tenha um destino antes do setup
# Isso evita o "Silêncio Sepulcral" se alguém usar log.info() antes da inicialização.
_early_logger = logging.getLogger("Rise")
if not _early_logger.handlers:
    _early_logger.addHandler(logging.NullHandler())

def setup_rise_logging() -> logging.Logger:
    """Configura o sistema de logs do Termitato com proteção total contra crashes."""
    logger = logging.getLogger("Rise")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False 

    # TRAVA DE SEGURANÇA 2: Limpeza profunda de handlers antigos
    if logger.handlers:
        for handler in logger.handlers:
            try:
                handler.close()
            except Exception:
                pass
        logger.handlers = [] # Garante que a lista esteja vazia (Memory Leak Fix)

    # Trava de segurança: tenta criar a pasta
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"[AVISO CRÍTICO] Não foi possível criar a pasta de logs ({e}). Usando apenas console.")
        _add_console_handler(logger, logging.DEBUG)
        return logger

    # --- 1. BIG LOG (rise_full.log) ---
    try:
        full_log_path = LOG_DIR / "rise_full.log"
        full_handler = RotatingFileHandler(full_log_path, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        full_handler.setLevel(logging.DEBUG)
        full_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        ))
        logger.addHandler(full_handler)
    except PermissionError:
        print("[AVISO] O 'rise_full.log' está bloqueado. O log completo não será gravado.")
    except Exception as e:
        print(f"[AVISO] Falha ao criar o log completo: {e}")

    # --- 2. DEBUG LOG (rise_debug.log) ---
    try:
        debug_log_path = LOG_DIR / "rise_debug.log"
        debug_handler = RotatingFileHandler(debug_log_path, maxBytes=2*1024*1024, backupCount=2, encoding="utf-8")
        debug_handler.setLevel(logging.INFO)
        debug_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        ))
        logger.addHandler(debug_handler)
    except PermissionError:
        print("[AVISO] O 'rise_debug.log' está bloqueado. O log de debug não será gravado.")
    except Exception as e:
        print(f"[AVISO] Falha ao criar o log de debug: {e}")

    # --- 3. CONSOLE (Sempre funciona, independente de arquivos) ---
    _add_console_handler(logger, logging.INFO)

    logger.info("=" * 60)
    logger.info("Termitato Mod Manager - Sistema de Logs Rise Iniciado")
    logger.info(f"Pasta de logs: {LOG_DIR}")
    
    return logger

# Exporta a instância global
log = logging.getLogger("Rise")