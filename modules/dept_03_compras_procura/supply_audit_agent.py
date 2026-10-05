"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: supply_audit_agent.py
Descripción: Agente Analista de Suministros, Inventario Crítico y Auditoría de Proveedores.
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
from modules.dept_03_compras_procura.web_scraper import GlobalWebScraper


class SupplyAuditAgent(BaseAgent):
    """Agente Analista de Compras e Inventario del Taller."""

    def __init__(self, web_scraper: Optional[GlobalWebScraper] = None):
        super().__init__(
            agent_id="analista_suministros",
            name="Agente Analista de Suministros y Proveedores",
            department="Compras y Procura",
            description="Auditoría de inventario de repuestos críticos, tóners, cabezales y análisis de compras nacionales e internacionales."
        )
        self.web_scraper = web_scraper or GlobalWebScraper()

    def _load_inventory(self) -> List[Dict[str, Any]]:
        """Carga el inventario de compras/stock."""
        if not os.path.exists(SystemConfig.PURCHASES_FILE):
            return []
        try:
            with open(SystemConfig.PURCHASES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_inventory(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(SystemConfig.PURCHASES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error guardando compras/inventario: {e}")

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Agente de Procura ejecutando tarea: {task_type}")

        if task_type == "audit_inventory":
            return self.audit_inventory()
        elif task_type == "register_purchase":
            return self.register_purchase(payload)
        elif task_type == "update_stock":
            return self.update_stock(payload)
        elif task_type == "search_supplier_prices":
            return self.search_supplier_prices(payload)
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

    def audit_inventory(self) -> AgentResponse:
        """Audita el stock actual contra umbrales mínimos requeridos."""
        inv = self._load_inventory()
        critical_items = []
        normal_items = []

        for item in inv:
            stock = int(item.get("current_stock", 0))
            min_stock = int(item.get("min_stock", 2))
            if stock <= min_stock:
                critical_items.append(item)
            else:
                normal_items.append(item)

        if critical_items:
            self.emit_event("low_stock_detected", {"critical_count": len(critical_items)})

        audit_data = {
            "total_items": len(inv),
            "critical_items": critical_items,
            "normal_items": normal_items,
            "status": "CRITICAL" if critical_items else "OPTIMAL"
        }

        return AgentResponse(
            success=True,
            data=audit_data,
            message=f"Auditoría completada. {len(critical_items)} ítems en stock crítico."
        )

    def register_purchase(self, payload: Dict[str, Any]) -> AgentResponse:
        """Registra una nueva adquisición o insumo en el inventario."""
        sku = payload.get("sku", f"SKU-{int(time.time())}")
        name = payload.get("name", "Insumo / Repuesto")
        category = payload.get("category", "Tóner")
        stock = int(payload.get("stock", 1))
        min_stock = int(payload.get("min_stock", 2))
        cost_usd = float(payload.get("cost_usd", 0.0))
        supplier = payload.get("supplier", "Nacional")

        inv = self._load_inventory()
        # Verificar si ya existe
        item_existente = next((x for x in inv if x.get("sku") == sku), None)
        if item_existente:
            item_existente["current_stock"] = int(item_existente.get("current_stock", 0)) + stock
            item_existente["cost_usd"] = cost_usd
        else:
            inv.append({
                "sku": sku,
                "name": name,
                "category": category,
                "current_stock": stock,
                "min_stock": min_stock,
                "cost_usd": cost_usd,
                "supplier": supplier,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        self._save_inventory(inv)
        return AgentResponse(
            success=True,
            data={"sku": sku, "name": name, "stock": stock},
            message=f"Insumo '{name}' ({sku}) registrado en inventario."
        )

    def update_stock(self, payload: Dict[str, Any]) -> AgentResponse:
        sku = payload.get("sku")
        new_stock = int(payload.get("new_stock", 0))
        inv = self._load_inventory()
        item = next((x for x in inv if x.get("sku") == sku), None)
        if item:
            item["current_stock"] = new_stock
            item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save_inventory(inv)
            return AgentResponse(success=True, message=f"Stock de {sku} actualizado a {new_stock}.")
        return AgentResponse(success=False, message=f"SKU {sku} no encontrado.")

    def search_supplier_prices(self, payload: Dict[str, Any]) -> AgentResponse:
        producto = payload.get("query", "")
        ambito = payload.get("ambito", "Nacional")
        importar = payload.get("incluye_importacion", False)

        hallazgos = self.web_scraper.buscar_sitios_web(producto, ambito=ambito)
        dictamen = self.web_scraper.analizar_con_gemini_v2(producto, hallazgos, ambito=ambito, incluye_importacion=importar)

        return AgentResponse(
            success=True,
            data={"dictamen": dictamen, "hallazgos": hallazgos},
            message="Rastreo y análisis de compras culminado."
        )
