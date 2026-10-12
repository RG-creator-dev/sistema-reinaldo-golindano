"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: core/cloud_sync.py
Descripción: Motor de sincronización optimizado hacia el servidor en la nube
             (Render) con revisión exhaustiva y autocompilación de PDFs faltantes.
=============================================================================
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import SystemConfig
from core.logger import app_logger
from core.event_bus import event_bus
from modules.dept_02_comercio_ventas.pdf_generator import PDFQuoteGenerator


class CloudSyncManager:
    """Administrador de sincronización con el servidor central en Render."""

    def __init__(self, sync_url: Optional[str] = None, sync_token: Optional[str] = None):
        self.sync_url = "https://sistema-reinaldo-golindano.onrender.com"
        self.sync_token = sync_token or getattr(SystemConfig, "RENDER_SYNC_TOKEN", "inversiones_reinaldo_golindano_sync_key")
        self.last_sync_time: Optional[str] = None
        self.is_syncing: bool = False

    def sync_bidirectional(self, timeout: int = 15) -> Dict[str, Any]:
        """
        Ejecuta la sincronización con el servidor en Render mediante GET.
        """
        if self.is_syncing:
            return {
                "success": False,
                "message": "Ya existe una sincronización en curso.",
                "new_transactions": 0,
                "new_quotes": 0
            }

        self.is_syncing = True
        app_logger.info(f"Iniciando sincronización con Render: {self.sync_url}")

        endpoint = f"{self.sync_url}/api/sync"
        headers = {
            "User-Agent": "IRG-Desktop-App/2.0",
            "Authorization": f"Bearer {self.sync_token}",
            "Accept": "application/json"
        }

        max_intentos = 2
        last_error = ""

        for intento in range(1, max_intentos + 1):
            try:
                resp = requests.get(endpoint, headers=headers, timeout=timeout)

                if resp.status_code == 200:
                    cloud_data = resp.json()
                    merge_result = self._merge_cloud_data(cloud_data)
                    self.last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    app_logger.info(
                        f"Sincronización exitosa: "
                        f"+{merge_result['new_transactions']} transacciones nuevas, +{merge_result['new_quotes']} cotizaciones nuevas."
                    )

                    event_bus.emit("cloud_sync_completed", {
                        "timestamp": self.last_sync_time,
                        "new_transactions": merge_result["new_transactions"],
                        "new_quotes": merge_result["new_quotes"],
                        "details": merge_result
                    })

                    self.is_syncing = False
                    return {
                        "success": True,
                        "message": f"Sincronización exitosa (+{merge_result['new_transactions']} trx, +{merge_result['new_quotes']} cot)",
                        "timestamp": self.last_sync_time,
                        **merge_result
                    }

                elif resp.status_code == 404:
                    app_logger.warning("El servidor Render respondió 404 en /api/sync.")
                    last_error = "Endpoint /api/sync no encontrado en el servidor."
                else:
                    last_error = f"Servidor Render respondió con código HTTP {resp.status_code}."

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                app_logger.info(f"Intento {intento}/{max_intentos} conectando con Render ({type(e).__name__})...")
                last_error = "El servidor de Render está reactivándose. Reintentando..."
                time.sleep(2)
            except Exception as e:
                app_logger.error(f"Error inesperado en sincronización: {e}", exc_info=True)
                last_error = str(e)
                break

        self.is_syncing = False
        return {
            "success": False,
            "message": last_error or "Sin conexión con el servidor Render.",
            "new_transactions": 0,
            "new_quotes": 0
        }

    def sync_from_cloud(self, timeout: int = 15) -> Dict[str, Any]:
        """Alias para sincronización."""
        return self.sync_bidirectional(timeout=timeout)

    def _merge_cloud_data(self, cloud_data: Dict[str, Any]) -> Dict[str, int]:
        """Fusiona los datos remotos con la base local y asegura que TODOS los PDFs existan físicamente."""
        new_trx_count = 0
        new_quote_count = 0
        new_workshop_count = 0

        # 1. Fusionar Libro Mayor (Ledger & Finanzas)
        remote_ledger = cloud_data.get("ledger") or cloud_data.get("finanzas") or []
        if isinstance(remote_ledger, list) and remote_ledger:
            local_ledger_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
            local_ledger = self._read_json_file(local_ledger_path)
            
            existing_ids = {r.get("id") for r in local_ledger if r.get("id")}
            existing_signatures = {
                (r.get("date"), round(float(r.get("amount_usd", 0.0)), 2), r.get("ref_code", ""))
                for r in local_ledger
            }

            added_trx = []
            for r in remote_ledger:
                trx_id = r.get("id")
                sig = (r.get("date"), round(float(r.get("amount_usd", 0.0)), 2), r.get("ref_code", ""))
                
                if trx_id and trx_id in existing_ids:
                    continue
                if sig in existing_signatures:
                    continue

                local_ledger.append(r)
                added_trx.append(r)
                if trx_id:
                    existing_ids.add(trx_id)
                existing_signatures.add(sig)

            if added_trx:
                self._write_json_file(local_ledger_path, local_ledger)
                finances_path = getattr(SystemConfig, "FINANCES_FILE", "data/finances.json")
                if finances_path and finances_path != local_ledger_path:
                    self._write_json_file(finances_path, local_ledger)
                new_trx_count = len(added_trx)

        # 2. Fusionar Cotizaciones y REVISAR TODA LA LISTA para autocompilar PDFs faltantes
        remote_quotes = cloud_data.get("cotizaciones") or cloud_data.get("quotes") or []
        if isinstance(remote_quotes, list) and remote_quotes:
            local_quotes_path = getattr(SystemConfig, "QUOTES_FILE", "data/cotizaciones.json")
            local_quotes = self._read_json_file(local_quotes_path)
            
            existing_quote_map = {r.get("quote_id"): r for r in local_quotes if r.get("quote_id")}
            added_quotes_count = 0

            # Primero unificamos cotizaciones nuevas de la nube al archivo local
            for q in remote_quotes:
                qid = q.get("quote_id") or f"COT-{int(time.time())}"
                q["quote_id"] = qid
                if qid not in existing_quote_map:
                    local_quotes.append(q)
                    existing_quote_map[qid] = q
                    added_quotes_count += 1

            # SEGUNDO: PASADA GENERAL SOBRE TODAS LAS COTIZACIONES LOCALES
            # Esto garantiza que CUALQUIER cotización sin PDF físico en la PC lo genere ahora mismo
            pdf_generated_any = False
            for q in local_quotes:
                qid = q.get("quote_id")
                current_pdf_path = q.get("pdf_path", "")
                
                # Verificamos si el archivo físico existe realmente en el disco duro
                pdf_exists = current_pdf_path and os.path.exists(current_pdf_path)

                if not pdf_exists:
                    try:
                        generated_pdf = PDFQuoteGenerator.generate(
                            quote_id=qid or "COT-REMOTE",
                            client_name=q.get("client_name", "Cliente Particular"),
                            client_rif=q.get("client_rif", "N/A"),
                            client_phone=q.get("client_phone", "N/A"),
                            client_company=q.get("client_company", "Particular"),
                            items=q.get("items", []),
                            tax_percent=float(q.get("tax_percent", 16.0)),
                            bcv_rate=float(q.get("bcv_rate", 849.56)),
                            notes=q.get("notes", "")
                        )
                        q["pdf_path"] = generated_pdf
                        pdf_generated_any = True
                        app_logger.info(f"PDF autocompilado con éxito en revisión general: {generated_pdf}")
                    except Exception as err_pdf:
                        app_logger.error(f"Error autocompilando PDF para cotización {qid}: {err_pdf}")

            # Guardamos cambios si hubo nuevas cotizaciones o PDFs generados
            if added_quotes_count > 0 or pdf_generated_any:
                self._write_json_file(local_quotes_path, local_quotes)
                new_quote_count = added_quotes_count

        # 3. Fusionar Taller / Servicios
        remote_workshop = cloud_data.get("servicios_taller") or cloud_data.get("workshop") or []
        if isinstance(remote_workshop, list) and remote_workshop:
            local_workshop_path = getattr(SystemConfig, "WORKSHOP_FILE", "data/servicios_taller.json")
            local_workshop = self._read_json_file(local_workshop_path)
            
            existing_w_ids = {w.get("id") or w.get("job_id") for w in local_workshop if (w.get("id") or w.get("job_id"))}
            added_w = []
            for w in remote_workshop:
                wid = w.get("id") or w.get("job_id")
                if wid and wid in existing_w_ids:
                    continue
                local_workshop.append(w)
                added_w.append(w)
                if wid:
                    existing_w_ids.add(wid)

            if added_w:
                self._write_json_file(local_workshop_path, local_workshop)
                new_workshop_count = len(added_w)

        # 4. Fusionar Configuración de Saldo Inicial si existe y es más reciente
        remote_settings = cloud_data.get("accounting_settings")
        if isinstance(remote_settings, dict) and "initial_balance_usd" in remote_settings:
            settings_path = os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "accounting_settings.json")
            local_settings = self._read_json_file(settings_path)
            if not local_settings or local_settings.get("initial_balance_usd", 0.0) == 0.0:
                if float(remote_settings.get("initial_balance_usd", 0.0)) > 0:
                    self._write_json_file(settings_path, remote_settings)

        return {
            "new_transactions": new_trx_count,
            "new_quotes": new_quote_count,
            "new_workshop": new_workshop_count
        }

    def _read_json_file(self, file_path: str) -> Any:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                app_logger.warning(f"Error leyendo {file_path}: {e}")
        return []

    def _write_json_file(self, file_path: str, data: Any) -> None:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Error escribiendo {file_path}: {e}")


# Instancia singleton del sincronizador
cloud_sync = CloudSyncManager()