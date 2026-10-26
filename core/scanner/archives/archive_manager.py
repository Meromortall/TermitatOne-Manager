from pathlib import Path
from utils.logs.rise_logger import log
from core.scanner.archives.zip_adapter import ZipAdapter
from core.scanner.archives.rar_adapter import RarAdapter
from core.scanner.archives.sevenz_adapter import SevenZAdapter

SUPPORTED_EXTENSIONS = [".zip", ".7z", ".rar"]

# TRAVA DE SEGURANÇA: Limite máximo de descompressão por arquivo (500 MB)
# Se um arquivo declarar ter mais que isso, é suspeito (Zip Bomb).
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024 

def get_archive_adapter(path: Path):
    """Retorna a classe adaptadora correta baseada na extensão."""
    ext = Path(path).suffix.lower()
    log.debug(f"[ArchiveManager] Selecionando adaptador para: {ext}")
    
    if ext == ".zip":
        return ZipAdapter()
    elif ext == ".7z":
        return SevenZAdapter()
    elif ext == ".rar":
        return RarAdapter()
    else:
        log.error(f"[ArchiveManager] Formato não suportado: {ext}")
        raise ValueError(f"Formato de arquivo não suportado: {ext}")

def is_supported_archive(path: Path) -> bool:
    """Verifica se a extensão é suportada."""
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

def list_archive_files(path: Path) -> list:
    """Lista os arquivos usando o adaptador correto, com tratamento de erros."""
    path = Path(path).resolve()
    
    if not path.is_file():
        raise FileNotFoundError(f"O arquivo compactado não existe: {path.name}")
        
    log.debug(f"[ArchiveManager] Solicitando lista de arquivos para: {path.name}")
    adapter = get_archive_adapter(path)
    
    try:
        files = adapter.list_files(path)
        
        # TRAVA DE SEGURANÇA: Verifica o tamanho declarado
        for f in files:
            # O adaptador deve nos informar o tamanho descomprimido
            uncompressed_size = f.get("uncompressed_size", 0)
            if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                log.critical(f"[ArchiveManager] 🚨 ZIP BOMB DETECTADA! '{f['name']}' declara ter {uncompressed_size} bytes.")
                raise ValueError(f"Arquivo suspeito de Zip Bomb: {f['name']}")
                
        return files
    except Exception as e:
        log.error(f"[ArchiveManager] Falha ao ler o arquivo {path.suffix}: {e}")
        # Se for RAR e der erro de execução, avisa o usuário amigavelmente
        if "RarCannotExec" in str(type(e)) or "WinRAR" in str(e):
            raise ValueError("Para abrir mods em .RAR, você precisa ter o WinRAR ou 7-Zip instalado no PC.")
        raise

def extract_file_from_archive(archive_path: Path, file_name: str, target_path: Path) -> None:
    """Extrai um arquivo usando o adaptador correto com verificação de segurança."""
    archive_path = Path(archive_path).resolve()
    target_path = Path(target_path).resolve()
    
    log.debug(f"[ArchiveManager] Extraindo '{file_name}' de: {archive_path.name}")
    
    # Trava de segurança: O destino não pode ser vazio
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
    
    adapter = get_archive_adapter(archive_path)
    
    try:
        adapter.extract_file(archive_path, file_name, target_path)
        log.debug(f"[ArchiveManager] Extração concluída: {target_path.name}")
    except Exception as e:
        log.error(f"[ArchiveManager] Falha ao extrair '{file_name}': {e}")
        raise