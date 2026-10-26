import json
from copy import deepcopy

import customtkinter as ctk

from ui.state.game_state import DATA_ROOT


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CONFIG_FILE = DATA_ROOT / "settings.json"

DEFAULT_SETTINGS = {
    "theme": "Sistema",
    "background": "Nenhum",
    "supercharge": "Nenhum",
    "background_music": True,
    "background_volume": 0.35,
    "animations_enabled": True,
}


# ============================================================
# 1. THEMES — PALETAS VISUAIS
# ============================================================

THEMES = {
    "Sistema": {
        "mode": "System",
        "bg_main": ("#EBEBEB", "#121212"),
        "bg_panel": ("#F2F2F2", "#1E1E1E"),
        "bg_card": ("#FFFFFF", "#2A2A2A"),
        "text_main": ("#000000", "#FFFFFF"),
        "text_muted": ("#666666", "#A0A0A0"),
        "border": ("#D0D0D0", "#383838"),
        "accent": ("#356AC3", "#6C9EFF"),
        "accent_hover": ("#2856A5", "#8AB1FF"),
        "button": ("#E0E0E0", "#333333"),
        "button_hover": ("#D0D0D0", "#444444"),
        "button_text": ("#FFFFFF", "#000000"), # <-- ADICIONADO
        "success": ("#27864A", "#65C982"),
        "warning": ("#A96900", "#F0B94D"),
        "danger": ("#C0392B", "#F16B60"),
    },

    "Escuro": {
        "mode": "Dark",
        "bg_main": "#121212",
        "bg_panel": "#1E1E1E",
        "bg_card": "#252525",
        "text_main": "#F5F5F5",
        "text_muted": "#A0A0A0",
        "border": "#383838",
        "accent": "#6C9EFF",
        "accent_hover": "#8AB1FF",
        "button": "#333333",
        "button_hover": "#444444",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#65C982",
        "warning": "#F0B94D",
        "danger": "#F16B60",
    },

    "Claro": {
        "mode": "Light",
        "bg_main": "#F0F0F0",
        "bg_panel": "#FFFFFF",
        "bg_card": "#E4E4E4",
        "text_main": "#202020",
        "text_muted": "#606060",
        "border": "#D0D0D0",
        "accent": "#356AC3",
        "accent_hover": "#2856A5",
        "button": "#E5E5E5",
        "button_hover": "#D5D5D5",
        "button_text": "#FFFFFF", # <-- ADICIONADO
        "success": "#27864A",
        "warning": "#A96900",
        "danger": "#C0392B",
    },

    "Cinza": {
        "mode": "Dark",
        "bg_main": "#181A1B",
        "bg_panel": "#222527",
        "bg_card": "#2C3033",
        "text_main": "#F0F0F0",
        "text_muted": "#A5AAAD",
        "border": "#41474B",
        "accent": "#A0AAB2",
        "accent_hover": "#C0C8CE",
        "button": "#353A3E",
        "button_hover": "#454C51",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#65C982",
        "warning": "#F0B94D",
        "danger": "#F16B60",
    },

    "Azul": {
        "mode": "Dark",
        "bg_main": "#101722",
        "bg_panel": "#172334",
        "bg_card": "#203149",
        "text_main": "#EDF4FF",
        "text_muted": "#A5B8D0",
        "border": "#304761",
        "accent": "#4D9EFF",
        "accent_hover": "#79B6FF",
        "button": "#263B54",
        "button_hover": "#344E6D",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#65C982",
        "warning": "#F0B94D",
        "danger": "#F16B60",
    },
}


# ============================================================
# 2. BACKGROUNDS — CENÁRIOS E AMBIENTAÇÃO
# ============================================================

BACKGROUNDS = {
    "Nenhum": {
        "image": None,
        "music": None,
    },

    "Mahabre - Cidade": {
        "image": "assets/backgrounds/mahabre_city.png",
        "music": "assets/audio/Fear & Hunger OST - Ma'habre Streets.mp3",
    },

    "Mahabre - Rua": {
        "image": "assets/backgrounds/mahabre_street.png",
        "music": "assets/audio/Fear & Hunger OST - Ma'habre Streets.mp3",
    },
}


# ============================================================
# 3. SUPERCHARGES — EXPERIÊNCIAS ESPECIAIS
# ============================================================

SUPERCHARGES = {
    "Nenhum": {
        "theme_override": None,
        "effects": [],
    },

    "Halloween": {
        "theme_override": "Halloween",
        "effects": ["hover_glow", "special_transitions"],
    },

    "Natal": {
        "theme_override": "Natal",
        "effects": ["seasonal_accents"],
    },

    "Valentine": {
        "theme_override": "Valentine",
        "effects": ["soft_highlights"],
    },

    "Super Dark": {
        "theme_override": "Super Dark",
        "effects": [],
    },

    "Super Light": {
        "theme_override": "Super Light",
        "effects": [],
    },
}


# ============================================================
# PALETAS ESPECIAIS
# ============================================================

