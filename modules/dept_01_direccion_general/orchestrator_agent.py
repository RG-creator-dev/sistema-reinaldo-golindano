"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: DIRECCIÓN GENERAL
Módulo: orchestrator_agent.py
Descripción: Agente Orquestador Central y Síntesis Ejecutiva con Inteligencia Artificial.
=============================================================================
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider


class OrchestratorAgent(BaseAgent):
    """Agente Orquestador Central y Síntesis de Dirección General."""

    def __init__(self):
        super().__init__(
            agent_id="orquestador_central",
            name="Agente Orquestador Central",
            department="Dirección General",
            description="Supervisión global de los 5 departamentos, auditoría de salud del sistema e informes ejecutivos de gestión."
        )
        self.sub_agents: Dict[str, BaseAgent] = {}

    def register_agent(self, key: str, agent: BaseAgent):
        """Registra un agente departamental bajo la supervisión de Dirección General."""
        self.sub_agents[key] = agent
        app_logger.info(f"[Agent.{self.agent_id}] Agente registrado en Orquestación: {key} -> {agent.name}")

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Orquestador ejecutando tarea: {task_type}")

        if task_type == "consolidate_executive_report":
            return self.consolidate_executive_report(payload)
        elif task_type == "get_system_health":
            return self.get_system_health()
        elif task_type == "broadcast_directive":
            return self.broadcast_directive(payload)
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

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

        # 1. Datos Financieros
        fin_status = "Sin registros"
        if "accounting" in self.sub_agents:
            res_fin = self.sub_agents["accounting"].execute("get_financial_summary", {})
            if res_fin.success:
                d = res_fin.data
                fin_status = f"Ingresos: ${d['total_income_usd']} | Gastos: ${d['total_expense_usd']} | Balance Neto: ${d['net_balance_usd']} ({d['net_balance_bs']} Bs)"

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
        - 🏛️ Finanzas: {fin_status}
        - 📦 Compras y Procura: {sup_status}
        - 💼 Ventas y Cotizaciones: {quotes_count} cotizaciones emitidas
        - 🛠️ Servicio Técnico y Taller: {workshop_count} órdenes activas/registradas

        Redacta un INFORME EJECUTIVO DE GESTIÓN estructurado:
        1. DIAGNÓSTICO ESTRATÉGICO GENERAL (Salud de las operaciones).
        2. ANÁLISIS DE RENTABILIDAD Y CAJA (Equilibrio USD/Bs).
        3. PLAN DE ACCIÓN INMEDIATO (Prioridades para el taller, reposición de tóners/piezas y metas de ventas).
        4. DIRECTRICES PARA LOS 5 DEPARTAMENTOS.
        """

        try:
            ai_report = self.call_gemini(prompt)
            report_data = {
                "report_text": ai_report,
                "timestamp": now_str,
                "bcv_rate": bcv["rate"]
            }
            self.emit_event("executive_report_ready", report_data)
            return AgentResponse(success=True, data=report_data, message="Informe ejecutivo consolidado exitosamente.")
        except Exception as e:
            app_logger.error(f"Error generando reporte ejecutivo: {e}")
            fallback_text = (
                f"INFORME EJECUTIVO LOCAL - {now_str}\n"
                f"Tasa BCV: {bcv['rate']:,.2f} Bs/USD\n\n"
                f"Finanzas: {fin_status}\n"
                f"Procura: {sup_status}\n"
                f"Cotizaciones Emitidas: {quotes_count}\n"
                f"Taller: {workshop_count} equipos\n"
            )
            return AgentResponse(success=True, data={"report_text": fallback_text}, message="Reporte consolidado localmente.")
