import shutil
import uuid
import os
from pathlib import Path
from core.paths.resolver import resolve_safe_target
from core.scanner.archives.archive_manager import extract_file_from_archive
from utils.hash_utils import calculate_file_hash
from utils.logs.rise_logger import log

def _get_exact_case_path(base_path: Path, relative_dest: str) -> Path:
    """
    Resolve o Case Sensitivity: Se o arquivo já existe no Windows, pega o nome exato 
    do disco para evitar que o banco de dados salve o case errado.
    """
    if base_path.exists():
        # Se o caminho já existe, retorna o caminho exato do Windows
        return base_path.resolve()
        
    # Se não existe, vamos procurar o pai para ver se o nome do arquivo bate case-insensitive
    parent_dir = base_path.parent
    if parent_dir.exists():
        for file_in_dir in parent_dir.iterdir():
            if file_in_dir.is_file() and file_in_dir.name.lower() == base_path.name.lower():
                log.debug(f"[Copier] Ajuste de Case: '{base_path.name}' -> '{file_in_dir.name}'")
                return file_in_dir.resolve()
                
    return base_path.resolve()

def _copy_single_file(item, temporary_target, source_path):
    temporary_target.parent.mkdir(parents=True, exist_ok=True)
    
    if item["kind"] == "directory":
        shutil.copy2(item["source"], temporary_target)
    else:
        extract_file_from_archive(source_path, item["source"], temporary_target)

def copy_files_to_game(game_root, source_path, files):
    """Copia os arquivos, lida com Case Sensitivity e retorna os hashes, otimizado."""
    log.info(f"[Copier] Iniciando cópia física e segura de {len(files)} arquivos...")
    
    installed_data = [] # Vamos guardar (destino_final, target_path, item)
    source_path = Path(source_path)

    for item in files:
        dest_rel = item["destination"]
        
        # 1. Resolve o destino bruto
        target_bruto = resolve_safe_target(game_root, dest_rel)
        
        # 2. Trava Anti-Case Sensitivity (A sua ideia em ação)
        target = _get_exact_case_path(target_bruto, dest_rel)
        
        # Se o case mudou, precisamos garantir que o destino no banco reflita o real
        safe_dest = target.relative_to(game_root).as_posix()
        item["destination"] = safe_dest # Atualiza o item original para o Manager salvar o case correto
        
        # 3. Cria um nome temporário único (Anti-Fantasma e Anti-Antivírus)
        temp_name = f"{target.name}.{uuid.uuid4().hex[:8]}.install_tmp"
        temporary_target = target.with_name(temp_name)
        
        try:
            _copy_single_file(item, temporary_target, source_path)
            
            # 4. Substituição Atômica
            try:
                temporary_target.replace(target)
                log.debug(f"[Copier] Arquivo copiado com sucesso: {safe_dest}")
            except PermissionError:
                log.error(f"[Copier] Arquivo bloqueado na substituição: {safe_dest}. O jogo está aberto?")
                raise RuntimeError(f"O arquivo '{safe_dest}' está bloqueado. Feche o jogo e tente novamente.")
                
            installed_data.append((safe_dest, target))
            
        except Exception as e:
            log.error(f"[Copier] Falha ao copiar {safe_dest}: {e}", exc_info=True)
            raise
        finally:
            # 5. Garante que o arquivo temporário não fique para trás se tudo der errado
            if temporary_target.exists():
                try:
                    temporary_target.unlink()
                except Exception as e:
                    log.warning(f"[Copier] Não foi possível limpar o temporário {temp_name}: {e}")

    # 6. Cálculo de Hash Otimizado (Reaproveitando o Path já resolvido)
    log.debug(f"[Copier] Calculando hashes de integridade para {len(installed_data)} arquivos...")
    installed_hashes = {}
    installed_destinations = []
    
    for safe_dest, target_path in installed_data:
        installed_destinations.append(safe_dest)
        try:
            installed_hashes[safe_dest] = calculate_file_hash(target_path)
        except Exception as e:
            log.error(f"[Copier] Alerta: Falha ao calcular hash de '{safe_dest}'. O mod será instalado sem hash de verificação: {e}")
            # Não lançamos exceção aqui para não quebrar a instalação inteira por causa de um hash

    log.info(f"[Copier] Todos os {len(installed_destinations)} arquivos foram copiados e processados.")
    return installed_destinations, installed_hashes