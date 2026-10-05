"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: SERVICIO TÉCNICO Y TALLER
Módulo: tech_diagnostics_agent.py
Descripción: Agente Diagnosticador Técnico de Alta Precisión especializado
             en Epson, HP, Canon y Samsung (código de errores, piezas y banco de pruebas).
=============================================================================
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger


class TechDiagnosticsAgent(BaseAgent):
    """Agente especialista en diagnóstico y soporte técnico de impresoras y fotocopiadoras."""

    def __init__(self):
        super().__init__(
            agent_id="diagnosticador_tecnico",
            name="Agente Diagnosticador Técnico Especialista",
            department="Servicio Técnico y Taller",
            description="Diagnóstico técnico avanzado de fallas mecánicas, electrónicas y de consumibles para Epson, HP, Canon y Samsung."
        )
        self.kb = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Base de conocimientos técnicos pre-cargada con procedimientos exactos de taller."""
        return {
            "epson": {
                "almohadillas": "Falla de almohadillas de tinta al 100%. Procedimiento: 1. Reseteo lógico del contador mediante software de servicio. 2. Desmontaje del módulo trasero inferior y sustitución física o lavado/secado de almohadillas para evitar derrames en placa madre.",
                "cabezal": "Inyectores obstruidos o impresión en blanco. Procedimiento: 1. Test de inyectores. 2. Purgado de dampers (eliminar vacío de aire). 3. Limpieza por ultrasonido o líquido limpia-cabezales específico si hay líneas faltantes. No forzar presión excesiva para proteger el piezoeléctrico.",
                "atasco_papel": "Atascamiento mecánico. Procedimiento: Inspeccionar objeto extraño en bandeja posterior, revisar sensor de paso de papel (flag óptico) y limpiar goma del rodillo pick-up con alcohol isopropílico."
            },
            "hp": {
                "error_50": "Error 50.x de Fusor. Procedimiento: Falla en unidad fusora térmica. Desarmar bloque fusor, medir continuidad de lámpara halógena/cerámica, termistor e inspeccionar desgaste de película de teflón y rodillo de presión.",
                "rodillo_pickup": "Patinado o no toma papel. Procedimiento: Sustitución de goma de arrastre (Pick-up roller) y almohadilla de separación (Separation pad).",
                "chip_toner": "Tóner no reconocido / Cartucho bloqueado. Procedimiento: Sustituir chip de cartucho (compatible con firmware de la placa formateadora) o verificar contactos metálicos internos del chasis."
            },
            "canon": {
                "drum_cilindro": "Líneas repetitivas o velo gris de fondo. Procedimiento: Sustitución de cilindro OPC y cuchilla dosificadora (wiper blade). Limpieza del PCR (Primary Charge Roller).",
                "atasco_ir": "Atasco frecuente en fotocopiadoras imageRUNNER. Procedimiento: Revisión de embragues de alimentación, rodillos de registro y sensores fotoeléctricos."
            },
            "samsung": {
                "toner_d111": "Fondo sucio o tóner claro. Procedimiento: Recarga con polvo magnético específico Samsung, limpieza de cuchilla dosificadora y reseteo de chip.",
                "sensor_fusor": "Sobrecalentamiento o atascamiento en salida. Procedimiento: Limpieza de termistores y uñas separadoras del rodillo fusor."
            }
        }

    def _load_workshop_jobs(self) -> List[Dict[str, Any]]:
        if not os.path.exists(SystemConfig.WORKSHOP_FILE):
            return []
        try:
            with open(SystemConfig.WORKSHOP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_workshop_jobs(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(SystemConfig.WORKSHOP_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando órdenes de taller: {e}")

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Agente Técnico ejecutando tarea: {task_type}")

        if task_type == "diagnose_equipment":
            return self.diagnosticar_equipo(payload)
        elif task_type == "register_repair_job":
            return self.registrar_orden_servicio(payload)
        elif task_type == "update_job_status":
            return self.actualizar_estado_orden(payload)
        elif task_type == "get_workshop_jobs":
            return AgentResponse(success=True, data=self._load_workshop_jobs())
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

    def diagnosticar_equipo(self, payload: Dict[str, Any]) -> AgentResponse:
        """Emite un diagnóstico paso a paso combinando base de conocimientos e IA."""
        marca = payload.get("brand", "Epson").lower()
        modelo = payload.get("model", "")
        sintomas = payload.get("symptoms", "")

        # Verificar coincidencias clave locales
        kb_sugerencias = []
        marca_kb = self.kb.get(marca, {})
        for k, v in marca_kb.items():
            if k in sintomas.lower():
                kb_sugerencias.append(v)

        prompt = f"""
        Eres el Jefe Técnico de Taller de 'Inversiones Reinaldo Golindano' (Especialista en impresoras y fotocopiadoras Epson, HP, Canon, Samsung).
        Equipo a diagnosticar:
        - Marca: {marca.upper()}
        - Modelo: {modelo}
        - Síntomas reportados / Código de error: "{sintomas}"

        Genera un dictamen técnico de alta precisión con la siguiente estructura:
        1. DIAGNÓSTICO PROBABLE: Causa raíz de la falla.
        2. PROCEDIMIENTO PASO A PASO: Pasos ordenados para desarmado, prueba con multímetro y corrección en banco de trabajo.
        3. REPUESTOS O INSUMOS REQUERIDOS: Lista de piezas con su nombre técnico comercial para cotización en Compras y Procura.
        4. TIEMPO ESTIMADO DE TALLER: Horas estimadas y nivel de dificultad técnica.
        """

        try:
            ai_diag = self.call_gemini(prompt)
            resultado = {
                "brand": marca.upper(),
                "model": modelo,
                "symptoms": sintomas,
                "diagnosis_text": ai_diag,
                "kb_references": kb_sugerencias,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.emit_event("diagnostic_completed", {"brand": marca, "model": modelo})
            return AgentResponse(success=True, data=resultado, message="Diagnóstico técnico emitido con éxito.")
        except Exception as e:
            app_logger.warning(f"Error consultando IA para diagnóstico: {e}")
            fallback = "\n".join(kb_sugerencias) if kb_sugerencias else "Revisión general mecánica requerida."
            return AgentResponse(
                success=True,
                data={"brand": marca.upper(), "model": modelo, "diagnosis_text": fallback},
                message="Diagnóstico generado con base de datos local de taller."
            )

    def registrar_orden_servicio(self, payload: Dict[str, Any]) -> AgentResponse:
        """Crea una orden de servicio técnico en taller."""
        job_id = f"ST-{int(time.time() % 100000)}"
        cliente = payload.get("client_name", "Particular")
        telefono = payload.get("client_phone", "N/A")
        equipo = f"{payload.get('brand', '')} {payload.get('model', '')}".strip()
        falla = payload.get("symptoms", "Mantenimiento general")
        costo_estimado = float(payload.get("cost_usd", 0.0))

        orden = {
            "job_id": job_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "client_name": cliente,
            "client_phone": telefono,
            "equipment": equipo,
            "symptoms": falla,
            "estimated_cost_usd": costo_estimado,
            "status": "En Banco de Prueba"  # En Banco de Prueba, Espera Repuesto, Reparado, Entregado
        }

        jobs = self._load_workshop_jobs()
        jobs.append(orden)
        self._save_workshop_jobs(jobs)

        self.emit_event("repair_job_registered", orden)
        return AgentResponse(success=True, data=orden, message=f"Orden {job_id} ingresada a taller.")

    def actualizar_estado_orden(self, payload: Dict[str, Any]) -> AgentResponse:
        job_id = payload.get("job_id")
        nuevo_estado = payload.get("status", "Reparado")

        jobs = self._load_workshop_jobs()
        encontrada = next((x for x in jobs if x.get("job_id") == job_id), None)
        if encontrada:
            encontrada["status"] = nuevo_estado
            encontrada["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_workshop_jobs(jobs)
            self.emit_event("repair_job_updated", encontrada)
            return AgentResponse(success=True, data=encontrada, message=f"Orden {job_id} actualizada a '{nuevo_estado}'.")

        return AgentResponse(success=False, message=f"Orden {job_id} no encontrada.")
