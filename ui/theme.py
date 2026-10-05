"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: ui/theme.py
Descripción: Paleta cromática corporativa y tipografías para CustomTkinter
=============================================================================
"""

class Theme:
    # Fondos y Paneles
    BG_DARK = "#0f172a"        # Fondo base principal (Slate 900)
    SIDEBAR_BG = "#090d16"     # Menú lateral oscuro
    CARD_BG = "#1e293b"        # Fondo de tarjetas y contenedores (Slate 800)
    CARD_BORDER = "#334155"    # Bordes sutiles (Slate 700)
    INPUT_BG = "#0f172a"       # Fondo de inputs y campos de texto
    
    # Acentos y Acciones
    PRIMARY = "#2563eb"        # Azul tecnológico corporativo (Blue 600)
    PRIMARY_HOVER = "#1d4ed8"  # Hover primario
    SUCCESS = "#16a34a"        # Verde éxito / Operación correcta (Green 600)
    SUCCESS_HOVER = "#15803d"
    WARNING = "#f59e0b"        # Ámbar alerta / Stock bajo (Amber 500)
    DANGER = "#ef4444"         # Rojo error / Crítico
    PURPLE = "#7c3aed"         # Púrpura IA / Diagnósticos avanzados (Violet 600)
    PURPLE_HOVER = "#6d28d9"
    CYAN = "#06b6d4"           # Cyan enlaces e importación Zoom

    # Tipografía y Textos
    TEXT_MAIN = "#f8fafc"      # Texto de alta lectura (Slate 50)
    TEXT_MUTED = "#94a3b8"     # Texto secundario (Slate 400)
    TEXT_DIM = "#64748b"       # Texto deshabilitado o notas al pie

    # Fuentes Estándar
    FONT_HEADLINE = ("Segoe UI", 18, "bold")
    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_CODE = ("Consolas", 10)
