"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: quote_catalog_agent.py
Descripción: Agente de Cotizaciones y Catálogo encargado de estructurar pedidos
             (por texto o voz transcrita) mediante Gemini AI y generar los
             presupuestos formales PDF con ReportLab.
=============================================================================
"""

import os
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger
from modules.dept_02_comercio_ventas.pdf_generator import PDFQuoteGenerator
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider


class QuoteCatalogAgent(BaseAgent):
    """Agente especialista en estructurar cotizaciones, detectar IVA y emitir presupuestos."""

    def __init__(self):
        super().__init__(
            agent_id="cotizador_catalogo",
            name="Agente de Cotizaciones y Catálogo",
            department="Comercio y Ventas",
            description="Procesa pedidos de clientes por voz/texto, extrae ítems, calcula IVA/BCV y genera presupuestos en PDF."
        )

    def _get_next_quote_id(self) -> str:
        """Determina el siguiente correlativo numérico de cotización (COT-XXXX)."""
        if not os.path.exists(SystemConfig.QUOTES_FILE):
            return "COT-1001"

        try:
            with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
            if not records:
                return "COT-1001"

            max_num = 1000
            for r in records:
                qid = str(r.get("quote_id", ""))
                nums = re.findall(r'\d+', qid)
                if nums:
                    num = int(nums[0])
                    if num > max_num:
                        max_num = num
            return f"COT-{max_num + 1}"
        except Exception as e:
            app_logger.warning(f"Error obteniendo correlativo: {e}")
            return f"COT-{int(time.time()) % 10000}"

    def _save_quote_record(self, record: Dict[str, Any]):
        """Persiste la cotización en cotizaciones.json manteniendo integridad."""
        records = []
        if os.path.exists(SystemConfig.QUOTES_FILE):
            try:
                with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []

        records.append(record)
        try:
            with open(SystemConfig.QUOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando cotización en JSON: {e}")

    def _parse_message_with_gemini(self, message_text: str) -> Dict[str, Any]:
        """Utiliza Gemini AI para extraer la intención, cliente, ítems, precios y condición de IVA."""
        sys_prompt = """
        Eres el asistente técnico de ventas de 'Inversiones Reinaldo Golindano' (taller especializado en impresoras Epson, HP, Canon, Samsung, venta de tóners, insumos y repuestos en Carabobo, Venezuela).
        Tu tarea es interpretar mensajes u órdenes dictadas (provenientes de Telegram o notas de voz) y estructurar una cotización formal.

        REGLAS ESTRICTAS:
        1. Identifica el nombre del cliente, empresa, teléfono y RIF si están presentes en el texto. Si no, usa valores por defecto lógicos.
        2. Extrae todos los ítems mencionados con su cantidad, precio unitario en USD y especificaciones técnicas precisas.
        3. DETECCIÓN DE IVA:
           - Por defecto, TODAS las cotizaciones deben incluir IVA (16%), por lo que 'sin_iva' debe ser FALSE.
           - ÚNICAMENTE si el usuario indica explícitamente palabras como: "sin iva", "exento", "no le metas iva", "libre de iva", marca 'sin_iva': TRUE.
        4. Si no se especificó un precio para un ítem común de taller, asigna un valor de referencia prudente de mercado (ej: Reseteo almohadillas Epson: $15.00, Mantenimiento preventivo: $20.00, Tóner HP 85A genérico: $18.00).

        Devuelve ÚNICAMENTE un JSON válido con esta estructura:
        {
          "client_name": "Nombre del cliente",
          "client_rif": "V-XXXXX o J-XXXXX o N/A",
          "client_phone": "Teléfono o N/A",
          "client_company": "Nombre de empresa o Particular",
          "sin_iva": false,
          "items": [
            {
              "description": "Descripción clara del repuesto o servicio",
              "specs": "Detalles técnicos (modelo de equipo, color, compatibilidad)",
              "qty": 1,
              "price_usd": 25.0
            }
          ],
          "notes": "Observaciones técnicas pertinentes"
        }
        """

        try:
            raw_response = self.call_gemini(prompt=message_text, system_instruction=sys_prompt)
            clean_json = raw_response
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            return json.loads(clean_json)
        except Exception as e:
            app_logger.warning(f"Error analizando orden con Gemini ({e}). Usando parser heurístico local.")
            return self._parse_message_locally(message_text)

    def _parse_message_locally(self, message_text: str) -> Dict[str, Any]:
        """Parser de contingencia en caso de indisponibilidad de API."""
        lower_txt = message_text.lower()
        sin_iva = any(x in lower_txt for x in ["sin iva", "siniva", "exento", "no iva", "libre de iva"])

        # Intentar extraer teléfono
        phone_match = re.search(r'(\+?58\s?|0)?4\d{2}[\s\-]?\d{7}', message_text)
        client_phone = phone_match.group(0) if phone_match else "0424-XXXXXXX"

        # Ítems básicos basados en el texto
        items = []
        lines = message_text.split("\n")
        for line in lines:
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 3:
                continue
            # Buscar si tiene precio (ej: $20 o 20$)
            p_match = re.search(r'\$?(\d+([.,]\d+)?)\$?', line_clean)
            price = float(p_match.group(1).replace(",", ".")) if p_match else 20.0
            items.append({
                "description": line_clean[:45],
                "specs": "Servicio técnico / Insumo especializado",
                "qty": 1,
                "price_usd": price
            })

        if not items:
            items.append({
                "description": "Servicio Técnico y Diagnóstico Especializado",
                "specs": "Mano de obra y evaluación en banco de pruebas",
                "qty": 1,
                "price_usd": 25.0
            })

        return {
            "client_name": "Cliente Solicitante",
            "client_rif": "N/A",
            "client_phone": client_phone,
            "client_company": "Particular",
            "sin_iva": sin_iva,
            "items": items,
            "notes": "Generado mediante sistema de procesamiento de órdenes."
        }

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Agente Cotizador ejecutando tarea: {task_type}")

        if task_type == "process_and_generate_quote":
            return self.process_and_generate_quote(payload)
        elif task_type == "parse_order":
            msg = payload.get("message_text", "")
            data = self._parse_message_with_gemini(msg)
            return AgentResponse(success=True, data=data)
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

    def process_and_generate_quote(self, payload: Dict[str, Any]) -> AgentResponse:
        """
        Procesa una orden completa (manual o vía IA), calcula montos, aplica tasa BCV
        y genera el documento PDF formal.
        """
        message_text = payload.get("message_text", "")
        manual_items = payload.get("items")
        client_name = payload.get("client_name")

        if manual_items:
            # Entrada manual o estructurada
            parsed_data = {
                "client_name": client_name or "Cliente Inversiones Reinaldo Golindano",
                "client_rif": payload.get("client_rif", "N/A"),
                "client_phone": payload.get("client_phone", "N/A"),
                "client_company": payload.get("client_company", "Particular"),
                "sin_iva": payload.get("sin_iva", False),
                "items": manual_items,
                "notes": payload.get("notes", "")
            }
        else:
            # Procesar texto dictado o mensaje de voz con IA
            parsed_data = self._parse_message_with_gemini(message_text)

        # Determinar alícuota de IVA: 16% por defecto, 0% si sin_iva es True
        sin_iva = parsed_data.get("sin_iva", False)
        tax_percent = 0.0 if sin_iva else SystemConfig.DEFAULT_IVA_PERCENT

        # Obtener Tasa Oficial del BCV
        bcv_info = BCVExchangeRateProvider.get_official_rate()
        bcv_rate = bcv_info["rate"]

        quote_id = self._get_next_quote_id()

        try:
            pdf_path = PDFQuoteGenerator.generate(
                quote_id=quote_id,
                client_name=parsed_data.get("client_name", "Cliente"),
                client_rif=parsed_data.get("client_rif", "N/A"),
                client_phone=parsed_data.get("client_phone", "N/A"),
                client_company=parsed_data.get("client_company", "Particular"),
                items=parsed_data.get("items", []),
                tax_percent=tax_percent,
                bcv_rate=bcv_rate,
                notes=parsed_data.get("notes", "")
            )

            # Calcular totales para registro
            subtotal = sum(float(it.get("qty", 1)) * float(it.get("price_usd", 0.0)) for it in parsed_data.get("items", []))
            tax_amt = round(subtotal * (tax_percent / 100.0), 2)
            total_usd = round(subtotal + tax_amt, 2)
            total_bs = round(total_usd * bcv_rate, 2)

            record = {
                "quote_id": quote_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "client_name": parsed_data.get("client_name"),
                "client_rif": parsed_data.get("client_rif"),
                "client_phone": parsed_data.get("client_phone"),
                "items": parsed_data.get("items"),
                "subtotal_usd": subtotal,
                "tax_percent": tax_percent,
                "tax_usd": tax_amt,
                "total_usd": total_usd,
                "bcv_rate": bcv_rate,
                "total_bs": total_bs,
                "pdf_path": pdf_path,
                "status": "Emitida"
            }

            self._save_quote_record(record)
            self.emit_event("quote_generated", record)

            return AgentResponse(
                success=True,
                data=record,
                message=f"Presupuesto {quote_id} generado exitosamente en PDF."
            )
        except Exception as e:
            app_logger.error(f"Error generando PDF de cotización: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                message=f"Error generando el documento PDF: {str(e)}"
            )
