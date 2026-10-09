"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: keep_alive.py
Descripción: Servidor Web Flask para Render con soporte para Health Check
             y Endpoint REST de Sincronización Bidireccional (/api/sync).
=============================================================================
"""

import os
import json
import threading
from flask import Flask, request, jsonify, make_response
from config import SystemConfig
from core.logger import app_logger

# Inicializar aplicación Flask
app = Flask(__name__)


def _read_json_safe(path: str):
    """Lee de forma segura un archivo JSON."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _write_json_safe(path: str, data: any) -> bool:
    """Escribe de forma segura datos en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        app_logger.error(f"Error escribiendo {path}: {e}")
        return False


def _merge_incoming_data(incoming: dict) -> dict:
    """Fusiona los datos entrantes del escritorio con el almacenamiento en Render."""
    summary = {"new_ledger": 0, "new_quotes": 0, "new_workshop": 0}

    # 1. Fusionar Libro Mayor (Ledger & Finanzas)
    if "ledger" in incoming and isinstance(incoming["ledger"], list):
        l_path = getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json")
        server_ledger = _read_json_safe(l_path)
        existing_ids = {r.get("id") for r in server_ledger if r.get("id")}
        existing_sigs = {
            (r.get("date"), round(float(r.get("amount_usd", 0.0)), 2), r.get("ref_code", ""))
            for r in server_ledger
        }

        added = 0
        for item in incoming["ledger"]:
            trx_id = item.get("id")
            sig = (item.get("date"), round(float(item.get("amount_usd", 0.0)), 2), item.get("ref_code", ""))
            
            if trx_id and trx_id in existing_ids:
                continue
            if sig in existing_sigs:
                continue

            server_ledger.append(item)
            if trx_id:
                existing_ids.add(trx_id)
            existing_sigs.add(sig)
            added += 1

        if added > 0:
            _write_json_safe(l_path, server_ledger)
            f_path = getattr(SystemConfig, "FINANCES_FILE", "data/finanzas.json")
            if f_path and f_path != l_path:
                _write_json_safe(f_path, server_ledger)
        summary["new_ledger"] = added

    # 2. Fusionar Cotizaciones
    if "cotizaciones" in incoming and isinstance(incoming["cotizaciones"], list):
        q_path = getattr(SystemConfig, "QUOTES_FILE", "data/cotizaciones.json")
        server_quotes = _read_json_safe(q_path)
        existing_q_ids = {q.get("quote_id") for q in server_quotes if q.get("quote_id")}

        added_q = 0
        for q in incoming["cotizaciones"]:
            qid = q.get("quote_id")
            if qid and qid in existing_q_ids:
                continue
            server_quotes.append(q)
            if qid:
                existing_q_ids.add(qid)
            added_q += 1

        if added_q > 0:
            _write_json_safe(q_path, server_quotes)
        summary["new_quotes"] = added_q

    # 3. Fusionar Taller
    if "servicios_taller" in incoming and isinstance(incoming["servicios_taller"], list):
        w_path = getattr(SystemConfig, "WORKSHOP_FILE", "data/servicios_taller.json")
        server_w = _read_json_safe(w_path)
        existing_w_ids = {w.get("id") or w.get("job_id") for w in server_w if (w.get("id") or w.get("job_id"))}

        added_w = 0
        for w in incoming["servicios_taller"]:
            wid = w.get("id") or w.get("job_id")
            if wid and wid in existing_w_ids:
                continue
            server_w.append(w)
            if wid:
                existing_w_ids.add(wid)
            added_w += 1

        if added_w > 0:
            _write_json_safe(w_path, server_w)
        summary["new_workshop"] = added_w

    # 4. Ajustes Contables
    if "accounting_settings" in incoming and isinstance(incoming["accounting_settings"], dict):
        s_path = os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "accounting_settings.json")
        if float(incoming["accounting_settings"].get("initial_balance_usd", 0.0)) > 0:
            _write_json_safe(s_path, incoming["accounting_settings"])

    return summary


@app.after_request
def after_request(response):
    """Habilita encabezados CORS para todas las respuestas."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    """Endpoint de estado para Render (Health Check)."""
    return "Inversiones Reinaldo Golindano - Servidor Cloud Render Activo y Operativo", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/api/status", methods=["GET"])
def api_status():
    """Estado operativo del backend."""
    return jsonify({
        "status": "running",
        "server": "Render Cloud Web Service",
        "app": SystemConfig.APP_NAME,
        "version": SystemConfig.APP_VERSION
    })


@app.route("/api/sync", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/data", methods=["GET", "POST", "OPTIONS"])
def api_sync():
    """
    Endpoint principal de sincronización bidireccional (Pull y Push):
    - GET: Descarga los registros actuales almacenados en el servidor Render.
    - POST: Recibe registros del escritorio, los fusiona en Render y retorna el estado actualizado.
    - OPTIONS: Atiende solicitudes de preflight CORS.
    """
    if request.method == "OPTIONS":
        return make_response("", 200)

    # 1. Si es POST: procesar los datos enviados desde el escritorio (PUSH)
    merged_summary = {}
    if request.method == "POST":
        incoming_data = request.get_json(silent=True) or {}
        merged_summary = _merge_incoming_data(incoming_data)

    # 2. Cargar estado actualizado del servidor para devolver al cliente (PULL)
    ledger_data = _read_json_safe(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
    quotes_data = _read_json_safe(getattr(SystemConfig, "QUOTES_FILE", "data/cotizaciones.json"))
    workshop_data = _read_json_safe(getattr(SystemConfig, "WORKSHOP_FILE", "data/servicios_taller.json"))
    purchases_data = _read_json_safe(getattr(SystemConfig, "PURCHASES_FILE", "data/compras.json"))

    settings_path = os.path.join(getattr(SystemConfig, "DATA_DIR", "data"), "accounting_settings.json")
    settings_data = _read_json_safe(settings_path)
    if isinstance(settings_data, list):
        settings_data = {"initial_balance_usd": 0.0}

    response_payload = {
        "status": "ok",
        "server": "Render Cloud Web Service",
        "app": SystemConfig.APP_NAME,
        "version": SystemConfig.APP_VERSION,
        "merged": merged_summary,
        "ledger": ledger_data,
        "finanzas": ledger_data,
        "cotizaciones": quotes_data,
        "servicios_taller": workshop_data,
        "compras": purchases_data,
        "accounting_settings": settings_data
    }

    return jsonify(response_payload)


def run_server():
    """Ejecuta el servidor web Flask en el puerto asignado por Render ($PORT)."""
    port = int(os.environ.get("PORT", 10000))
    app_logger.info(f"Levantando servidor Flask de Render en 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def keep_alive():
    """Inicia el servidor Flask en un hilo en segundo plano."""
    t = threading.Thread(target=run_server, daemon=True, name="RenderFlaskSyncServer")
    t.start()


if __name__ == "__main__":
    run_server() 
# Sincronización activa con Render ok