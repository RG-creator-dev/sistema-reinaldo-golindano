"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Punto de Entrada Principal con Consola (main.py)
=============================================================================
"""

import sys
from config import SystemConfig
from core.logger import app_logger
from ui.main_window import MainWindow


def main():
    """Inicializa la configuración, directorios, bot en segundo plano y bucle gráfico principal."""
    app_logger.info("=" * 70)
    app_logger.info(f"Iniciando {SystemConfig.APP_NAME} (v{SystemConfig.APP_VERSION})")
    app_logger.info("=" * 70)

    # Asegurar estructura de carpetas
    SystemConfig.ensure_directories()
    app_logger.info(f"Rutas del sistema listas. Carpeta de exportación: {SystemConfig.QUOTES_DIR}")

    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        app_logger.critical(f"Error fatal en la ejecución de la aplicación: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
