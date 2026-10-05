"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: core/base_agent.py
Descripción: Contrato abstracto y funcionalidad base para los Agentes IA
=============================================================================
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from config import SystemConfig
from core.logger import app_logger
from core.event_bus import system_event_bus


class AgentResponse:
    """Estructura normalizada para las respuestas emitidas por los agentes del sistema."""
    
    def __init__(self, success: bool, data: Any = None, message: str = "", raw_response: str = ""):
        self.success = success
        self.data = data or {}
        self.message = message
        self.raw_response = raw_response
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "raw_response": self.raw_response,
            "timestamp": self.timestamp
        }


class BaseAgent(ABC):
    """Clase base para todos los agentes de los 5 departamentos."""

    def __init__(self, agent_id: str, name: str, department: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.department = department
        self.description = description
        self.is_active = True
        self.gemini_client = None
        self.usar_genai_nuevo = False
        
        self._init_gemini_client()

    def _init_gemini_client(self):
        """Inicializa el cliente Gemini utilizando el SDK oficial moderno con fallback."""
        api_key = SystemConfig.GEMINI_API_KEY
        if not api_key:
            app_logger.warning(f"[{self.name}] No se detectó GEMINI_API_KEY en la configuración.")
            return

        try:
            from google import genai
            self.gemini_client = genai.Client(api_key=api_key)
            self.usar_genai_nuevo = True
            app_logger.info(f"[Agent.{self.agent_id}] Cliente google.genai inicializado exitosamente para {self.name}.")
        except Exception as e:
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=api_key)
                self.gemini_client = genai_old
                self.usar_genai_nuevo = False
                app_logger.info(f"[Agent.{self.agent_id}] Cliente google.generativeai inicializado (fallback) para {self.name}.")
            except Exception as e2:
                app_logger.error(f"[Agent.{self.agent_id}] Error al inicializar Gemini API: {e2}")

    def call_gemini(self, prompt: str, system_instruction: str = "", model_name: str = "gemini-3.6-flash") -> str:
        """
        Ejecuta una consulta a Gemini con reintentos y tolerancia a fallos 503 / 429.
        Soporta modelos: gemini-3.6-flash, gemini-3.6-pro, gemini-flash-latest.
        """
        if not self.gemini_client:
            raise ValueError(f"[{self.name}] Gemini Client no está disponible. Verifique GEMINI_API_KEY.")

        modelos_a_probar = [model_name, "gemini-3-flash-preview", "gemini-flash-lite-latest", "gemini-3.6-flash", "gemini-3.6-pro"]
        # Eliminar duplicados manteniendo orden
        vistos = set()
        modelos_ordenados = [m for m in modelos_a_probar if not (m in vistos or vistos.add(m))]

        for modelo in modelos_ordenados:
            for intento in range(1, 4):
                try:
                    if self.usar_genai_nuevo:
                        from google.genai import types
                        config = None
                        if system_instruction:
                            config = types.GenerateContentConfig(system_instruction=system_instruction)
                        
                        resp = self.gemini_client.models.generate_content(
                            model=modelo,
                            contents=prompt,
                            config=config
                        )
                        return resp.text.strip() if resp.text else ""
                    else:
                        m = self.gemini_client.GenerativeModel(
                            model_name=modelo,
                            system_instruction=system_instruction if system_instruction else None
                        )
                        resp = m.generate_content(prompt)
                        return resp.text.strip() if resp.text else ""

                except Exception as e:
                    err_msg = str(e)
                    app_logger.warning(f"[Agent.{self.agent_id}] Intento {intento} con modelo {modelo} falló: {err_msg}")
                    if any(x in err_msg.lower() for x in ["503", "429", "unavailable", "quota", "resource_exhausted"]):
                        time.sleep(2 * intento)
                    else:
                        break  # Si es otro tipo de error, intentar con siguiente modelo

        raise RuntimeError(f"[{self.name}] No fue posible obtener respuesta de Gemini tras múltiples reintentos.")

    @abstractmethod
    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        """Punto de entrada principal para ejecutar tareas asignadas al agente."""
        pass

    def emit_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None):
        """Emite un evento asociado a este agente a través del EventBus central."""
        event_key = f"{self.department}.{self.agent_id}.{event_name}"
        data = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "department": self.department,
            "payload": payload or {},
            "timestamp": datetime.now().isoformat()
        }
        system_event_bus.publish(event_key, data)

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado operativo actual del agente."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "department": self.department,
            "active": self.is_active,
            "gemini_ready": self.gemini_client is not None,
            "sdk_mode": "google.genai (nuevo)" if self.usar_genai_nuevo else "google.generativeai (legado)"
        }
