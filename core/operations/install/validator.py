import os
from pathlib import Path
from core.paths.resolver import resolve_safe_target
from core.mod_manager.registry_query import find_file_owner
from utils.logs.rise_logger import log

def prepare_and_validate_files(game_root, data_root, game_key, files):
    """Valida se os arquivos podem ser instalados com checagem de permissões e caminhos."""
    if not files:
        log.warning("[Validator] Lista de arquivos vazia para validar.")
        return []

    log.debug(f"[Validator] Iniciando validação de {len(files)} arquivos...")
    valid_files = []
    
    # Trava de Segurança Extra: Garante que o data_root não está dentro do jogo
    game_root = Path(game_root).resolve()
    data_root = Path(data_root).resolve()
    try:
        data_root.relative_to(game_root)
        log.critical("[Validator] 🚨 ERRO FATAL: O data_root está dentro da pasta do jogo!")
        raise ValueError("Configuração inválida: os dados do gerenciador não podem ficar dentro do jogo.")
    except ValueError:
        pass

    # Cache de pastas já validadas para não testar permissão 500 vezes no mesmo lugar
    checked_dirs = set()

    for item in files:
        dest = item["destination"].replace("\\", "/")
        
        try:
            target = resolve_safe_target(game_root, dest)
        except ValueError as e:
            log.error(f"[Validator] Caminho inválido bloqueado: '{dest}' ({e})")
            raise ValueError(f"Caminho inválido no mod: {dest}")

        # 1. Verifica se o destino já é uma pasta (não pode ser)
        if target.exists() and not target.is_file():
            log.error(f"[Validator] O destino já existe e é uma pasta: {dest}")
            raise ValueError(f"O destino '{dest}' é uma pasta no jogo, não um arquivo.")

        # 2. Verifica se as pastas pai existem e se temos permissão de escrita
        parent_dir = target.parent
        if parent_dir not in checked_dirs:
            try:
                # Tenta criar a pasta (exist_ok=True) para ver se temos permissão
                parent_dir.mkdir(parents=True, exist_ok=True)
                
                # Verifica se o caminho não colidiu com um arquivo existente
                if not parent_dir.is_dir():
                    raise NotADirectoryError(f"O caminho '{parent_dir}' é um arquivo, não uma pasta.")
                    
                checked_dirs.add(parent_dir)
            except PermissionError:
                log.critical(f"[Validator] 🚨 PERMISSÃO NEGADA: O Windows bloqueou a escrita em '{parent_dir}'.")
                raise PermissionError(
                    f"O Windows bloqueou a escrita na pasta do jogo.\n"
                    f"Tente executar o Termitato como Administrador ou mover o jogo para outra pasta (ex: fora de 'Program Files')."
                )
            except Exception as e:
                log.error(f"[Validator] Falha ao preparar a pasta de destino '{parent_dir}': {e}")
                raise RuntimeError(f"Não foi possível criar a pasta no jogo: {e}")

        # 3. Verifica conflito de dono (Case-Insensitive)
        owner = find_file_owner(data_root, game_key, dest)
        if owner:
            action = item.get("conflict_action")
            if action != "overwrite":
                log.warning(f"[Validator] Conflito detectado! '{dest}' pertence a '{owner['name']}'")
                raise ValueError(f"Conflito com o mod '{owner['name']}': {dest}")
            else:
                log.info(f"[Validator] Sobrescrita autorizada pelo usuário para: {dest}")

        valid_files.append(item)
        
    log.info(f"[Validator] Validação concluída. {len(valid_files)} arquivos aprovados.")
    return valid_files