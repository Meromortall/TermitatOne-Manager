from pathlib import Path, PurePosixPath, PureWindowsPath
from utils.logs.rise_logger import log

# Nomes que o Windows se recusa a criar como arquivos
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", 
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def is_safe_path(file_path: str | Path) -> bool:
    """Verifica se o caminho Ã© relativo, seguro e nÃ£o usa nomes proibidos pelo Windows."""
    normalized = str(file_path).replace("\\", "/")
    path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(normalized)

    if not normalized:
        log.error("[PathValidator] Caminho rejeitado: estÃ¡ vazio.")
        return False
        
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        log.error(f"[PathValidator] Caminho rejeitado: absoluto ou drive ({file_path})")
        return False
        
    if ".." in path.parts:
        log.error(f"[PathValidator] Caminho rejeitado: path traversal '..' ({file_path})")
        return False

    # NOVA TRAVA: Verifica se alguma parte do caminho tem nome reservado do Windows
    for part in path.parts:
        # Pega o nome sem a extensÃ£o (ex: "CON.txt" -> "CON") e em maiÃºsculas
        stem = PurePosixPath(part).stem.upper()
        if stem in WINDOWS_RESERVED_NAMES:
            log.error(f"[PathValidator] Caminho rejeitado: usa nome reservado do Windows '{stem}' ({file_path})")
            return False
            
    return True
    
def extract_www_path(file_path: str | Path) -> str | None:
    """Se o caminho for seguro, extrai o destino comeÃ§ando pela pasta 'www'."""
    if not is_safe_path(file_path):
        raise ValueError(f"Caminho inseguro bloqueado: {file_path}")

    path = PurePosixPath(str(file_path).replace("\\", "/"))
    parts = path.parts
    
    for index, part in enumerate(parts):
        if part.lower() == "www":
            www_path = PurePosixPath(*parts[index:]).as_posix()
            log.debug(f"[PathValidator] Pasta 'www' encontrada. Caminho limpo: {www_path}")
            return www_path

    log.debug(f"[PathValidator] Caminho seguro, mas sem pasta 'www': {file_path}")
    return None

