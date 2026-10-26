"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: accounting_agent.py
Descripción: Agente Administrador y Contable con gestión de Saldo Inicial,
             desglose analítico por categorías, cierre y archivo mensual automatizado
             según calendario venezolano (UTC-4) y exportación a Escritorio (JSON/CSV).
=============================================================================
"""

import csv
import json
import os
import time
from datetime import datetime, timezone, timedelta
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

# Zona horaria oficial de Venezuela: UTC-4 permanente
VENEZUELA_TZ = timezone(timedelta(hours=-4))


class AccountingAgent(BaseAgent):
    """Agente de Administración y Finanzas del sistema."""

    def __init__(self, gateway_manager: Optional[PaymentGatewayManager] = None):
        super().__init__(
            agent_id="administrador_contable",
            name="Agente Administrador y Contable",
            department="Administración y Finanzas",
            description="Control contable con saldo inicial, desglose por categorías, cierre mensual y registro en tiempo real."
        )
        self.gateway_manager = gateway_manager or PaymentGatewayManager()
        
        # Configurar la API key de Gemini para el procesamiento de visión
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
            except Exception as e:
                app_logger.warning(f"Error al configurar genai: {e}")

    # ─── Helpers de Horario y Rutas ──────────────────────────────────────────

    @classmethod
    def get_venezuela_now(cls) -> datetime:
        """Retorna la fecha y hora actual en la zona horaria de Venezuela (UTC-4)."""
        return datetime.now(VENEZUELA_TZ)

    @classmethod
    def get_current_month_key(cls) -> str:
        """Retorna el identificador del mes actual venezolano (ej. '2026-10')."""
        vz = cls.get_venezuela_now()
        return f"{vz.year}-{vz.month:02d}"

    def get_desktop_backup_dir(self) -> str:
        """
        Obtiene y asegura la carpeta de respaldos de cierres financieros
        directamente en el Escritorio del usuario.
        """
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = getattr(SystemConfig, "EXPORTS_DIR", "exports")
        backup_dir = os.path.join(desktop, "Respaldos_Financieros_Cierres")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    def _get_settings_path(self) -> str:
        """Asegura la ruta para guardar configuraciones del agente como el saldo inicial."""
        base_dir = os.path.dirname(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "accounting_settings.json")

    def _load_settings(self) -> Dict[str, Any]:
        """Carga las configuraciones guardadas (ej. saldo inicial, mes activo)."""
        path = self._get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {
            "initial_balance_usd": 0.0,
            "active_month": self.get_current_month_key(),
            "monthly_initial_balances": {}
        }

    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Guarda las configuraciones del agente."""
        path = self._get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando configuraciones contables: {e}")

    def get_initial_balance_for_period(self, year: int, month: int) -> float:
        """Retorna el saldo inicial configurado o arrastrado para un mes específico."""
        settings = self._load_settings()
        key = f"{year}-{month:02d}"
        monthly = settings.get("monthly_initial_balances", {})
        if key in monthly:
            try:
                return float(monthly[key])
            except (ValueError, TypeError):
                pass
        return float(settings.get("initial_balance_usd", 0.0))

    def set_initial_balance_for_period(self, amount_usd: float, year: Optional[int] = None, month: Optional[int] = None) -> None:
        """Establece el saldo inicial para un período específico y actualiza el global."""
        settings = self._load_settings()
        val = round(float(amount_usd), 2)
        settings["initial_balance_usd"] = val
        if "monthly_initial_balances" not in settings or not isinstance(settings["monthly_initial_balances"], dict):
            settings["monthly_initial_balances"] = {}

        if year is not None and month is not None:
            settings["monthly_initial_balances"][f"{year}-{month:02d}"] = val
        else:
            vz = self.get_venezuela_now()
            settings["monthly_initial_balances"][f"{vz.year}-{vz.month:02d}"] = val

        self._save_settings(settings)

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
        """Guarda y unifica las transacciones en el archivo oficial del Libro Mayor para Render y Escritorio."""
        try:
            ledger_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
            finances_path = getattr(SystemConfig, "FINANCES_FILE", "data/finanzas.json")
            
            os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

            # Guardar en ledger principal
            with open(ledger_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            # Guardar en archivo de finanzas sincronizado
            if finances_path and finances_path != ledger_path:
                os.makedirs(os.path.dirname(finances_path), exist_ok=True)
                with open(finances_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            app_logger.error(f"Error guardando ledger principal: {e}")

    # ─── Cuentas por Cobrar (CxC) y Cuentas por Pagar (CxP) ───────────────────

    def _get_cxc_cxp_path(self) -> str:
        return getattr(SystemConfig, "CXC_CXP_FILE", os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "cxc_cxp.json"))

    def _load_cxc_cxp(self) -> List[Dict[str, Any]]:
        """Carga los registros de Cuentas por Cobrar y por Pagar."""
        path = self._get_cxc_cxp_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                app_logger.error(f"Error cargando archivo CxC/CxP: {e}")
        return []

    def _save_cxc_cxp(self, data: List[Dict[str, Any]]) -> None:
        """Guarda los registros de Cuentas por Cobrar y por Pagar."""
        path = self._get_cxc_cxp_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando archivo CxC/CxP: {e}")

    # ─── Clasificación Inteligente de Categorías ──────────────────────────────

    @classmethod
    def categorize_record(cls, record: Dict[str, Any]) -> str:
        """
        Clasifica una transacción exactamente en las categorías analíticas requeridas:
        Moto, Sueldos, Servicios, Gasolina, Comisión Bancaria, Mercancía, Oficina, Herramientas,
        Servicio Técnico, Ventas, Gastos Operativos, Otros Gastos, Otros Ingresos.
        """
        cat = (record.get("category") or "").strip()
        desc = (record.get("description") or "").strip().lower()
        t_type = (record.get("type") or "").strip().lower()

        # Mapeo de normalización directa
        cat_map = {
            "moto": "Moto",
            "motos": "Moto",
            "sueldo": "Sueldos",
            "sueldos": "Sueldos",
            "nomina": "Sueldos",
            "nómina": "Sueldos",
            "servicios": "Servicios",
            "servicio": "Servicios",
            "gasolina": "Gasolina",
            "combustible": "Gasolina",
            "comision bancaria": "Comisión Bancaria",
            "comisión bancaria": "Comisión Bancaria",
            "comisiones bancarias": "Comisión Bancaria",
            "comisiones": "Comisión Bancaria",
            "mercancia": "Mercancía",
            "mercancía": "Mercancía",
            "mercancias": "Mercancía",
            "mercancías": "Mercancía",
            "oficina": "Oficina",
            "herramientas": "Herramientas",
            "herramienta": "Herramientas",
            "servicio técnico": "Servicio Técnico",
            "servicio tecnico": "Servicio Técnico",
            "taller": "Servicio Técnico",
            "ventas": "Ventas / Facturación",
            "venta": "Ventas / Facturación",
            "venta de tóner/insumos": "Ventas / Facturación",
            "compra repuestos": "Mercancía",
            "gastos operativos": "Gastos Operativos",
            "flete zoom casilleros": "Servicios"
        }

        if cat.lower() in cat_map:
            return cat_map[cat.lower()]

        # Deducción por palabras clave en descripción si categoría es genérica o ausente
        if any(k in desc for k in ["moto", "caucho", "aceite moto", "freno moto", "cadena moto", "repuesto moto"]):
            return "Moto"
        if any(k in desc for k in ["sueldo", "nomina", "nómina", "quincena", "pago sueldo", "pago de sueldo"]):
            return "Sueldos"
        if any(k in desc for k in ["gasolina", "combustible", "gasoil", "estacion de servicio", "e/s"]):
            return "Gasolina"
        if any(k in desc for k in ["telefono", "teléfono", "internet", "luz", "agua", "cantv", "corpoelec", "fibra", "servicio", "alquiler"]):
            return "Servicios"
        if any(k in desc for k in ["comision", "comisión", "igtf", "debito bancario", "débito bancario", "comision bcv"]):
            return "Comisión Bancaria"
        if any(k in desc for k in ["mercancia", "mercancía", "proveedor", "proveedores", "compra", "toner", "tóner", "tinta", "repuesto", "repuestos", "insumo", "insumos"]):
            return "Mercancía"
        if any(k in desc for k in ["oficina", "papel", "limpieza", "cafe", "café", "bolsa", "suministros"]):
            return "Oficina"
        if any(k in desc for k in ["herramienta", "herramientas", "cautin", "cautín", "multimetro", "multímetro", "tester", "destornillador", "estaño", "estacion de calor"]):
            return "Herramientas"

        # Clasificación por tipo de transacción
        if t_type in ["ingreso", "ingresos"]:
            if any(k in desc for k in ["factura", "cobro", "reparacion", "reparación", "mantenimiento", "servicio", "revision", "revisión", "diagnostico", "diagnóstico", "taller"]):
                return "Servicio Técnico"
            if any(k in desc for k in ["venta", "toner", "tinta"]):
                return "Ventas / Facturación"
            return "Otros Ingresos"
        else:
            if any(k in desc for k in ["viatico", "viático", "viaticos", "mercado", "salud", "medicina", "comida", "almuerzo"]):
                return "Gastos Operativos"
            return "Otros Gastos"

    # ─── Desglose Analítico por Categorías ────────────────────────────────────

    def get_category_breakdown(self, year: int, month: int) -> Dict[str, Any]:
        """
        Calcula contadores y montos consolidados desglosados exactamente por categoría,
        tanto en dólares ($) como en bolívares (Bs) según la tasa BCV oficial del día
        de cada transacción, replicando la estructura de las hojas de control mensual.
        """
        ledger = self._load_ledger()
        
        # Filtrar por período
        records_periodo = []
        for r in ledger:
            fecha_str = str(r.get("date", ""))[:10]
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                if dt.year == year and dt.month == month:
                    records_periodo.append(r)
            except Exception:
                pass

        # Categorías estándar requeridas
        expense_categories = [
            "Moto",
            "Sueldos",
            "Servicios",
            "Gasolina",
            "Comisión Bancaria",
            "Mercancía",
            "Oficina",
            "Herramientas",
            "Gastos Operativos",
            "Otros Gastos"
        ]

        income_categories = [
            "Servicio Técnico",
            "Ventas / Facturación",
            "Otros Ingresos"
        ]

        cat_stats = {}
        for cat in expense_categories + income_categories:
            cat_stats[cat] = {
                "category": cat,
                "amount_usd": 0.0,
                "amount_bs": 0.0,
                "count": 0,
                "percentage": 0.0,
                "transactions": []
            }

        total_income_usd = 0.0
        total_income_bs = 0.0
        total_expense_usd = 0.0
        total_expense_bs = 0.0
        bcv_rates = []

        for r in records_periodo:
            cat = self.categorize_record(r)
            if cat not in cat_stats:
                cat_stats[cat] = {
                    "category": cat,
                    "amount_usd": 0.0,
                    "amount_bs": 0.0,
                    "count": 0,
                    "percentage": 0.0,
                    "transactions": []
                }

            usd = float(r.get("amount_usd", 0.0))
            bcv = float(r.get("bcv_rate", 0.0))
            if bcv > 0:
                bcv_rates.append(bcv)
            
            # Monto en bolívares según la tasa BCV del día de la transacción
            bs = float(r.get("amount_bs", 0.0))
            if bs <= 0 and bcv > 0:
                bs = round(usd * bcv, 2)

            t_type = (r.get("type") or "").strip().lower()
            is_income = t_type == "ingreso"

            if is_income:
                total_income_usd += usd
                total_income_bs += bs
            else:
                total_expense_usd += usd
                total_expense_bs += bs

            cat_stats[cat]["amount_usd"] += usd
            cat_stats[cat]["amount_bs"] += bs
            cat_stats[cat]["count"] += 1
            cat_stats[cat]["transactions"].append({
                **r,
                "resolved_category": cat,
                "amount_bs": bs
            })

        # Redondear y calcular porcentajes de distribución
        for cat, data in cat_stats.items():
            data["amount_usd"] = round(data["amount_usd"], 2)
            data["amount_bs"] = round(data["amount_bs"], 2)
            if cat in income_categories:
                data["percentage"] = round((data["amount_usd"] / total_income_usd * 100), 1) if total_income_usd > 0 else 0.0
            else:
                data["percentage"] = round((data["amount_usd"] / total_expense_usd * 100), 1) if total_expense_usd > 0 else 0.0

        avg_bcv = round(sum(bcv_rates) / len(bcv_rates), 2) if bcv_rates else 0.0
        initial_balance_usd = self.get_initial_balance_for_period(year, month)
        initial_balance_bs = round(initial_balance_usd * (avg_bcv or 1.0), 2)
        net_balance_usd = round(initial_balance_usd + total_income_usd - total_expense_usd, 2)
        net_balance_bs = round(initial_balance_bs + total_income_bs - total_expense_bs, 2)

        return {
            "period": f"{year}-{month:02d}",
            "year": year,
            "month": month,
            "total_income_usd": round(total_income_usd, 2),
            "total_income_bs": round(total_income_bs, 2),
            "total_expense_usd": round(total_expense_usd, 2),
            "total_expense_bs": round(total_expense_bs, 2),
            "initial_balance_usd": initial_balance_usd,
            "initial_balance_bs": initial_balance_bs,
            "net_balance_usd": net_balance_usd,
            "net_balance_bs": net_balance_bs,
            "operating_margin_usd": round(total_income_usd - total_expense_usd, 2),
            "operating_margin_bs": round(total_income_bs - total_expense_bs, 2),
            "average_bcv_rate": avg_bcv,
            "total_transactions": len(records_periodo),
            "categories": cat_stats,
            "expense_categories": expense_categories,
            "income_categories": income_categories,
            "records": records_periodo
        }

    # ─── Rutina de Respaldo y Archivo en el Escritorio (JSON/CSV) ─────────────

    def export_monthly_backup(self, year: int, month: int, dest_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta y archiva automáticamente los datos consolidados del mes en formatos
        JSON y CSV en la carpeta de respaldos en el escritorio del usuario.
        """
        summary = self.get_category_breakdown(year, month)
        period_str = f"{year}_{month:02d}"
        
        backup_base = dest_dir or self.get_desktop_backup_dir()
        period_folder = os.path.join(backup_base, f"Cierre_{period_str}")
        os.makedirs(period_folder, exist_ok=True)

        json_file_path = os.path.join(period_folder, f"cierre_financiero_{period_str}.json")
        csv_file_path = os.path.join(period_folder, f"cierre_financiero_{period_str}.csv")

        # 1. Exportar archivo JSON estructurado
        export_payload = {
            "sistema": "Inversiones Reinaldo Golindano",
            "periodo": f"{year}-{month:02d}",
            "fecha_emision_venezuela": self.get_venezuela_now().strftime("%Y-%m-%d %H:%M:%S"),
            "resumen_general": {
                "saldo_inicial_usd": summary["initial_balance_usd"],
                "saldo_inicial_bs": summary["initial_balance_bs"],
                "total_ingresos_usd": summary["total_income_usd"],
                "total_ingresos_bs": summary["total_income_bs"],
                "total_gastos_usd": summary["total_expense_usd"],
                "total_gastos_bs": summary["total_expense_bs"],
                "margen_operativo_usd": summary["operating_margin_usd"],
                "margen_operativo_bs": summary["operating_margin_bs"],
                "balance_neto_en_caja_usd": summary["net_balance_usd"],
                "balance_neto_en_caja_bs": summary["net_balance_bs"],
                "tasa_bcv_promedio": summary["average_bcv_rate"],
                "total_transacciones": summary["total_transactions"]
            },
            "desglose_por_categoria": summary["categories"],
            "movimientos_detallados": summary["records"]
        }

        with open(json_file_path, "w", encoding="utf-8") as jf:
            json.dump(export_payload, jf, indent=2, ensure_ascii=False)

        # 2. Exportar archivo CSV con codificación UTF-8-SIG para compatibilidad perfecta con Excel
        with open(csv_file_path, "w", encoding="utf-8-sig", newline="") as cf:
            writer = csv.writer(cf)
            writer.writerow(["INVERSIONES REINALDO GOLINDANO - REPORTE DE CONTROL FINANCIERO Y CIERRE MENSUAL"])
            writer.writerow(["Período:", f"{year}-{month:02d}", "Fecha Emisión:", self.get_venezuela_now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([
                "Saldo Inicial ($):", summary["initial_balance_usd"],
                "Ingresos Totales ($):", summary["total_income_usd"],
                "Gastos Totales ($):", summary["total_expense_usd"],
                "Balance Neto ($):", summary["net_balance_usd"]
            ])
            writer.writerow([])
            writer.writerow(["=== DESGLOSE ANALÍTICO POR CATEGORÍA ==="])
            writer.writerow(["Categoría", "Monto ($ USD)", "Monto (Bs según BCV del día)", "N° Operaciones", "% Distribución"])
            for cat_name, data in summary["categories"].items():
                if data["count"] > 0 or data["amount_usd"] > 0:
                    writer.writerow([
                        cat_name,
                        f"${data['amount_usd']:,.2f}",
                        f"{data['amount_bs']:,.2f} Bs",
                        data["count"],
                        f"{data['percentage']}%"
                    ])
            writer.writerow([])
            writer.writerow(["=== DETALLE COMPLETO DE TRANSACCIONES ==="])
            writer.writerow(["ID Transacción", "Fecha", "Tipo", "Categoría", "Monto ($ USD)", "Tasa BCV del Día", "Monto (Bs)", "Método de Pago", "N° Referencia", "Descripción"])
            for r in summary["records"]:
                cat = self.categorize_record(r)
                u = float(r.get("amount_usd", 0.0))
                b = float(r.get("amount_bs", 0.0))
                rate_val = float(r.get("bcv_rate", 0.0))
                writer.writerow([
                    r.get("id", ""),
                    r.get("date", ""),
                    r.get("type", ""),
                    cat,
                    f"${u:,.2f}",
                    rate_val,
                    f"{b:,.2f} Bs",
                    r.get("method", ""),
                    r.get("ref_code", ""),
                    r.get("description", "")
                ])

        # Guardar también copia interna en monthly_reports
        internal_dir = os.path.join(
            os.path.dirname(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")),
            "monthly_reports",
            f"{year}-{month:02d}"
        )
        os.makedirs(internal_dir, exist_ok=True)
        with open(os.path.join(internal_dir, "reporte_cierre.json"), "w", encoding="utf-8") as f:
            json.dump(export_payload, f, indent=2, ensure_ascii=False)

        app_logger.info(f"Respaldo consolidado generado con éxito en Escritorio: {period_folder}")
        return {
            "period": f"{year}-{month:02d}",
            "json_path": json_file_path,
            "csv_path": csv_file_path,
            "folder": period_folder,
            "summary": summary
        }

    # ─── Automatización de Cierre y Nuevo Mes (Hora de Venezuela) ─────────────

    def check_and_perform_monthly_rollover(self) -> Optional[Dict[str, Any]]:
        """
        Verifica si se ha iniciado un nuevo mes calendario según la hora local de Venezuela (UTC-4).
        Al comenzar un nuevo mes:
        1. Archiva y respalda automáticamente los datos consolidados del mes cerrado en el Escritorio (JSON/CSV).
        2. Configura el saldo inicial del nuevo mes transfiriendo el balance neto del mes anterior.
        3. Prepara la aplicación para que la interfaz se limpie al recibir las operaciones del nuevo mes en curso.
        """
        now_vz = self.get_venezuela_now()
        current_month_key = f"{now_vz.year}-{now_vz.month:02d}"

        settings = self._load_settings()
        active_month = settings.get("active_month")

        if not active_month:
            settings["active_month"] = current_month_key
            self._save_settings(settings)
            return None

        # Si el mes activo registrado es anterior al mes actual venezolano
        if active_month < current_month_key:
            app_logger.info(
                f"Transición a nuevo mes calendario venezolano detectada: {active_month} -> {current_month_key}. "
                f"Ejecutando rutina de archivo automático en el Escritorio..."
            )
            try:
                prev_y, prev_m = [int(p) for p in active_month.split("-")]
            except Exception:
                prev_y, prev_m = now_vz.year, now_vz.month - 1
                if prev_m == 0:
                    prev_m = 12
                    prev_y -= 1

            # 1. Rutina de archivo automático en el escritorio
            backup_res = self.export_monthly_backup(prev_y, prev_m)
            summary = backup_res["summary"]

            # 2. Configurar el saldo inicial del nuevo mes con el balance neto anterior
            nuevo_saldo = summary["net_balance_usd"]
            if "monthly_initial_balances" not in settings or not isinstance(settings["monthly_initial_balances"], dict):
                settings["monthly_initial_balances"] = {}
            settings["monthly_initial_balances"][current_month_key] = nuevo_saldo
            settings["initial_balance_usd"] = nuevo_saldo
            settings["active_month"] = current_month_key
            settings["last_closed_month"] = active_month
            self._save_settings(settings)

            self.emit_event("monthly_closed", {
                "closed_month": active_month,
                "new_month": current_month_key,
                "backup": backup_res
            })

            return backup_res

        return None

    # ─── Ejecución de Tareas del Agente ───────────────────────────────────────

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
        elif task_type == "get_category_breakdown":
            year = payload.get("year") or self.get_venezuela_now().year
            month = payload.get("month") or self.get_venezuela_now().month
            data = self.get_category_breakdown(int(year), int(month))
            return AgentResponse(success=True, data=data, message="Desglose analítico calculado exitosamente.")
        elif task_type == "export_monthly_backup":
            year = payload.get("year") or self.get_venezuela_now().year
            month = payload.get("month") or self.get_venezuela_now().month
            dest = payload.get("dest_dir")
            res = self.export_monthly_backup(int(year), int(month), dest)
            return AgentResponse(success=True, data=res, message=f"Respaldo generado con éxito en: {res['folder']}")
        elif task_type == "monthly_close":
            year = payload.get("year")
            month = payload.get("month")
            return self.perform_monthly_close(year=year, month=month)
        elif task_type == "reconcile_crypto":
            return self.reconcile_crypto(payload)
        elif task_type == "create_payment_link":
            return self.create_payment_link(payload)
        elif task_type == "record_cxc_cxp":
            return self.record_cxc_cxp(payload)
        elif task_type == "settle_cxc_cxp":
            return self.settle_cxc_cxp(payload)
        elif task_type == "get_cxc_cxp_summary":
            return self.get_cxc_cxp_summary()
        elif task_type == "delete_cxc_cxp":
            return self.delete_cxc_cxp(payload)
        else:
            return AgentResponse(
                success=False,
                message=f"Tarea '{task_type}' no reconocida por el Agente Contable."
            )

    def set_initial_balance(self, payload: Dict[str, Any]) -> AgentResponse:
        """Establece o actualiza el saldo inicial en USD requerido por la interfaz gráfica."""
        amount_usd = float(payload.get("initial_balance_usd", 0.0))
        year = payload.get("year")
        month = payload.get("month")
        self.set_initial_balance_for_period(amount_usd, year, month)
        settings = self._load_settings()

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

        record_date = payload.get("date") or self.get_venezuela_now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": f"TRX-{int(time.time() * 1000)}",
            "date": record_date,
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
            message=f"Transacción {record['id']} registrada con éxito: ${amount_usd:,.2f} USD ({amount_bs:,.2f} Bs a tasa {rate:,.2f} BCV)."
        )

    def call_gemini_with_image(self, prompt: str, image_path: str, model_name: str = "gemini-3.8-flash") -> str:
        """Procesa la imagen directamente con Gemini y respaldo."""
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
        """Analiza el comprobante enviado por Telegram y lo registra en tiempo real con categorización precisa."""
        if not image_path or not os.path.exists(image_path):
            return AgentResponse(success=False, message="No se encontró la imagen del comprobante.")

        prompt_vision = f"""
Analiza este comprobante de pago bancario venezolano. Extrae la información en formato JSON estricto con estas llaves:
1. "amount_number": El monto exacto reflejado en el comprobante en números (ej: 4.61 o 12500.00).
2. "currency": La moneda explícita del ticket ("BS" o "USD").
3. "bank_origin": El banco emisor. DEBES seguir estas reglas de clasificación de forma ESTRICTA:

   === REGLAS DE CLASIFICACIÓN DE BANCO ORIGEN ===

   BBVA Provincial - Clasifica como "BBVA Provincial" ÚNICAMENTE si detectas:
      * Texto explícito "BBVA Provincial", "BBVA" o "Dinero Rápido BBVA Provincial".
      * Encabezados de pago como "Pagar a Otros Bancos" o "Pagar a Mismo Banco".
      * Etiquetas de campos: "Identificación:", "Concepto:", "Fecha:" y "Referencia:".
      * Botones inferiores: "Compartir como imagen" o "Compartir como texto".

   Banco Mercantil - Clasifica como "Banco Mercantil" ÚNICAMENTE si detectas:
      * Encabezado de cuenta con asteriscos (ej. "Corriente *7434").
      * Etiquetas exclusivas: "Monto disponible", "Monto anterior", "Centro origen", "Tipo de movimiento" o "Número de movimiento".
      * Botón inferior con icono de triángulo o texto "Quiero".

   REGLA DE ESTRICTA CERTEZA:
      * Si NO encuentras ninguna palabra clave o etiqueta exclusiva de Provincial o Mercantil,
        NO debes adivinar ni asumir ningún banco por defecto.
      * En ese caso devuelve exactamente: "Banco Desconocido / Requiere Revisión".
      * Para otros bancos identificados por nombre propio en el comprobante
        (Banesco, BDV, Zelle, Binance, etc.), usa su nombre tal como aparece en la imagen.

4. "ref_code": El número de referencia o confirmación (campo "Referencia" o "Número de movimiento").
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
            
            # Clasificación inteligente de categoría
            categoria_final = "General"
            cap_lower = caption.lower()
            if "moto" in cap_lower or "caucho" in cap_lower or "aceite moto" in cap_lower:
                categoria_final = "Moto"
            elif "gasolina" in cap_lower or "combustible" in cap_lower or "gasoil" in cap_lower:
                categoria_final = "Gasolina"
            elif "sueldo" in cap_lower or "nomina" in cap_lower or "nómina" in cap_lower or "quincena" in cap_lower:
                categoria_final = "Sueldos"
            elif any(k in cap_lower for k in ["internet", "telefono", "teléfono", "cantv", "corpoelec", "luz", "agua", "servicio"]):
                categoria_final = "Servicios"
            elif "comision" in cap_lower or "comisión" in cap_lower or "igtf" in cap_lower:
                categoria_final = "Comisión Bancaria"
            elif any(k in cap_lower for k in ["mercancia", "mercancía", "repuestos", "repuesto", "toner", "tóner", "tinta", "proveedor"]):
                categoria_final = "Mercancía"
            elif "oficina" in cap_lower or "papel" in cap_lower or "limpieza" in cap_lower:
                categoria_final = "Oficina"
            elif "herramienta" in cap_lower or "herramientas" in cap_lower or "cautin" in cap_lower:
                categoria_final = "Herramientas"
            elif any(k in cap_lower for k in ["reparacion", "reparación", "taller", "mantenimiento"]):
                categoria_final = "Servicio Técnico"

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
        Ejecuta el cierre de mes consolidando los registros y respaldándolos en el Escritorio.
        Preserva el histórico en el Libro Mayor y transfiere el balance final como saldo inicial del mes siguiente.
        """
        now_vz = self.get_venezuela_now()
        target_year = year if year is not None else now_vz.year
        target_month = month if month is not None else now_vz.month

        # Generar respaldo en el Escritorio (JSON y CSV)
        backup_res = self.export_monthly_backup(target_year, target_month)
        summary = backup_res["summary"]

        # Calcular el período siguiente
        next_m = target_month + 1
        next_y = target_year
        if next_m > 12:
            next_m = 1
            next_y += 1
        next_period_key = f"{next_y}-{next_m:02d}"

        # Configurar saldo inicial arrastrado al siguiente período
        settings = self._load_settings()
        nuevo_saldo_inicial = summary["net_balance_usd"]
        if "monthly_initial_balances" not in settings or not isinstance(settings["monthly_initial_balances"], dict):
            settings["monthly_initial_balances"] = {}

        settings["monthly_initial_balances"][next_period_key] = nuevo_saldo_inicial
        settings["initial_balance_usd"] = nuevo_saldo_inicial
        settings["last_closed_month"] = f"{target_year}-{target_month:02d}"
        settings["active_month"] = next_period_key
        self._save_settings(settings)

        self.emit_event("monthly_closed", {
            "period": f"{target_year}-{target_month:02d}",
            "next_period": next_period_key,
            "backup_folder": backup_res["folder"],
            "summary": summary
        })

        return AgentResponse(
            success=True,
            data=backup_res,
            message=(
                f"Cierre de {target_year}-{target_month:02d} completado con éxito.\n"
                f"Respaldo archivado en el Escritorio:\n{backup_res['folder']}\n"
                f"Saldo final ${nuevo_saldo_inicial:,.2f} USD transferido como saldo inicial para {next_period_key}."
            )
        )

    def get_financial_summary(self, year: Optional[int] = None, month: Optional[int] = None) -> AgentResponse:
        """Calcula el resumen financiero incluyendo el Saldo Inicial y las transacciones filtradas por período."""
        ledger = self._load_ledger()
        
        if year is not None and month is not None:
            filtered_ledger = []
            for r in ledger:
                f_str = str(r.get("date", ""))[:10]
                try:
                    dt = datetime.strptime(f_str, "%Y-%m-%d")
                    if dt.year == year and dt.month == month:
                        filtered_ledger.append(r)
                except Exception:
                    pass
            active_txs = filtered_ledger
            initial_balance_usd = self.get_initial_balance_for_period(year, month)
        else:
            active_txs = ledger
            settings = self._load_settings()
            initial_balance_usd = float(settings.get("initial_balance_usd", 0.0))

        def _is_inc(t):
            return str(t).strip().lower() in ("ingreso",)

        def _is_exp(t):
            return str(t).strip().lower() in ("gasto", "egreso")

        total_income_usd = sum(float(r.get("amount_usd", 0.0)) for r in active_txs if _is_inc(r.get("type")))
        total_expense_usd = sum(float(r.get("amount_usd", 0.0)) for r in active_txs if _is_exp(r.get("type")))
        total_income_bs = sum(float(r.get("amount_bs", 0.0)) for r in active_txs if _is_inc(r.get("type")))
        total_expense_bs = sum(float(r.get("amount_bs", 0.0)) for r in active_txs if _is_exp(r.get("type")))

        net_balance_usd = initial_balance_usd + total_income_usd - total_expense_usd

        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))
        initial_balance_bs = round(initial_balance_usd * rate, 2)
        net_balance_bs = round(initial_balance_bs + total_income_bs - total_expense_bs, 2)

        summary = {
            "initial_balance_usd": round(initial_balance_usd, 2),
            "total_income_usd": round(total_income_usd, 2),
            "total_expense_usd": round(total_expense_usd, 2),
            "net_balance_usd": round(net_balance_usd, 2),
            "bcv_rate": rate,
            "bcv_source": bcv_data.get("fuente", "BCV Oficial"),
            "initial_balance_bs": initial_balance_bs,
            "total_income_bs": round(total_income_bs, 2),
            "total_expense_bs": round(total_expense_bs, 2),
            "net_balance_bs": net_balance_bs,
            "total_transactions": len(active_txs),
            "latest_transactions": active_txs[-5:] if active_txs else []
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
                "category": "Ventas / Facturación",
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

    # ─── Lógica Contable de Cuentas por Cobrar y por Pagar ───────────────────

    def record_cxc_cxp(self, payload: Dict[str, Any]) -> AgentResponse:
        """
        Registra una nueva Cuenta por Cobrar (CxC) o Cuenta por Pagar (CxP).
        Campos:
        - type: 'CxC' (Cliente debe a la empresa) o 'CxP' (Empresa debe a Proveedor)
        - entity_name: Nombre del Cliente o Proveedor
        - concept: Concepto detallado de la operación
        - amount_usd: Monto en USD (o amount_bs con currency='BS')
        - issue_date: Fecha de emisión (YYYY-MM-DD)
        - due_date: Fecha de vencimiento (YYYY-MM-DD)
        - status: 'Pendiente', 'Abonado', 'Pagado' (por defecto 'Pendiente')
        """
        c_type = payload.get("type", "CxC").strip()
        if c_type not in ("CxC", "CxP"):
            c_type = "CxC"

        entity_name = payload.get("entity_name", "").strip()
        concept = payload.get("concept", "").strip()
        if not entity_name or not concept:
            return AgentResponse(success=False, message="Cliente/Proveedor y Concepto son obligatorios.")

        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))
        if rate <= 0:
            rate = 1.0

        raw_usd = float(payload.get("amount_usd", 0.0))
        raw_bs = float(payload.get("amount_bs", 0.0))
        currency = payload.get("currency", "USD")

        if currency == "BS" and raw_bs > 0:
            amount_usd = round(raw_bs / rate, 2)
            amount_bs = round(raw_bs, 2)
        else:
            amount_usd = round(raw_usd, 2)
            amount_bs = round(amount_usd * rate, 2)

        if amount_usd <= 0 and amount_bs <= 0:
            return AgentResponse(success=False, message="El monto debe ser un valor positivo.")

        now_vz = self.get_venezuela_now()
        issue_date = payload.get("issue_date") or now_vz.strftime("%Y-%m-%d")
        due_date = payload.get("due_date") or now_vz.strftime("%Y-%m-%d")
        status = payload.get("status", "Pendiente").strip().capitalize()
        if status not in ("Pendiente", "Abonado", "Pagado"):
            status = "Pendiente"

        prefix = "CXC" if c_type == "CxC" else "CXP"
        rec_id = f"{prefix}-{int(time.time() * 1000)}"

        item = {
            "id": rec_id,
            "type": c_type,
            "entity_name": entity_name,
            "concept": concept,
            "amount_usd": amount_usd,
            "amount_bs": amount_bs,
            "bcv_rate": rate,
            "issue_date": str(issue_date)[:10],
            "due_date": str(due_date)[:10],
            "status": status,
            "amount_paid_usd": 0.0,
            "amount_paid_bs": 0.0,
            "payment_method": payload.get("payment_method", "Pendiente"),
            "notes": payload.get("notes", ""),
            "created_at": now_vz.strftime("%Y-%m-%d %H:%M:%S"),
            "ledger_trx_id": None,
            "settled_at": None
        }

        # Si el usuario lo registra directamente como 'Pagado', liquidar de inmediato en Libro Mayor
        if status == "Pagado":
            method = payload.get("payment_method", "Pago Móvil")
            cat = payload.get("category") or ("Ventas / Facturación" if c_type == "CxC" else "Mercancía")
            trx_type = "Ingreso" if c_type == "CxC" else "Egreso"
            desc_prefix = "Cobro CxC" if c_type == "CxC" else "Pago CxP"
            trx_desc = f"{desc_prefix} - {entity_name}: {concept}"
            
            trx_res = self.record_transaction({
                "type": trx_type,
                "amount_usd": amount_usd,
                "amount_bs": amount_bs,
                "method": method,
                "category": cat,
                "description": trx_desc,
                "ref_code": rec_id
            })
            if trx_res.success:
                item["ledger_trx_id"] = trx_res.data.get("id")
                item["settled_at"] = now_vz.strftime("%Y-%m-%d %H:%M:%S")
                item["amount_paid_usd"] = amount_usd
                item["amount_paid_bs"] = amount_bs
                item["payment_method"] = method

        items = self._load_cxc_cxp()
        items.append(item)
        self._save_cxc_cxp(items)

        self.emit_event("cxc_cxp_recorded", item)
        tipo_str = "Cuenta por Cobrar (CxC)" if c_type == "CxC" else "Cuenta por Pagar (CxP)"
        return AgentResponse(
            success=True,
            data=item,
            message=f"{tipo_str} registrada exitosamente: {entity_name} - ${amount_usd:,.2f} USD ({amount_bs:,.2f} Bs)."
        )

    def settle_cxc_cxp(self, payload: Dict[str, Any]) -> AgentResponse:
        """
        Liquidación / Pago de una Cuenta por Cobrar o Pagar.
        Registra automáticamente la transacción correspondiente (Ingreso o Egreso)
        en el Libro Mayor principal, garantizando la consistencia contable sin duplicar datos.
        """
        rec_id = payload.get("cxc_cxp_id", "").strip()
        if not rec_id:
            return AgentResponse(success=False, message="ID de cuenta por cobrar/pagar requerido.")

        items = self._load_cxc_cxp()
        target_idx = None
        for i, it in enumerate(items):
            if it.get("id") == rec_id:
                target_idx = i
                break

        if target_idx is None:
            return AgentResponse(success=False, message=f"No se encontró el registro {rec_id}.")

        item = items[target_idx]

        # REGLA DE CONSISTENCIA Y ANTI-DUPLICACIÓN:
        if item.get("status") == "Pagado" or item.get("ledger_trx_id"):
            return AgentResponse(
                success=False,
                message=f"El registro {rec_id} ya se encuentra liquidado y asentado en el Libro Mayor (ID: {item.get('ledger_trx_id')}). No se duplica la operación."
            )

        c_type = item.get("type", "CxC")
        entity_name = item.get("entity_name", "")
        concept = item.get("concept", "")
        amount_usd = float(item.get("amount_usd", 0.0))
        
        # Tasa oficial actual para la liquidación
        bcv_data = BCVExchangeRateProvider.get_official_rate()
        current_rate = float(bcv_data.get("rate", item.get("bcv_rate", 1.0)))
        amount_bs = round(amount_usd * current_rate, 2)

        method = payload.get("payment_method") or "Pago Móvil"
        ref_code = payload.get("ref_code") or rec_id
        category = payload.get("category")
        if not category:
            category = "Servicio Técnico" if c_type == "CxC" else "Mercancía"

        trx_type = "Ingreso" if c_type == "CxC" else "Egreso"
        prefix = "Cobro CxC" if c_type == "CxC" else "Pago CxP"
        description = f"{prefix} - {entity_name}: {concept}"

        # 1. Registrar automáticamente en el Libro Mayor principal
        trx_res = self.record_transaction({
            "type": trx_type,
            "amount_usd": amount_usd,
            "amount_bs": amount_bs,
            "method": method,
            "category": category,
            "description": description,
            "ref_code": ref_code
        })

        if not trx_res.success:
            return AgentResponse(
                success=False,
                message=f"Error registrando en Libro Mayor: {trx_res.message}"
            )

        ledger_trx = trx_res.data
        ledger_id = ledger_trx.get("id")

        # 2. Actualizar el registro CxC/CxP con el ID del Libro Mayor para trazabilidad
        now_vz = self.get_venezuela_now()
        item["status"] = "Pagado"
        item["amount_paid_usd"] = amount_usd
        item["amount_paid_bs"] = amount_bs
        item["ledger_trx_id"] = ledger_id
        item["payment_method"] = method
        item["settled_at"] = now_vz.strftime("%Y-%m-%d %H:%M:%S")
        if payload.get("notes"):
            item["notes"] = f"{item.get('notes', '')} | Liquidación: {payload.get('notes')}".strip(" |")

        items[target_idx] = item
        self._save_cxc_cxp(items)

        self.emit_event("cxc_cxp_settled", {
            "cxc_cxp_id": rec_id,
            "ledger_trx_id": ledger_id,
            "type": c_type,
            "amount_usd": amount_usd,
            "amount_bs": amount_bs
        })

        accion_str = "Cobro registrado como INGRESO" if c_type == "CxC" else "Pago registrado como EGRESO"
        return AgentResponse(
            success=True,
            data={"cxc_cxp": item, "ledger_transaction": ledger_trx},
            message=(
                f"¡{rec_id} marcado como PAGADO con éxito!\n\n"
                f"• {accion_str} en Libro Mayor (ID: {ledger_id})\n"
                f"• Monto: ${amount_usd:,.2f} USD | {amount_bs:,.2f} Bs (Tasa: {current_rate:,.2f})\n"
                f"• Método: {method}"
            )
        )

    def get_cxc_cxp_summary(self) -> AgentResponse:
        """Calcula los totales y lista de Cuentas por Cobrar y por Pagar."""
        items = self._load_cxc_cxp()
        
        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))

        total_cxc_pending_usd = 0.0
        total_cxp_pending_usd = 0.0
        total_cxc_paid_usd = 0.0
        total_cxp_paid_usd = 0.0

        count_cxc_pending = 0
        count_cxp_pending = 0
        count_overdue = 0

        today_str = self.get_venezuela_now().strftime("%Y-%m-%d")

        for it in items:
            t = it.get("type", "CxC")
            st = it.get("status", "Pendiente")
            usd = float(it.get("amount_usd", 0.0))
            due = str(it.get("due_date", ""))[:10]

            if st in ("Pendiente", "Abonado"):
                if t == "CxC":
                    total_cxc_pending_usd += usd
                    count_cxc_pending += 1
                else:
                    total_cxp_pending_usd += usd
                    count_cxp_pending += 1

                if due and due < today_str:
                    count_overdue += 1
            elif st == "Pagado":
                if t == "CxC":
                    total_cxc_paid_usd += usd
                else:
                    total_cxp_paid_usd += usd

        summary = {
            "total_cxc_pending_usd": round(total_cxc_pending_usd, 2),
            "total_cxc_pending_bs": round(total_cxc_pending_usd * rate, 2),
            "total_cxp_pending_usd": round(total_cxp_pending_usd, 2),
            "total_cxp_pending_bs": round(total_cxp_pending_usd * rate, 2),
            "total_cxc_paid_usd": round(total_cxc_paid_usd, 2),
            "total_cxp_paid_usd": round(total_cxp_paid_usd, 2),
            "count_cxc_pending": count_cxc_pending,
            "count_cxp_pending": count_cxp_pending,
            "count_overdue": count_overdue,
            "total_records": len(items),
            "bcv_rate": rate,
            "records": items
        }

        return AgentResponse(success=True, data=summary, message="Resumen CxC/CxP obtenido.")

    def delete_cxc_cxp(self, payload: Dict[str, Any]) -> AgentResponse:
        """Elimina un registro de CxC o CxP."""
        rec_id = payload.get("cxc_cxp_id", "").strip()
        items = self._load_cxc_cxp()
        initial_len = len(items)
        items = [i for i in items if i.get("id") != rec_id]
        if len(items) < initial_len:
            self._save_cxc_cxp(items)
            return AgentResponse(success=True, message=f"Registro {rec_id} eliminado exitosamente.")
        return AgentResponse(success=False, message=f"No se encontró el registro {rec_id}.")
