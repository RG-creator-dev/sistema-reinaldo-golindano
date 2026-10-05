"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: invoice_parser.py
Descripción: Extracción inteligente de datos de facturas y recibos con Gemini Vision.
=============================================================================
"""

import os
import json
import re
from typing import Dict, Any, Optional
from config import SystemConfig
from core.logger import app_logger


class InvoiceEmitterParser:
    """Extrae datos fiscales estructurados de facturas físicas o digitales mediante IA."""

    def __init__(self):
        self.api_key = SystemConfig.GEMINI_API_KEY

    def parse_invoice(self, file_path_or_text: str) -> Dict[str, Any]:
        """Procesa una factura en imagen o texto para extraer emisor, RIF, montos y fecha."""
        prompt = f"""
        Analiza el siguiente texto o documento correspondiente a una factura/comprobante de pago en Venezuela.
        Extrae y devuelve ÚNICAMENTE un JSON válido con la siguiente estructura:
        {{
            "emisor": "Nombre o Razón Social",
            "rif": "J-XXXXXXXX-X o V-XXXXXXXX-X",
            "numero_factura": "000000",
            "fecha": "YYYY-MM-DD",
            "subtotal": 0.0,
            "iva": 0.0,
            "total": 0.0,
            "moneda": "USD o VES",
            "concepto": "Descripción general de insumos o servicios"
        }}

        Contenido / Referencia:
        {file_path_or_text}
        """

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            raw = resp.text.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return json.loads(raw)
        except Exception as e:
            app_logger.warning(f"Error procesando factura con Gemini: {e}")
            return {
                "emisor": "Proveedor No Identificado",
                "rif": "N/A",
                "numero_factura": "S/N",
                "fecha": "",
                "total": 0.0,
                "moneda": "USD",
                "concepto": "Extracción manual requerida"
            }
