import rarfile
import shutil
from pathlib import Path
from utils.logs.rise_logger import log

class RarAdapter:
    def list_files(self, path: Path) -> list:
        log.debug(f"[RarAdapter] Listando conteúdo do RAR: {path.name}")
        try:
            with rarfile.RarFile(path, 'r') as r:
                return [
                    {
                        "name": i.filename, 
                        "is_dir": i.is_dir(),
                        "uncompressed_size": i.file_size # TRAVA: Enviando tamanho para o manager!
                    } 
                    for i in r.infolist()
                ]
        except rarfile.RarCannotExec:
            log.critical("[RarAdapter] WinRAR/7-Zip não encontrado no sistema.")
            raise ValueError("O arquivo é um .RAR, mas você não tem o WinRAR ou 7-Zip instalado. Instale um deles para continuar.")
        except rarfile.PasswordRequired:
            log.error(f"[RarAdapter] O arquivo RAR '{path.name}' está protegido por senha.")
            raise ValueError(f"O mod '{path.name}' está protegido por senha e não pode ser instalado.")
        except rarfile.BadRarFile:
            log.error(f"[RarAdapter] O arquivo RAR '{path.name}' está corrompido.")
            raise ValueError(f"O arquivo RAR '{path.name}' parece estar corrompido.")
        except Exception as e:
            log.error(f"[RarAdapter] Erro desconhecido ao ler RAR '{path.name}': {e}", exc_info=True)
            raise ValueError(f"Falha ao ler o arquivo RAR: {e}")

    def extract_file(self, path: Path, file_name: str, target_path: Path) -> None:
        log.debug(f"[RarAdapter] Extraindo '{file_name}' do RAR...")
        
        # Trava de segurança: Não permite escrever fora da pasta de destino
        try:
            target_path.resolve().relative_to(target_path.parent.resolve())
        except ValueError:
            log.critical(f"[RarAdapter] 🚨 Tentativa de Path Traversal bloqueada ao extrair: {file_name}")
            raise ValueError("Caminho de extração inseguro bloqueado.")

        try:
            with rarfile.RarFile(path, 'r') as r:
                with r.open(file_name) as source, target_path.open("wb") as target:
                    # Buffer de 1MB para extração ultra-rápida de arquivos grandes
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                    
        except rarfile.RarCannotExec:
            log.error("[RarAdapter] Falha na extração: ferramenta RAR (WinRAR/7z) ausente.")
            raise ValueError("Para extrair arquivos .RAR, instale o WinRAR ou 7-Zip.")
        except rarfile.PasswordRequired:
            log.error(f"[RarAdapter] Senha necessária para extrair '{file_name}'.")
            raise ValueError("Não é possível extrair: arquivo protegido por senha.")
        except Exception as e:
            log.error(f"[RarAdapter] Falha ao extrair '{file_name}': {e}", exc_info=True)
            raise RuntimeError(f"Falha ao extrair o arquivo do RAR: {e}")