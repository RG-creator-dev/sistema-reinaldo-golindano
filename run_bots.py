"""
Script unificador para iniciar los bots de Telegram y el servidor web Flask 
(con soporte para /api/sync) en Render utilizando procesos independientes.
"""
import multiprocessing
import time
from core.logger import app_logger
from keep_alive import run_server  # Servidor web Flask para la sincronización

def run_commercial_bot():
    try:
        app_logger.info("Iniciando Bot de Comercio y Ventas...")
        from modules.dept_02_comercio_ventas.telegram_voice_bot import telegram_controller
        telegram_controller.start()
        
        while telegram_controller.is_active:
            time.sleep(1)
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
    app_logger.info("=== LEVANTANDO SERVICIOS COMPLETOS EN RENDER ===")
    
    # 1. Iniciar los bots de Telegram en procesos separados
    p1 = multiprocessing.Process(target=run_commercial_bot)
    p2 = multiprocessing.Process(target=run_finance_bot)
    
    p1.start()
    p2.start()
    
    # 2. Iniciar el servidor web Flask en el hilo principal para atender /api/sync
    try:
        app_logger.info("Iniciando servidor web Flask para sincronización...")
        run_server()
    except Exception as e:
        app_logger.error(f"Error crítico en el servidor Flask: {e}", exc_info=True)
    
    # Mantener supervisión
    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        app_logger.info("Deteniendo servicios...")
        p1.terminate()
        p2.terminate()