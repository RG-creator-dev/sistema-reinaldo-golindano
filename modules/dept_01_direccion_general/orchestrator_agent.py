"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: DIRECCIÓN GENERAL
Módulo: orchestrator_agent.py
Descripción: Agente Orquestador Central y Síntesis Ejecutiva con Inteligencia Artificial.
             Control autónomo de auditorías diarias (CxC vencidas, Libro Mayor USD/VES)
             y activación del Orquestador B2B de campañas semanales (Google Sheets).
=============================================================================
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider

VENEZUELA_TZ = timezone(timedelta(hours=-4))


class OrchestratorAgent(BaseAgent):
    """Agente Orquestador Central y Síntesis de Dirección General."""

    def __init__(self):
        super().__init__(
            agent_id="orquestador_central",
            name="Agente Orquestador Central",
            department="Dirección General",
            description="Supervisión global de los 5 departamentos, auditoría de salud del sistema, detección de CxC y campañas B2B."
        )
        self.sub_agents: Dict[str, BaseAgent] = {}

    def register_agent(self, key: str, agent: BaseAgent):
        """Registra un agente departamental bajo la supervisión de Dirección General."""
        self.sub_agents[key] = agent
        app_logger.info(f"[Agent.{self.agent_id}] Agente registrado en Orquestación: {key} -> {agent.name}")

    def execute(self, task_type: str, payload: Dict[str, Any] = None) -> AgentResponse:
        if payload is None:
            payload = {}
        app_logger.info(f"Orquestador ejecutando tarea: {task_type}")

        if task_type == "consolidate_executive_report":
            return self.consolidate_executive_report(payload)
        elif task_type == "get_system_health":
            return self.get_system_health()
        elif task_type == "broadcast_directive":
            return self.broadcast_directive(payload)
        elif task_type == "daily_autonomous_scan":
            return self.scan_daily_autonomous_audit()
        elif task_type == "execute_b2b_campaign":
            return self.execute_b2b_weekly_campaign(payload)
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

    # -------------------------------------------------------------------------
    # 1. Tareas Autónomas: Escaneo Diario en Segundo Plano (CxC + Finanzas)
    # -------------------------------------------------------------------------

    def scan_daily_autonomous_audit(self) -> AgentResponse:
        """
        Rutina de escaneo diario autónomo del Director General:
        a) Detecta Cuentas por Cobrar (CxC) vencidas con detalle de clientes y montos ($ y Bs).
        b) Consolida automáticamente los resúmenes financieros del Libro Mayor (USD y VES)
           según la tasa oficial actual del BCV.
        """
        now_vz = datetime.now(VENEZUELA_TZ)
        today_str = now_vz.strftime("%Y-%m-%d")

        # Tasa oficial actual del BCV
        bcv_data = BCVExchangeRateProvider.get_official_rate()
        rate = float(bcv_data.get("rate", 1.0))
        if rate <= 0:
            rate = 1.0

        # a) Detección de Cuentas por Cobrar (CxC) Vencidas
        overdue_cxc = []
        pending_cxc = []
        total_overdue_usd = 0.0
        total_pending_cxc_usd = 0.0

        cxc_path = getattr(SystemConfig, "CXC_CXP_FILE", os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "cxc_cxp.json"))
        if os.path.exists(cxc_path):
            try:
                with open(cxc_path, "r", encoding="utf-8") as f:
                    cxc_records = json.load(f)
                    for r in cxc_records:
                        if r.get("type") == "CxC" and r.get("status") in ("Pendiente", "Abonado"):
                            usd = float(r.get("amount_usd", 0.0))
                            bs = round(usd * rate, 2)
                            total_pending_cxc_usd += usd
                            pending_cxc.append(r)

                            due_date = str(r.get("due_date", ""))[:10]
                            if due_date and due_date < today_str:
                                # Calcular días de retraso
                                try:
                                    d_due = datetime.strptime(due_date, "%Y-%m-%d").date()
                                    d_today = now_vz.date()
                                    dias_vencido = (d_today - d_due).days
                                except Exception:
                                    dias_vencido = 1

                                total_overdue_usd += usd
                                overdue_cxc.append({
                                    "id": r.get("id"),
                                    "entity_name": r.get("entity_name"),
                                    "concept": r.get("concept"),
                                    "amount_usd": usd,
                                    "amount_bs": bs,
                                    "issue_date": r.get("issue_date"),
                                    "due_date": due_date,
                                    "days_overdue": dias_vencido,
                                    "status": r.get("status")
                                })
            except Exception as e:
                app_logger.error(f"Error escaneando CxC en Dirección General: {e}")

        # Ordenar CxC vencidas por días de mora (mayor a menor)
        overdue_cxc.sort(key=lambda x: -x["days_overdue"])

        # b) Consolidación Financiera del Libro Mayor (USD / VES)
        fin_summary = {
            "initial_balance_usd": 0.0,
            "initial_balance_bs": 0.0,
            "total_income_usd": 0.0,
            "total_income_bs": 0.0,
            "total_expense_usd": 0.0,
            "total_expense_bs": 0.0,
            "net_balance_usd": 0.0,
            "net_balance_bs": 0.0,
            "bcv_rate": rate
        }

        # Consultar directamente al agente contable si está disponible
        if "accounting" in self.sub_agents:
            res_fin = self.sub_agents["accounting"].execute("get_financial_summary", {"year": now_vz.year, "month": now_vz.month})
            if res_fin.success:
                fin_summary = res_fin.data
        else:
            # Cálculo alternativo local
            ledger_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
            if os.path.exists(ledger_path):
                try:
                    with open(ledger_path, "r", encoding="utf-8") as f:
                        ledger = json.load(f)
                    
                    # Filtrar por mes en curso
                    cur_y = now_vz.year
                    cur_m = now_vz.month
                    for r in ledger:
                        f_str = str(r.get("date", ""))[:10]
                        try:
                            dt = datetime.strptime(f_str, "%Y-%m-%d")
                            if dt.year == cur_y and dt.month == cur_m:
                                u = float(r.get("amount_usd", 0.0))
                                b = float(r.get("amount_bs", 0.0))
                                if b <= 0:
                                    b = round(u * rate, 2)
                                if str(r.get("type", "")).strip().lower() == "ingreso":
                                    fin_summary["total_income_usd"] += u
                                    fin_summary["total_income_bs"] += b
                                else:
                                    fin_summary["total_expense_usd"] += u
                                    fin_summary["total_expense_bs"] += b
                        except Exception:
                            pass
                    
                    fin_summary["net_balance_usd"] = round(fin_summary["total_income_usd"] - fin_summary["total_expense_usd"], 2)
                    fin_summary["net_balance_bs"] = round(fin_summary["total_income_bs"] - fin_summary["total_expense_bs"], 2)
                except Exception as e:
                    app_logger.error(f"Error consolidando finanzas en auditoría autónoma: {e}")

        audit_data = {
            "timestamp": now_vz.strftime("%Y-%m-%d %H:%M:%S"),
            "bcv_rate": rate,
            "overdue_cxc": overdue_cxc,
            "overdue_count": len(overdue_cxc),
            "overdue_total_usd": round(total_overdue_usd, 2),
            "overdue_total_bs": round(total_overdue_usd * rate, 2),
            "pending_cxc_count": len(pending_cxc),
            "pending_cxc_total_usd": round(total_pending_cxc_usd, 2),
            "pending_cxc_total_bs": round(total_pending_cxc_usd * rate, 2),
            "financial_summary": fin_summary
        }

        self.emit_event("daily_autonomous_audit_completed", audit_data)
        return AgentResponse(
            success=True,
            data=audit_data,
            message=(
                f"Auditoría diaria completada: {len(overdue_cxc)} CxC vencidas detectadas "
                f"(${total_overdue_usd:,.2f} USD). Resumen financiero consolidado (Tasa: {rate:,.2f} Bs)."
            )
        )

    # -------------------------------------------------------------------------
    # 2. Activación del Orquestador B2B Semanal (Un solo clic o Programado)
    # -------------------------------------------------------------------------

    def execute_b2b_weekly_campaign(self, payload: Dict[str, Any] = None) -> AgentResponse:
        """
        Activa el Orquestador B2B para generar automáticamente las 3 publicaciones
        semanales (Lunes, Miércoles, Viernes) con fotos reales e inserción directa en Google Sheets.
        """
        payload = payload or {}
        cat_filtro = payload.get("categoria_filtro")

        b2b_agent = self.sub_agents.get("b2b_marketing")
        if not b2b_agent:
            from modules.dept_02_comercio_ventas.b2b_marketing_agent import B2BMarketingAgent
            b2b_agent = B2BMarketingAgent()
            self.register_agent("b2b_marketing", b2b_agent)

        app_logger.info(f"Director General activando Orquestador B2B (Filtro: {cat_filtro or 'Rotación Automática'})...")
        res = b2b_agent.generar_lote_semanal(categoria_filtro=cat_filtro)

        if res.success:
            self.emit_event("executive_b2b_campaign_triggered", {
                "triggered_by": "Director General",
                "filter": cat_filtro,
                "posts": res.data
            })

        return res

    # -------------------------------------------------------------------------
    # 3. Supervisión, Salud del Sistema e Informes Ejecutivos
    # -------------------------------------------------------------------------

    def get_system_health(self) -> AgentResponse:
        """Verifica la salud operativa de todos los componentes y servicios del sistema."""
        bcv_status = BCVExchangeRateProvider.get_official_rate()

        agents_health = {}
        for k, ag in self.sub_agents.items():
            agents_health[k] = ag.get_status()

        health_data = {
            "system_name": SystemConfig.APP_NAME,
            "version": SystemConfig.APP_VERSION,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bcv_rate": bcv_status["rate"],
            "bcv_status": bcv_status["status"],
            "gemini_api_configured": bool(SystemConfig.GEMINI_API_KEY),
            "telegram_token_configured": bool(SystemConfig.TELEGRAM_BOT_TOKEN),
            "agents_registered": len(self.sub_agents),
            "agents": agents_health
        }

        return AgentResponse(success=True, data=health_data, message="Estado del sistema óptimo.")

    def broadcast_directive(self, payload: Dict[str, Any]) -> AgentResponse:
        """Envía una directriz ejecutiva a través del EventBus central."""
        directiva = payload.get("directive", "Mantener alerta de stock crítico")
        prioridad = payload.get("priority", "NORMAL")
        self.emit_event("executive_directive", {"directive": directiva, "priority": prioridad})
        return AgentResponse(success=True, message=f"Directiva emitida a todos los departamentos ({prioridad}).")

    def consolidate_executive_report(self, payload: Dict[str, Any] = None) -> AgentResponse:
        """
        Sintetiza la información en tiempo real de los 5 departamentos y genera
        un informe de gestión con recomendaciones de negocio usando Gemini AI.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Auditoría de Cuentas y Finanzas
        audit_res = self.scan_daily_autonomous_audit()
        audit_data = audit_res.data
        fin_d = audit_data["financial_summary"]
        fin_status = (
            f"Ingresos: ${fin_d['total_income_usd']:,.2f} ({fin_d['total_income_bs']:,.2f} Bs) | "
            f"Gastos: ${fin_d['total_expense_usd']:,.2f} ({fin_d['total_expense_bs']:,.2f} Bs) | "
            f"Balance Neto en Caja: ${fin_d['net_balance_usd']:,.2f} ({fin_d['net_balance_bs']:,.2f} Bs) | "
            f"CxC Vencidas: {audit_data['overdue_count']} (${audit_data['overdue_total_usd']:,.2f} USD)"
        )

        # 2. Datos de Procura y Stock
        sup_status = "Sin registros"
        if "supply_audit" in self.sub_agents:
            res_sup = self.sub_agents["supply_audit"].execute("audit_inventory", {})
            if res_sup.success:
                crit = len(res_sup.data.get("critical_items", []))
                tot = res_sup.data.get("total_items", 0)
                sup_status = f"Total ítems: {tot} | Ítems en estado crítico: {crit}"

        # 3. Datos de Cotizaciones
        quotes_count = 0
        if os.path.exists(SystemConfig.QUOTES_FILE):
            try:
                with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                    recs = json.load(f)
                    quotes_count = len(recs)
            except Exception:
                pass

        # 4. Datos de Taller
        workshop_count = 0
        if os.path.exists(SystemConfig.WORKSHOP_FILE):
            try:
                with open(SystemConfig.WORKSHOP_FILE, "r", encoding="utf-8") as f:
                    w_recs = json.load(f)
                    workshop_count = len(w_recs)
            except Exception:
                pass

        bcv = BCVExchangeRateProvider.get_official_rate()

        prompt = f"""
        Eres el Director General de 'Inversiones Reinaldo Golindano' (Empresa líder en Carabobo en servicio técnico de impresoras/fotocopiadoras Epson, HP, Canon, Samsung, venta de suministros e insumos).
        Fecha de reporte: {now_str}
        Tasa Oficial BCV: {bcv['rate']:,.2f} Bs/USD

        ESTADO ACTUAL DE OPERACIONES EN LOS DEPARTAMENTOS:
        - 🏛️ Finanzas y Cobranzas: {fin_status}
        - 📦 Compras y Procura: {sup_status}
        - 💼 Ventas y Cotizaciones: {quotes_count} cotizaciones emitidas
        - 🛠️ Servicio Técnico y Taller: {workshop_count} órdenes activas/registradas

        Redacta un INFORME EJECUTIVO DE GESTIÓN estructurado:
        1. DIAGNÓSTICO ESTRATÉGICO GENERAL (Salud de las operaciones).
        2. ANÁLISIS DE RENTABILIDAD Y CAJA (Equilibrio USD/Bs y recuperación de CxC vencidas).
        3. PLAN DE ACCIÓN INMEDIATO (Prioridades para el taller, reposición de tóners/piezas, campañas B2B semanales y metas de ventas).
        4. DIRECTRICES PARA LOS 5 DEPARTAMENTOS.
        """

        try:
            ai_report = self.call_gemini(prompt)
            report_data = {
                "report_text": ai_report,
                "timestamp": now_str,
                "bcv_rate": bcv["rate"],
                "audit": audit_data
            }
            self.emit_event("executive_report_ready", report_data)
            return AgentResponse(success=True, data=report_data, message="Informe ejecutivo consolidado exitosamente.")
        except Exception as e:
            app_logger.error(f"Error generando reporte ejecutivo con IA: {e}")
            fallback_text = (
                f"INFORME EJECUTIVO LOCAL - {now_str}\n"
                f"Tasa BCV: {bcv['rate']:,.2f} Bs/USD\n\n"
                f"Finanzas y Cobranzas:\n{fin_status}\n\n"
                f"Procura y Stock: {sup_status}\n"
                f"Cotizaciones Emitidas: {quotes_count}\n"
                f"Taller: {workshop_count} equipos\n"
            )
            return AgentResponse(success=True, data={"report_text": fallback_text, "audit": audit_data}, message="Reporte consolidado localmente.")
