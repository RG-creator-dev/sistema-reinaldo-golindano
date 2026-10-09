"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: config.py
Descripción: Configuración centralizada de rutas, credenciales y parámetros
=============================================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()


class SystemConfig:
    APP_NAME = "Sistema de Gestión de Inversiones Reinaldo Golindano"
    APP_VERSION = "2.0.0"
    
    # Directorios Base y Rutas del Sistema
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
    QUOTES_DIR = os.path.join(EXPORTS_DIR, "cotizaciones")
    REPORTS_DIR = os.path.join(EXPORTS_DIR, "reportes")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    # Archivos de Datos (JSON)
    QUOTES_FILE = os.path.join(DATA_DIR, "cotizaciones.json")
    LEDGER_FILE = os.path.join(DATA_DIR, "ledger.json")
    FINANCES_FILE = os.path.join(DATA_DIR, "finanzas.json")
    PURCHASES_FILE = os.path.join(DATA_DIR, "compras.json")
    WORKSHOP_FILE = os.path.join(DATA_DIR, "servicios_taller.json")
    MOVEMENTS_FILE = os.path.join(DATA_DIR, "movimientos.json")
    
    # Rutas de Recursos Externos (Solo Lectura)
    RUTA_PUBLICIDAD_IMAGENES = r"C:\Users\TRADING_PRO\Desktop\publicidad\Img de Gemini"
    
    # Credenciales de API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
    
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    CRYPTOMUS_API_KEY = os.getenv("CRYPTOMUS_API_KEY", "")
    CRYPTOMUS_MERCHANT_ID = os.getenv("CRYPTOMUS_MERCHANT_ID", "")

    # Datos Estructurados del Emisor Fiscal (Técnico de Alta Precisión)
    EMISOR_NOMBRE = os.getenv("EMISOR_NOMBRE", "Inversiones Reinaldo Golindano Romero")
    EMISOR_RIF = os.getenv("EMISOR_RIF", "V-13508338-7")
    EMISOR_DIRECCION = os.getenv("EMISOR_DIRECCION", "FP. Calle Cuarta Etapa Manzana 9 Casa N° 28 - Guacara - Edo. Carabobo")
    EMISOR_ZONA_POSTAL = os.getenv("EMISOR_ZONA_POSTAL", "2016")
    EMISOR_TELEFONO = os.getenv("EMISOR_TELEFONO", "0424-494.91.35")
    EMISOR_EMAIL = os.getenv("EMISOR_EMAIL", "inversionesreinaldog@gmail.com")
    EMISOR_DESCRIPCION = os.getenv(
        "EMISOR_DESCRIPCION_SERVICIOS",
        "Servicio Técnico Especializado en Fotocopiadoras e Impresoras (Epson, HP, Canon, Samsung), Venta de Insumos, Repuestos y Consumibles"
    )
    
    # Parámetros Comerciales
    DEFAULT_IVA_PERCENT = 16.0  # 16% de IVA por defecto
    BCV_API_URL = "https://ve.dolarapi.com/v1/dolares/oficial"
    DEFAULT_BCV_RATE = 849.56   # Tasa de respaldo si no hay internet

    # Sincronización en la Nube (Render)
    RENDER_SYNC_URL = os.getenv("RENDER_SYNC_URL", "https://imsucopias-telegram-bot.onrender.com")
    RENDER_SYNC_TOKEN = os.getenv("RENDER_SYNC_TOKEN", "inversiones_reinaldo_golindano_sync_key")
    AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "True").lower() in ("true", "1", "t")

    # Control de Instancia de Telegram Bot (False por defecto para evitar Conflicto 409 con Render)
    ENABLE_LOCAL_TELEGRAM_POLLING = os.getenv("ENABLE_LOCAL_TELEGRAM_POLLING", "False").lower() in ("true", "1", "t")


    @classmethod
    def ensure_directories(cls):
        """Crea todos los directorios necesarios y archivos de base de datos vacíos si no existen."""
        for directory in [cls.DATA_DIR, cls.EXPORTS_DIR, cls.QUOTES_DIR, cls.REPORTS_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)
            
        # Asegurar archivos JSON vacíos sin datos basura
        for file_path in [cls.QUOTES_FILE, cls.LEDGER_FILE, cls.FINANCES_FILE, cls.PURCHASES_FILE, cls.WORKSHOP_FILE, cls.MOVEMENTS_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("[]")
