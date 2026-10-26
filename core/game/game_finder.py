from pathlib import Path
from core.game.steam_locator import find_steam_base_path, get_all_steam_libraries
from core.game.manifest_parser import get_install_folder_name
from utils.logs.rise_logger import log

STEAM_APP_IDS = {
    "Fear & Hunger": "1002300",
    "Fear & Hunger 2: Termina": "2171440",
}

def find_installed_games() -> dict:
    """Procura os jogos suportados nas bibliotecas da Steam com validação de estrutura."""
    log.info("[GameFinder] Iniciando busca por jogos instalados...")
    
    steam_path = find_steam_base_path()
    if not steam_path:
        log.error("[GameFinder] Busca abortada: caminho da Steam não pôde ser determinado.")
        return {}

    libraries = get_all_steam_libraries(steam_path)
    if not libraries:
        log.warning("[GameFinder] Nenhuma biblioteca válida da Steam encontrada.")
        return {}
        
    found_games = {}

    for library in libraries:
        log.debug(f"[GameFinder] Verificando jogos na biblioteca: {library}")
        common_dir = library / "steamapps" / "common"
        
        for game_name, app_id in STEAM_APP_IDS.items():
            if game_name in found_games:
                continue

            manifest = library / "steamapps" / f"appmanifest_{app_id}.acf"
            install_folder = get_install_folder_name(manifest)

            if not install_folder:
                continue

            game_path = common_dir / install_folder

            try:
                # TRAVA 1: Verifica a pasta do jogo e a pasta 'www' com proteção a OSError
                if not game_path.is_dir():
                    log.warning(f"[GameFinder] Manifesto existe, mas a pasta do jogo sumiu: {game_path}")
                    continue
                    
                if not (game_path / "www").is_dir():
                    log.warning(f"[GameFinder] ❌ Jogo '{game_name}' encontrado, mas a pasta 'www' está faltando (instalação incompleta?).")
                    continue
                    
                # Se chegou aqui, o jogo é 100% válido
                found_games[game_name] = game_path.resolve()
                log.info(f"[GameFinder] ✅ Jogo validado: {game_name} em {game_path}")
                
            except OSError as e:
                log.error(f"[GameFinder] Erro de acesso à pasta do jogo '{game_name}' em {game_path}: {e}")
                continue

    if not found_games:
        log.warning("[GameFinder] Nenhum jogo suportado foi encontrado ou validado.")
    else:
        log.info(f"[GameFinder] Busca concluída. {len(found_games)} jogo(s) pronto(s) para uso.")

    return found_games