import hashlib
import os
from pathlib import Path
from utils.logs.rise_logger import log

def calculate_file_hash(file_path: str | Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    """
    Calcula o SHA-256 com buffers otimizados e detecção de concorrência.
    Se o arquivo mudar de tamanho durante a leitura, um erro é lançado.
    """
    path = Path(file_path)
    log.debug(f"[HashUtils] Calculando hash SHA-256 para: {path.name}")
    
    try:
        # Trava 1: Tenta capturar o estado inicial do arquivo (evita a corrida de I/O)
        stat_inicial = path.stat()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"O caminho não é um arquivo válido: {path}")
    except FileNotFoundError:
        log.error(f"[HashUtils] Arquivo não encontrado para hash: {path}")
        raise
    except PermissionError:
        log.error(f"[HashUtils] Sem permissão de leitura no arquivo: {path}")
        raise

    digest = hashlib.sha256()
    
    try:
        with path.open("rb") as file:
            # Trava 2: Buffer de 4MB (mais rápido que 1MB e seguro para RAM)
            for chunk in iter(lambda: file.read(chunk_size), b""):
                digest.update(chunk)
                
        # Trava 3: Verificação de Concorrência (O arquivo mudou no meio do caminho?)
        stat_final = path.stat()
        if stat_inicial.st_size != stat_final.st_size or stat_inicial.st_mtime != stat_final.st_mtime:
            log.critical(f"[HashUtils] 🚨 CONCORRÊNCIA: O arquivo '{path.name}' foi modificado durante o cálculo do hash!")
            raise RuntimeError(f"Arquivo modificado durante o processo de leitura: {path.name}")

        hash_final = digest.hexdigest()
        log.debug(f"[HashUtils] Hash concluído para {path.name} ({stat_inicial.st_size} bytes): {hash_final[:8]}...")
        return hash_final
        
    except PermissionError:
        log.error(f"[HashUtils] Acesso negado (arquivo bloqueado por outro processo?): {path}")
        raise PermissionError(f"Sem permissão para ler o arquivo: {path.name}")
    except Exception as e:
        log.error(f"[HashUtils] Erro inesperado ao ler o arquivo {path}: {e}", exc_info=True)
        raise