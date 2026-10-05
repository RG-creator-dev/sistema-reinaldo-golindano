"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: accounting_agent.py
Descripción: Agente Administrador y Contable con gestión de Saldo Inicial,
             registro en tiempo real, visión con Gemini 3.8 y Cierre Mensual.
=============================================================================
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from PIL import Image
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger
from modules.dept_04_administracion_finanzas.payment_gateways import (
    PaymentGatewayManager,
    BCVExchangeRateProvider
)


class AccountingAgent(BaseAgent):
    """Agente de Administración y Finanzas del sistema."""

    def __init__(self, gateway_manager: Optional[PaymentGatewayManager] = None):
        super().__init__(
            agent_id="administrador_contable",
            name="Agente Administrador y Contable",
            department="Administración y Finanzas",
            description="Control contable con saldo inicial, registro en tiempo real y cierre mensual."
        )
        self.gateway_manager = gateway_manager or PaymentGatewayManager()
        
        # Configurar la API key de Gemini para el procesamiento de visión
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

    def _get_settings_path(self) -> str:
        """Asegura la ruta para guardar configuraciones del agente como el saldo inicial."""
        base_dir = os.path.dirname(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "accounting_settings.json")

    def _load_settings(self) -> Dict[str, Any]:
        """Carga las configuraciones guardadas (ej. saldo inicial)."""
        path = self._get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"initial_balance_usd": 0.0}

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Guarda las configuraciones del agente."""
        path = self._get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando configuraciones contables: {e}")

    def _load_ledger(self) -> List[Dict[str, Any]]:
        """Carga las transacciones directamente desde el archivo principal del Libro Mayor."""
        ledger_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
        if os.path.exists(ledger_path):
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                app_logger.error(f"Error cargando ledger principal: {e}")
        return []

    def _save_ledger(self, data: List[Dict[str, Any]]) -> None:
        """Guarda y sincroniza las transacciones para que se actualicen al instante en la UI."""
        try:
            ledger_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
            finances_path = getattr(SystemConfig, "FINANCES_FILE", "data/finances.json")
            
            os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

            with open(ledger_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            if finances_path and finances_path != ledger_path:
                os.makedirs(os.path.dirname(finances_path), exist_ok=True)
                with open(finances_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            app_logger.error(f"Error guardando ledger principal: {e}")

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Agente Contable ejecutando tarea: {task_type}")

        if task_type == "record_transaction":
            return self.record_transaction(payload)
        elif task_type == "set_initial_balance":
            return self.set_initial_balance(payload)
        elif task_type == "process_telegram_receipt":
            image_path = payload.get("image_path")
            caption = payload.get("caption", "")
            return self.process_telegram_receipt(image_path, caption)
        elif task_type == "get_financial_summary":
            year = payload.get("year")
            month = payload.get("month")
            return self.get_financial_summary(year=year, month=month)
        elif task_type == "monthly_close":
            year = payload.get("year")
            month = payload.get("month")
            return self.perform_monthly_close(year=year, month=month)
        elif task_type == "reconcile_crypto":
            return self.reconcile_crypto(payload)
        elif task_type == "create_payment_link":
            return self.create_payment_link(payload)
        else:
            return AgentResponse(
                success=False,
                message=f"Tarea '{task_type}' no reconocida por el Agente Contable."
            )

    def set_initial_balance(self, payload: Dict[str, Any]) -> AgentResponse:
        """Establece o actualiza el saldo inicial en USD requerido por la interfaz gráfica."""
        amount_usd = float(payload.get("initial_balance_usd", 0.0))
        settings = self._load_settings()
        settings["initial_balance_usd"] = round(amount_usd, 2)
        self._save_settings(settings)

        return AgentResponse(
            success=True,
            data=settings,
            message=f"Saldo inicial configurado correctamente en ${amount_usd:,.2f} USD."
        )

    def record_transaction(self, payload: Dict[str, Any]) -> AgentResponse:
        """Registra un nuevo ingreso o gasto reflejándose inmediatamente en la app y el bot."""
        t_type = payload.get("type", "Egreso")
        description = payload.get("description", "Operación sin descripción")
        method = payload.get("method", "Pago Móvil")
        category = payload.get("category", "General")
        ref_code = payload.get("ref_code", "")

        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))
        if rate <= 0:
            rate = 1.0

        raw_amount_usd = float(payload.get("amount_usd", 0.0))
        raw_amount_bs = float(payload.get("amount_bs", 0.0))
        currency_origin = payload.get("currency", "USD")

        if currency_origin == "BS" and raw_amount_bs > 0:
            amount_usd = round(raw_amount_bs / rate, 2)
            amount_bs = round(raw_amount_bs, 2)
        else:
            amount_usd = round(raw_amount_usd, 2)
            amount_bs = round(amount_usd * rate, 2)

        record = {
            "id": f"TRX-{int(time.time() * 1000)}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": t_type,
            "amount_usd": amount_usd,
            "bcv_rate": rate,
            "amount_bs": amount_bs,
            "method": method,
            "category": category,
            "description": description,
            "ref_code": ref_code
        }

        ledger = self._load_ledger()
        ledger.append(record)
        self._save_ledger(ledger)

        self.emit_event("transaction_recorded", record)
        return AgentResponse(
            success=True,
            data=record,
            message=f"Transacción {record['id']} registrada con éxito: ${amount_usd:,.2f} USD ({amount_bs:,.2f} Bs a tasa {rate} BCV)."
        )

    def call_gemini_with_image(self, prompt: str, image_path: str, model_name: str = "gemini-3.8-flash") -> str:
        """Procesa la imagen directamente con Gemini 3.8 y respaldo en 3.6."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró el archivo de imagen en: {image_path}")

        try:
            img = Image.open(image_path)
        except Exception as e:
            raise Exception(f"No se pudo abrir la imagen con PIL: {e}")

        models_to_try = [model_name, "gemini-3.8-flash", "gemini-3.6-flash"]
        
        response = None
        last_err = None
        for m in models_to_try:
            try:
                model = genai.GenerativeModel(m)
                response = model.generate_content([img, prompt])
                if response and response.text:
                    break
            except Exception as ex:
                last_err = ex
                continue
        
        if not response or not response.text:
            raise Exception(f"No se pudo obtener respuesta de los modelos Gemini Vision: {last_err}")
            
        return response.text

    def process_telegram_receipt(self, image_path: str, caption: str = "") -> AgentResponse:
        """Analiza el comprobante enviado por Telegram y lo registra en tiempo real."""
        if not image_path or not os.path.exists(image_path):
            return AgentResponse(success=False, message="No se encontró la imagen del comprobante.")

        prompt_vision = f"""
Analiza este comprobante de pago bancario. Extrae la información en formato JSON estricto con estas llaves:
1. "amount_number": El monto exacto reflejado en el comprobante en números (ej: 4.61 o 12500.00).
2. "currency": La moneda explícita del ticket ("BS" o "USD").
3. "bank_origin": El banco o método emisor (ej: Provincial, Banesco, Mercantil, Zelle, Binance).
4. "ref_code": El número de referencia o confirmación.
5. "transaction_type": "Egreso" (pago realizado) o "Ingreso" (pago recibido).

Texto adicional del usuario: "{caption}"

Devuelve ÚNICAMENTE un JSON válido sin texto adicional ni bloques de markdown.
"""

        try:
            respuesta_ia = self.call_gemini_with_image(
                prompt=prompt_vision,
                image_path=image_path,
                model_name="gemini-3.8-flash"
            )

            limpio = respuesta_ia.strip()
            if limpio.startswith("```json"):
                limpio = limpio[7:]
            if limpio.endswith("```"):
                limpio = limpio[:-3]
            
            datos_ia = json.loads(limpio.strip())

            monto_val = float(datos_ia.get("amount_number", 0.0))
            moneda_val = datos_ia.get("currency", "BS")
            
            descripcion_final = caption if caption else f"Comprobante - Ref: {datos_ia.get('ref_code', 'N/A')}"
            
            categoria_final = "General"
            cap_lower = caption.lower()
            if "gasolina" in cap_lower:
                categoria_final = "Gasolina"
            elif "sueldo" in cap_lower or "nomina" in cap_lower:
                categoria_final = "Sueldo"
            elif "internet" in cap_lower:
                categoria_final = "Internet"
            elif "mercancia" in cap_lower or "repuestos" in cap_lower:
                categoria_final = "Mercancia"
            elif "oficina" in cap_lower:
                categoria_final = "Oficina"

            payload_registro = {
                "type": datos_ia.get("transaction_type", "Ingreso"),
                "amount_usd": monto_val if moneda_val == "USD" else 0.0,
                "amount_bs": monto_val if moneda_val == "BS" else 0.0,
                "currency": moneda_val,
                "method": datos_ia.get("bank_origin", "Pago Móvil"),
                "category": categoria_final,
                "description": descripcion_final,
                "ref_code": datos_ia.get("ref_code", "")
            }

            return self.record_transaction(payload_registro)

        except Exception as e:
            app_logger.error(f"Error procesando comprobante visual: {e}", exc_info=True)
            return AgentResponse(success=False, message=f"Error al procesar la imagen con IA: {str(e)}")

    def perform_monthly_close(self, year: Optional[int] = None, month: Optional[int] = None) -> AgentResponse:
        """
        Ejecuta el cierre de mes:
        1. Toma el saldo inicial y las transacciones actuales.
        2. Genera un reporte único consolidado y lo guarda en 'data/monthly_reports/{mes}/reporte_cierre.json'.
        3. Limpia el Libro Mayor y reinicia el saldo inicial para comenzar el nuevo mes en blanco.
        """
        now = datetime.now()
        target_year = year if year is not None else now.year
        target_month = month if month is not None else now.month

        ledger = self._load_ledger()
        settings = self._load_settings()
        initial_balance = float(settings.get("initial_balance_usd", 0.0))

        total_income_usd = sum(float(r.get("amount_usd", 0.0)) for r in ledger if r.get("type") == "Ingreso")
        total_expense_usd = sum(float(r.get("amount_usd", 0.0)) for r in ledger if r.get("type") in ["Gasto", "Egreso"])
        net_balance_usd = initial_balance + total_income_usd - total_expense_usd
        
        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))

        reporte_consolidado = {
            "periodo": f"{target_year}-{target_month:02d}",
            "fecha_cierre": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resumen": {
                "saldo_inicial_usd": round(initial_balance, 2),
                "total_ingresos_usd": round(total_income_usd, 2),
                "total_gastos_usd": round(total_expense_usd, 2),
                "balance_neto_usd": round(net_balance_usd, 2),
                "tasa_bcv_cierre": rate,
                "total_transacciones": len(ledger)
            },
            "movimientos": ledger
        }

        base_dir = os.path.dirname(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
        month_folder = os.path.join(base_dir, "monthly_reports", f"{target_year}-{target_month:02d}")
        os.makedirs(month_folder, exist_ok=True)

        report_file_path = os.path.join(month_folder, "reporte_cierre.json")
        try:
            with open(report_file_path, "w", encoding="utf-8") as f:
                json.dump(reporte_consolidado, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return AgentResponse(success=False, message=f"Error guardando el reporte de cierre: {e}")

        # Reiniciar para el nuevo mes
        self._save_ledger([])
        self._save_settings({"initial_balance_usd": 0.0})

        self.emit_event("monthly_closed", {"period": f"{target_year}-{target_month:02d}", "path": report_file_path})
        return AgentResponse(
            success=True,
            data={"report_path": report_file_path},
            message=f"Cierre mensual de {target_year}-{target_month:02d} realizado con éxito."
        )

    def get_financial_summary(self, year: Optional[int] = None, month: Optional[int] = None) -> AgentResponse:
        """Calcula el resumen financiero incluyendo el Saldo Inicial y las transacciones."""
        ledger = self._load_ledger()
        settings = self._load_settings()
        initial_balance_usd = float(settings.get("initial_balance_usd", 0.0))
        
        total_income_usd = sum(float(r.get("amount_usd", 0.0)) for r in ledger if r.get("type") == "Ingreso")
        total_expense_usd = sum(float(r.get("amount_usd", 0.0)) for r in ledger if r.get("type") in ["Gasto", "Egreso"])
        
        net_balance_usd = initial_balance_usd + total_income_usd - total_expense_usd
        
        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))

        summary = {
            "initial_balance_usd": round(initial_balance_usd, 2),
            "total_income_usd": round(total_income_usd, 2),
            "total_expense_usd": round(total_expense_usd, 2),
            "net_balance_usd": round(net_balance_usd, 2),
            "bcv_rate": rate,
            "bcv_source": bcv_data.get("fuente", "BCV Oficial"),
            "initial_balance_bs": round(initial_balance_usd * rate, 2),
            "total_income_bs": round(total_income_usd * rate, 2),
            "total_expense_bs": round(total_expense_usd * rate, 2),
            "net_balance_bs": round(net_balance_usd * rate, 2),
            "total_transactions": len(ledger),
            "latest_transactions": ledger[-5:] if ledger else []
        }

        self.emit_event("financial_summary_updated", summary)
        return AgentResponse(
            success=True,
            data=summary,
            message="Resumen financiero calculado correctamente."
        )

    def reconcile_crypto(self, payload: Dict[str, Any]) -> AgentResponse:
        """Concilia un pago realizado mediante Binance Pay."""
        ref_id = payload.get("ref_id", "")
        amount_usd = float(payload.get("amount_usd", 0.0))
        description = payload.get("description", "Pago recibido vía USDT")

        veri = self.gateway_manager.verify_binance_payment(ref_id)
        if veri.get("verified"):
            trx_res = self.record_transaction({
                "type": "Ingreso",
                "amount_usd": amount_usd,
                "currency": "USD",
                "method": "Binance USDT",
                "category": "Venta / Servicio Cripto",
                "description": description,
                "ref_code": ref_id
            })
            return AgentResponse(
                success=True,
                data={"verification": veri, "transaction": trx_res.data},
                message=f"Pago USDT conciliado y registrado ({ref_id})."
            )

        return AgentResponse(success=False, message="No se pudo verificar el pago cripto.")

    def create_payment_link(self, payload: Dict[str, Any]) -> AgentResponse:
        """Genera un enlace de pago en Binance."""
        order_id = payload.get("order_id", f"ORD-{int(time.time())}")
        amount = float(payload.get("amount_usd", 0.0))
        item_name = payload.get("item_name", "Servicio Técnico / Insumos")
        res = self.gateway_manager.create_binance_order(order_id, amount, item_name)
        return AgentResponse(success=True, data=res, message="Orden Binance Pay generada.")