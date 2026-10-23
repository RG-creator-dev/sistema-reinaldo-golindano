"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: ui_view.py
Descripción: Vista gráfica CustomTkinter para control financiero, Libro Mayor,
             Saldo Inicial y tasa oficial del Banco Central de Venezuela (BCV).
=============================================================================
"""

import threading
import tkinter as tk
from datetime import datetime, date
from tkinter import ttk, messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider


class AdminFinanzasView(ctk.CTkFrame):
    """Panel de control del Departamento de Administración y Finanzas."""

    def __init__(self, master, agent: AccountingAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or AccountingAgent()
        # Período activo: tupla (year, month) — mes actual por defecto
        _hoy = date.today()
        self._periodo_seleccionado = (_hoy.year, _hoy.month)

        self._init_ui()
        self.actualizar_balance()

    def _init_ui(self):
        # 1. Cabecera y Tasa BCV
        header_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(
            title_box,
            text="🏛️ ADMINISTRACIÓN Y FINANZAS",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Control de Caja, Conciliación Cripto (Binance USDT) y Libro Mayor",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Widget destacado de la Tasa BCV
        bcv_box = ctk.CTkFrame(header_frame, fg_color=Theme.BG_DARK, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        bcv_box.pack(side="right", padx=15, pady=10)

        self.lbl_bcv_rate = ctk.CTkLabel(
            bcv_box,
            text="Tasa BCV: Consultando...",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.SUCCESS
        )
        self.lbl_bcv_rate.pack(side="left", padx=10, pady=5)

        btn_refresh_bcv = ctk.CTkButton(
            bcv_box,
            text="🔄 Actualizar",
            width=80,
            height=28,
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self.forzar_actualizacion_bcv
        )
        btn_refresh_bcv.pack(side="right", padx=10, pady=5)

        # Botón discreto "+ Nueva Transacción" en la cabecera
        btn_nueva_tx = ctk.CTkButton(
            bcv_box,
            text="+ Nueva Transacción",
            width=155,
            height=28,
            font=Theme.FONT_SMALL,
            fg_color=Theme.CARD_BORDER,
            hover_color=Theme.PRIMARY,
            command=self.abrir_dialogo_transaccion
        )
        btn_nueva_tx.pack(side="right", padx=(10, 4), pady=5)

        # 2. Tarjetas de Resumen Financiero (4 Tarjetas: Saldo Inicial, Ingresos, Gastos, Balance Neto)
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=15, pady=5)
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Tarjeta Saldo Inicial
        self.card_saldo_inicial = ctk.CTkFrame(cards_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_saldo_inicial.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_saldo_inicial, text="SALDO INICIAL CAJA", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_val_saldo_inicial = ctk.CTkLabel(self.card_saldo_inicial, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN)
        self.lbl_val_saldo_inicial.pack(pady=(0, 2))
        
        btn_editar_saldo = ctk.CTkButton(
            self.card_saldo_inicial,
            text="✏️ Configurar",
            width=90,
            height=24,
            font=("Segoe UI", 8, "bold"),
            fg_color=Theme.CARD_BORDER,
            hover_color=Theme.PRIMARY,
            command=self.dialogo_saldo_inicial
        )
        btn_editar_saldo.pack(pady=(0, 8))

        # Tarjeta Ingresos
        self.card_ingresos = ctk.CTkFrame(cards_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_ingresos.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_ingresos, text="TOTAL INGRESOS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_val_ingresos = ctk.CTkLabel(self.card_ingresos, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.SUCCESS)
        self.lbl_val_ingresos.pack(pady=(0, 31))  # Espaciado equilibrado con la tarjeta vecina

        # Tarjeta Egresos
        self.card_egresos = ctk.CTkFrame(cards_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_egresos.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_egresos, text="TOTAL GASTOS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_val_egresos = ctk.CTkLabel(self.card_egresos, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.DANGER)
        self.lbl_val_egresos.pack(pady=(0, 31))

        # Tarjeta Balance Neto
        self.card_balance = ctk.CTkFrame(cards_frame, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        self.card_balance.grid(row=0, column=3, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_balance, text="BALANCE NETO EN CAJA", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_val_balance = ctk.CTkLabel(self.card_balance, text="$0.00 | 0.00 Bs", font=Theme.FONT_SUBTITLE, text_color=Theme.PRIMARY)
        self.lbl_val_balance.pack(pady=(0, 31))

        # 3. Contenedor Principal: Tabla del Libro Mayor (ancho completo)
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=15, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        # Tabla del Libro Mayor
        table_container = ctk.CTkFrame(main_content, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        table_container.grid(row=0, column=0, sticky="nsew", pady=5)

        # ── Barra de cabecera de la tabla: título + selector de período ──
        table_header = ctk.CTkFrame(table_container, fg_color="transparent")
        table_header.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            table_header,
            text="Libro Mayor (Movimientos Contables)",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        # Selector de período (combo derecho)
        periodo_right = ctk.CTkFrame(table_header, fg_color="transparent")
        periodo_right.pack(side="right")

        ctk.CTkLabel(
            periodo_right,
            text="Período:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 6))

        self._periodo_opciones = self._generar_opciones_periodo()
        self.combo_periodo = ctk.CTkComboBox(
            periodo_right,
            values=self._periodo_opciones,
            width=160,
            state="readonly",
            command=self._on_cambio_periodo
        )
        # Seleccionar el mes actual (primer elemento = más reciente)
        self.combo_periodo.set(self._periodo_opciones[0])
        self.combo_periodo.pack(side="left")

        # Etiqueta decorativa que muestra el período activo junto a la tabla
        self.lbl_periodo_activo = ctk.CTkLabel(
            table_container,
            text="",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_periodo_activo.pack(anchor="w", padx=15, pady=(0, 6))

        # Estilo de Treeview nativo de Tkinter integrado con paleta oscura
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=Theme.INPUT_BG, foreground=Theme.TEXT_MAIN, fieldbackground=Theme.INPUT_BG, rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=Theme.CARD_BORDER, foreground=Theme.TEXT_MAIN, font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", Theme.PRIMARY)])

        tree_scroll = ttk.Scrollbar(table_container, orient="vertical")
        columns = ("fecha", "tipo", "usd", "bs", "metodo", "descripcion")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("usd", text="Monto ($)")
        self.tree.heading("bs", text="Monto (Bs)")
        self.tree.heading("metodo", text="Método")
        self.tree.heading("descripcion", text="Descripción")

        self.tree.column("fecha", width=125, anchor="center")
        self.tree.column("tipo", width=70, anchor="center")
        self.tree.column("usd", width=85, anchor="e")
        self.tree.column("bs", width=110, anchor="e")
        self.tree.column("metodo", width=120, anchor="center")
        self.tree.column("descripcion", width=220)

        self.tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        tree_scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    def forzar_actualizacion_bcv(self):
        """Consulta en segundo plano la tasa oficial más reciente del BCV."""
        def _task():
            bcv = BCVExchangeRateProvider.get_official_rate(force_refresh=True)
            self.after(0, self._render_bcv, bcv)

        threading.Thread(target=_task, daemon=True).start()

    def _render_bcv(self, bcv_info):
        rate = bcv_info.get("rate", 0.0)
        self.lbl_bcv_rate.configure(text=f"Tasa BCV: {rate:,.2f} Bs/USD ({bcv_info.get('status', 'OK')})")
        self.actualizar_balance()

    def dialogo_saldo_inicial(self):
        """Abre una ventana emergente para configurar o actualizar el saldo inicial de caja."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Configurar Saldo Inicial")
        dialog.geometry("340x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Establecer Saldo Inicial (USD):", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(pady=(20, 5))
        
        entry = ctk.CTkEntry(dialog, placeholder_text="0.00", font=Theme.FONT_BODY, width=200)
        entry.pack(pady=5)

        def guardar():
            val_str = entry.get().strip().replace(",", ".")
            try:
                val = float(val_str)
                if val < 0:
                    raise ValueError()
                # Llamada al agente contable para actualizar el saldo inicial
                resp = self.agent.execute("set_initial_balance", {"initial_balance_usd": val})
                if resp.success:
                    messagebox.showinfo("Éxito", "Saldo inicial actualizado correctamente.")
                    dialog.destroy()
                    self.actualizar_balance()
                else:
                    messagebox.showerror("Error", resp.message)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico válido.")

        btn_save = ctk.CTkButton(dialog, text="Guardar Saldo", fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, command=guardar)
        btn_save.pack(pady=(10, 15))

    def abrir_dialogo_transaccion(self):
        """Abre un modal flotante con el formulario de registro de transacción."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Transacción")
        dialog.geometry("420x380")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Registrar Nueva Transacción", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 8))

        # Tipo de Movimiento
        ctk.CTkLabel(dialog, text="Tipo de Movimiento:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        seg_tipo_dlg = ctk.CTkSegmentedButton(dialog, values=["Ingreso", "Gasto"], selected_color=Theme.PRIMARY)
        seg_tipo_dlg.set("Ingreso")
        seg_tipo_dlg.pack(fill="x", padx=20, pady=2)

        # Monto en USD
        ctk.CTkLabel(dialog, text="Monto (USD):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        entry_monto_dlg = ctk.CTkEntry(dialog, placeholder_text="0.00", font=Theme.FONT_BODY)
        entry_monto_dlg.pack(fill="x", padx=20, pady=2)

        # Método de Pago
        ctk.CTkLabel(dialog, text="Método de Pago:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        combo_metodo_dlg = ctk.CTkComboBox(
            dialog,
            values=["Pago Móvil", "Transferencia Bancaria", "Binance USDT", "Efectivo USD", "Efectivo Bs"],
            state="readonly"
        )
        combo_metodo_dlg.set("Pago Móvil")
        combo_metodo_dlg.pack(fill="x", padx=20, pady=2)

        # Categoría
        ctk.CTkLabel(dialog, text="Categoría:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        combo_cat_dlg = ctk.CTkComboBox(
            dialog,
            values=["Servicio Técnico", "Venta de Tóner/Insumos", "Compra Repuestos", "Gastos Operativos", "Flete Zoom Casilleros", "Otros"],
            state="readonly"
        )
        combo_cat_dlg.set("Servicio Técnico")
        combo_cat_dlg.pack(fill="x", padx=20, pady=2)

        # Descripción / Referencia
        ctk.CTkLabel(dialog, text="Descripción / N° Referencia:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        entry_desc_dlg = ctk.CTkEntry(dialog, placeholder_text="Ej: Mantenimiento L3250 Ref: 8934", font=Theme.FONT_BODY)
        entry_desc_dlg.pack(fill="x", padx=20, pady=2)

        def _guardar():
            monto_str = entry_monto_dlg.get().strip()
            desc = entry_desc_dlg.get().strip()
            if not monto_str:
                messagebox.showwarning("Atención", "Por favor ingresa un monto válido.")
                return
            try:
                monto = float(monto_str.replace(",", "."))
                if monto <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un valor numérico positivo.")
                return

            tipo = seg_tipo_dlg.get()
            metodo = combo_metodo_dlg.get()
            categoria = combo_cat_dlg.get()

            resp = self.agent.execute("record_transaction", {
                "type": tipo,
                "amount_usd": monto,
                "method": metodo,
                "category": categoria,
                "description": desc or f"Registro de {tipo.lower()}"
            })
            if resp.success:
                dialog.destroy()
                self.actualizar_balance()
                messagebox.showinfo("Éxito", resp.message)
            else:
                messagebox.showerror("Error", resp.message)

        ctk.CTkButton(
            dialog,
            text="💾 Registrar en Libro Mayor",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=_guardar
        ).pack(fill="x", padx=20, pady=(14, 16))

    def registrar_transaccion(self):
        monto_str = self.entry_monto.get().strip()
        desc = self.entry_desc.get().strip()
        if not monto_str:
            messagebox.showwarning("Atención", "Por favor ingresa un monto válido.")
            return

        try:
            monto = float(monto_str.replace(",", "."))
            if monto <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un valor numérico positivo.")
            return

        tipo = self.seg_tipo.get()
        metodo = self.combo_metodo.get()
        categoria = self.combo_categoria.get()

        resp = self.agent.execute("record_transaction", {
            "type": tipo,
            "amount_usd": monto,
            "method": metodo,
            "category": categoria,
            "description": desc or f"Registro de {tipo.lower()}"
        })

        if resp.success:
            self.entry_monto.delete(0, "end")
            self.entry_desc.delete(0, "end")
            self.actualizar_balance()
            messagebox.showinfo("Éxito", resp.message)
        else:
            messagebox.showerror("Error", resp.message)

    # ─── Helpers de período ───────────────────────────────────────────────────

    _MESES_ES = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def _generar_opciones_periodo(self, ventana_meses: int = 24) -> list:
        """Genera lista de períodos 'Mes YYYY' desde el mes actual hacia atrás."""
        hoy = date.today()
        opciones = []
        for delta in range(ventana_meses):
            # Retroceder mes a mes
            m = hoy.month - delta
            y = hoy.year
            while m <= 0:
                m += 12
                y -= 1
            opciones.append(f"{self._MESES_ES[m]} {y}")
        return opciones

    def _parse_periodo(self, texto: str):
        """Convierte 'Octubre 2026' -> (2026, 10). Retorna None si falla."""
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
        """Callback del combo de período: actualiza estado y refresca vista."""
        parsed = self._parse_periodo(seleccion)
        if parsed:
            self._periodo_seleccionado = parsed
        self.actualizar_balance()

    # ─── Balance y tabla ──────────────────────────────────────────────────────

    def actualizar_balance(self):
        """Actualiza tarjetas de totales y tabla contable filtradas por período."""
        res = self.agent.execute("get_financial_summary", {})
        if not res.success:
            return

        d = res.data
        rate = d.get("bcv_rate", 1.0)
        self.lbl_bcv_rate.configure(text=f"Tasa BCV: {rate:,.2f} Bs/USD")

        # Saldo Inicial (global, no filtrado por período)
        ini_usd = d.get("initial_balance_usd", 0.0)
        ini_bs  = d.get("initial_balance_bs",  0.0)
        self.lbl_val_saldo_inicial.configure(text=f"${ini_usd:,.2f} | {ini_bs:,.2f} Bs")

        # ── Filtrar ledger por el período seleccionado ──
        year_sel, month_sel = self._periodo_seleccionado
        ledger = self.agent._load_ledger()

        registros_periodo = []
        for r in ledger:
            fecha_str = r.get("date", "")
            try:
                # Soporta formatos "YYYY-MM-DD HH:MM:SS" y "YYYY-MM-DD"
                dt = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                if dt.year == year_sel and dt.month == month_sel:
                    registros_periodo.append(r)
            except (ValueError, TypeError):
                pass

        # ── Helpers de clasificación: insensible a mayúsculas y sinónimos ──
        def _es_ingreso(tipo: str) -> bool:
            return tipo.strip().lower() in ("ingreso",)

        def _es_gasto(tipo: str) -> bool:
            return tipo.strip().lower() in ("gasto", "egreso")

        # ── Recalcular totales del período ──
        total_ing_usd = sum(r.get("amount_usd", 0.0) for r in registros_periodo if _es_ingreso(r.get("type", "")))
        total_gst_usd = sum(r.get("amount_usd", 0.0) for r in registros_periodo if _es_gasto(r.get("type", "")))
        net_usd       = ini_usd + total_ing_usd - total_gst_usd

        total_ing_bs = sum(r.get("amount_bs", 0.0) for r in registros_periodo if _es_ingreso(r.get("type", "")))
        total_gst_bs = sum(r.get("amount_bs", 0.0) for r in registros_periodo if _es_gasto(r.get("type", "")))
        net_bs       = ini_bs + total_ing_bs - total_gst_bs

        self.lbl_val_ingresos.configure(text=f"${total_ing_usd:,.2f} | {total_ing_bs:,.2f} Bs")
        self.lbl_val_egresos.configure(text=f"${total_gst_usd:,.2f} | {total_gst_bs:,.2f} Bs")
        self.lbl_val_balance.configure(text=f"${net_usd:,.2f} | {net_bs:,.2f} Bs")

        # ── Etiqueta de período activo ──
        nombre_mes = self._MESES_ES[month_sel]
        n = len(registros_periodo)
        self.lbl_periodo_activo.configure(
            text=f"Mostrando {n} movimiento{'s' if n != 1 else ''} de {nombre_mes} {year_sel}"
        )

        # ── Poblar tabla ──
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in reversed(registros_periodo):
            tipo      = r.get("type", "")
            es_gasto  = _es_gasto(tipo)
            tag       = "gasto" if es_gasto else "ingreso"
            signo     = "-" if es_gasto else ""
            usd_val   = r.get("amount_usd", 0.0)
            bs_val    = r.get("amount_bs",  0.0)
            self.tree.insert("", "end", tags=(tag,), values=(
                r.get("date", ""),
                tipo,
                f"{signo}${usd_val:,.2f}",
                f"{signo}{bs_val:,.2f} Bs",
                r.get("method", ""),
                r.get("description", "")
            ))

        self.tree.tag_configure("ingreso", foreground="#4ade80")
        self.tree.tag_configure("gasto",   foreground="#f87171")