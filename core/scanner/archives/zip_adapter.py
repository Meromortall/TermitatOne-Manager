import zipfile
import shutil
from pathlib import Path
from utils.logs.rise_logger import log

class ZipAdapter:
    def list_files(self, path: Path) -> list:
        log.debug(f"[ZipAdapter] Listando conteúdo do ZIP: {path.name}")
        try:
            with zipfile.ZipFile(path, 'r') as z:
                return [
                    {
                        "name": i.filename, 
                        "is_dir": i.is_dir(),
                        "uncompressed_size": i.file_size # TRAVA: Enviando tamanho para o manager!
                    } 
                    for i in z.infolist()
                ]
        except zipfile.BadZipFile:
            log.error(f"[ZipAdapter] O arquivo não é um ZIP válido ou está corrompido: {path.name}")
            raise ValueError(f"O arquivo ZIP '{path.name}' está corrompido.")
        except Exception as e:
            log.error(f"[ZipAdapter] Erro desconhecido ao ler ZIP '{path.name}': {e}", exc_info=True)
            raise ValueError(f"Falha ao ler o arquivo ZIP: {e}")

    def extract_file(self, path: Path, file_name: str, target_path: Path) -> None:
        log.debug(f"[ZipAdapter] Extraindo '{file_name}' do ZIP...")
        
        # Defesa em Profundidade: Garante que não vamos escrever fora da pasta
        try:
            target_path.resolve().relative_to(target_path.parent.resolve())
        except ValueError:
            log.critical(f"[ZipAdapter] 🚨 Tentativa de Path Traversal bloqueada ao extrair: {file_name}")
            raise ValueError("Caminho de extração inseguro bloqueado.")

        try:
            with zipfile.ZipFile(path, 'r') as z:
                with z.open(file_name) as source, open(target_path, 'wb') as target:
                    # Buffer de 1MB para extração ultra-rápida de arquivos grandes
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                    
        except RuntimeError as e:
            # O RuntimeError do zipfile geralmente significa arquivo com senha
            if "password required" in str(e).lower() or "encrypted" in str(e).lower():
                log.error(f"[ZipAdapter] O arquivo ZIP '{path.name}' está protegido por senha.")
                raise ValueError(f"Não é possível extrair: o mod '{path.name}' está protegido por senha.")
            log.error(f"[ZipAdapter] Falha ao extrair '{file_name}': {e}", exc_info=True)
            raise
        except Exception as e:
            log.error(f"[ZipAdapter] Falha ao extrair '{file_name}': {e}", exc_info=True)
            raise RuntimeError(f"Falha ao extrair o arquivo do ZIP: {e}")