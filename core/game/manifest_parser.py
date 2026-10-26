import re
from pathlib import Path
from utils.logs.rise_logger import log

def get_install_folder_name(manifest_path: Path) -> str | None:
    """Lê o arquivo .acf e extrai o nome da pasta do jogo, com proteção contra Path Traversal."""
    if not manifest_path.is_file():
        log.debug(f"[ManifestParser] Arquivo de manifesto não existe: {manifest_path.name}")
        return None

    log.debug(f"[ManifestParser] Lendo manifesto: {manifest_path.name}")
    try:
        # TRAVA 1: Ignora BOM e substitui caracteres inválidos para não crashar
        content = manifest_path.read_text(encoding="utf-8-sig", errors="replace")
        
        # TRAVA 2: Regex case-insensitive
        match = re.search(r'"installdir"\s*"([^"]+)"', content, re.IGNORECASE)
        
        if match:
            raw_folder_name = match.group(1).replace("\\\\", "\\")
            
            # TRAVA 3: Sanitização contra Path Traversal
            # Pega apenas o nome final da pasta, ignorando qualquer ".." ou caminho absoluto
            safe_folder_name = Path(raw_folder_name).name
            
            if not safe_folder_name or safe_folder_name in (".", ".."):
                log.error(f"[ManifestParser] 🚨 Tentativa de Path Traversal detectada no manifesto: '{raw_folder_name}'")
                return None
                
            log.debug(f"[ManifestParser] Nome da pasta extraído com segurança: {safe_folder_name}")
            return safe_folder_name
        
        log.warning(f"[ManifestParser] Manifesto encontrado, mas a chave 'installdir' está ausente: {manifest_path.name}")
        return None
        
    except OSError as e:
        log.error(f"[ManifestParser] Erro de leitura no arquivo {manifest_path.name}: {e}")
        return None
    except Exception as e:
        log.error(f"[ManifestParser] Erro inesperado ao processar {manifest_path.name}: {e}", exc_info=True)
        return None