"""
Script unificador para iniciar los bots de Telegram de Inversiones Reinaldo Golindano en Render.
"""
import threading
import time
from core.logger import app_logger

def run_commercial_bot():
    try:
        app_logger.info("Iniciando Bot de Comercio y Ventas...")
        from modules.dept_02_comercio_ventas.telegram_voice_bot import main as start_commercial
        start_commercial()
    except Exception as e:
        app_logger.error(f"Error en Bot de Comercio: {e}", exc_info=True)

def run_finance_bot():
    try:
        app_logger.info("Iniciando Bot de Administración y Finanzas...")
        from modules.dept_04_administracion_finanzas.telegram_finanzas_bot import main as start_finance
        start_finance()
    except Exception as e:
        app_logger.error(f"Error en Bot de Finanzas: {e}", exc_info=True)

if __name__ == "__main__":
    app_logger.info("=== LEVANTANDO SERVICIOS DE TELEGRAM EN LA NUBE ===")
    
    # Lanzar cada bot en un hilo separado para que corran simultáneamente
    t1 = threading.Thread(target=run_commercial_bot, daemon=True)
    t2 = threading.Thread(target=run_finance_bot, daemon=True)
    
    t1.start()
    t2.start()
    
    # Mantener el proceso principal activo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app_logger.info("Deteniendo servicios...")