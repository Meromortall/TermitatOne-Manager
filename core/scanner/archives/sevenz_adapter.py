import py7zr
import shutil
import tempfile
from pathlib import Path
from utils.logs.rise_logger import log

class SevenZAdapter:
    def list_files(self, path: Path) -> list:
        log.debug(f"[SevenZAdapter] Listando conteúdo do 7z: {path.name}")
        try:
            with py7zr.SevenZipFile(path, 'r') as z:
                return [
                    {
                        "name": i.filename, 
                        "is_dir": i.is_directory,
                        "uncompressed_size": i.uncompressed # TRAVA: Enviando tamanho para o manager!
                    } 
                    for i in z.list()
                ]
        except py7zr.exceptions.PasswordRequired:
            log.error(f"[SevenZAdapter] O arquivo 7z '{path.name}' está protegido por senha.")
            raise ValueError(f"O mod '{path.name}' está protegido por senha.")
        except py7zr.exceptions.Bad7zFile:
            log.error(f"[SevenZAdapter] O arquivo 7z '{path.name}' está corrompido.")
            raise ValueError(f"O arquivo 7z '{path.name}' parece estar corrompido.")
        except Exception as e:
            log.error(f"[SevenZAdapter] Erro desconhecido ao ler 7z '{path.name}': {e}", exc_info=True)
            raise ValueError(f"Falha ao ler o arquivo 7z: {e}")

    def extract_file(self, path: Path, file_name: str, target_path: Path) -> None:
        log.debug(f"[SevenZAdapter] Extraindo '{file_name}' do 7z...")
        
        # Trava de segurança: Não permite escrever fora da pasta de destino
        try:
            target_path.resolve().relative_to(target_path.parent.resolve())
        except ValueError:
            log.critical(f"[SevenZAdapter] 🚨 Tentativa de Path Traversal bloqueada ao extrair: {file_name}")
            raise ValueError("Caminho de extração inseguro bloqueado.")

        # Usamos um diretório temporário para extrair sem estourar a memória RAM
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                with py7zr.SevenZipFile(path, 'r') as z:
                    # Extrai apenas o arquivo desejado para a pasta temp
                    z.extract(path=temp_path, targets=[file_name])
                    
                # O arquivo extraído mantém a estrutura de pastas original dentro do temp
                extracted_file = temp_path / file_name
                
                if not extracted_file.exists():
                    log.warning(f"[SevenZAdapter] O arquivo '{file_name}' não foi encontrado após a extração.")
                    raise FileNotFoundError(f"Arquivo não encontrado no 7z: {file_name}")
                
                # Move o arquivo extraído para o destino final
                shutil.move(str(extracted_file), str(target_path))
                log.debug(f"[SevenZAdapter] Extração concluída com sucesso: {target_path.name}")
                
            except py7zr.exceptions.PasswordRequired:
                log.error(f"[SevenZAdapter] Senha necessária para extrair '{file_name}'.")
                raise ValueError("Não é possível extrair: arquivo protegido por senha.")
            except Exception as e:
                log.error(f"[SevenZAdapter] Falha ao extrair '{file_name}': {e}", exc_info=True)
                raise RuntimeError(f"Falha ao extrair o arquivo do 7z: {e}")