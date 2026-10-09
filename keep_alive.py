"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: keep_alive.py
Descripción: Servidor HTTP para Render con soporte para Health Check
             y Endpoint REST de Sincronización Bidireccional (/api/sync).
=============================================================================
"""

import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from config import SystemConfig


class RenderSyncHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para Render: Health check y API de Sincronización Bidireccional."""

    def _read_json_safe(self, path: str):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _write_json_safe(self, path: str, data: any):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "" or path == "/health":
            # Health check para Render
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"Inversiones Reinaldo Golindano - Bot & Sync Server is alive and running!")

        elif path == "/api/sync" or path == "/api/data":
            # Endpoint de sincronización de registros remotos (PULL)
            ledger_data = self._read_json_safe(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
            quotes_data = self._read_json_safe(getattr(SystemConfig, "QUOTES_FILE", "data/cotizaciones.json"))
            workshop_data = self._read_json_safe(getattr(SystemConfig, "WORKSHOP_FILE", "data/servicios_taller.json"))
            purchases_data = self._read_json_safe(getattr(SystemConfig, "PURCHASES_FILE", "data/compras.json"))

            settings_path = os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "accounting_settings.json")
            settings_data = self._read_json_safe(settings_path)
            if isinstance(settings_data, list):
                settings_data = {"initial_balance_usd": 0.0}

            payload = {
                "status": "ok",
                "server": "Render Cloud Worker",
                "app": SystemConfig.APP_NAME,
                "version": SystemConfig.APP_VERSION,
                "ledger": ledger_data,
                "cotizaciones": quotes_data,
                "servicios_taller": workshop_data,
                "compras": purchases_data,
                "accounting_settings": settings_data
            }
            self._send_json(200, payload)

        elif path == "/api/status":
            payload = {
                "status": "running",
                "server": "Render Cloud",
                "app": SystemConfig.APP_NAME,
                "version": SystemConfig.APP_VERSION
            }
            self._send_json(200, payload)

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/sync" or path == "/api/push":
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode('utf-8'))

                # Fusión en el servidor de Render (PUSH desde el escritorio)
                merged_summary = self._merge_server_data(data)

                self._send_json(200, {
                    "status": "success",
                    "message": "Datos integrados correctamente en el servidor Render.",
                    "merged": merged_summary
                })
            except Exception as e:
                self._send_json(400, {"status": "error", "message": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _merge_server_data(self, incoming_data: dict) -> dict:
        """Fusiona los datos enviados desde el escritorio en los archivos de Render."""
        res = {"new_ledger": 0, "new_quotes": 0, "new_workshop": 0}

        # 1. Ledger
        if "ledger" in incoming_data and isinstance(incoming_data["ledger"], list):
            l_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
            local = self._read_json_safe(l_path)
            existing_ids = {r.get("id") for r in local if r.get("id")}
            added = 0
            for item in incoming_data["ledger"]:
                if item.get("id") and item.get("id") not in existing_ids:
                    local.append(item)
                    existing_ids.add(item.get("id"))
                    added += 1
            if added:
                self._write_json_safe(l_path, local)
                f_path = getattr(SystemConfig, "FINANCES_FILE", "data/finanzas.json")
                if f_path and f_path != l_path:
                    self._write_json_safe(f_path, local)
            res["new_ledger"] = added

        # 2. Quotes
        if "cotizaciones" in incoming_data and isinstance(incoming_data["cotizaciones"], list):
            q_path = getattr(SystemConfig, "QUOTES_FILE", "data/cotizaciones.json")
            local_q = self._read_json_safe(q_path)
            existing_q_ids = {q.get("quote_id") for q in local_q if q.get("quote_id")}
            added_q = 0
            for q in incoming_data["cotizaciones"]:
                if q.get("quote_id") and q.get("quote_id") not in existing_q_ids:
                    local_q.append(q)
                    existing_q_ids.add(q.get("quote_id"))
                    added_q += 1
            if added_q:
                self._write_json_safe(q_path, local_q)
            res["new_quotes"] = added_q

        # 3. Settings
        if "accounting_settings" in incoming_data and isinstance(incoming_data["accounting_settings"], dict):
            s_path = os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "accounting_settings.json")
            if incoming_data["accounting_settings"].get("initial_balance_usd", 0) > 0:
                self._write_json_safe(s_path, incoming_data["accounting_settings"])

        return res

    def log_message(self, format, *args):
        # Silenciar logs continuos en consola
        return


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), RenderSyncHandler)
    print(f"Servidor web y sincronizador de Render activo en el puerto {port}")
    server.serve_forever()


def keep_alive():
    t = threading.Thread(target=run_server, daemon=True, name="RenderSyncWebServer")
    t.start()


if __name__ == "__main__":
    run_server()