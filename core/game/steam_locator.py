import winreg
import re
from pathlib import Path
from utils.logs.rise_logger import log

def find_steam_base_path() -> Path | None:
    """Encontra a instalação principal da Steam, checando Usuário Atual e Sistema."""
    log.debug("[SteamLocator] Buscando caminho base da Steam no Registro do Windows...")
    
    # Tenta primeiro no usuário atual (HKCU), depois no sistema global (HKLM)
    registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"), # Padrão do Windows 64-bit
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
    ]
    
    for hive, subkey in registry_paths:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "SteamPath")
                steam_path = Path(path)
                if steam_path.exists():
                    log.info(f"[SteamLocator] Steam encontrada no registro: {path}")
                    return steam_path.resolve()
        except FileNotFoundError:
            continue # Não achou nessa chave, tenta a próxima
        except OSError as e:
            log.error(f"[SteamLocator] Erro de acesso ao registro ({subkey}): {e}")
            
    log.warning("[SteamLocator] Steam não encontrada no registro do Windows (nem HKCU nem HKLM).")
    return None

def get_all_steam_libraries(steam_base_path: Path | None) -> set[Path]:
    """Retorna um set com todas as pastas de biblioteca da Steam (incluindo outros HDs)."""
    # TRAVA DE SEGURANÇA 1: O crash do None
    if not steam_base_path or not steam_base_path.exists():
        log.warning("[SteamLocator] Caminho base da Steam é inválido ou não existe.")
        return set()
        
    log.debug(f"[SteamLocator] Analisando bibliotecas a partir de: {steam_base_path}")
    libraries = {steam_base_path.resolve()}
    vdf_path = steam_base_path / "steamapps" / "libraryfolders.vdf"

    if not vdf_path.exists():
        log.warning("[SteamLocator] libraryfolders.vdf não encontrado. Assumindo que só existe a biblioteca padrão.")
        return libraries

    try:
        # TRAVA DE SEGURANÇA 2: Usa utf-8-sig e replace para não estourar com BOM ou caracteres especiais
        content = vdf_path.read_text(encoding="utf-8-sig", errors="replace")
        
        # TRAVA DE SEGURANÇA 3: Regex mais flexível (case-insensitive e aceita tabs/espaços)
        # Procura por: "path" "C:\\SteamLibrary" ou "Path"     "D:\\Games"
        matches = re.finditer(r'"path"\s*"([^"]+)"', content, re.IGNORECASE)
        
        for match in matches:
            # Desescapa as barras invertidas do VDF (C:\\Steam -> C:\Steam)
            raw_path = match.group(1).replace("\\\\", "\\")
            lib_path = Path(raw_path)
            
            if lib_path.is_dir():
                libraries.add(lib_path.resolve())
                log.debug(f"[SteamLocator] Biblioteca adicional encontrada: {lib_path}")
            else:
                log.warning(f"[SteamLocator] Caminho no VDF não existe (HD desconectado?): {lib_path}")
                
    except Exception as e:
        log.error(f"[SteamLocator] Erro ao ler o arquivo VDF de bibliotecas: {e}", exc_info=True)

    log.info(f"[SteamLocator] Total de bibliotecas encontradas para busca: {len(libraries)}")
    return libraries