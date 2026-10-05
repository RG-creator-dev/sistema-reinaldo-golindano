"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: ui_view.py
Descripción: Interfaz gráfica CustomTkinter integrada con Cotizador Formal ReportLab,
             Control de Bot de Telegram, Monitoreo de Mercado Libre y Marketing B2B.
=============================================================================
"""

import os
import re
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from config import SystemConfig
from ui.theme import Theme
from modules.dept_02_comercio_ventas.quote_catalog_agent import QuoteCatalogAgent
from modules.dept_02_comercio_ventas.telegram_voice_bot import telegram_controller
from modules.dept_02_comercio_ventas.ml_scraper import MercadoLibreTracker
from modules.dept_02_comercio_ventas.b2b_marketing_agent import B2BMarketingAgent
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider


class ComercioVentasView(ctk.CTkFrame):
    """Panel unificado del Departamento de Comercio y Ventas."""

    def __init__(self, master, agent: QuoteCatalogAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or QuoteCatalogAgent()
        self.ml_tracker = MercadoLibreTracker()
        self.marketing_agent = B2BMarketingAgent()

        self.ml_resultados_cache = []

        self._init_ui()
        self._cargar_historial_cotizaciones()

    def _init_ui(self):
        # 1. Cabecera Departamental
        header = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="💼 COMERCIO Y VENTAS", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Cotizaciones de Alta Precisión, Bot de Telegram, Monitoreo Nacional y Publicidad B2B", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # 2. Pestañas de Trabajo
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_DARK, segmented_button_selected_color=Theme.PRIMARY)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_cotizador = self.tabview.add("📄 Cotizador & Presupuestos")
        self.tab_telegram = self.tabview.add("🤖 Bot de Telegram")
        self.tab_ml = self.tabview.add("🛒 Mercado Libre (Nacional)")
        self.tab_marketing = self.tabview.add("📢 Marketing B2B")

        self._build_tab_cotizador()
        self._build_tab_telegram()
        self._build_tab_mercadolibre()
        self._build_tab_marketing()

    # -------------------------------------------------------------------------
    # PESTAÑA 1: COTIZADOR FORMAL (PDF)
    # -------------------------------------------------------------------------
    def _build_tab_cotizador(self):
        tab = self.tab_cotizador
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Generador de Cotizaciones
        left_frame = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        left_frame.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(left_frame, text="Emisión de Presupuesto Formal (ReportLab)", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        # Entrada asistida por IA (Voz/Texto)
        ctk.CTkLabel(left_frame, text="Dictado u Orden Rápida (Procesada con IA):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.txt_orden_ia = ctk.CTkTextbox(left_frame, height=75, font=Theme.FONT_BODY, fg_color=Theme.INPUT_BG)
        self.txt_orden_ia.pack(fill="x", padx=15, pady=4)
        self.txt_orden_ia.insert("1.0", "Cliente Repuestos Valencia solicita 2 tóner HP 85A a $18 y servicio de cambio de almohadillas Epson L3110 a $15.")

        # Datos del Cliente
        grid_client = ctk.CTkFrame(left_frame, fg_color="transparent")
        grid_client.pack(fill="x", padx=15, pady=5)
        grid_client.grid_columnconfigure((0, 1), weight=1)

        self.entry_cli_name = ctk.CTkEntry(grid_client, placeholder_text="Nombre del Cliente")
        self.entry_cli_name.grid(row=0, column=0, padx=(0, 4), pady=3, sticky="ew")
        self.entry_cli_rif = ctk.CTkEntry(grid_client, placeholder_text="RIF / C.I.")
        self.entry_cli_rif.grid(row=0, column=1, padx=(4, 0), pady=3, sticky="ew")

        self.entry_cli_phone = ctk.CTkEntry(grid_client, placeholder_text="Teléfono")
        self.entry_cli_phone.grid(row=1, column=0, padx=(0, 4), pady=3, sticky="ew")
        self.entry_cli_company = ctk.CTkEntry(grid_client, placeholder_text="Empresa / Particular")
        self.entry_cli_company.grid(row=1, column=1, padx=(4, 0), pady=3, sticky="ew")

        # Configuración de IVA y Condiciones
        opts_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        opts_frame.pack(fill="x", padx=15, pady=6)

        self.var_incluir_iva = ctk.BooleanVar(value=True)  # Por defecto CON IVA (16%)
        self.chk_iva = ctk.CTkCheckBox(
            opts_frame,
            text="Incluir IVA del 16% (Por Defecto)",
            variable=self.var_incluir_iva,
            font=Theme.FONT_BODY_BOLD,
            checkbox_height=20,
            checkbox_width=20
        )
        self.chk_iva.pack(side="left")

        # Botón de Generar PDF
        btn_generar_pdf = ctk.CTkButton(
            left_frame,
            text="🚀 Generar Presupuesto Formal (PDF)",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            height=36,
            command=self._generar_cotizacion_ui
        )
        btn_generar_pdf.pack(fill="x", padx=15, pady=(10, 10))

        # Panel Derecho: Historial de Cotizaciones Emitidas
        right_frame = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        right_frame.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        top_hist = ctk.CTkFrame(right_frame, fg_color="transparent")
        top_hist.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(top_hist, text="Historial de Cotizaciones Emitidas", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(side="left")

        btn_abrir_pdf = ctk.CTkButton(
            top_hist,
            text="📂 Abrir PDF Seleccionado",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            width=160,
            height=28,
            command=self._abrir_pdf_seleccionado
        )
        btn_abrir_pdf.pack(side="right")

        # Tabla de Historial
        tree_scroll = ttk.Scrollbar(right_frame, orient="vertical")
        cols = ("id", "fecha", "cliente", "total_usd", "total_bs")
        self.tree_cotizaciones = ttk.Treeview(right_frame, columns=cols, show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.tree_cotizaciones.yview)

        self.tree_cotizaciones.heading("id", text="N° Cotización")
        self.tree_cotizaciones.heading("fecha", text="Fecha")
        self.tree_cotizaciones.heading("cliente", text="Cliente")
        self.tree_cotizaciones.heading("total_usd", text="Total USD")
        self.tree_cotizaciones.heading("total_bs", text="Total Bs (BCV)")

        self.tree_cotizaciones.column("id", width=95, anchor="center")
        self.tree_cotizaciones.column("fecha", width=120, anchor="center")
        self.tree_cotizaciones.column("cliente", width=150)
        self.tree_cotizaciones.column("total_usd", width=85, anchor="e")
        self.tree_cotizaciones.column("total_bs", width=110, anchor="e")

        self.tree_cotizaciones.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        tree_scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    def _generar_cotizacion_ui(self):
        orden_txt = self.txt_orden_ia.get("1.0", "end").strip()
        if not orden_txt:
            messagebox.showwarning("Atención", "Por favor ingresa un texto u orden para cotizar.")
            return

        sin_iva = not self.var_incluir_iva.get()
        cli_name = self.entry_cli_name.get().strip() or None
        cli_rif = self.entry_cli_rif.get().strip() or "N/A"
        cli_phone = self.entry_cli_phone.get().strip() or "N/A"
        cli_comp = self.entry_cli_company.get().strip() or "Particular"

        payload = {
            "message_text": orden_txt,
            "client_name": cli_name,
            "client_rif": cli_rif,
            "client_phone": cli_phone,
            "client_company": cli_comp,
            "sin_iva": sin_iva
        }

        resp = self.agent.execute("process_and_generate_quote", payload)
        if resp.success:
            self._cargar_historial_cotizaciones()
            pdf_path = resp.data.get("pdf_path")
            qid = resp.data.get("quote_id")
            total_usd = resp.data.get("total_usd")
            total_bs = resp.data.get("total_bs")

            if messagebox.askyesno("Cotización Generada", f"¡Presupuesto {qid} generado con éxito!\nTotal: ${total_usd:,.2f} ({total_bs:,.2f} Bs)\n\n¿Deseas abrir el archivo PDF ahora?"):
                if pdf_path and os.path.exists(pdf_path):
                    os.startfile(pdf_path)
        else:
            messagebox.showerror("Error", resp.message)

    def _cargar_historial_cotizaciones(self):
        for it in self.tree_cotizaciones.get_children():
            self.tree_cotizaciones.delete(it)

        if os.path.exists(SystemConfig.QUOTES_FILE):
            import json
            try:
                with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                    recs = json.load(f)
                for r in reversed(recs):
                    self.tree_cotizaciones.insert("", "end", values=(
                        r.get("quote_id", ""),
                        r.get("date", ""),
                        r.get("client_name", ""),
                        f"${r.get('total_usd', 0.0):,.2f}",
                        f"{r.get('total_bs', 0.0):,.2f} Bs"
                    ), tags=(r.get("pdf_path", ""),))
            except Exception:
                pass

    def _abrir_pdf_seleccionado(self):
        sel = self.tree_cotizaciones.selection()
        if not sel:
            messagebox.showinfo("Información", "Selecciona una cotización de la tabla para abrir el PDF.")
            return

        tags = self.tree_cotizaciones.item(sel[0], "tags")
        if tags and len(tags) > 0 and os.path.exists(tags[0]):
            os.startfile(tags[0])
        else:
            messagebox.showwarning("Aviso", "El archivo PDF no se encuentra disponible en disco.")

    # -------------------------------------------------------------------------
    # PESTAÑA 2: BOT DE TELEGRAM
    # -------------------------------------------------------------------------
    def _build_tab_telegram(self):
        tab = self.tab_telegram

        ctrl_frame = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(ctrl_frame, text="Control del Bot de Telegram (@InversionesRG_bot)", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        bot_status_bar = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        bot_status_bar.pack(fill="x", padx=15, pady=5)

        is_active = telegram_controller.is_active
        status_text = "🟢 Estado: ACTIVO (Escuchando en vivo)" if is_active else "🔴 Estado: DETENIDO"
        status_color = Theme.SUCCESS if is_active else Theme.DANGER
        btn_text = "⏹️ Detener Bot" if is_active else "▶️ Iniciar Bot de Telegram"
        btn_color = Theme.DANGER if is_active else Theme.SUCCESS
        btn_hover = "#dc2626" if is_active else Theme.SUCCESS_HOVER

        self.lbl_bot_status = ctk.CTkLabel(
            bot_status_bar,
            text=status_text,
            font=Theme.FONT_BODY_BOLD,
            text_color=status_color
        )
        self.lbl_bot_status.pack(side="left", padx=5)

        self.btn_toggle_bot = ctk.CTkButton(
            bot_status_bar,
            text=btn_text,
            font=Theme.FONT_BODY_BOLD,
            fg_color=btn_color,
            hover_color=btn_hover,
            width=180,
            command=self._toggle_telegram_bot
        )
        self.btn_toggle_bot.pack(side="right", padx=5)

        # Instrucciones de uso para el usuario
        info_box = ctk.CTkFrame(tab, fg_color=Theme.INPUT_BG, corner_radius=8)
        info_box.pack(fill="x", padx=10, pady=5)
        instrucciones = (
            "💡 FLUJO AUTOMATIZADO VÍA TELEGRAM:\n"
            "1. Al iniciar el bot, éste escucha notas de voz y mensajes en @InversionesRG_bot.\n"
            "2. Las notas de voz se transcriben de forma nativa con Gemini AI.\n"
            "3. Se extraen ítems, precios y condición de IVA (16% por defecto / sin IVA).\n"
            "4. Se emite el PDF formal y el bot lo envía de vuelta directamente al chat del cliente."
        )
        ctk.CTkLabel(info_box, text=instrucciones, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, justify="left").pack(anchor="w", padx=15, pady=8)

        # Log de actividad en vivo
        log_frame = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(log_frame, text="Registro de Actividad en Vivo (Telegram)", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        self.txt_telegram_log = ctk.CTkTextbox(log_frame, font=Theme.FONT_CODE, fg_color=Theme.INPUT_BG)
        self.txt_telegram_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _toggle_telegram_bot(self):
        if not telegram_controller.is_active:
            telegram_controller.start()
            self.lbl_bot_status.configure(text="🟢 Estado: ACTIVO (Escuchando en vivo)", text_color=Theme.SUCCESS)
            self.btn_toggle_bot.configure(text="⏹️ Detener Bot", fg_color=Theme.DANGER, hover_color="#dc2626")
            self._log_tg("Bot de Telegram iniciado correctamente.")
        else:
            telegram_controller.stop()
            self.lbl_bot_status.configure(text="🔴 Estado: DETENIDO", text_color=Theme.DANGER)
            self.btn_toggle_bot.configure(text="▶️ Iniciar Bot de Telegram", fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER)
            self._log_tg("Bot de Telegram detenido.")

    def _log_tg(self, msg: str):
        self.txt_telegram_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.txt_telegram_log.see("end")

    # -------------------------------------------------------------------------
    # PESTAÑA 3: MERCADO LIBRE (MONITOREO NACIONAL)
    # -------------------------------------------------------------------------
    def _build_tab_mercadolibre(self):
        tab = self.tab_ml

        search_bar = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        search_bar.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(search_bar, text="Producto a Rastrear en Venezuela:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="left", padx=(15, 5), pady=10)
        self.entry_ml_query = ctk.CTkEntry(search_bar, width=280, font=Theme.FONT_BODY)
        self.entry_ml_query.pack(side="left", padx=5, pady=10)
        self.entry_ml_query.insert(0, "Toner HP 85A CE285A")

        self.btn_ml_buscar = ctk.CTkButton(
            search_bar,
            text="🔍 Iniciar Rastreo",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            width=130,
            command=self._iniciar_rastreo_ml_thread
        )
        self.btn_ml_buscar.pack(side="left", padx=5, pady=10)

        self.btn_ml_analizar = ctk.CTkButton(
            search_bar,
            text="🤖 Analizar Oportunidades (IA)",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            state="disabled",
            width=180,
            command=self._iniciar_analisis_ml_ia_thread
        )
        self.btn_ml_analizar.pack(side="left", padx=5, pady=10)

        self.btn_ml_export = ctk.CTkButton(
            search_bar,
            text="📥 Exportar CSV",
            font=Theme.FONT_SMALL,
            fg_color="#0284c7",
            hover_color="#0369a1",
            state="disabled",
            width=110,
            command=self._exportar_ml_csv
        )
        self.btn_ml_export.pack(side="left", padx=5, pady=10)

        # Barra de Estado del Rastreo Mercado Libre
        self.lbl_ml_status = ctk.CTkLabel(
            tab,
            text="Estado: Listo para rastrear en Mercado Libre Venezuela.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_ml_status.pack(anchor="w", padx=15, pady=(2, 0))

        # Indicadores de Precios
        metrics_frame = ctk.CTkFrame(tab, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=10, pady=5)
        metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_ml_min = ctk.CTkLabel(metrics_frame, text="Precio Mínimo: $--", font=Theme.FONT_BODY_BOLD, fg_color="#0284c7", corner_radius=6, height=30)
        self.lbl_ml_min.grid(row=0, column=0, padx=4, sticky="ew")
        self.lbl_ml_avg = ctk.CTkLabel(metrics_frame, text="Precio Promedio: $--", font=Theme.FONT_BODY_BOLD, fg_color="#b45309", corner_radius=6, height=30)
        self.lbl_ml_avg.grid(row=0, column=1, padx=4, sticky="ew")
        self.lbl_ml_max = ctk.CTkLabel(metrics_frame, text="Precio Máximo: $--", font=Theme.FONT_BODY_BOLD, fg_color="#be185d", corner_radius=6, height=30)
        self.lbl_ml_max.grid(row=0, column=2, padx=4, sticky="ew")

        # Contenedor Inferior: Tabla ML + Dictamen IA
        bottom_box = ctk.CTkFrame(tab, fg_color="transparent")
        bottom_box.pack(fill="both", expand=True, padx=10, pady=5)
        bottom_box.grid_columnconfigure(0, weight=3)
        bottom_box.grid_columnconfigure(1, weight=2)
        bottom_box.grid_rowconfigure(0, weight=1)

        # Tabla de publicaciones
        table_wrap = ctk.CTkFrame(bottom_box, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        table_wrap.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        ml_scroll = ttk.Scrollbar(table_wrap, orient="vertical")
        cols = ("prod", "precio", "ubicacion", "link")
        self.tree_ml = ttk.Treeview(table_wrap, columns=cols, show="headings", yscrollcommand=ml_scroll.set)
        ml_scroll.config(command=self.tree_ml.yview)

        self.tree_ml.heading("prod", text="Publicación (Mercado Libre)")
        self.tree_ml.heading("precio", text="Precio")
        self.tree_ml.heading("ubicacion", text="Ubicación")
        self.tree_ml.heading("link", text="Enlace URL")

        self.tree_ml.column("prod", width=250)
        self.tree_ml.column("precio", width=70, anchor="center")
        self.tree_ml.column("ubicacion", width=90, anchor="center")
        self.tree_ml.column("link", width=180)

        self.tree_ml.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        ml_scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.tree_ml.bind("<Double-1>", lambda e: self._abrir_enlace_ml())

        # Dictamen IA
        ai_wrap = ctk.CTkFrame(bottom_box, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        ai_wrap.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        ctk.CTkLabel(ai_wrap, text="Dictamen de Oportunidades (IA)", font=Theme.FONT_SUBTITLE, text_color=Theme.PURPLE).pack(anchor="w", padx=10, pady=(8, 4))

        # Contenedor dedicado con Scrollbar para garantizar visibilidad y navegación
        ai_text_container = tk.Frame(ai_wrap, bg=Theme.INPUT_BG)
        ai_text_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ai_scroll = ttk.Scrollbar(ai_text_container, orient="vertical")
        self.txt_ml_ai = tk.Text(
            ai_text_container,
            wrap="word",
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#ffffff",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            inactiveselectbackground="#1e293b",
            font=("Segoe UI", 10),
            yscrollcommand=ai_scroll.set,
            relief="flat",
            padx=10,
            pady=10
        )
        ai_scroll.config(command=self.txt_ml_ai.yview)

        self.txt_ml_ai.pack(side="left", fill="both", expand=True)
        ai_scroll.pack(side="right", fill="y")

        # Configuración explícita de estilos y colores sobre fondo oscuro
        self.txt_ml_ai.tag_config("normal", foreground="#f8fafc", font=("Segoe UI", 10))
        self.txt_ml_ai.tag_config("heading", foreground="#c084fc", font=("Segoe UI", 11, "bold"))
        self.txt_ml_ai.tag_config("bold", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        self.txt_ml_ai.tag_config("highlight_ahorro", foreground="#4ade80", font=("Segoe UI", 10, "bold"))
        self.txt_ml_ai.tag_config("highlight_marca", foreground="#60a5fa", font=("Segoe UI", 10, "bold"))
        self.txt_ml_ai.tag_config("highlight_conv", foreground="#facc15", font=("Segoe UI", 10, "bold"))
        self.txt_ml_ai.tag_config("price", foreground="#34d399", font=("Segoe UI", 10, "bold"))
        self.txt_ml_ai.tag_config("link", foreground="#38bdf8", underline=True, font=("Segoe UI", 10, "bold"))

        self.txt_ml_ai.insert("1.0", "Inicia un rastreo para cargar las ofertas de Mercado Libre y generar el análisis de compras.", "normal")
        self.txt_ml_ai.config(state="disabled")

    def _iniciar_rastreo_ml_thread(self):
        query = self.entry_ml_query.get().strip()
        if not query:
            messagebox.showwarning("Atención", "Por favor ingresa un producto para rastrear en Mercado Libre.")
            return

        self.btn_ml_buscar.configure(state="disabled", text="⏳ Rastreando...")
        self.btn_ml_analizar.configure(state="disabled")
        self.btn_ml_export.configure(state="disabled")
        self.lbl_ml_status.configure(
            text=f"Rastreando Mercado Libre Venezuela para '{query}' (Top 60 menor precio)...",
            text_color=Theme.PRIMARY
        )

        def _task():
            try:
                self.ml_resultados_cache = self.ml_tracker.buscar_mercado_libre(query)
                metrics = self.ml_tracker.calcular_metricas(self.ml_resultados_cache)
                self.after(0, self._render_ml_results, metrics)
            except Exception as e:
                app_logger.error(f"Error en rastreo ML: {e}")
                self.after(0, self._render_ml_error, str(e))

        threading.Thread(target=_task, daemon=True).start()

    def _render_ml_error(self, err_msg: str):
        self.btn_ml_buscar.configure(state="normal", text="🔍 Iniciar Rastreo")
        self.lbl_ml_status.configure(text=f"Error durante el rastreo: {err_msg}", text_color=Theme.DANGER)

    def _render_ml_results(self, metrics):
        self.btn_ml_buscar.configure(state="normal", text="🔍 Iniciar Rastreo")

        for it in self.tree_ml.get_children():
            self.tree_ml.delete(it)

        for row in self.ml_resultados_cache:
            self.tree_ml.insert("", "end", values=row)

        cant = len(self.ml_resultados_cache)
        if metrics["count"] > 0:
            self.lbl_ml_min.configure(text=f"Precio Mínimo: ${metrics['min']:,.2f}")
            self.lbl_ml_avg.configure(text=f"Precio Promedio: ${metrics['avg']:,.2f}")
            self.lbl_ml_max.configure(text=f"Precio Máximo: ${metrics['max']:,.2f}")
            self.btn_ml_analizar.configure(state="normal")
            self.btn_ml_export.configure(state="normal")
            self.lbl_ml_status.configure(
                text=f"Rastreo finalizado: {cant} publicaciones cargadas con éxito.",
                text_color=Theme.SUCCESS
            )
        else:
            self.lbl_ml_min.configure(text="Precio Mínimo: $--")
            self.lbl_ml_avg.configure(text="Precio Promedio: $--")
            self.lbl_ml_max.configure(text="Precio Máximo: $--")
            if cant > 0:
                self.btn_ml_analizar.configure(state="normal")
                self.btn_ml_export.configure(state="normal")
                self.lbl_ml_status.configure(
                    text=f"Rastreo finalizado: {cant} publicaciones cargadas (precios a convenir / variables).",
                    text_color=Theme.SUCCESS
                )
            else:
                self.lbl_ml_status.configure(
                    text="No se encontraron publicaciones en Mercado Libre para este criterio.",
                    text_color=Theme.WARNING
                )

    def _iniciar_analisis_ml_ia_thread(self):
        query = self.entry_ml_query.get().strip()
        if not self.ml_resultados_cache:
            messagebox.showinfo("Información", "Primero debes ejecutar un rastreo con resultados.")
            return

        self.btn_ml_analizar.configure(state="disabled", text="⏳ Evaluando...")
        self.lbl_ml_status.configure(text="Gemini IA evaluando publicaciones y dictaminando oportunidades...", text_color=Theme.PRIMARY)
        self.txt_ml_ai.config(state="normal")
        self.txt_ml_ai.delete("1.0", "end")
        self.txt_ml_ai.insert("1.0", "Analizando las mejores opciones capturadas con IA...\nEspere unos instantes.\n", "normal")
        self.txt_ml_ai.config(state="disabled")

        def _task():
            try:
                dictamen = self.ml_tracker.analizar_con_ia(query, self.ml_resultados_cache)
                self.after(0, self._render_ml_ai, dictamen)
            except Exception as e:
                self.after(0, self._render_ml_ai, f"Error generando análisis de IA: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def _render_ml_ai(self, dictamen: str):
        self.btn_ml_analizar.configure(state="normal", text="🤖 Analizar Oportunidades (IA)")
        self.lbl_ml_status.configure(text="Dictamen de oportunidades completado con éxito.", text_color=Theme.SUCCESS)

        self.txt_ml_ai.config(state="normal")
        self.txt_ml_ai.delete("1.0", "end")

        # Patrones para enlaces Markdown [Texto](URL) y URLs directas https://...
        md_link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)')
        raw_url_pattern = re.compile(r'(?<!\()(https?://[^\s\)\],]+)')
        bold_pattern = re.compile(r'\*\*([^\*]+)\*\*')

        tag_counter = 0

        for linea in dictamen.split("\n"):
            linea_strip = linea.strip()

            # Encabezados de sección (### o Títulos ejecutivos)
            if linea_strip.startswith("###") or linea_strip.startswith("##") or linea_strip.startswith("####"):
                clean_h = re.sub(r'^#+\s*', '', linea_strip)
                if "Ahorro Máximo" in clean_h:
                    self.txt_ml_ai.insert("end", f"🎯 {clean_h}\n", "highlight_ahorro")
                elif "Calidad de Marca" in clean_h:
                    self.txt_ml_ai.insert("end", f"⭐ {clean_h}\n", "highlight_marca")
                elif "Mayor Conveniencia" in clean_h:
                    self.txt_ml_ai.insert("end", f"⚡ {clean_h}\n", "highlight_conv")
                elif "Dictamen" in clean_h:
                    self.txt_ml_ai.insert("end", f"📋 {clean_h}\n", "heading")
                else:
                    self.txt_ml_ai.insert("end", f"{clean_h}\n", "heading")
                continue

            # Buscar enlaces en la línea
            enlaces_encontrados = []
            for m in md_link_pattern.finditer(linea):
                enlaces_encontrados.append((m.start(), m.end(), m.group(1), m.group(2), "md"))
            for m in raw_url_pattern.finditer(linea):
                if not any(st <= m.start() < en for st, en, _, _, _ in enlaces_encontrados):
                    enlaces_encontrados.append((m.start(), m.end(), "Ver Publicación en Mercado Libre", m.group(1), "raw"))

            enlaces_encontrados.sort(key=lambda x: x[0])

            if not enlaces_encontrados:
                # Línea sin enlaces: procesar negritas con alto contraste
                if "**" in linea:
                    sub_pos = 0
                    for bm in bold_pattern.finditer(linea):
                        if bm.start() > sub_pos:
                            self.txt_ml_ai.insert("end", linea[sub_pos:bm.start()], "normal")
                        txt_bold = bm.group(1)
                        if "Ahorro Máximo" in txt_bold:
                            self.txt_ml_ai.insert("end", txt_bold, "highlight_ahorro")
                        elif "Calidad de Marca" in txt_bold:
                            self.txt_ml_ai.insert("end", txt_bold, "highlight_marca")
                        elif "Mayor Conveniencia" in txt_bold:
                            self.txt_ml_ai.insert("end", txt_bold, "highlight_conv")
                        else:
                            self.txt_ml_ai.insert("end", txt_bold, "bold")
                        sub_pos = bm.end()
                    if sub_pos < len(linea):
                        self.txt_ml_ai.insert("end", linea[sub_pos:], "normal")
                    self.txt_ml_ai.insert("end", "\n", "normal")
                else:
                    self.txt_ml_ai.insert("end", linea + "\n", "normal")
            else:
                # Línea con enlaces: procesar texto y crear hipervínculo interactivo
                sub_pos = 0
                for start, end, label, url, ltype in enlaces_encontrados:
                    if start > sub_pos:
                        chunk = linea[sub_pos:start]
                        # Limpiar marcadores de Markdown residuales
                        chunk_clean = chunk.replace("**Enlace:**", "Enlace:").replace("**", "")
                        self.txt_ml_ai.insert("end", chunk_clean, "normal")

                    tag_name = f"link_tag_{tag_counter}"
                    tag_counter += 1

                    self.txt_ml_ai.insert("end", f"🔗 {label}", ("link", tag_name))
                    self.txt_ml_ai.tag_bind(tag_name, "<Enter>", lambda e: self.txt_ml_ai.config(cursor="hand2"))
                    self.txt_ml_ai.tag_bind(tag_name, "<Leave>", lambda e: self.txt_ml_ai.config(cursor=""))
                    self.txt_ml_ai.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))

                    sub_pos = end

                if sub_pos < len(linea):
                    chunk_tail = linea[sub_pos:].replace("**", "")
                    self.txt_ml_ai.insert("end", chunk_tail, "normal")
                self.txt_ml_ai.insert("end", "\n", "normal")

        self.txt_ml_ai.config(state="disabled")

    def _abrir_enlace_ml(self):
        sel = self.tree_ml.selection()
        if sel:
            vals = self.tree_ml.item(sel[0], "values")
            if len(vals) >= 4 and vals[3].startswith("http"):
                webbrowser.open(vals[3])

    def _exportar_ml_csv(self):
        if not self.ml_resultados_cache:
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if fpath:
            if self.ml_tracker.exportar_csv(fpath, self.ml_resultados_cache):
                messagebox.showinfo("Éxito", f"Reporte guardado:\n{fpath}")

    # -------------------------------------------------------------------------
    # PESTAÑA 4: MARKETING Y PUBLICIDAD B2B
    # -------------------------------------------------------------------------
    def _build_tab_marketing(self):
        tab = self.tab_marketing

        header_mkt = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        header_mkt.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_mkt, text="Estrategia Publicitaria y Publicaciones Semanales B2B", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(side="left", padx=15, pady=10)

        self.btn_gen_campana = ctk.CTkButton(
            header_mkt,
            text="Generar Lote Semanal (L-M-V)",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._iniciar_marketing_thread
        )
        self.btn_gen_campana.pack(side="right", padx=15, pady=10)

        self.txt_mkt_output = ctk.CTkTextbox(tab, font=Theme.FONT_BODY, fg_color=Theme.CARD_BG)
        self.txt_mkt_output.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.txt_mkt_output.insert(
            "1.0",
            "Banco de 105 temas corporativos B2B disponibles.\n"
            "Horizonte garantizado sin repeticion: 100+ publicaciones.\n"
            "Estilo: Formal ejecutivo — dirigido a Gerentes de Compras, Administradores y Jefes de IT.\n\n"
            "Presiona 'Generar Lote Semanal' para redactar las 3 publicaciones B2B corporativas."
        )

    def _iniciar_marketing_thread(self):
        self.btn_gen_campana.configure(state="disabled")
        self.txt_mkt_output.delete("1.0", "end")
        self.txt_mkt_output.insert(
            "1.0",
            "Generando publicaciones corporativas B2B...\n"
            "Seleccionando temas unicos del banco estrategico...\n"
        )

        def _task():
            import json as _json
            siguiente_id = 1
            try:
                if os.path.exists(SystemConfig.QUOTES_FILE):
                    with open(SystemConfig.QUOTES_FILE, "r", encoding="utf-8") as f:
                        quotes = _json.load(f)
                    if quotes:
                        nums = []
                        for q in quotes:
                            raw = str(q.get("quote_id", "")).replace("COT-", "")
                            if raw.isdigit():
                                nums.append(int(raw))
                        if nums:
                            siguiente_id = max(nums) + 1
            except Exception:
                pass

            payload = {
                "siguiente_id": siguiente_id,
                "historial_copys": [],
            }
            res = self.marketing_agent.execute("generate_weekly_batch", payload)
            self.after(0, self._render_marketing_batch, res)

        threading.Thread(target=_task, daemon=True).start()

    def _render_marketing_batch(self, res):
        self.btn_gen_campana.configure(state="normal")
        self.txt_mkt_output.delete("1.0", "end")

        if res.success:
            posts = res.data
            separador = "=" * 70
            out = f"LOTE SEMANAL B2B GENERADO  —  ESTILO CORPORATIVO EJECUTIVO\n{separador}\n\n"
            for i, p in enumerate(posts, 1):
                banco_id = p.get("banco_tema_id", "-")
                pilar = p.get("pilar", "-")
                titulo = p.get("titulo_orientativo", "-")
                dia = p.get("dia_semana", f"Post {i}")
                out += f"[ PUBLICACION {i} | {dia} {p['fecha_programada']} ]\n"
                out += f"Banco ID: {banco_id} | Pilar: {pilar}\n"
                out += f"Enfoque: {titulo}\n"
                out += f"Categoria imagen: [{p['categoria']}] | Foto: {p['foto_asignada']}\n"
                out += f"WhatsApp directo: {p['whatsapp_url']}\n"
                out += f"\nCOPY DE LA PUBLICACION:\n{p['copy']}\n"
                out += f"\n{'-' * 70}\n\n"
            self.txt_mkt_output.insert("1.0", out)
        else:
            self.txt_mkt_output.insert("1.0", f"Error generando publicaciones: {res.message}")
