"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: core/event_bus.py
Descripción: Bus de eventos asíncrono y desacoplado (Patrón Observer)
=============================================================================
"""

import threading
from typing import Callable, Dict, List, Any
from core.logger import app_logger


class EventBus:
    """Bus de eventos thread-safe para comunicación desacoplada entre departamentos."""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Suscribe una función callback a un tipo de evento determinado."""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            if callback not in self._listeners[event_type]:
                self._listeners[event_type].append(callback)
                app_logger.debug(f"EventBus: Suscrito a '{event_type}'")

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Cancela la suscripción de un callback a un tipo de evento."""
        with self._lock:
            if event_type in self._listeners and callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
                app_logger.debug(f"EventBus: Desuscrito de '{event_type}'")

    def publish(self, event_type: str, data: Any = None, async_exec: bool = True) -> None:
        """Emite un evento notificando a todos los escuchas registrados."""
        with self._lock:
            callbacks = list(self._listeners.get(event_type, []))
            # Oyentes globales (wildcard)
            callbacks.extend(self._listeners.get("*", []))

        app_logger.info(f"EventBus: Evento emitido '{event_type}' con {len(callbacks)} oyentes.")

        def _notify():
            for cb in callbacks:
                try:
                    cb(data)
                except Exception as e:
                    app_logger.error(f"EventBus: Error en callback para evento '{event_type}': {e}", exc_info=True)

        if async_exec:
            thread = threading.Thread(target=_notify, daemon=True)
            thread.start()
        else:
            _notify()


# Instancia única transversal para todo el sistema
system_event_bus = EventBus()
