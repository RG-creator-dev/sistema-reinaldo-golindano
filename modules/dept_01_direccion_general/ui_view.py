"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: DIRECCIÓN GENERAL
Módulo: ui_view.py
Descripción: Panel ejecutivo de Dirección General con KPIs en tiempo real,
             monitoreo de agentes IA y generación de informes de gestión.
=============================================================================
"""

import threading
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_01_direccion_general.orchestrator_agent import OrchestratorAgent
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider


class DireccionGeneralView(ctk.CTkFrame):
    """Panel ejecutivo central del Director General."""

    def __init__(self, master, agent: OrchestratorAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or OrchestratorAgent()

        self._init_ui()
        self.actualizar_kpis()

    def _init_ui(self):
        # 1. Cabecera Ejecutiva
        header = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="👑 DIRECCIÓN GENERAL", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Centro de Comando, Supervisión Estratégica y Síntesis Ejecutiva con IA", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

        self.btn_generar_informe = ctk.CTkButton(
            header,
            text="📈 Consolidar Informe Ejecutivo (IA)",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            command=self._iniciar_informe_thread
        )
        self.btn_generar_informe.pack(side="right", padx=15, pady=10)

        # 2. Métricas Clave (KPIs)
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=15, pady=5)
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # KPI 1: Cotizaciones
        card1 = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        card1.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(card1, text="COTIZACIONES EMITIDAS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_quotes = ctk.CTkLabel(card1, text="0", font=Theme.FONT_TITLE, text_color=Theme.PRIMARY)
        self.lbl_kpi_quotes.pack(pady=(0, 8))

        # KPI 2: Stock Crítico
        card2 = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        card2.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(card2, text="SUMINISTROS CRÍTICOS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_stock = ctk.CTkLabel(card2, text="0 ítems", font=Theme.FONT_TITLE, text_color=Theme.WARNING)
        self.lbl_kpi_stock.pack(pady=(0, 8))

        # KPI 3: Balance Neto en Caja
        card3 = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        card3.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(card3, text="BALANCE EN CAJA (USD)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_finanzas = ctk.CTkLabel(card3, text="$0.00", font=Theme.FONT_TITLE, text_color=Theme.SUCCESS)
        self.lbl_kpi_finanzas.pack(pady=(0, 8))

        # KPI 4: Órdenes de Taller
        card4 = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        card4.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(card4, text="EQUIPOS EN TALLER", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_taller = ctk.CTkLabel(card4, text="0 equipos", font=Theme.FONT_TITLE, text_color=Theme.CYAN)
        self.lbl_kpi_taller.pack(pady=(0, 8))

        # 3. Estado Operativo de los 5 Agentes Departamentales
        agents_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        agents_frame.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(agents_frame, text="Estado de Agentes IA Conectados:", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left", padx=15, pady=8)

        for d_name in ["Dirección General", "Comercio y Ventas", "Compras y Procura", "Adm. y Finanzas", "Servicio Técnico"]:
            badge = ctk.CTkLabel(
                agents_frame,
                text=f"🟢 {d_name}",
                font=Theme.FONT_SMALL,
                fg_color=Theme.INPUT_BG,
                corner_radius=6,
                padx=8,
                pady=4
            )
            badge.pack(side="left", padx=5, pady=8)

        # 4. Visor del Informe Ejecutivo
        report_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        report_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        ctk.CTkLabel(report_frame, text="Informe Ejecutivo de Gestión Estratégica (Consolidado IA)", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        self.txt_informe = ctk.CTkTextbox(report_frame, font=Theme.FONT_BODY, fg_color=Theme.INPUT_BG)
        self.txt_informe.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.txt_informe.insert("1.0", "Presiona 'Consolidar Informe Ejecutivo (IA)' para generar un reporte integral en tiempo real con datos sincronizados de los 5 departamentos.")

    def actualizar_kpis(self):
        """Consulta los datos reales de los módulos y actualiza los indicadores numéricos."""
        import os, json
        from config import SystemConfig

        # Cotizaciones
        q_count = 0
        if os.path.exists(SystemConfig.QUOTES_FILE):
            try:
                with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                    q_count = len(json.load(f))
            except Exception:
                pass
        self.lbl_kpi_quotes.configure(text=str(q_count))

        # Taller
        w_count = 0
        if os.path.exists(SystemConfig.WORKSHOP_FILE):
            try:
                with open(SystemConfig.WORKSHOP_FILE, "r", encoding="utf-8") as f:
                    w_count = len(json.load(f))
            except Exception:
                pass
        self.lbl_kpi_taller.configure(text=f"{w_count} equipos")

        # Finanzas (Incluyendo Saldo Inicial + Ingresos - Gastos)
        initial_balance = 0.0
        base_dir = os.path.dirname(getattr(SystemConfig, "LEDGER_FILE", "data/ledger.json"))
        settings_path = os.path.join(base_dir, "accounting_settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    initial_balance = float(settings.get("initial_balance_usd", 0.0))
            except Exception:
                pass

        net_bal = initial_balance
        if os.path.exists(SystemConfig.LEDGER_FILE):
            try:
                with open(SystemConfig.LEDGER_FILE, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
                    for r in ledger:
                        amt = float(r.get("amount_usd", 0.0))
                        if r.get("type") == "Ingreso":
                            net_bal += amt
                        else:
                            net_bal -= amt
            except Exception:
                pass
        self.lbl_kpi_finanzas.configure(text=f"${net_bal:,.2f}")

    def _iniciar_informe_thread(self):
        self.btn_generar_informe.configure(state="disabled")
        self.txt_informe.delete("1.0", "end")
        self.txt_informe.insert("1.0", "⏳ Sincronizando métricas departamentales y redactando informe ejecutivo con Gemini IA...\n")

        def _task():
            res = self.agent.execute("consolidate_executive_report", {})
            self.after(0, self._render_informe, res)

        threading.Thread(target=_task, daemon=True).start()

    def _render_informe(self, res):
        self.btn_generar_informe.configure(state="normal")
        self.txt_informe.delete("1.0", "end")
        if res.success:
            self.txt_informe.insert("1.0", res.data.get("report_text", ""))
        else:
            self.txt_informe.insert("1.0", f"Error generando informe: {res.message}")
        self.actualizar_kpis()
