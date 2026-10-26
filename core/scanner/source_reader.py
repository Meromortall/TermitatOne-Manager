import os
from pathlib import Path
from core.scanner.archives.archive_manager import is_supported_archive, list_archive_files
from utils.logs.rise_logger import log

def get_raw_files(source: str | Path):
    """
    Lê um diretório ou arquivo compactado e devolve um gerador de tuplas 
    (caminho_relativo, fonte_original, tipo).
    """
    source = Path(source).resolve()
    log.debug(f"[SourceReader] Iniciando leitura da origem: {source}")

    if not source.exists():
        log.error(f"[SourceReader] Origem não encontrada: {source}")
        raise FileNotFoundError(f"Mod não encontrado: {source}")

    # CASO 1: É uma pasta no Windows
    if source.is_dir():
        log.info(f"[SourceReader] Origem é um diretório. Varrendo árvore de arquivos...")
        
        # Usamos os.walk com followlinks=False para não seguir atalhos maliciosos
        for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
            for filename in filenames:
                full_path = Path(dirpath) / filename
                
                # Trava de segurança: Ignora arquivos que são atalhos (symlinks)
                if full_path.is_symlink():
                    log.warning(f"[SourceReader] Ignorando atalho (symlink): {filename}")
                    continue
                    
                try:
                    # Trava de segurança: Testa a leitura antes de entregar
                    _ = full_path.stat()
                    
                    rel_path = full_path.relative_to(source).as_posix()
                    yield rel_path, full_path, "directory"
                    
                except (PermissionError, OSError) as e:
                    log.warning(f"[SourceReader] Arquivo bloqueado ignorado: {filename} ({e})")
                    continue

    # CASO 2: É um arquivo compactado (ZIP, RAR, 7z)
    elif source.is_file() and is_supported_archive(source):
        ext = source.suffix.lower()
        log.info(f"[SourceReader] Origem é um arquivo compactado ({ext}). Lendo conteúdo...")
        
        try:
            archive_files = list_archive_files(source)
            
            if not archive_files:
                log.warning(f"[SourceReader] O arquivo {ext} está vazio.")
                
            for item in archive_files:
                if not item["is_dir"]:
                    yield item["name"], item["name"], "archive"
                    
        except Exception as e:
            log.error(f"[SourceReader] Erro ao ler o arquivo compactado ({ext}): {e}", exc_info=True)
            raise ValueError(f"Falha ao ler o arquivo compactado: {e}")
            
    # CASO 3: O usuário tentou abrir uma imagem, um txt, etc.
    else:
        log.error(f"[SourceReader] Formato não suportado ou caminho inválido: {source}")
        raise ValueError("Formato inválido. Use um arquivo ZIP, 7z, RAR ou uma pasta de mod.")