SPECIAL_THEMES = {
    "Halloween": {
        "mode": "Dark",
        "bg_main": "#160E0A",
        "bg_panel": "#24150F",
        "bg_card": "#352016",
        "text_main": "#FFF0E1",
        "text_muted": "#C0A18D",
        "border": "#59331D",
        "accent": "#FF8C00",
        "accent_hover": "#FFAA33",
        "button": "#402619",
        "button_hover": "#59331D",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#80C878",
        "warning": "#FFC04D",
        "danger": "#FF6257",
    },

    "Natal": {
        "mode": "Dark",
        "bg_main": "#101711",
        "bg_panel": "#19251B",
        "bg_card": "#233328",
        "text_main": "#F0F8EF",
        "text_muted": "#A9BDAA",
        "border": "#354A39",
        "accent": "#D44B4B",
        "accent_hover": "#F06A6A",
        "button": "#2C4031",
        "button_hover": "#3B5541",
        "button_text": "#FFFFFF", # <-- ADICIONADO
        "success": "#72CF86",
        "warning": "#E9C46A",
        "danger": "#F16B60",
    },

    "Valentine": {
        "mode": "Dark",
        "bg_main": "#1A1018",
        "bg_panel": "#281725",
        "bg_card": "#382034",
        "text_main": "#FFF0FA",
        "text_muted": "#C6A7BC",
        "border": "#57354E",
        "accent": "#F078AE",
        "accent_hover": "#FF9BC7",
        "button": "#44273D",
        "button_hover": "#59334F",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#80C878",
        "warning": "#F0C66A",
        "danger": "#FF7185",
    },

    "Super Dark": {
        "mode": "Dark",
        "bg_main": "#080808",
        "bg_panel": "#101010",
        "bg_card": "#181818",
        "text_main": "#F5F5F5",
        "text_muted": "#909090",
        "border": "#292929",
        "accent": "#FFFFFF",
        "accent_hover": "#D0D0D0",
        "button": "#1C1C1C",
        "button_hover": "#292929",
        "button_text": "#000000", # <-- ADICIONADO
        "success": "#65C982",
        "warning": "#F0B94D",
        "danger": "#F16B60",
    },

    "Super Light": {
        "mode": "Light",
        "bg_main": "#FFFFFF",
        "bg_panel": "#FAFAFA",
        "bg_card": "#F0F0F0",
        "text_main": "#111111",
        "text_muted": "#666666",
        "border": "#DADADA",
        "accent": "#202020",
        "accent_hover": "#444444",
        "button": "#EAEAEA",
        "button_hover": "#DADADA",
        "button_text": "#FFFFFF", # <-- ADICIONADO
        "success": "#27864A",
        "warning": "#A96900",
        "danger": "#C0392B",
    },
}


# ============================================================
# CONFIGURAÇÕES — CARREGAMENTO E PERSISTÊNCIA
# ============================================================

def load_settings() -> dict:
    settings = deepcopy(DEFAULT_SETTINGS)

    if not CONFIG_FILE.exists():
        return settings

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            saved_settings = json.load(file)

        if not isinstance(saved_settings, dict):
            return settings

        settings.update(saved_settings)

    except (OSError, json.JSONDecodeError):
        return settings

    if settings.get("theme") == "Halloween":
        settings["theme"] = "Escuro"
        if settings.get("supercharge") in (None, "Nenhum"):
            settings["supercharge"] = "Halloween"

    if settings.get("theme") not in THEMES:
        settings["theme"] = DEFAULT_SETTINGS["theme"]

    if settings.get("background") not in BACKGROUNDS:
        settings["background"] = "Nenhum"

    if settings.get("supercharge") not in SUPERCHARGES:
        settings["supercharge"] = "Nenhum"

    try:
        volume = float(settings["background_volume"])
        settings["background_volume"] = max(0.0, min(1.0, volume))
    except (TypeError, ValueError):
        settings["background_volume"] = DEFAULT_SETTINGS["background_volume"]

    return settings


def save_settings(settings: dict) -> None:
    if not isinstance(settings, dict):
        raise TypeError("settings precisa ser um dicionário.")

    current_settings = load_settings()
    current_settings.update(settings)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(current_settings, file, indent=4, ensure_ascii=False)


# ============================================================
# RESOLUÇÃO DO TEMA ATIVO
# ============================================================

def get_theme_colors(
    theme_name: str,
    supercharge_name: str = "Nenhum",
) -> dict:
    if theme_name not in THEMES:
        theme_name = "Escuro"

    colors = deepcopy(THEMES[theme_name])

    supercharge = SUPERCHARGES.get(
        supercharge_name,
        SUPERCHARGES["Nenhum"],
    )

    override = supercharge.get("theme_override")

    if override in SPECIAL_THEMES:
        colors = deepcopy(SPECIAL_THEMES[override])


    # TRAVA DELUXE: Resolve as tuplas (claro, escuro) para uma única cor (string)
    # para que o ttk.Treeview e outros componentes nativos não quebrem.
    final_colors = {}
    for key, value in colors.items():
        if isinstance(value, tuple):
            # Se for tupla, pega o índice 1 (Dark) se o modo for Dark, senão índice 0 (Light)
            if colors["mode"] == "Dark" or (colors["mode"] == "System" and ctk.get_appearance_mode() == "Dark"):
                final_colors[key] = value[1]
            else:
                final_colors[key] = value[0]
        else:
            final_colors[key] = value

    return final_colors

def get_active_theme_colors() -> dict:
    settings = load_settings()
    return get_theme_colors(settings["theme"], settings["supercharge"])


def get_background_config(background_name: str = None) -> dict:
    if background_name is None:
        background_name = load_settings()["background"]

    background = BACKGROUNDS.get(
        background_name,
        BACKGROUNDS["Nenhum"],
    )

    return deepcopy(background)