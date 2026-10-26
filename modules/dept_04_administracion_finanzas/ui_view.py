"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: ui_view.py
Descripción: Vista gráfica CustomTkinter para control financiero, Libro Mayor,
             Saldo Inicial, tasa oficial del Banco Central de Venezuela (BCV),
             navegación a Vista de Desglose Analítico por categorías, módulo de
             Cuentas por Cobrar (CxC) y Cuentas por Pagar (CxP), visualización
             ampliada de registros en grande y cierre mensual automatizado
             según calendario venezolano (UTC-4).
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
from modules.dept_04_administracion_finanzas.detailed_breakdown_view import DetailedBreakdownView
from modules.dept_04_administracion_finanzas.cxc_cxp_view import CxcCxpView
from modules.dept_04_administracion_finanzas.record_detail_modal import RecordDetailModal


class AdminFinanzasView(ctk.CTkFrame):
    """Panel de control del Departamento de Administración y Finanzas."""

    def __init__(self, master, agent: AccountingAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or AccountingAgent()

        # 1. Automatización de Cierre y Nuevo Mes (Hora Local Venezolana UTC-4)
        self._check_monthly_rollover()

        vz_now = self.agent.get_venezuela_now()
        self._periodo_seleccionado = (vz_now.year, vz_now.month)

        self.vista_actual = "libro_mayor"  # "libro_mayor", "desglose", "cxc_cxp"
        self.desglose_view = None
        self.cxc_cxp_view = None

        self._init_ui()
        self.actualizar_balance()

    def _check_monthly_rollover(self):
        """Ejecuta en segundo plano la verificación de cierre y archivo automático de mes."""
        try:
            rollover_result = self.agent.check_and_perform_monthly_rollover()
            if rollover_result:
                self.after(500, self._notificar_cierre_automatico, rollover_result)
        except Exception:
            pass

    def _notificar_cierre_automatico(self, rollover_result: dict):
        folder = rollover_result.get("folder", "")
        period = rollover_result.get("period", "")
        messagebox.showinfo(
            "Cierre Mensual Automatizado (Calendario Venezolano)",
            f"Se ha detectado el inicio de un nuevo mes calendario según la hora local de Venezuela.\n\n"
            f"• Los datos consolidados del período {period} han sido archivados exitosamente en su Escritorio:\n"
            f"{folder}\n\n"
            f"• El Libro Mayor principal se ha preparado limpio para recibir las nuevas operaciones del mes en curso.\n"
            f"• Todo el histórico del mes cerrado se encuentra respaldado en JSON y CSV (Excel)."
        )

    def _init_ui(self):
        # ── 1. Cabecera y Tasa BCV ──
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
            text="Control de Caja, Conciliación Cripto (Binance USDT), CxC/CxP y Libro Mayor",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Contenedor de Botones y Widget BCV en la Cabecera
        header_right = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_right.pack(side="right", padx=15, pady=10)

        # BOTÓN ESTRATÉGICO 1: Desglose por Categorías
        self.btn_nav_desglose = ctk.CTkButton(
            header_right,
            text="📊 Desglose por Categorías",
            width=180,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.alternar_vista_desglose
        )
        self.btn_nav_desglose.pack(side="right", padx=(8, 0))

        # BOTÓN ESTRATÉGICO 2: Cuentas por Cobrar y por Pagar (CxC / CxP)
        self.btn_nav_cxc_cxp = ctk.CTkButton(
            header_right,
            text="💳 Cuentas CxC / CxP",
            width=165,
            height=30,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.alternar_vista_cxc_cxp
        )
        self.btn_nav_cxc_cxp.pack(side="right", padx=(8, 0))

        # Botón discreto "+ Nueva Transacción"
        btn_nueva_tx = ctk.CTkButton(
            header_right,
            text="+ Nueva Transacción",
            width=145,
            height=30,
            font=Theme.FONT_SMALL,
            fg_color=Theme.CARD_BORDER,
            hover_color=Theme.PRIMARY,
            command=self.abrir_dialogo_transaccion
        )
        btn_nueva_tx.pack(side="right", padx=(8, 0))

        # Widget destacado de la Tasa BCV
        bcv_box = ctk.CTkFrame(header_right, fg_color=Theme.BG_DARK, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        bcv_box.pack(side="right", padx=0)

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

        # ── 2. Contenedor Maestro Intercambiable (Libro Mayor vs Desglose vs CxC/CxP) ──
        self.main_view_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view_container.pack(fill="both", expand=True)

        # Construir la vista tradicional del Libro Mayor (intacta)
        self._build_libro_mayor_view()

    def _build_libro_mayor_view(self):
        """Construye la vista principal del Libro Mayor con sus 4 tarjetas y tabla contable."""
        self.libro_mayor_frame = ctk.CTkFrame(self.main_view_container, fg_color="transparent")
        self.libro_mayor_frame.pack(fill="both", expand=True)

        # ── Tarjetas de Resumen Financiero (4 Tarjetas) ──
        cards_frame = ctk.CTkFrame(self.libro_mayor_frame, fg_color="transparent")
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
        self.lbl_val_ingresos.pack(pady=(0, 31))

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

        # ── Contenedor Principal: Tabla del Libro Mayor (ancho completo) ──
        main_content = ctk.CTkFrame(self.libro_mayor_frame, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=15, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        # Tabla del Libro Mayor
        table_container = ctk.CTkFrame(main_content, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        table_container.grid(row=0, column=0, sticky="nsew", pady=5)

        # ── Barra de cabecera de la tabla: título + botón ver en grande + selector de período + botón respaldo ──
        table_header = ctk.CTkFrame(table_container, fg_color="transparent")
        table_header.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            table_header,
            text="Libro Mayor (Movimientos Contables)",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        # Selector de período y botones
        periodo_right = ctk.CTkFrame(table_header, fg_color="transparent")
        periodo_right.pack(side="right")

        # BOTÓN DE VISUALIZACIÓN AMPLIADA (MODAL / VENTANA GRANDE)
        btn_ver_grande = ctk.CTkButton(
            periodo_right,
            text="🔍 Ver Registro en Grande",
            width=165,
            height=28,
            font=Theme.FONT_BODY_BOLD,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.abrir_registro_seleccionado_grande
        )
        btn_ver_grande.pack(side="left", padx=(0, 10))

        btn_respaldo_rapido = ctk.CTkButton(
            periodo_right,
            text="📥 Respaldar Mes",
            width=115,
            height=28,
            font=Theme.FONT_SMALL,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.exportar_respaldo_rapido
        )
        btn_respaldo_rapido.pack(side="left", padx=(0, 10))

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
            width=150,
            state="readonly",
            command=self._on_cambio_periodo
        )
        # Seleccionar el período activo
        y, m = self._periodo_seleccionado
        nom = f"{self._MESES_ES[m]} {y}"
        if nom in self._periodo_opciones:
            self.combo_periodo.set(nom)
        else:
            self.combo_periodo.set(self._periodo_opciones[0])
        self.combo_periodo.pack(side="left")

        # Etiqueta que muestra el período activo junto a la tabla
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

        # Doble clic en cualquier fila del Libro Mayor abre automáticamente la ficha ampliada en grande
        self.tree.bind("<Double-1>", lambda e: self.abrir_registro_seleccionado_grande())

        self.tree.tag_configure("ingreso", foreground="#4ade80")
        self.tree.tag_configure("gasto",   foreground="#f87171")

    # ─── Alternancia entre Vistas (Libro Mayor, Desglose y CxC / CxP) ─────────

    def alternar_vista_desglose(self):
        """Alterna hacia la Vista de Desglose Analítico por categorías."""
        if self.vista_actual == "desglose":
            self.mostrar_vista_libro_mayor()
        else:
            self.mostrar_vista_desglose()

    def alternar_vista_cxc_cxp(self):
        """Alterna hacia la Vista de Cuentas por Cobrar y por Pagar."""
        if self.vista_actual == "cxc_cxp":
            self.mostrar_vista_libro_mayor()
        else:
            self.mostrar_vista_cxc_cxp()

    def mostrar_vista_desglose(self):
        """Oculta el Libro Mayor/CxC y despliega la Vista de Desglose Analítico por categorías."""
        self.libro_mayor_frame.pack_forget()
        if self.cxc_cxp_view:
            self.cxc_cxp_view.pack_forget()

        if self.desglose_view is None:
            self.desglose_view = DetailedBreakdownView(
                self.main_view_container,
                agent=self.agent,
                on_back_callback=self.mostrar_vista_libro_mayor,
                initial_period=self._periodo_seleccionado
            )
        else:
            self.desglose_view.set_periodo(*self._periodo_seleccionado)

        self.desglose_view.pack(fill="both", expand=True)
        self.vista_actual = "desglose"
        self.btn_nav_desglose.configure(text="📖 Ver Libro Mayor", fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        self.btn_nav_cxc_cxp.configure(text="💳 Cuentas CxC / CxP", fg_color="#0284c7", hover_color="#0369a1")

    def mostrar_vista_cxc_cxp(self):
        """Oculta el Libro Mayor/Desglose y despliega la Vista de Cuentas por Cobrar y por Pagar."""
        self.libro_mayor_frame.pack_forget()
        if self.desglose_view:
            self.desglose_view.pack_forget()

        if self.cxc_cxp_view is None:
            self.cxc_cxp_view = CxcCxpView(
                self.main_view_container,
                agent=self.agent,
                on_back_callback=self.mostrar_vista_libro_mayor
            )
        else:
            self.cxc_cxp_view.actualizar_datos()

        self.cxc_cxp_view.pack(fill="both", expand=True)
        self.vista_actual = "cxc_cxp"
        self.btn_nav_cxc_cxp.configure(text="📖 Ver Libro Mayor", fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        self.btn_nav_desglose.configure(text="📊 Desglose por Categorías", fg_color="#7c3aed", hover_color="#6d28d9")

    def mostrar_vista_libro_mayor(self):
        """Oculta las vistas secundarias y regresa a la vista principal del Libro Mayor."""
        if self.desglose_view:
            self.desglose_view.pack_forget()
        if self.cxc_cxp_view:
            self.cxc_cxp_view.pack_forget()

        self.libro_mayor_frame.pack(fill="both", expand=True)
        self.vista_actual = "libro_mayor"
        self.btn_nav_desglose.configure(text="📊 Desglose por Categorías", fg_color="#7c3aed", hover_color="#6d28d9")
        self.btn_nav_cxc_cxp.configure(text="💳 Cuentas CxC / CxP", fg_color="#0284c7", hover_color="#0369a1")
        self.actualizar_balance()

    # ─── Visualización Ampliada en Grande del Registro Seleccionado ───────────

    def abrir_registro_seleccionado_grande(self):
        """Abre la ficha técnica ampliada del movimiento contable seleccionado en el Libro Mayor."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección requerida", "Por favor seleccione un movimiento de la tabla para ver su ficha ampliada.")
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        fecha_val = values[0]
        desc_val = values[5]
        
        # Buscar el registro completo en el ledger
        ledger = self.agent._load_ledger()
        found_tx = None
        for r in reversed(ledger):
            if str(r.get("date", "")) == fecha_val and str(r.get("description", "")) == desc_val:
                found_tx = r
                break

        if not found_tx:
            usd_clean = values[2].replace("$", "").replace("-", "").replace("+", "").replace(",", "").strip()
            bs_clean = values[3].replace("Bs", "").replace("-", "").replace("+", "").replace(",", "").strip()
            try:
                usd_num = float(usd_clean)
            except Exception:
                usd_num = 0.0
            try:
                bs_num = float(bs_clean)
            except Exception:
                bs_num = 0.0

            found_tx = {
                "id": f"TRX-{int(datetime.now().timestamp())}",
                "date": fecha_val,
                "type": values[1],
                "amount_usd": usd_num,
                "amount_bs": bs_num,
                "method": values[4],
                "description": desc_val,
                "category": "General",
                "bcv_rate": round(bs_num / usd_num, 2) if usd_num > 0 else 0.0
            }

        RecordDetailModal(
            self,
            record=found_tx,
            record_type="ledger",
            agent=self.agent,
            on_update_callback=self.actualizar_balance
        )

    def exportar_respaldo_rapido(self):
        """Exporta de forma inmediata un respaldo en formato JSON y CSV al Escritorio."""
        y, m = self._periodo_seleccionado
        try:
            res = self.agent.export_monthly_backup(y, m)
            messagebox.showinfo(
                "Respaldo en Escritorio Completado",
                f"Respaldo del período {self._MESES_ES[m]} {y} generado exitosamente en su Escritorio:\n\n"
                f"📁 Carpeta:\n{res['folder']}\n\n"
                f"Archivos:\n"
                f"• {res['json_path']}\n"
                f"• {res['csv_path']}"
            )
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo guardar el respaldo en el escritorio:\n{e}")

    # ─── Tasa BCV y Operaciones ──────────────────────────────────────────────

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
        dialog.geometry("340x220")
        dialog.resizable(False, False)
        dialog.grab_set()

        year_sel, month_sel = self._periodo_seleccionado
        nombre_mes = self._MESES_ES[month_sel]

        ctk.CTkLabel(
            dialog,
            text=f"Saldo Inicial para {nombre_mes} {year_sel} (USD):",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN
        ).pack(pady=(20, 5))
        
        current_init = self.agent.get_initial_balance_for_period(year_sel, month_sel)
        entry = ctk.CTkEntry(dialog, font=Theme.FONT_BODY, width=200)
        entry.insert(0, f"{current_init:.2f}")
        entry.pack(pady=5)

        def guardar():
            val_str = entry.get().strip().replace(",", ".")
            try:
                val = float(val_str)
                if val < 0:
                    raise ValueError()
                resp = self.agent.execute("set_initial_balance", {
                    "initial_balance_usd": val,
                    "year": year_sel,
                    "month": month_sel
                })
                if resp.success:
                    messagebox.showinfo("Éxito", f"Saldo inicial para {nombre_mes} {year_sel} actualizado correctamente.")
                    dialog.destroy()
                    self.actualizar_balance()
                    if self.desglose_view:
                        self.desglose_view.actualizar_desglose()
                else:
                    messagebox.showerror("Error", resp.message)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico válido.")

        btn_save = ctk.CTkButton(dialog, text="Guardar Saldo", fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, command=guardar)
        btn_save.pack(pady=(15, 10))

    def abrir_dialogo_transaccion(self):
        """Abre un modal flotante con el formulario de registro de transacción con categorías estandarizadas."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Transacción")
        dialog.geometry("440x410")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Registrar Nueva Transacción", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 6))

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

        # Categoría Financiera Analítica
        ctk.CTkLabel(dialog, text="Categoría Financiera:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(4, 0))
        categorias_opciones = [
            "Moto",
            "Sueldos",
            "Servicios",
            "Gasolina",
            "Comisión Bancaria",
            "Mercancía",
            "Oficina",
            "Herramientas",
            "Servicio Técnico",
            "Ventas / Facturación",
            "Gastos Operativos",
            "Otros"
        ]
        combo_cat_dlg = ctk.CTkComboBox(
            dialog,
            values=categorias_opciones,
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
                if self.desglose_view:
                    self.desglose_view.actualizar_desglose()
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

    # ─── Helpers de Período ───────────────────────────────────────────────────

    _MESES_ES = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def _generar_opciones_periodo(self, ventana_meses: int = 24) -> list:
        """Genera lista de períodos 'Mes YYYY' desde el mes actual hacia atrás."""
        vz = self.agent.get_venezuela_now()
        opciones = []
        for delta in range(ventana_meses):
            m = vz.month - delta
            y = vz.year
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
        if self.desglose_view:
            self.desglose_view.set_periodo(*self._periodo_seleccionado)

    # ─── Balance y Tabla Principal ────────────────────────────────────────────

    def actualizar_balance(self):
        """Actualiza tarjetas de totales y tabla contable filtradas por período."""
        year_sel, month_sel = self._periodo_seleccionado
        res = self.agent.execute("get_financial_summary", {"year": year_sel, "month": month_sel})
        if not res.success:
            return

        d = res.data
        rate = d.get("bcv_rate", 1.0)
        self.lbl_bcv_rate.configure(text=f"Tasa BCV: {rate:,.2f} Bs/USD")

        # Saldo Inicial del período seleccionado
        ini_usd = d.get("initial_balance_usd", 0.0)
        ini_bs  = d.get("initial_balance_bs",  0.0)
        self.lbl_val_saldo_inicial.configure(text=f"${ini_usd:,.2f} | {ini_bs:,.2f} Bs")

        # ── Filtrar ledger por el período seleccionado ──
        ledger = self.agent._load_ledger()

        registros_periodo = []
        for r in ledger:
            fecha_str = str(r.get("date", ""))
            try:
                dt = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                if dt.year == year_sel and dt.month == month_sel:
                    registros_periodo.append(r)
            except (ValueError, TypeError):
                pass

        def _es_ingreso(tipo: str) -> bool:
            return tipo.strip().lower() in ("ingreso",)

        def _es_gasto(tipo: str) -> bool:
            return tipo.strip().lower() in ("gasto", "egreso")

        # Recalcular totales del período
        total_ing_usd = sum(float(r.get("amount_usd", 0.0)) for r in registros_periodo if _es_ingreso(r.get("type", "")))
        total_gst_usd = sum(float(r.get("amount_usd", 0.0)) for r in registros_periodo if _es_gasto(r.get("type", "")))
        net_usd       = ini_usd + total_ing_usd - total_gst_usd

        total_ing_bs = sum(float(r.get("amount_bs", 0.0)) for r in registros_periodo if _es_ingreso(r.get("type", "")))
        total_gst_bs = sum(float(r.get("amount_bs", 0.0)) for r in registros_periodo if _es_gasto(r.get("type", "")))
        net_bs       = ini_bs + total_ing_bs - total_gst_bs

        self.lbl_val_ingresos.configure(text=f"${total_ing_usd:,.2f} | {total_ing_bs:,.2f} Bs")
        self.lbl_val_egresos.configure(text=f"${total_gst_usd:,.2f} | {total_gst_bs:,.2f} Bs")
        self.lbl_val_balance.configure(text=f"${net_usd:,.2f} | {net_bs:,.2f} Bs")

        # Etiqueta de período activo
        nombre_mes = self._MESES_ES[month_sel]
        n = len(registros_periodo)
        self.lbl_periodo_activo.configure(
            text=f"Mostrando {n} movimiento{'s' if n != 1 else ''} de {nombre_mes} {year_sel}"
        )

        # Poblar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in reversed(registros_periodo):
            tipo      = r.get("type", "")
            es_gasto  = _es_gasto(tipo)
            tag       = "gasto" if es_gasto else "ingreso"
            signo     = "-" if es_gasto else ""
            usd_val   = float(r.get("amount_usd", 0.0))
            bs_val    = float(r.get("amount_bs",  0.0))
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
