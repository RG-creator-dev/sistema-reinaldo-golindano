"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: keep_alive.py
Descripción: Servidor Web Flask para Render con soporte para Health Check
             y Endpoint REST de Sincronización Bidireccional (/api/sync).
             Incluye el hilo autónomo de Dirección General (Auditoría + B2B).
=============================================================================
"""

import os
import json
import threading
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, make_response
from config import SystemConfig
from core.logger import app_logger
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent
from modules.dept_03_compras_procura.web_scraper import GlobalWebScraper
from modules.dept_03_compras_procura.supply_audit_agent import SupplyAuditAgent
from modules.dept_01_direccion_general.orchestrator_agent import OrchestratorAgent

# Inicializar aplicación Flask
app = Flask(__name__)

VENEZUELA_TZ = timezone(timedelta(hours=-4))

# Instancias singleton para el servidor web en la nube
accounting_agent = AccountingAgent()
web_scraper = GlobalWebScraper()
supply_agent = SupplyAuditAgent(web_scraper=web_scraper)


def background_director_scheduler():
    """
    Hilo en segundo plano para ejecutar la rutina autónoma del Director General.
    Configurado temporalmente para dispararse hoy a las 8:50 a.m. (hora de Venezuela).
    """
    app_logger.info("[BackgroundScheduler] Hilo monitor de Dirección General iniciado correctamente.")
    orchestrator = OrchestratorAgent()
    
    test_executed_today = False
    
    while True:
        try:
            now = datetime.now(VENEZUELA_TZ)
            
            # Condición para la prueba: Hora 8, Minuto 50
            if now.hour == 8 and now.minute == 50 and not test_executed_today:
                app_logger.info("[Director General] Ejecutando rutina autónoma matutina (Prueba 8:50 AM): Auditoría + B2B...")
                
                # 1. Fase de Operaciones y Auditoría Diaria (CxC y Libro Mayor)
                res_audit = orchestrator.execute("daily_autonomous_scan", {})
                app_logger.info(f"[Director General] Resultado Auditoría: {res_audit.message}")
                
                # 2. Fase de Marketing B2B (Generación de publicaciones semanales en Google Sheets)
                res_b2b = orchestrator.execute("execute_b2b_campaign", {})
                app_logger.info(f"[Director General] Resultado Campaña B2B: {res_b2b.message}")
                
                test_executed_today = True
                time.sleep(61)  # Evita múltiples ejecuciones en el mismo minuto
            
            if now.minute != 50:
                test_executed_today = False
                
            time.sleep(30)  # Revisa el reloj cada 30 segundos
        except Exception as e:
            app_logger.error(f"[BackgroundScheduler] Error crítico en hilo autónomo: {e}")
            time.sleep(30)


# =============================================================================
# LANZAR EL HILO AUTOMÁTICAMENTE AL ARRANCAR EL SERVIDOR (Render / Gunicorn)
# =============================================================================
try:
    scheduler_thread = threading.Thread(target=background_director_scheduler, daemon=True, name="DirectorGeneralThread")
    scheduler_thread.start()
    app_logger.info("[KeepAlive] Hilo autónomo del Director General lanzado en segundo plano con éxito.")
except Exception as e:
    app_logger.error(f"[KeepAlive] No se pudo iniciar el hilo secundario: {e}")


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
    """Endpoint principal de sincronización bidireccional (Pull y Push)."""
    if request.method == "OPTIONS":
        return make_response("", 200)

    merged_summary = {}
    if request.method == "POST":
        incoming_data = request.get_json(silent=True) or {}
        merged_summary = _merge_incoming_data(incoming_data)

    ledger_data = accounting_agent._load_ledger()
    if not ledger_data:
        ledger_data = _read_json_safe(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
        if not ledger_data:
            ledger_data = _read_json_safe(getattr(SystemConfig, "FINANCES_FILE", "data/finanzas.json"))

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


def _convert_dictamen_markdown_to_html(md_text: str) -> str:
    """Convierte el dictamen markdown a HTML seguro con hipervínculos interactivos."""
    if not md_text:
        return "<p class='text-muted'>Sin información disponible.</p>"

    import re
    escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    escaped = re.sub(r'^### (.*?)$', r'<h3 class="text-primary mt-4 mb-2">\1</h3>', escaped, flags=re.MULTILINE)
    escaped = re.sub(r'^#### (.*?)$', r'<h4 class="text-info mt-3 mb-1">\1</h4>', escaped, flags=re.MULTILINE)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(
        r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener noreferrer" class="link-btn">🔗 \1</a>',
        escaped
    )
    escaped = re.sub(
        r'(?<!href=")(https?://[^\s\)\],<]+)',
        r'<a href="\1" target="_blank" rel="noopener noreferrer" class="link-btn">\1</a>',
        escaped
    )

    lineas = []
    for l in escaped.split("\n"):
        l_strip = l.strip()
        if l_strip.startswith("- ") or l_strip.startswith("• "):
            lineas.append(f"<li class='mb-1'>{l_strip[2:]}</li>")
        elif l_strip == "---":
            lineas.append("<hr class='my-3 border-secondary'>")
        elif l_strip:
            lineas.append(f"<p class='mb-2'>{l_strip}</p>")
        else:
            lineas.append("")

    return "\n".join(lineas)


@app.route("/api/procura", methods=["GET", "POST", "OPTIONS"])
def api_procura():
    """Endpoint REST para el Módulo de Rastreo y Procura Web Multirrubro."""
    if request.method == "OPTIONS":
        return make_response("", 200)

    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form.to_dict() or {}
    else:
        payload = request.args.to_dict()

    producto = payload.get("query") or payload.get("producto") or payload.get("q") or ""
    producto = producto.strip()
    if not producto:
        return jsonify({
            "status": "error",
            "message": "Por favor especifique el término a rastrear mediante el parámetro 'query' o 'q'."
        }), 400

    ambito = payload.get("ambito", "Nacional")
    importar = str(payload.get("incluye_importacion", payload.get("importar", "false"))).lower() in ("true", "1", "yes", "si")

    try:
        hallazgos = web_scraper.buscar_sitios_web(producto, ambito=ambito)
        dictamen = web_scraper.analizar_con_gemini_v2(producto, hallazgos, ambito=ambito, incluye_importacion=importar)

        return jsonify({
            "status": "ok",
            "producto": producto,
            "ambito": ambito,
            "incluye_importacion": importar,
            "total_hallazgos": len(hallazgos),
            "hallazgos": hallazgos,
            "dictamen": dictamen
        })
    except Exception as e:
        app_logger.error(f"Error procesando procura en API: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error interno en el módulo de procura: {str(e)}"
        }), 500


@app.route("/procura", methods=["GET", "POST"])
def view_procura_panel():
    """Panel Web de Rastreo y Procura (Render/Cloud)."""
    producto = ""
    ambito = "Nacional"
    incluye_importacion = False
    dictamen_html = ""
    hallazgos = []
    busqueda_ejecutada = False

    if request.method == "POST":
        producto = request.form.get("query", "").strip()
        ambito = request.form.get("ambito", "Nacional")
        incluye_importacion = "incluye_importacion" in request.form
    elif request.method == "GET" and request.args.get("query"):
        producto = request.args.get("query", "").strip()
        ambito = request.args.get("ambito", "Nacional")
        incluye_importacion = request.args.get("incluye_importacion", "0").lower() in ("1", "true", "si")

    if producto:
        busqueda_ejecutada = True
        try:
            hallazgos = web_scraper.buscar_sitios_web(producto, ambito=ambito)
            dictamen_raw = web_scraper.analizar_con_gemini_v2(
                producto, hallazgos, ambito=ambito, incluye_importacion=incluye_importacion
            )
            dictamen_html = _convert_dictamen_markdown_to_html(dictamen_raw)
        except Exception as e:
            app_logger.error(f"Error generando dictamen web: {e}", exc_info=True)
            dictamen_html = f"<div class='alert alert-warning'>Aviso durante la consulta: {e}</div>"

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inversiones Reinaldo Golindano | Módulo de Procura Web</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #0f172a; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; min-height: 100vh; }}
        .card-custom {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }}
        .text-primary {{ color: #38bdf8 !important; }}
        .text-info {{ color: #67e8f9 !important; }}
        .btn-success-custom {{ background-color: #10b981; border-color: #10b981; font-weight: 600; }}
        .btn-success-custom:hover {{ background-color: #059669; border-color: #059669; }}
        .link-btn {{ color: #38bdf8; text-decoration: underline; font-weight: 600; display: inline-block; margin: 2px 0; }}
        .link-btn:hover {{ color: #7dd3fc; text-decoration: none; }}
        .results-box {{ background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 24px; line-height: 1.6; }}
        .badge-ambito {{ background-color: #334155; color: #94a3b8; font-size: 0.85rem; padding: 4px 10px; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="card card-custom p-4 mb-4">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                    <h2 class="h4 mb-1 text-primary">📦 MÓDULO DE PROCURA Y RASTREO WEB ABIERTO</h2>
                    <p class="text-muted mb-0 small">Inversiones Reinaldo Golindano | Búsqueda Multirrubro con IA (Sin Mercado Libre)</p>
                </div>
                <div class="d-flex gap-2">
                    <a href="/api/sync" class="btn btn-sm btn-outline-secondary">📡 Sincronización REST</a>
                    <a href="/health" class="btn btn-sm btn-outline-info">💚 Estado Servidor</a>
                </div>
            </div>
        </div>
        <div class="card card-custom p-4 mb-4">
            <form method="POST" action="/procura">
                <div class="row g-3 align-items-end">
                    <div class="col-md-5">
                        <label class="form-label small text-muted">Producto / Insumo / Repuesto a Rastrear:</label>
                        <input type="text" name="query" class="form-control form-control-lg bg-dark text-light border-secondary" placeholder="Ej: Toner HP CE285A 85A, Taladro, Fusor..." value="{producto}" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small text-muted">Ámbito Geográfico:</label>
                        <select name="ambito" class="form-select bg-dark text-light border-secondary">
                            <option value="Nacional" {"selected" if ambito == "Nacional" else ""}>🇻🇪 Nacional (Venezuela)</option>
                            <option value="Internacional" {"selected" if ambito == "Internacional" else ""}>🌍 Internacional (Global)</option>
                            <option value="Ambos" {"selected" if ambito == "Ambos" else ""}>🌐 Ambos (Nac. e Intl.)</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="incluye_importacion" id="chkZoom" {"checked" if incluye_importacion else ""}>
                            <label class="form-check-label small" for="chkZoom">Zoom Casilleros</label>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-success-custom w-100 py-2">🔍 Rastrear con IA</button>
                    </div>
                </div>
            </form>
        </div>
        {"<div class='card card-custom p-4 mb-4'>" if busqueda_ejecutada else ""}
        {"<div class='d-flex justify-content-between align-items-center mb-3'>" if busqueda_ejecutada else ""}
        {"<h3 class='h5 text-primary mb-0'>📋 Dictamen Estratégico de Compra y Opciones Disponibles</h3>" if busqueda_ejecutada else ""}
        {f"<span class='badge-ambito'>Ámbito: {ambito} | Exclusión: Mercado Libre</span>" if busqueda_ejecutada else ""}
        {"</div>" if busqueda_ejecutada else ""}
        {f"<div class='results-box'>{dictamen_html}</div>" if busqueda_ejecutada else ""}
        {"</div>" if busqueda_ejecutada else ""}
    </div>
</body>
</html>
"""
    return html_template, 200, {"Content-Type": "text/html; charset=utf-8"}


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