"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: telegram_voice_bot.py
Descripción: Bot interactivo de Telegram (@InversionesRG_bot) para recepción
             de notas de voz y mensajes de texto. Transcripción con Gemini AI,
             emisión automática de cotizaciones ReportLab y entrega en PDF.
=============================================================================
"""

import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import telebot
from telebot import apihelper
from config import SystemConfig
from core.logger import app_logger
from modules.dept_02_comercio_ventas.quote_catalog_agent import QuoteCatalogAgent
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider

# Ajuste de timeouts para conexiones móviles
apihelper.CONNECT_TIMEOUT = 15
apihelper.READ_TIMEOUT = 30


class TelegramBotController:
    """Controlador multihilo para arrancar y detener el Bot de Telegram desde la interfaz gráfica."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or SystemConfig.TELEGRAM_BOT_TOKEN
        self.bot: Optional[telebot.TeleBot] = None
        self.thread: Optional[threading.Thread] = None
        self.is_active = False
        self.agent = QuoteCatalogAgent()
        self.activity_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        self._setup_bot()

    def _setup_bot(self):
        if not self.token:
            app_logger.warning("No se configuró TELEGRAM_BOT_TOKEN.")
            return

        try:
            self.bot = telebot.TeleBot(self.token, parse_mode="HTML")
            self._register_handlers()
        except Exception as e:
            app_logger.error(f"Error inicializando telebot: {e}")

    def _log_activity(self, user_name: str, msg_type: str, details: str):
        with self._lock:
            self.activity_log.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "user": user_name,
                "type": msg_type,
                "details": details
            })
            if len(self.activity_log) > 50:
                self.activity_log.pop(0)

    def _register_handlers(self):
        if not self.bot:
            return

        @self.bot.message_handler(commands=['start', 'ayuda', 'help'])
        def send_welcome(message):
            chat_id = message.chat.id
            user = message.from_user.first_name or "Estimado Cliente"
            
            bcv = BCVExchangeRateProvider.get_official_rate()
            rate = bcv["rate"]

            welcome_msg = (
                f"👋 <b>¡Bienvenido al Asistente Técnico de Inversiones Reinaldo Golindano!</b>\n\n"
                f"Soy tu analista automatizado para cotización de insumos y servicios técnicos de impresoras y fotocopiadoras (Epson, HP, Canon, Samsung).\n\n"
                f"💵 <b>Tasa BCV del día:</b> <code>{rate:,.2f} Bs/USD</code>\n\n"
                f"<b>¿Cómo generar una cotización?</b>\n"
                f"1️⃣ <b>Escribe un mensaje de texto</b> indicando los productos o servicios que necesitas.\n"
                f"2️⃣ <b>O envíame una NOTA DE VOZ</b> 🎙️ explicándome la falla o repuesto que buscas.\n\n"
                f"📌 <i>Por defecto todas las cotizaciones incluyen IVA (16%), salvo que indiques expresamente <b>'sin IVA'</b> en tu mensaje.</i>\n\n"
                f"¡Pruébalo ahora enviando un mensaje o audio!"
            )
            self.bot.send_message(chat_id, welcome_msg)
            self._log_activity(user, "Comando", "/start recibido")

        @self.bot.message_handler(commands=['tasa'])
        def send_tasa(message):
            bcv = BCVExchangeRateProvider.get_official_rate(force_refresh=True)
            msg = (
                f"📊 <b>Tasa Oficial del Banco Central de Venezuela (BCV)</b>\n"
                f"💵 <b>Valor:</b> <code>{bcv['rate']:,.2f} Bs/USD</code>\n"
                f"📅 <b>Fecha:</b> {bcv.get('fecha', 'Hoy')}\n"
                f"🏛️ <b>Fuente:</b> {bcv.get('fuente', 'Oficial')}"
            )
            self.bot.send_message(message.chat.id, msg)

        @self.bot.message_handler(content_types=['text'])
        def handle_text_order(message):
            chat_id = message.chat.id
            user = message.from_user.first_name or "Cliente"
            texto = message.text.strip()

            if texto.startswith('/'):
                return

            self._log_activity(user, "Texto", texto[:40])
            self.bot.send_message(chat_id, "⏳ <i>Analizando requerimiento y estructurando presupuesto formal...</i>")

            # Procesar orden a través del agente
            self._process_and_reply(chat_id, user, texto)

        @self.bot.message_handler(content_types=['voice', 'audio'])
        def handle_voice_order(message):
            chat_id = message.chat.id
            user = message.from_user.first_name or "Cliente"

            self.bot.send_message(chat_id, "🎙️ <i>Recibí tu nota de voz. Transcribiendo con Gemini IA...</i>")

            try:
                # Descargar archivo de audio de Telegram
                file_info = self.bot.get_file(message.voice.file_id)
                audio_bytes = self.bot.download_file(file_info.file_path)

                # Transcribir con Gemini SDK moderno
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=SystemConfig.GEMINI_API_KEY)
                prompt_transcripcion = (
                    "Transcribe con máxima precisión técnica lo que dice esta nota de voz en español de Venezuela. "
                    "Presta especial atención a nombres de marcas (Epson, HP, Canon, Samsung), modelos (L3110, L3250, M141w, etc.), "
                    "repuestos (almohadillas, tóner 85A, fusor, rodillos, cabezal), cantidades, precios y si menciona 'sin IVA'."
                )

                resp = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                        prompt_transcripcion
                    ]
                )
                texto_transcrito = resp.text.strip() if resp.text else ""
                self._log_activity(user, "Voz Transcrita", texto_transcrito[:40])

                self.bot.send_message(
                    chat_id,
                    f"📝 <b>Transcripción detectada:</b>\n<i>\"{texto_transcrito}\"</i>\n\n⚙️ <i>Generando presupuesto técnico...</i>"
                )

                self._process_and_reply(chat_id, user, texto_transcrito)

            except Exception as e:
                app_logger.error(f"Error procesando nota de voz en Telegram: {e}", exc_info=True)
                self.bot.send_message(
                    chat_id,
                    f"⚠️ Ocurrió un inconveniente al procesar el audio: {e}\nPor favor intenta dictarlo nuevamente o envíalo en texto."
                )

    def _process_and_reply(self, chat_id: int, user_name: str, text_content: str):
        """Genera el presupuesto con QuoteCatalogAgent y lo entrega en Telegram."""
        try:
            resp = self.agent.execute("process_and_generate_quote", {
                "message_text": text_content,
                "client_name": user_name
            })

            if resp.success:
                data = resp.data
                pdf_path = data.get("pdf_path")
                quote_id = data.get("quote_id", "COT-XXXX")
                total_usd = data.get("total_usd", 0.0)
                total_bs = data.get("total_bs", 0.0)
                bcv = data.get("bcv_rate", 1.0)
                iva_pct = data.get("tax_percent", 16.0)

                iva_str = "IVA (16%) incluido" if iva_pct > 0 else "Exento de IVA"

                caption = (
                    f"📄 <b>PRESUPUESTO FORMAL: {quote_id}</b>\n"
                    f"👤 <b>Cliente:</b> {user_name}\n"
                    f"💵 <b>Total USD:</b> ${total_usd:,.2f} ({iva_str})\n"
                    f"🇻🇪 <b>Total en Bolívares (BCV {bcv:,.2f}):</b> {total_bs:,.2f} Bs\n\n"
                    f"💳 <b>Métodos de Pago:</b>\n"
                    f"• Pago Móvil / Transferencias (Banesco, Mercantil, Provincial, BDV)\n"
                    f"• Binance USDT (Binance Pay)\n\n"
                    f"🛡️ <i>Garantía técnica de 30 días en mano de obra y repuestos.</i>"
                )

                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        self.bot.send_document(
                            chat_id,
                            pdf_file,
                            caption=caption,
                            visible_file_name=f"Presupuesto_{quote_id}_{user_name}.pdf"
                        )
                else:
                    self.bot.send_message(chat_id, caption)

                self._log_activity(user_name, "PDF Entregado", f"{quote_id} - ${total_usd}")

            else:
                self.bot.send_message(
                    chat_id,
                    f"❌ No se pudo generar la cotización: {resp.message}"
                )

        except Exception as e:
            app_logger.error(f"Error enviando presupuesto por Telegram: {e}", exc_info=True)
            self.bot.send_message(chat_id, f"⚠️ Error en el generador: {e}")

    def start(self):
        """Inicia el bot en un hilo en segundo plano dedicado exclusivamente a la escucha permanente."""
        if self.is_active or not self.bot:
            return

        self.is_active = True

        def _polling_loop():
            app_logger.info("Bot de Telegram (@InversionesRG_bot) iniciado en modo polling continuo concurrente.")
            while self.is_active:
                try:
                    self.bot.infinity_polling(timeout=20, long_polling_timeout=15)
                except Exception as e:
                    if not self.is_active:
                        break
                    app_logger.warning(f"Reconexión en bucle de Telegram Bot tras evento: {e}")
                    time.sleep(3)
            app_logger.info("Servicio de escucha de Telegram Bot detenido.")

        self.thread = threading.Thread(target=_polling_loop, daemon=True, name="TelegramVoiceBotThread")
        self.thread.start()

    def stop(self):
        """Detiene de forma ordenada el bot de Telegram."""
        self.is_active = False
        if self.bot:
            try:
                self.bot.stop_polling()
            except Exception as e:
                app_logger.warning(f"Aviso al detener polling de bot: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self.is_active,
            "token_configured": bool(self.token),
            "log_count": len(self.activity_log),
            "logs": list(reversed(self.activity_log))
        }


# Instancia única controladora del Bot
telegram_controller = TelegramBotController()
