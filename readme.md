# 🕯️ Termitat One Manager V3.2

Um gerenciador de mods moderno, seguro e independente para **Fear & Hunger** e **Fear & Hunger 2: Termina**.

![Versão](https://img.shields.io/badge/vers%C3%A3o-3.2-brightgreen)
![Plataforma](https://img.shields.io/badge/plataforma-Windows-blue)
![Licença](https://img.shields.io/badge/licen%C3%A7a-GPL--3.0-orange)

## ✨ Funcionalidades
- **Instalação Segura:** Criação de backups automáticos e rollback em caso de falha.
- **Resolução Inteligente:** Identifica automaticamente onde os arquivos do mod devem ser colocados, mesmo sem a pasta `www/`.
- **Suporte a Formatos:** Instala mods em `.zip`, `.rar` e `.7z`.
- **Sistema de Conflitos:** Avisa se dois mods alteram o mesmo arquivo e permite escolher qual manter.
- **Temas e Imersão:** Temas escuros, claros e especiais (Halloween, Natal), além de cenários de fundo (em breve).
- **Modo Vanilla:** Desinstalação limpa, restaurando 100% dos arquivos originais do jogo.

## 🚀 Como Usar (Para Usuários)
1. Baixe o arquivo `TermitatoModManager.exe` na aba de [Releases](link_para_releases).
2. Coloque o `.exe` em uma pasta de sua preferência.
3. Abra o programa. Ele detectará automaticamente os jogos instalados na sua Steam.
4. Arraste seus mods (ZIP/RAR/7z) para dentro do gerenciador e clique em "Instalar".

## 🛠️ Como Compilar (Para Desenvolvedores)
Se você quiser rodar o código-fonte ou compilar o seu próprio `.exe`:
1. Clone o repositório: `git clone https://github.com/seu-usuario/termitato.git`
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o app: `python gui.py`
4. Para gerar o executável: `pyinstaller --noconsole --onefile ...` (veja a documentação interna).

## ⚠️ Aviso Legal e Créditos
- Este software foi criado com o auxílio de **Inteligência Artificial** e **não possui fins lucrativos**.
- **Fear & Hunger** e **Fear & Hunger 2: Termina** são propriedade intelectual de **Miro Haverinen**. Este é um projeto feito por fãs (fan-made) e não possui vínculo oficial com o criador.
- Todo o código-fonte deste gerenciador é aberto e livre para a comunidade.

## 🤝 Contribuições
Sinta-se à vontade para abrir *Issues* com bugs e sugestões, ou enviar *Pull Requests* com melhorias! Toda ajuda é bem-vinda.