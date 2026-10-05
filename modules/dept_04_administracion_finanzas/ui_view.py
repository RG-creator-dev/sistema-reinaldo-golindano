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

        # 3. Contenedor Inferior: Formulario + Tabla del Libro Mayor
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=15, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=2)
        main_content.grid_rowconfigure(0, weight=1)

        # Formulario de Registro
        form_frame = ctk.CTkFrame(main_content, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        form_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew", pady=5)

        ctk.CTkLabel(form_frame, text="Nueva Transacción", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 4))

        # Tipo de Operación
        ctk.CTkLabel(form_frame, text="Tipo de Movimiento:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(2, 0))
        self.seg_tipo = ctk.CTkSegmentedButton(form_frame, values=["Ingreso", "Gasto"], selected_color=Theme.PRIMARY)
        self.seg_tipo.set("Ingreso")
        self.seg_tipo.pack(fill="x", padx=15, pady=2)

        # Monto en USD
        ctk.CTkLabel(form_frame, text="Monto (USD):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(2, 0))
        self.entry_monto = ctk.CTkEntry(form_frame, placeholder_text="0.00", font=Theme.FONT_BODY)
        self.entry_monto.pack(fill="x", padx=15, pady=2)

        # Método de Pago
        ctk.CTkLabel(form_frame, text="Método de Pago:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(2, 0))
        self.combo_metodo = ctk.CTkComboBox(
            form_frame,
            values=["Pago Móvil", "Transferencia Bancaria", "Binance USDT", "Efectivo USD", "Efectivo Bs"],
            state="readonly"
        )
        self.combo_metodo.set("Pago Móvil")
        self.combo_metodo.pack(fill="x", padx=15, pady=2)

        # Categoría
        ctk.CTkLabel(form_frame, text="Categoría:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(2, 0))
        self.combo_categoria = ctk.CTkComboBox(
            form_frame,
            values=["Servicio Técnico", "Venta de Tóner/Insumos", "Compra Repuestos", "Gastos Operativos", "Flete Zoom Casilleros", "Otros"],
            state="readonly"
        )
        self.combo_categoria.set("Servicio Técnico")
        self.combo_categoria.pack(fill="x", padx=15, pady=2)

        # Descripción / Referencia
        ctk.CTkLabel(form_frame, text="Descripción / N° Referencia:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(2, 0))
        self.entry_desc = ctk.CTkEntry(form_frame, placeholder_text="Ej: Mantenimiento L3250 Ref: 8934", font=Theme.FONT_BODY)
        self.entry_desc.pack(fill="x", padx=15, pady=2)

        # Botón Guardar (con márgenes equilibrados para verse completo)
        btn_guardar = ctk.CTkButton(
            form_frame,
            text="💾 Registrar en Libro Mayor",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self.registrar_transaccion
        )
        btn_guardar.pack(fill="x", padx=15, pady=(12, 12))

        # Tabla del Libro Mayor
        table_container = ctk.CTkFrame(main_content, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        table_container.grid(row=0, column=1, sticky="nsew", pady=5)

        ctk.CTkLabel(table_container, text="Libro Mayor (Movimientos Contables)", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(12, 8))

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

    def actualizar_balance(self):
        """Actualiza las tarjetas de totales y recarga la tabla contable."""
        res = self.agent.execute("get_financial_summary", {})
        if res.success:
            d = res.data
            rate = d.get("bcv_rate", 1.0)
            self.lbl_bcv_rate.configure(text=f"Tasa BCV: {rate:,.2f} Bs/USD")
            
            # Mostrar Saldo Inicial
            ini_usd = d.get("initial_balance_usd", 0.0)
            ini_bs = d.get("initial_balance_bs", 0.0)
            self.lbl_val_saldo_inicial.configure(text=f"${ini_usd:,.2f} | {ini_bs:,.2f} Bs")

            # Mostrar Totales
            self.lbl_val_ingresos.configure(text=f"${d['total_income_usd']:,.2f} | {d['total_income_bs']:,.2f} Bs")
            self.lbl_val_egresos.configure(text=f"${d['total_expense_usd']:,.2f} | {d['total_expense_bs']:,.2f} Bs")
            self.lbl_val_balance.configure(text=f"${d['net_balance_usd']:,.2f} | {d['net_balance_bs']:,.2f} Bs")

            # Limpiar y rellenar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)

            ledger = self.agent._load_ledger()
            for r in reversed(ledger):
                self.tree.insert("", "end", values=(
                    r.get("date", ""),
                    r.get("type", ""),
                    f"${r.get('amount_usd', 0.0):,.2f}",
                    f"{r.get('amount_bs', 0.0):,.2f} Bs",
                    r.get("method", ""),
                    r.get("description", "")
                ))