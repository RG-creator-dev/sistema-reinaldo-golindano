"""
Script unificador para iniciar los bots de Telegram y el servidor web en Render
utilizando procesos independientes para evitar conflictos de hilos.
"""
import multiprocessing
import time
from core.logger import app_logger
from keep_alive import keep_alive  # Servidor web fantasma para Render

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
    app_logger.info("=== LEVANTANDO SERVICIOS DE TELEGRAM EN LA NUBE (MULTIPROCESS) ===")
    
    # 1. Lanzar los bots en procesos separados (cada uno con su propio intérprete y hilo principal)
    p1 = multiprocessing.Process(target=run_commercial_bot)
    p2 = multiprocessing.Process(target=run_finance_bot)
    
    p1.start()
    p2.start()
    
    # 2. Ejecutar el servidor web keep_alive en el proceso principal para atender el puerto de Render
    try:
        app_logger.info("Iniciando servidor web principal (keep_alive)...")
        keep_alive()
    except Exception as e:
        app_logger.error(f"Error crítico en keep_alive: {e}", exc_info=True)
    
    # Mantener el proceso vivo y supervisar
    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        app_logger.info("Deteniendo servicios...")
        p1.terminate()
        p2.terminate()