"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: cxc_cxp_view.py
Descripción: Sección manual dedicada a la gestión de Cuentas por Cobrar (CxC)
             y Cuentas por Pagar (CxP), liquidación directa con el Libro Mayor
             y visualización ampliada en ventanas grandes.
=============================================================================
"""

from datetime import datetime, date
from tkinter import ttk, messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent
from modules.dept_04_administracion_finanzas.record_detail_modal import RecordDetailModal


class CxcCxpView(ctk.CTkFrame):
    """
    Vista integral y manual de Cuentas por Cobrar (CxC) y Cuentas por Pagar (CxP).
    Permite registrar créditos, vencimientos, proveedores/clientes y liquidar
    automáticamente en el Libro Mayor principal sin duplicación.
    """

    def __init__(self, master, agent: AccountingAgent = None, on_back_callback = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or AccountingAgent()
        self.on_back_callback = on_back_callback

        self._tipo_filtro = "Todas"
        self._estatus_filtro = "Todos"
        self._filtro_busqueda = ""
        self._records_cache = []

        self._init_ui()
        self.actualizar_datos()

    def _init_ui(self):
        # ── 1. Cabecera del Módulo de CxC y CxP ──
        header_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 8))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            title_box,
            text="💳 CUENTAS POR COBRAR (CxC) Y POR PAGAR (CxP)",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Control de compromisos y cobranzas con liquidación directa en el Libro Mayor",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Botones de Acción en la Cabecera
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.pack(side="right", padx=15, pady=10)

        # Botón Nueva CxC (Cobrar)
        btn_nueva_cxc = ctk.CTkButton(
            controls_box,
            text="+ Nueva CxC (Cobrar)",
            width=150,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda: self.abrir_dialogo_registro("CxC")
        )
        btn_nueva_cxc.pack(side="left", padx=(0, 8))

        # Botón Nueva CxP (Pagar)
        btn_nueva_cxp = ctk.CTkButton(
            controls_box,
            text="+ Nueva CxP (Pagar)",
            width=150,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=lambda: self.abrir_dialogo_registro("CxP")
        )
        btn_nueva_cxp.pack(side="left", padx=(0, 8))

        # Botón Refrescar
        btn_refresh = ctk.CTkButton(
            controls_box,
            text="🔄",
            width=40,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.CARD_BORDER,
            hover_color=Theme.PRIMARY,
            command=self.actualizar_datos
        )
        btn_refresh.pack(side="left", padx=(0, 8))

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

        # ── 2. Cuatro Tarjetas de Resumen KPI ──
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=15, pady=4)
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # KPI 1: CxC Pendientes (Cuentas por cobrar a clientes)
        self.card_cxc = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_cxc.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_cxc, text="POR COBRAR PENDIENTE (CxC)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_cxc = ctk.CTkLabel(self.card_cxc, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color="#38bdf8")
        self.lbl_kpi_cxc.pack(pady=(0, 2))
        self.lbl_sub_cxc = ctk.CTkLabel(self.card_cxc, text="0 facturas pendientes", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_cxc.pack(pady=(0, 8))

        # KPI 2: CxP Pendientes (Cuentas por pagar a proveedores)
        self.card_cxp = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_cxp.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_cxp, text="POR PAGAR PENDIENTE (CxP)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_cxp = ctk.CTkLabel(self.card_cxp, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color="#fb923c")
        self.lbl_kpi_cxp.pack(pady=(0, 2))
        self.lbl_sub_cxp = ctk.CTkLabel(self.card_cxp, text="0 compromisos pendientes", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_cxp.pack(pady=(0, 8))

        # KPI 3: Total Liquidado / Cobrado y Pagado
        self.card_pagado = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_pagado.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_pagado, text="TOTAL YA LIQUIDADO", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_pagado = ctk.CTkLabel(self.card_pagado, text="$0.00 USD", font=Theme.FONT_SUBTITLE, text_color=Theme.SUCCESS)
        self.lbl_kpi_pagado.pack(pady=(0, 2))
        self.lbl_sub_pagado = ctk.CTkLabel(self.card_pagado, text="Asentado en Libro Mayor", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_pagado.pack(pady=(0, 8))

        # KPI 4: Alertas de Vencimiento
        self.card_vencidos = ctk.CTkFrame(kpi_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_vencidos.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(self.card_vencidos, text="ALERTAS DE VENCIMIENTO", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_vencidos = ctk.CTkLabel(self.card_vencidos, text="0 Alertas", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN)
        self.lbl_kpi_vencidos.pack(pady=(0, 2))
        self.lbl_sub_vencidos = ctk.CTkLabel(self.card_vencidos, text="Facturas vencidas o por vencer", font=("Segoe UI", 8), text_color=Theme.TEXT_DIM)
        self.lbl_sub_vencidos.pack(pady=(0, 8))

        # ── 3. Barra de Filtros y Herramientas ──
        filter_bar = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=8, height=48)
        filter_bar.pack(fill="x", padx=15, pady=(6, 8))

        # Filtro de Tipo (Todas / CxC / CxP)
        self.seg_tipo = ctk.CTkSegmentedButton(
            filter_bar,
            values=["Todas", "Cuentas por Cobrar (CxC)", "Cuentas por Pagar (CxP)"],
            selected_color=Theme.PRIMARY,
            command=self._on_tipo_filter_changed
        )
        self.seg_tipo.set("Todas")
        self.seg_tipo.pack(side="left", padx=12, pady=8)

        # Filtro de Estatus (Todos / Pendiente / Abonado / Pagado)
        ctk.CTkLabel(filter_bar, text="Estatus:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="left", padx=(10, 4))
        self.combo_estatus = ctk.CTkComboBox(
            filter_bar,
            values=["Todos", "Pendiente", "Abonado", "Pagado"],
            width=120,
            state="readonly",
            command=self._on_estatus_filter_changed
        )
        self.combo_estatus.set("Todos")
        self.combo_estatus.pack(side="left", padx=(0, 10))

        # Campo de Búsqueda Rápida por texto
        self.entry_search = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Buscar por cliente, proveedor o concepto...",
            font=Theme.FONT_SMALL,
            width=240
        )
        self.entry_search.pack(side="left", padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", lambda e: self._on_search_changed())

        # BOTÓN DE EXPANSIÓN / VER EN GRANDE
        btn_ver_grande = ctk.CTkButton(
            filter_bar,
            text="🔍 Ver en Grande",
            width=130,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.abrir_detalle_seleccionado
        )
        btn_ver_grande.pack(side="right", padx=(4, 12))

        # Botón Liquidar / Marcar como Pagado
        btn_liquidar = ctk.CTkButton(
            filter_bar,
            text="💳 Liquidar Cuenta",
            width=125,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self.liquidar_seleccionado
        )
        btn_liquidar.pack(side="right", padx=(4, 6))

        # ── 4. Contenedor de Tabla de Cuentas ──
        table_container = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        table_container.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # Cabecera de estado de tabla
        tbl_top = ctk.CTkFrame(table_container, fg_color="transparent")
        tbl_top.pack(fill="x", padx=15, pady=(10, 4))

        self.lbl_table_info = ctk.CTkLabel(
            tbl_top,
            text="Mostrando 0 cuentas registradas (Doble clic en cualquier fila para ampliar en grande)",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_table_info.pack(side="left")

        # Treeview nativo de Tkinter estilizado
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "CxcCxp.Treeview",
            background=Theme.INPUT_BG,
            foreground=Theme.TEXT_MAIN,
            fieldbackground=Theme.INPUT_BG,
            rowheight=26,
            font=("Segoe UI", 9)
        )
        style.configure(
            "CxcCxp.Treeview.Heading",
            background=Theme.CARD_BORDER,
            foreground=Theme.TEXT_MAIN,
            font=("Segoe UI", 9, "bold")
        )
        style.map("CxcCxp.Treeview", background=[("selected", Theme.PRIMARY)])

        tree_scroll = ttk.Scrollbar(table_container, orient="vertical")
        columns = ("id", "tipo", "entidad", "concepto", "usd", "bs", "emision", "vencimiento", "estatus", "asiento")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="CxcCxp.Treeview",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("id", text="ID")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("entidad", text="Cliente / Proveedor")
        self.tree.heading("concepto", text="Concepto")
        self.tree.heading("usd", text="Monto ($)")
        self.tree.heading("bs", text="Monto (Bs)")
        self.tree.heading("emision", text="Emisión")
        self.tree.heading("vencimiento", text="Vencimiento")
        self.tree.heading("estatus", text="Estatus")
        self.tree.heading("asiento", text="Ref Libro Mayor")

        self.tree.column("id", width=120, anchor="center")
        self.tree.column("tipo", width=65, anchor="center")
        self.tree.column("entidad", width=180, anchor="w")
        self.tree.column("concepto", width=220, anchor="w")
        self.tree.column("usd", width=85, anchor="e")
        self.tree.column("bs", width=110, anchor="e")
        self.tree.column("emision", width=95, anchor="center")
        self.tree.column("vencimiento", width=105, anchor="center")
        self.tree.column("estatus", width=90, anchor="center")
        self.tree.column("asiento", width=130, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 10))
        tree_scroll.pack(side="right", fill="y", padx=(0, 12), pady=(0, 10))

        # Doble clic abre automáticamente la visualización ampliada
        self.tree.bind("<Double-1>", lambda e: self.abrir_detalle_seleccionado())

        # Configurar colores de filas
        self.tree.tag_configure("pagado", foreground="#4ade80")
        self.tree.tag_configure("pendiente_cxc", foreground="#38bdf8")
        self.tree.tag_configure("pendiente_cxp", foreground="#fb923c")
        self.tree.tag_configure("vencido", foreground="#f87171")

    # ─── Navegación y Volver ──────────────────────────────────────────────────

    def _volver_al_libro_mayor(self):
        if self.on_back_callback:
            self.on_back_callback()

    # ─── Carga y Filtrado de Datos ───────────────────────────────────────────

    def actualizar_datos(self):
        """Consulta el agente contable y refresca tarjetas de KPI y la tabla."""
        res = self.agent.get_cxc_cxp_summary()
        if not res.success:
            return

        d = res.data
        self._records_cache = d.get("records", [])

        # Actualizar KPIs
        cxc_usd = d.get("total_cxc_pending_usd", 0.0)
        cxc_bs = d.get("total_cxc_pending_bs", 0.0)
        self.lbl_kpi_cxc.configure(text=f"${cxc_usd:,.2f} | {cxc_bs:,.2f} Bs")
        n_cxc = d.get("count_cxc_pending", 0)
        self.lbl_sub_cxc.configure(text=f"{n_cxc} cuenta{'s' if n_cxc != 1 else ''} por cobrar")

        cxp_usd = d.get("total_cxp_pending_usd", 0.0)
        cxp_bs = d.get("total_cxp_pending_bs", 0.0)
        self.lbl_kpi_cxp.configure(text=f"${cxp_usd:,.2f} | {cxp_bs:,.2f} Bs")
        n_cxp = d.get("count_cxp_pending", 0)
        self.lbl_sub_cxp.configure(text=f"{n_cxp} compromiso{'s' if n_cxp != 1 else ''} por pagar")

        paid_usd = d.get("total_cxc_paid_usd", 0.0) + d.get("total_cxp_paid_usd", 0.0)
        self.lbl_kpi_pagado.configure(text=f"${paid_usd:,.2f} USD")

        n_overdue = d.get("count_overdue", 0)
        if n_overdue > 0:
            self.lbl_kpi_vencidos.configure(text=f"⚠️ {n_overdue} Vencida{'s' if n_overdue != 1 else ''}", text_color=Theme.DANGER)
        else:
            self.lbl_kpi_vencidos.configure(text="✅ Al día (0 alertas)", text_color=Theme.SUCCESS)

        self._render_tabla()

    def _on_tipo_filter_changed(self, valor):
        self._tipo_filtro = valor
        self._render_tabla()

    def _on_estatus_filter_changed(self, valor):
        self._estatus_filtro = valor
        self._render_tabla()

    def _on_search_changed(self):
        self._filtro_busqueda = self.entry_search.get().strip().lower()
        self._render_tabla()

    def _render_tabla(self):
        """Puebla la tabla aplicando los filtros de tipo, estatus y texto de búsqueda."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        hoy_str = datetime.now().strftime("%Y-%m-%d")
        filtrados = []

        for r in self._records_cache:
            c_type = r.get("type", "CxC")
            status = r.get("status", "Pendiente")

            # Filtro por Tipo
            if self._tipo_filtro == "Cuentas por Cobrar (CxC)" and c_type != "CxC":
                continue
            if self._tipo_filtro == "Cuentas por Pagar (CxP)" and c_type != "CxP":
                continue

            # Filtro por Estatus
            if self._estatus_filtro != "Todos" and status != self._estatus_filtro:
                continue

            # Filtro por Texto
            if self._filtro_busqueda:
                searchable = f"{r.get('entity_name', '')} {r.get('concept', '')} {r.get('id', '')}".lower()
                if self._filtro_busqueda not in searchable:
                    continue

            filtrados.append(r)

        self.lbl_table_info.configure(
            text=f"Mostrando {len(filtrados)} cuentas registradas • Doble clic o botón 'Ver en Grande' para ficha técnica completa"
        )

        for r in reversed(filtrados):
            c_type = r.get("type", "CxC")
            status = r.get("status", "Pendiente")
            due = str(r.get("due_date", ""))[:10]

            # Asignación de tag para color
            if status == "Pagado":
                tag = "pagado"
            elif due and due < hoy_str:
                tag = "vencido"
            elif c_type == "CxC":
                tag = "pendiente_cxc"
            else:
                tag = "pendiente_cxp"

            usd = float(r.get("amount_usd", 0.0))
            bs = float(r.get("amount_bs", 0.0))
            ledger_id = r.get("ledger_trx_id") or "Pendiente"

            self.tree.insert("", "end", tags=(tag,), values=(
                r.get("id", ""),
                c_type,
                r.get("entity_name", ""),
                r.get("concept", ""),
                f"${usd:,.2f}",
                f"{bs:,.2f} Bs",
                r.get("issue_date", ""),
                due,
                f"● {status}",
                ledger_id
            ))

    # ─── Acciones de Visualización y Liquidación ──────────────────────────────

    def _get_selected_record(self):
        """Retorna el diccionario de datos del registro actualmente seleccionado en la tabla."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección requerida", "Por favor seleccione una cuenta de la lista.")
            return None

        item_values = self.tree.item(selected[0], "values")
        if not item_values:
            return None

        rec_id = item_values[0]
        for r in self._records_cache:
            if r.get("id") == rec_id:
                return r
        return None

    def abrir_detalle_seleccionado(self):
        """Abre la ventana flotante de gran tamaño con la ficha técnica detallada del registro."""
        record = self._get_selected_record()
        if not record:
            return

        RecordDetailModal(
            self,
            record=record,
            record_type="cxc_cxp",
            agent=self.agent,
            on_update_callback=self.actualizar_datos
        )

    def liquidar_seleccionado(self):
        """Abre directamente la acción de liquidación para el registro seleccionado."""
        record = self._get_selected_record()
        if not record:
            return

        if record.get("status") == "Pagado" or record.get("ledger_trx_id"):
            messagebox.showinfo(
                "Cuenta Ya Liquidada",
                f"Esta cuenta ({record.get('id')}) ya se encuentra pagada y asentada en el Libro Mayor (ID: {record.get('ledger_trx_id')})."
            )
            return

        # Abrir el modal ampliado que cuenta con el botón de confirmación de liquidación
        modal = RecordDetailModal(
            self,
            record=record,
            record_type="cxc_cxp",
            agent=self.agent,
            on_update_callback=self.actualizar_datos
        )
        modal._liquidar_registro()

    # ─── Modal de Registro Manual de CxC / CxP ───

    def abrir_dialogo_registro(self, tipo_inicial="CxC"):
        """Abre una ventana emergente para registrar manualmente una nueva CxC o CxP."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Registrar {'Cuenta por Cobrar (CxC)' if tipo_inicial == 'CxC' else 'Cuenta por Pagar (CxP)'}")
        dlg.geometry("450x520")
        dlg.resizable(False, False)
        dlg.grab_set()

        ctk.CTkLabel(
            dlg,
            text=f"Nueva Operación: {'Cuenta por Cobrar (CxC)' if tipo_inicial == 'CxC' else 'Cuenta por Pagar (CxP)'}",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(16, 6))

        # Selector de Tipo (CxC vs CxP)
        ctk.CTkLabel(dlg, text="Tipo de Cuenta:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(2, 0))
        seg_tipo_dlg = ctk.CTkSegmentedButton(dlg, values=["CxC (Por Cobrar)", "CxP (Por Pagar)"], selected_color=Theme.PRIMARY)
        seg_tipo_dlg.set("CxC (Por Cobrar)" if tipo_inicial == "CxC" else "CxP (Por Pagar)")
        seg_tipo_dlg.pack(fill="x", padx=20, pady=2)

        # Cliente / Proveedor
        lbl_entidad = ctk.CTkLabel(dlg, text="Cliente:" if tipo_inicial == "CxC" else "Proveedor:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        lbl_entidad.pack(anchor="w", padx=20, pady=(4, 0))
        entry_entidad = ctk.CTkEntry(dlg, placeholder_text="Nombre de la empresa, cliente o proveedor", font=Theme.FONT_BODY)
        entry_entidad.pack(fill="x", padx=20, pady=2)

        def _cambiar_etiqueta_tipo(val):
            if "CxC" in val:
                lbl_entidad.configure(text="Cliente:")
            else:
                lbl_entidad.configure(text="Proveedor:")
        seg_tipo_dlg.configure(command=_cambiar_etiqueta_tipo)

        # Concepto
        ctk.CTkLabel(dlg, text="Concepto de la Operación:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        entry_concepto = ctk.CTkEntry(dlg, placeholder_text="Ej: Venta 2 Tóner HP 85A a crédito", font=Theme.FONT_BODY)
        entry_concepto.pack(fill="x", padx=20, pady=2)

        # Monto y Moneda
        ctk.CTkLabel(dlg, text="Monto (USD):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        entry_monto = ctk.CTkEntry(dlg, placeholder_text="0.00", font=Theme.FONT_BODY)
        entry_monto.pack(fill="x", padx=20, pady=2)

        # Fechas: Emisión y Vencimiento
        fechas_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        fechas_frame.pack(fill="x", padx=20, pady=4)
        fechas_frame.grid_columnconfigure((0, 1), weight=1)

        hoy_str = datetime.now().strftime("%Y-%m-%d")
        
        # Emisión
        col_emision = ctk.CTkFrame(fechas_frame, fg_color="transparent")
        col_emision.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkLabel(col_emision, text="Fecha Emisión (AAAA-MM-DD):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")
        entry_emision = ctk.CTkEntry(col_emision, font=Theme.FONT_BODY)
        entry_emision.insert(0, hoy_str)
        entry_emision.pack(fill="x", pady=2)

        # Vencimiento
        col_venc = ctk.CTkFrame(fechas_frame, fg_color="transparent")
        col_venc.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(col_venc, text="Fecha Vencimiento:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")
        entry_venc = ctk.CTkEntry(col_venc, font=Theme.FONT_BODY)
        # Por defecto 15 días posteriores
        try:
            from datetime import timedelta
            venc_default = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        except Exception:
            venc_default = hoy_str
        entry_venc.insert(0, venc_default)
        entry_venc.pack(fill="x", pady=2)

        # Estatus Inicial
        ctk.CTkLabel(dlg, text="Estatus:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        combo_status = ctk.CTkComboBox(dlg, values=["Pendiente", "Abonado", "Pagado"], state="readonly")
        combo_status.set("Pendiente")
        combo_status.pack(fill="x", padx=20, pady=2)

        # Notas Adicionales
        ctk.CTkLabel(dlg, text="Notas Adicionales / Referencia:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        entry_notas = ctk.CTkEntry(dlg, placeholder_text="Opcional: Factura N° 1084 / Contacto", font=Theme.FONT_BODY)
        entry_notas.pack(fill="x", padx=20, pady=2)

        def _guardar():
            tipo_sel = "CxC" if "CxC" in seg_tipo_dlg.get() else "CxP"
            entidad = entry_entidad.get().strip()
            concepto = entry_concepto.get().strip()
            monto_str = entry_monto.get().strip().replace(",", ".")

            if not entidad or not concepto:
                messagebox.showwarning("Campos Requeridos", "Debe ingresar el Cliente/Proveedor y el Concepto.")
                return

            try:
                monto = float(monto_str)
                if monto <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Monto Inválido", "Por favor ingrese un monto numérico positivo.")
                return

            emision = entry_emision.get().strip() or hoy_str
            vencimiento = entry_venc.get().strip() or hoy_str
            status = combo_status.get()
            notas = entry_notas.get().strip()

            resp = self.agent.record_cxc_cxp({
                "type": tipo_sel,
                "entity_name": entidad,
                "concept": concepto,
                "amount_usd": monto,
                "issue_date": emision,
                "due_date": vencimiento,
                "status": status,
                "notes": notas
            })

            if resp.success:
                dlg.destroy()
                self.actualizar_datos()
                messagebox.showinfo("Registro Exitoso", resp.message)
            else:
                messagebox.showerror("Error", resp.message)

        btn_save = ctk.CTkButton(
            dlg,
            text="💾 Guardar Cuenta",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=_guardar
        )
        btn_save.pack(fill="x", padx=20, pady=(16, 12))
