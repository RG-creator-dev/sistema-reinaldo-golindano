"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: detailed_breakdown_view.py
Descripción: Vista de Desglose Analítico por Categorías financieras (Moto,
             Sueldos, Servicios, Gasolina, Comisión Bancaria, Mercancía,
             Oficina, Herramientas, etc.) tanto en USD ($) como en Bs según
             tasa BCV oficial del día de la transacción, con archivo y respaldo
             local en Escritorio.
=============================================================================
"""

import os
from datetime import date
from tkinter import ttk, messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent
from modules.dept_04_administracion_finanzas.record_detail_modal import RecordDetailModal


class DetailedBreakdownView(ctk.CTkFrame):
    """
    Vista de Desglose Analítico Detallado por Categorías Financieras.
    Muestra contadores de ingresos, gastos, utilidades y barras de distribución
    por categoría tanto en dólares ($) como en bolívares (Bs) a tasa BCV histórica.
    """

    _MESES_ES = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    CATEGORY_METADATA = {
        "Moto": {"icon": "🏍️", "color": "#38bdf8", "type": "expense"},
        "Sueldos": {"icon": "👥", "color": "#818cf8", "type": "expense"},
        "Servicios": {"icon": "⚡", "color": "#a855f7", "type": "expense"},
        "Gasolina": {"icon": "⛽", "color": "#eab308", "type": "expense"},
        "Comisión Bancaria": {"icon": "🏦", "color": "#f43f5e", "type": "expense"},
        "Mercancía": {"icon": "📦", "color": "#f97316", "type": "expense"},
        "Oficina": {"icon": "🏢", "color": "#14b8a6", "type": "expense"},
        "Herramientas": {"icon": "🔧", "color": "#06b6d4", "type": "expense"},
        "Gastos Operativos": {"icon": "📋", "color": "#ec4899", "type": "expense"},
        "Otros Gastos": {"icon": "📑", "color": "#94a3b8", "type": "expense"},
        "Servicio Técnico": {"icon": "🛠️", "color": "#22c55e", "type": "income"},
        "Ventas / Facturación": {"icon": "💼", "color": "#10b981", "type": "income"},
        "Otros Ingresos": {"icon": "💰", "color": "#34d399", "type": "income"}
    }

    def __init__(self, master, agent: AccountingAgent = None, on_back_callback=None, initial_period=None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or AccountingAgent()
        self.on_back_callback = on_back_callback

        if initial_period:
            self._periodo_seleccionado = initial_period
        else:
            vz_now = self.agent.get_venezuela_now()
            self._periodo_seleccionado = (vz_now.year, vz_now.month)

        self._current_filter_category = "Todas las categorías"
        self._current_tab = "Gastos por Categoría"
        self._breakdown_data = {}

        self._init_ui()
        self.actualizar_desglose()

    def _init_ui(self):
        # ── 1. Cabecera de la Vista de Desglose ──
        header_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 8))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            title_box,
            text="📊 VISTA DE DESGLOSE ANALÍTICO (POR CATEGORÍAS)",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Métricas en USD ($) y Bolívares (Bs) a tasa BCV oficial del día de cada transacción",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Botones y controles de la cabecera derecha
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.pack(side="right", padx=15, pady=10)

        # Selector de Período
        ctk.CTkLabel(
            controls_box,
            text="Período:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))

        self._periodo_opciones = self._generar_opciones_periodo()
        self.combo_periodo = ctk.CTkComboBox(
            controls_box,
            values=self._periodo_opciones,
            width=150,
            state="readonly",
            command=self._on_cambio_periodo
        )
        # Seleccionar el período inicial
        y, m = self._periodo_seleccionado
        nombre_sel = f"{self._MESES_ES[m]} {y}"
        if nombre_sel in self._periodo_opciones:
            self.combo_periodo.set(nombre_sel)
        else:
            self.combo_periodo.set(self._periodo_opciones[0])
        self.combo_periodo.pack(side="left", padx=(0, 10))

        # Botón Exportar Respaldo al Escritorio (JSON/CSV)
        btn_export = ctk.CTkButton(
            controls_box,
            text="📥 Respaldo Escritorio",
            width=140,
            height=30,
            font=Theme.FONT_SMALL,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.exportar_respaldo_escritorio
        )
        btn_export.pack(side="left", padx=(0, 8))

        # Botón Cierre de Mes
        btn_cierre = ctk.CTkButton(
            controls_box,
            text="📦 Cerrar Mes",
            width=105,
            height=30,
            font=Theme.FONT_SMALL,
            fg_color=Theme.WARNING,
            hover_color="#d97706",
            command=self.solicitar_cierre_mensual
        )
        btn_cierre.pack(side="left", padx=(0, 8))

        # Botón Volver al Libro Mayor
        btn_volver = ctk.CTkButton(
            controls_box,
            text="📖 Libro Mayor",
            width=120,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._volver_al_libro_mayor
        )
        btn_volver.pack(side="left")

        # ── 2. Cuatro Tarjetas KPI Superiores ──
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=15, pady=4)
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # KPI 1: Total Ingresos
        self.card_ingresos = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_ingresos.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_ingresos, text="TOTAL INGRESOS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_ingresos = ctk.CTkLabel(self.card_ingresos, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.SUCCESS)
        self.lbl_kpi_ingresos.pack(pady=(0, 2))
        self.lbl_sub_ingresos = ctk.CTkLabel(self.card_ingresos, text="0 operaciones", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_ingresos.pack(pady=(0, 8))

        # KPI 2: Total Gastos
        self.card_gastos = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_gastos.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_gastos, text="TOTAL GASTOS OPERATIVOS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_gastos = ctk.CTkLabel(self.card_gastos, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.DANGER)
        self.lbl_kpi_gastos.pack(pady=(0, 2))
        self.lbl_sub_gastos = ctk.CTkLabel(self.card_gastos, text="0 operaciones", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_gastos.pack(pady=(0, 8))

        # KPI 3: Margen Operativo / Utilidad
        self.card_margen = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_margen.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_margen, text="MARGEN OPERATIVO / UTILIDAD", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_margen = ctk.CTkLabel(self.card_margen, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.PRIMARY)
        self.lbl_kpi_margen.pack(pady=(0, 2))
        self.lbl_sub_margen = ctk.CTkLabel(self.card_margen, text="Ingresos menos Gastos del período", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_margen.pack(pady=(0, 8))

        # KPI 4: Tasa BCV Promedio Ponderada
        self.card_bcv = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_bcv.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_bcv, text="TASA BCV HISTÓRICA PROMEDIO", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_bcv = ctk.CTkLabel(self.card_bcv, text="0.00 Bs/USD", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN)
        self.lbl_kpi_bcv.pack(pady=(0, 2))
        self.lbl_sub_bcv = ctk.CTkLabel(self.card_bcv, text="Ponderada según operaciones", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_bcv.pack(pady=(0, 8))

        # ── 3. Panel de Desglose por Categorías y Contenedor de Pestañas ──
        body_container = ctk.CTkFrame(self, fg_color="transparent")
        body_container.pack(fill="both", expand=True, padx=15, pady=(6, 12))
        body_container.grid_columnconfigure(0, weight=1)
        body_container.grid_rowconfigure(1, weight=1)

        # Barra superior con SegmentedButton para alternar entre categorías
        tab_bar = ctk.CTkFrame(body_container, fg_color="transparent")
        tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.seg_tipo_vista = ctk.CTkSegmentedButton(
            tab_bar,
            values=["Gastos por Categoría", "Ingresos por Categoría", "Consolidado General"],
            selected_color=Theme.PRIMARY,
            command=self._on_cambio_tipo_vista
        )
        self.seg_tipo_vista.set("Gastos por Categoría")
        self.seg_tipo_vista.pack(side="left")

        # Contenedor de Contenido Principal Dividido (Tarjetas de Categorías Arriba, Tabla Detallada Abajo)
        split_frame = ctk.CTkFrame(body_container, fg_color="transparent")
        split_frame.grid(row=1, column=0, sticky="nsew")
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_rowconfigure(0, weight=1)
        split_frame.grid_rowconfigure(1, weight=1)

        # A. Contenedor de Tarjetas de Categorías (Scrollable horizontal/vertical)
        self.scroll_cards = ctk.CTkScrollableFrame(
            split_frame,
            fg_color=Theme.CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=Theme.CARD_BORDER,
            height=200
        )
        self.scroll_cards.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        # B. Tabla Detallada de Movimientos de la Categoría
        table_container = ctk.CTkFrame(
            split_frame,
            fg_color=Theme.CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=Theme.CARD_BORDER
        )
        table_container.grid(row=1, column=0, sticky="nsew")

        # Cabecera de la tabla con selector de categoría y subtotales
        tbl_hdr = ctk.CTkFrame(table_container, fg_color="transparent")
        tbl_hdr.pack(fill="x", padx=12, pady=(10, 6))

        self.lbl_table_title = ctk.CTkLabel(
            tbl_hdr,
            text="Movimientos Detallados del Período",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_table_title.pack(side="left")

        filter_right = ctk.CTkFrame(tbl_hdr, fg_color="transparent")
        filter_right.pack(side="right")

        ctk.CTkLabel(
            filter_right,
            text="Filtrar Categoría:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))

        self.combo_filtro_cat = ctk.CTkComboBox(
            filter_right,
            values=["Todas las categorías"],
            width=200,
            state="readonly",
            command=self._on_filtro_categoria_cambiado
        )
        self.combo_filtro_cat.set("Todas las categorías")
        self.combo_filtro_cat.pack(side="left")

        # Botón para Ver Registro en Grande
        btn_ver_grande = ctk.CTkButton(
            filter_right,
            text="🔍 Ver en Grande",
            width=120,
            height=28,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.abrir_registro_seleccionado_grande
        )
        btn_ver_grande.pack(side="left", padx=(8, 0))

        # Treeview nativo de transacciones
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Desglose.Treeview",
            background=Theme.INPUT_BG,
            foreground=Theme.TEXT_MAIN,
            fieldbackground=Theme.INPUT_BG,
            rowheight=24,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Desglose.Treeview.Heading",
            background=Theme.CARD_BORDER,
            foreground=Theme.TEXT_MAIN,
            font=("Segoe UI", 9, "bold")
        )
        style.map("Desglose.Treeview", background=[("selected", Theme.PRIMARY)])

        tree_scroll = ttk.Scrollbar(table_container, orient="vertical")
        cols = ("fecha", "tipo", "categoria", "usd", "bcv", "bs", "metodo", "ref", "descripcion")
        self.tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            style="Desglose.Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("usd", text="Monto ($)")
        self.tree.heading("bcv", text="Tasa BCV")
        self.tree.heading("bs", text="Monto (Bs)")
        self.tree.heading("metodo", text="Método")
        self.tree.heading("ref", text="N° Ref")
        self.tree.heading("descripcion", text="Descripción")

        self.tree.column("fecha", width=120, anchor="center")
        self.tree.column("tipo", width=70, anchor="center")
        self.tree.column("categoria", width=120, anchor="w")
        self.tree.column("usd", width=85, anchor="e")
        self.tree.column("bcv", width=85, anchor="e")
        self.tree.column("bs", width=110, anchor="e")
        self.tree.column("metodo", width=110, anchor="center")
        self.tree.column("ref", width=95, anchor="center")
        self.tree.column("descripcion", width=220)

        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 10))
        tree_scroll.pack(side="right", fill="y", padx=(0, 12), pady=(0, 10))

        self.tree.tag_configure("ingreso", foreground="#4ade80")
        self.tree.tag_configure("gasto", foreground="#f87171")

        # Doble clic abre automáticamente la ficha técnica ampliada
        self.tree.bind("<Double-1>", lambda e: self.abrir_registro_seleccionado_grande())

    # ─── Navegación y Período ────────────────────────────────────────────────

    def _volver_al_libro_mayor(self):
        if self.on_back_callback:
            self.on_back_callback()

    def _generar_opciones_periodo(self, ventana_meses: int = 24) -> list:
        hoy = date.today()
        opciones = []
        for delta in range(ventana_meses):
            m = hoy.month - delta
            y = hoy.year
            while m <= 0:
                m += 12
                y -= 1
            opciones.append(f"{self._MESES_ES[m]} {y}")
        return opciones

    def _parse_periodo(self, texto: str):
        partes = texto.strip().split()
        if len(partes) != 2:
            return None
        try:
            mes_idx = self._MESES_ES.index(partes[0])
            anio = int(partes[1])
            return (anio, mes_idx)
        except (ValueError, IndexError):
            return None

    def _on_cambio_periodo(self, seleccion: str):
        parsed = self._parse_periodo(seleccion)
        if parsed:
            self._periodo_seleccionado = parsed
            self.actualizar_desglose()

    def set_periodo(self, year: int, month: int):
        """Permite sincronizar el período desde la vista padre."""
        self._periodo_seleccionado = (year, month)
        nombre = f"{self._MESES_ES[month]} {year}"
        if nombre in self._periodo_opciones:
            self.combo_periodo.set(nombre)
        self.actualizar_desglose()

    def _on_cambio_tipo_vista(self, seleccion: str):
        self._current_tab = seleccion
        self._render_category_cards()

    def _on_filtro_categoria_cambiado(self, seleccion: str):
        self._current_filter_category = seleccion
        self._render_transactions_table()

    # ─── Lógica de Renderizado y Actualización ───────────────────────────────

    def actualizar_desglose(self):
        """Calcula el desglose con el agente contable y refresca contadores, tarjetas y tabla."""
        y, m = self._periodo_seleccionado
        self._breakdown_data = self.agent.get_category_breakdown(y, m)

        d = self._breakdown_data
        ing_usd = d.get("total_income_usd", 0.0)
        ing_bs = d.get("total_income_bs", 0.0)
        gas_usd = d.get("total_expense_usd", 0.0)
        gas_bs = d.get("total_expense_bs", 0.0)
        margen_usd = d.get("operating_margin_usd", 0.0)
        margen_bs = d.get("operating_margin_bs", 0.0)
        avg_bcv = d.get("average_bcv_rate", 0.0)

        # Actualizar Tarjetas KPI
        self.lbl_kpi_ingresos.configure(text=f"${ing_usd:,.2f} | {ing_bs:,.2f} Bs")
        n_ing = sum(1 for r in d.get("records", []) if str(r.get("type", "")).strip().lower() == "ingreso")
        self.lbl_sub_ingresos.configure(text=f"{n_ing} transacción{'es' if n_ing != 1 else ''}")

        self.lbl_kpi_gastos.configure(text=f"${gas_usd:,.2f} | {gas_bs:,.2f} Bs")
        n_gas = sum(1 for r in d.get("records", []) if str(r.get("type", "")).strip().lower() in ("gasto", "egreso"))
        self.lbl_sub_gastos.configure(text=f"{n_gas} egreso{'s' if n_gas != 1 else ''}")

        signo_margen = "+" if margen_usd >= 0 else ""
        color_margen = Theme.SUCCESS if margen_usd >= 0 else Theme.DANGER
        self.lbl_kpi_margen.configure(
            text=f"{signo_margen}${margen_usd:,.2f} | {signo_margen}{margen_bs:,.2f} Bs",
            text_color=color_margen
        )

        bcv_txt = f"{avg_bcv:,.2f} Bs/USD" if avg_bcv > 0 else "N/A"
        self.lbl_kpi_bcv.configure(text=bcv_txt)

        # Actualizar opciones del combo de filtro de categorías
        cat_names = sorted(list(d.get("categories", {}).keys()))
        combo_vals = ["Todas las categorías"] + [c for c in cat_names if d["categories"][c]["count"] > 0]
        if self._current_filter_category not in combo_vals:
            self._current_filter_category = "Todas las categorías"
        self.combo_filtro_cat.configure(values=combo_vals)
        self.combo_filtro_cat.set(self._current_filter_category)

        self._render_category_cards()
        self._render_transactions_table()

    def _render_category_cards(self):
        """Renderiza las tarjetas con contadores, montos en $ y Bs, y barra visual de distribución."""
        for child in self.scroll_cards.winfo_children():
            child.destroy()

        d = self._breakdown_data
        categories = d.get("categories", {})
        if not categories:
            ctk.CTkLabel(
                self.scroll_cards,
                text="No hay movimientos registrados para este período.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED
            ).pack(pady=30)
            return

        # Filtrar categorías según la pestaña seleccionada
        if self._current_tab == "Gastos por Categoría":
            keys = [
                k for k in categories.keys()
                if self.CATEGORY_METADATA.get(k, {}).get("type", "expense") == "expense"
            ]
        elif self._current_tab == "Ingresos por Categoría":
            keys = [
                k for k in categories.keys()
                if self.CATEGORY_METADATA.get(k, {}).get("type", "expense") == "income"
            ]
        else:
            keys = list(categories.keys())

        # Ordenar primero las categorías con monto mayor a 0, luego alfabéticamente
        keys.sort(key=lambda k: (-categories[k]["amount_usd"], k))

        # Crear cuadrícula responsiva de 3 columnas
        cols_count = 3
        for col_idx in range(cols_count):
            self.scroll_cards.grid_columnconfigure(col_idx, weight=1)

        row_idx = 0
        col_idx = 0

        for cat_name in keys:
            cdata = categories[cat_name]
            meta = self.CATEGORY_METADATA.get(cat_name, {"icon": "📌", "color": Theme.PRIMARY})
            icon = meta.get("icon", "📌")
            accent_color = meta.get("color", Theme.PRIMARY)

            usd = cdata.get("amount_usd", 0.0)
            bs = cdata.get("amount_bs", 0.0)
            count = cdata.get("count", 0)
            pct = cdata.get("percentage", 0.0)

            # Tarjeta de Categoría
            card = ctk.CTkFrame(
                self.scroll_cards,
                fg_color=Theme.BG_DARK,
                corner_radius=8,
                border_width=1,
                border_color=Theme.CARD_BORDER
            )
            card.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

            # Fila Superior: Icono, Nombre y Badge de Porcentaje
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                top_row,
                text=f"{icon} {cat_name}",
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.TEXT_MAIN
            ).pack(side="left")

            pct_badge = ctk.CTkLabel(
                top_row,
                text=f"{pct:.1f}%",
                font=("Segoe UI", 8, "bold"),
                text_color=accent_color
            )
            pct_badge.pack(side="right")

            # Fila Central: Montos en $ y Bs
            amounts_row = ctk.CTkFrame(card, fg_color="transparent")
            amounts_row.pack(fill="x", padx=10, pady=(2, 4))

            ctk.CTkLabel(
                amounts_row,
                text=f"${usd:,.2f}",
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.TEXT_MAIN
            ).pack(anchor="w")

            ctk.CTkLabel(
                amounts_row,
                text=f"{bs:,.2f} Bs (BCV Oficial)",
                font=("Segoe UI", 8),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w")

            # Barra de progreso visual que representa el porcentaje
            progress = ctk.CTkProgressBar(
                card,
                height=6,
                corner_radius=3,
                progress_color=accent_color,
                fg_color=Theme.CARD_BORDER
            )
            progress.pack(fill="x", padx=10, pady=(4, 6))
            fraction = min(max(pct / 100.0, 0.0), 1.0)
            progress.set(fraction)

            # Pie de tarjeta: Conteo de operaciones y botón interactivo para filtrar
            footer_row = ctk.CTkFrame(card, fg_color="transparent")
            footer_row.pack(fill="x", padx=10, pady=(0, 8))

            ctk.CTkLabel(
                footer_row,
                text=f"{count} movimiento{'s' if count != 1 else ''}",
                font=("Segoe UI", 8),
                text_color=Theme.TEXT_DIM
            ).pack(side="left")

            btn_ver = ctk.CTkButton(
                footer_row,
                text="Ver detalle",
                width=75,
                height=22,
                font=("Segoe UI", 8),
                fg_color=Theme.CARD_BORDER,
                hover_color=accent_color,
                command=lambda c=cat_name: self._seleccionar_categoria_filtro(c)
            )
            btn_ver.pack(side="right")

            col_idx += 1
            if col_idx >= cols_count:
                col_idx = 0
                row_idx += 1

    def _seleccionar_categoria_filtro(self, category_name: str):
        """Permite que el usuario haga clic en una categoría para filtrar instantáneamente la tabla."""
        self._current_filter_category = category_name
        self.combo_filtro_cat.set(category_name)
        self._render_transactions_table()

    def _render_transactions_table(self):
        """Puebla la tabla de transacciones según la categoría filtrada."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        d = self._breakdown_data
        records = d.get("records", [])

        # Filtrar si hay categoría específica seleccionada
        if self._current_filter_category and self._current_filter_category != "Todas las categorías":
            records_filtrados = [
                r for r in records
                if self.agent.categorize_record(r) == self._current_filter_category
            ]
            self.lbl_table_title.configure(
                text=f"Movimientos de la categoría: {self._current_filter_category} ({len(records_filtrados)} registros)"
            )
        else:
            records_filtrados = records
            self.lbl_table_title.configure(
                text=f"Todos los Movimientos del Período ({len(records_filtrados)} registros)"
            )

        for r in reversed(records_filtrados):
            t_type = (r.get("type") or "").strip()
            es_gasto = t_type.lower() in ("gasto", "egreso")
            tag = "gasto" if es_gasto else "ingreso"
            signo = "-" if es_gasto else "+"

            cat = self.agent.categorize_record(r)
            usd = float(r.get("amount_usd", 0.0))
            bcv = float(r.get("bcv_rate", 0.0))
            bs = float(r.get("amount_bs", 0.0))
            if bs <= 0 and bcv > 0:
                bs = round(usd * bcv, 2)

            self.tree.insert("", "end", tags=(tag,), values=(
                r.get("date", ""),
                t_type,
                cat,
                f"{signo}${usd:,.2f}",
                f"{bcv:,.2f}" if bcv > 0 else "N/A",
                f"{signo}{bs:,.2f} Bs",
                r.get("method", ""),
                r.get("ref_code", "") or "—",
                r.get("description", "")
            ))

    # ─── Rutinas de Respaldo y Cierre de Mes ──────────────────────────────────

    def exportar_respaldo_escritorio(self):
        """Exporta manualmente el respaldo consolidado en formatos JSON y CSV al Escritorio."""
        y, m = self._periodo_seleccionado
        try:
            res = self.agent.export_monthly_backup(y, m)
            messagebox.showinfo(
                "Respaldo Exitoso en el Escritorio",
                f"¡Los datos consolidados del período {self._MESES_ES[m]} {y} se guardaron exitosamente!\n\n"
                f"📁 Carpeta de respaldo:\n{res['folder']}\n\n"
                f"Archivos generados:\n"
                f"• {os.path.basename(res['json_path'])}\n"
                f"• {os.path.basename(res['csv_path'])} (Listo para Excel con codificación UTF-8)\n\n"
                f"Total Ingresos: ${res['summary']['total_income_usd']:,.2f} | Total Gastos: ${res['summary']['total_expense_usd']:,.2f}"
            )
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo generar el respaldo en el escritorio:\n{e}")

    def solicitar_cierre_mensual(self):
        """Solicita confirmación y ejecuta el cierre mensual y respaldo en el Escritorio."""
        y, m = self._periodo_seleccionado
        nombre_mes = f"{self._MESES_ES[m]} {y}"

        confirma = messagebox.askyesno(
            "Confirmación de Cierre Mensual",
            f"¿Desea ejecutar el cierre mensual consolidado para {nombre_mes}?\n\n"
            f"Esta operación:\n"
            f"1. Generará un respaldo completo (JSON y CSV) en la carpeta de respaldos del Escritorio.\n"
            f"2. Transferirá el balance neto de {nombre_mes} como saldo inicial para el mes siguiente.\n"
            f"3. Mantendrá disponible todo el histórico contable para consultas.\n\n"
            f"¿Proceder con el cierre?",
            icon="question"
        )
        if not confirma:
            return

        try:
            resp = self.agent.perform_monthly_close(y, m)
            if resp.success:
                messagebox.showinfo("Cierre Mensual Exitoso", resp.message)
                self.actualizar_desglose()
            else:
                messagebox.showerror("Error en Cierre", resp.message)
        except Exception as e:
            messagebox.showerror("Error en Cierre", f"Ocurrió un error al procesar el cierre:\n{e}")

    def abrir_registro_seleccionado_grande(self):
        """Abre la ficha técnica ampliada del movimiento contable seleccionado."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección requerida", "Por favor seleccione un movimiento de la tabla para ver su ficha ampliada.")
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        fecha_val = values[0]
        desc_val = values[8]

        records = self._breakdown_data.get("records", [])
        found_tx = None
        for r in reversed(records):
            if str(r.get("date", "")) == fecha_val and str(r.get("description", "")) == desc_val:
                found_tx = r
                break

        if not found_tx:
            usd_clean = values[3].replace("$", "").replace("-", "").replace("+", "").replace(",", "").strip()
            bs_clean = values[5].replace("Bs", "").replace("-", "").replace("+", "").replace(",", "").strip()
            try:
                usd_num = float(usd_clean)
            except Exception:
                usd_num = 0.0
            try:
                bs_num = float(bs_clean)
            except Exception:
                bs_num = 0.0

            found_tx = {
                "id": f"TRX-{fecha_val}",
                "date": fecha_val,
                "type": values[1],
                "category": values[2],
                "amount_usd": usd_num,
                "amount_bs": bs_num,
                "method": values[6],
                "ref_code": values[7],
                "description": desc_val,
                "bcv_rate": float(values[4]) if values[4] != "N/A" else 0.0
            }

        RecordDetailModal(
            self,
            record=found_tx,
            record_type="ledger",
            agent=self.agent,
            on_update_callback=self.actualizar_desglose
        )
