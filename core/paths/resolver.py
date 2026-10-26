from pathlib import Path, PurePosixPath
from utils.logs.rise_logger import log

def resolve_safe_target(game_path: str | Path, relative_path: str | Path) -> Path:
    """Garante que o destino final resolvido continue dentro da pasta do jogo."""
    game_root = Path(game_path).resolve()
    
    # Normaliza a barra para evitar bugs no Windows
    clean_relative = PurePosixPath(str(relative_path).replace("\\", "/"))
    target = (game_root / Path(*clean_relative.parts)).resolve()

    log.debug(f"[PathResolver] Resolvendo alvo. Relativo: '{relative_path}' -> Absoluto: '{target}'")

    try:
        # A MÃGICA: Verifica se o alvo real (com symlinks resolvidos) ainda estÃ¡ dentro do jogo
        target.relative_to(game_root)
    except ValueError:
        log.critical(f"[PathResolver] ðŸš¨ FALHA DE SEGURANÃ‡A: Tentativa de escapar da pasta do jogo! (Destino: {target} | Jogo: {game_root})")
        raise ValueError("O destino estÃ¡ fora da pasta do jogo.")

    log.debug(f"[PathResolver] Destino aprovado com seguranÃ§a: {target}")
    return target

