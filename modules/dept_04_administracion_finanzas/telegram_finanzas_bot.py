"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: telegram_finanzas_bot.py
Descripción: Bot de Telegram para recepción de comprobantes y gestión contable.
=============================================================================
"""

import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.logger import app_logger
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Inicializar agente contable
contable_agent = AccountingAgent()

# Obtener el token directamente desde el entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN_ACTIVO_FINANZAS")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de bienvenida del bot."""
    user = update.effective_user
    await update.message.reply_text(
        f"¡Hola, {user.first_name}! Soy tu Agente Administrador y Contable.\n"
        "Envíame una foto de tu comprobante de pago con una descripción (ej. 'Gasolina', 'Sueldo', 'Repuestos') "
        "y lo registraré automáticamente en las finanzas de la empresa."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la recepción de imágenes de comprobantes de pago."""
    message = update.message
    if not message.photo:
        return

    await message.reply_text("📥 Capture recibido. Analizando comprobante con IA y registrando en Finanzas...")

    image_path = None
    try:
        # Obtener la foto de mayor resolución
        photo_file = await message.photo[-1].get_file()
        
        # Crear directorio temporal si no existe
        os.makedirs("temp_receipts", exist_ok=True)
        image_path = os.path.join("temp_receipts", f"receipt_{message.chat_id}_{int(photo_file.file_id[-6:], 36)}.jpg")
        
        # Descargar el archivo
        await photo_file.download_to_drive(image_path)
        
        caption = message.caption or ""
        
        # Ejecutar tarea en el Agente Contable
        response = contable_agent.execute("process_telegram_receipt", {
            "image_path": image_path,
            "caption": caption
        })

        if response.success:
            await message.reply_text(f"✅ ¡Transacción registrada con éxito!\n\n{response.message}")
        else:
            await message.reply_text(f"❌ Error al procesar el comprobante:\n{response.message}")

    except Exception as e:
        app_logger.error(f"Error inesperado al procesar imagen en bot: {e}", exc_info=True)
        await message.reply_text(f"⚠️ Ocurrió un error inesperado al procesar la imagen: {str(e)}")

    finally:
        # Limpiar archivo temporal de forma segura
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass

def main() -> None:
    """Función principal para iniciar el bot de Telegram."""
    if not TELEGRAM_TOKEN:
        app_logger.error("No se encontró el token de Telegram para Finanzas en el entorno (.env).")
        print("Error: Configura TELEGRAM_BOT_API_TOKEN_ACTIVO_FINANZAS en tu archivo .env")
        return

    app_logger.info("Iniciando Bot de Telegram para Administración y Finanzas...")
    
    # Configurar la aplicación con tiempos de espera ampliados (timeouts) y el token del .env
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .connect_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    # Registrar manejadores
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app_logger.info("Bot de Telegram para Administración y Finanzas iniciado correctamente desde el .env...")
    
    # Iniciar el bot en modo polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()