"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Punto de Entrada del Servidor Web (app.py) para Render y Gunicorn
=============================================================================
"""

import os
from keep_alive import app, run_server

# Exponer la instancia de Flask para Gunicorn / WSGI
application = app

if __name__ == "__main__":
    run_server()
