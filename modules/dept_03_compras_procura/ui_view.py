"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: ui_view.py
Descripción: Interfaz gráfica CustomTkinter integrada con Rastreador Web Global,
             Calculadora Zoom Casilleros y Panel Analista de Compras.
=============================================================================
"""

import re
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_03_compras_procura.web_scraper import GlobalWebScraper
from modules.dept_03_compras_procura.supply_audit_agent import SupplyAuditAgent


class ComprasProcuraView(ctk.CTkFrame):
    """Panel unificado del Departamento de Compras y Procura."""

    def __init__(self, master, agent: SupplyAuditAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or SupplyAuditAgent()
        self.motor_web = GlobalWebScraper()

        self._init_ui()
        self._cargar_tabla_inventario()

    def _init_ui(self):
        # 1. Cabecera Departamental
        header = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="📦 COMPRAS Y PROCURA", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Rastreador Web Global, Logística Zoom Casilleros y Panel Analista de Suministros", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # 2. Pestañas
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_DARK, segmented_button_selected_color=Theme.PRIMARY)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_scraper = self.tabview.add("🌐 Rastreador Web & Zoom Casilleros")
        self.tab_analista = self.tabview.add("📊 Panel Analista de Compras e Inventario")

        self._build_tab_scraper()
        self._build_tab_analista()

    # -------------------------------------------------------------------------
    # PESTAÑA 1: RASTREADOR WEB GLOBAL & ZOOM CASILLEROS
    # -------------------------------------------------------------------------
    def _build_tab_scraper(self):
        tab = self.tab_scraper

        search_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        search_box.pack(fill="x", padx=10, pady=5)

        # Fila 1: Producto
        f1 = ctk.CTkFrame(search_box, fg_color="transparent")
        f1.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(f1, text="Producto / Suministro a Rastrear:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="left", padx=(0, 10))
        self.entry_web_query = ctk.CTkEntry(f1, width=320, font=Theme.FONT_BODY)
        self.entry_web_query.pack(side="left", padx=5)
        self.entry_web_query.insert(0, "Toner HP CE285A 85A")

        self.btn_web_buscar = ctk.CTkButton(
            f1,
            text="🔍 Buscar en la Web",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self._iniciar_busqueda_web_thread
        )
        self.btn_web_buscar.pack(side="left", padx=10)

        # Fila 2: Parámetros (Ámbito y Casillero Zoom)
        f2 = ctk.CTkFrame(search_box, fg_color="transparent")
        f2.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(f2, text="Ámbito de Búsqueda:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="left", padx=(0, 5))
        self.combo_ambito = ctk.CTkComboBox(f2, values=["Nacional", "Internacional", "Ambos"], state="readonly", width=130)
        self.combo_ambito.set("Nacional")
        self.combo_ambito.pack(side="left", padx=5)

        self.var_zoom = ctk.BooleanVar(value=False)
        self.chk_zoom = ctk.CTkCheckBox(f2, text="Calcular Importación (Zoom Casilleros: $5.50/lb + $5 manejo)", variable=self.var_zoom, font=Theme.FONT_BODY)
        self.chk_zoom.pack(side="left", padx=20)

        # Estado
        self.lbl_web_status = ctk.CTkLabel(tab, text="Estado: Listo para buscar.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        self.lbl_web_status.pack(anchor="w", padx=15, pady=2)

        # Área de Resultados con Enlaces Clicables
        res_frame = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        res_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        ctk.CTkLabel(res_frame, text="Dictamen de Costos, Proveedores e Importación (IA)", font=Theme.FONT_SUBTITLE, text_color=Theme.PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))

        # Cuadro de texto tkinter para soporte nativo de hipervínculos
        text_container = tk.Frame(res_frame, bg=Theme.INPUT_BG)
        text_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        scroll = ttk.Scrollbar(text_container, orient="vertical")
        self.txt_web_result = tk.Text(
            text_container,
            wrap="word",
            bg=Theme.INPUT_BG,
            fg=Theme.TEXT_MAIN,
            font=("Segoe UI", 10),
            yscrollcommand=scroll.set,
            relief="flat"
        )
        scroll.config(command=self.txt_web_result.yview)

        self.txt_web_result.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Configuración de estilo para etiquetas de enlace
        self.txt_web_result.tag_config("link", foreground="#38bdf8", underline=True)
        self.txt_web_result.tag_bind("link", "<Enter>", lambda e: self.txt_web_result.config(cursor="hand2"))
        self.txt_web_result.tag_bind("link", "<Leave>", lambda e: self.txt_web_result.config(cursor=""))

        self.txt_web_result.insert("1.0", "Ingresa un insumo o repuesto y presiona 'Buscar en la Web'.\nEl sistema consultará proveedores, comparará precios y calculará fletes si seleccionas Zoom Casilleros.")
        self.txt_web_result.config(state="disabled")

    def _iniciar_busqueda_web_thread(self):
        query = self.entry_web_query.get().strip()
        if not query:
            messagebox.showwarning("Atención", "Por favor ingresa un producto a buscar.")
            return

        self.btn_web_buscar.configure(state="disabled")
        self.lbl_web_status.configure(text="Ejecutando rastreo web abierto y análisis de compras...", text_color=Theme.PRIMARY)

        self.txt_web_result.config(state="normal")
        self.txt_web_result.delete("1.0", "end")
        self.txt_web_result.insert("1.0", "Consultando proveedores y evaluando mejores costos en tiempo real...\nEspere unos instantes.\n")
        self.txt_web_result.config(state="disabled")

        def _task():
            ambito = self.combo_ambito.get()
            importar = self.var_zoom.get()
            hallazgos = self.motor_web.buscar_sitios_web(query, ambito=ambito)
            dictamen = self.motor_web.analizar_con_gemini_v2(query, hallazgos, ambito=ambito, incluye_importacion=importar)
            self.after(0, self._render_web_dictamen, dictamen)

        threading.Thread(target=_task, daemon=True).start()

    def _render_web_dictamen(self, dictamen: str):
        self.btn_web_buscar.configure(state="normal")
        self.lbl_web_status.configure(text="Rastreo y dictamen completados con éxito.", text_color=Theme.SUCCESS)

        self.txt_web_result.config(state="normal")
        self.txt_web_result.delete("1.0", "end")

        # Parser de URLs para crear hipervínculos interactivos
        url_pattern = re.compile(r'(https?://[^\s\)\],]+)')
        pos = 0
        tag_count = 0

        for match in url_pattern.finditer(dictamen):
            start, end = match.span()
            url = match.group(0)

            if start > pos:
                self.txt_web_result.insert("end", dictamen[pos:start])

            tag_name = f"link_{tag_count}"
            tag_count += 1
            self.txt_web_result.insert("end", url, ("link", tag_name))
            self.txt_web_result.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            pos = end

        if pos < len(dictamen):
            self.txt_web_result.insert("end", dictamen[pos:])

        self.txt_web_result.config(state="disabled")

    # -------------------------------------------------------------------------
    # PESTAÑA 2: PANEL ANALISTA DE COMPRAS E INVENTARIO
    # -------------------------------------------------------------------------
    def _build_tab_analista(self):
        tab = self.tab_analista
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Formulario de Registro de Insumos
        left_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        left_box.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(left_box, text="Registrar Insumo / Repuesto", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(left_box, text="SKU / Código:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_sku = ctk.CTkEntry(left_box, placeholder_text="Ej: TON-HP-85A")
        self.entry_sku.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left_box, text="Nombre del Insumo:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_nombre = ctk.CTkEntry(left_box, placeholder_text="Ej: Tóner HP 85A CE285A")
        self.entry_nombre.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left_box, text="Categoría Técnica:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.combo_cat_insumo = ctk.CTkComboBox(
            left_box,
            values=["Tóner Láser", "Tintas / Cabezales", "Almohadillas Epson", "Fusor / Películas", "Rodillos / Pick Up", "Engranajes / Mecánica"],
            state="readonly"
        )
        self.combo_cat_insumo.set("Tóner Láser")
        self.combo_cat_insumo.pack(fill="x", padx=15, pady=3)

        f_nums = ctk.CTkFrame(left_box, fg_color="transparent")
        f_nums.pack(fill="x", padx=15, pady=3)
        f_nums.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(f_nums, text="Stock Inicial:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self.entry_stock = ctk.CTkEntry(f_nums, placeholder_text="5")
        self.entry_stock.grid(row=1, column=0, padx=(0, 4), pady=2, sticky="ew")

        ctk.CTkLabel(f_nums, text="Stock Mínimo:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).grid(row=0, column=1, sticky="w")
        self.entry_min_stock = ctk.CTkEntry(f_nums, placeholder_text="2")
        self.entry_min_stock.grid(row=1, column=1, padx=(4, 0), pady=2, sticky="ew")

        ctk.CTkLabel(left_box, text="Costo Unitario Ref ($):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_costo = ctk.CTkEntry(left_box, placeholder_text="12.50")
        self.entry_costo.pack(fill="x", padx=15, pady=3)

        btn_agregar_insumo = ctk.CTkButton(
            left_box,
            text="➕ Registrar Insumo en Stock",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._registrar_insumo_ui
        )
        btn_agregar_insumo.pack(fill="x", padx=15, pady=(12, 6))

        btn_auditar = ctk.CTkButton(
            left_box,
            text="🔍 Auditar Stock Crítico",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.WARNING,
            hover_color="#d97706",
            command=self._auditar_stock_ui
        )
        btn_auditar.pack(fill="x", padx=15, pady=(0, 10))

        # Panel Derecho: Tabla de Inventario de Suministros
        right_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        right_box.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(right_box, text="Inventario de Repuestos y Suministros del Taller", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        inv_scroll = ttk.Scrollbar(right_box, orient="vertical")
        cols = ("sku", "nombre", "categoria", "stock", "min", "costo")
        self.tree_inv = ttk.Treeview(right_box, columns=cols, show="headings", yscrollcommand=inv_scroll.set)
        inv_scroll.config(command=self.tree_inv.yview)

        self.tree_inv.heading("sku", text="SKU")
        self.tree_inv.heading("nombre", text="Insumo / Repuesto")
        self.tree_inv.heading("categoria", text="Categoría")
        self.tree_inv.heading("stock", text="Stock")
        self.tree_inv.heading("min", text="Mín.")
        self.tree_inv.heading("costo", text="Costo ($)")

        self.tree_inv.column("sku", width=95, anchor="center")
        self.tree_inv.column("nombre", width=180)
        self.tree_inv.column("categoria", width=120)
        self.tree_inv.column("stock", width=55, anchor="center")
        self.tree_inv.column("min", width=55, anchor="center")
        self.tree_inv.column("costo", width=70, anchor="e")

        self.tree_inv.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        inv_scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    def _registrar_insumo_ui(self):
        sku = self.entry_sku.get().strip()
        nombre = self.entry_nombre.get().strip()
        cat = self.combo_cat_insumo.get()
        stock_str = self.entry_stock.get().strip()
        min_str = self.entry_min_stock.get().strip()
        costo_str = self.entry_costo.get().strip()

        if not sku or not nombre:
            messagebox.showwarning("Atención", "Por favor completa el SKU y el nombre del insumo.")
            return

        try:
            stock = int(stock_str) if stock_str else 0
            min_stk = int(min_str) if min_str else 2
            costo = float(costo_str.replace(",", ".")) if costo_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "Los valores de stock y costo deben ser numéricos.")
            return

        resp = self.agent.execute("register_purchase", {
            "sku": sku,
            "name": nombre,
            "category": cat,
            "stock": stock,
            "min_stock": min_stk,
            "cost_usd": costo,
            "supplier": "Nacional / Importación"
        })

        if resp.success:
            self.entry_sku.delete(0, "end")
            self.entry_nombre.delete(0, "end")
            self.entry_stock.delete(0, "end")
            self.entry_costo.delete(0, "end")
            self._cargar_tabla_inventario()
            messagebox.showinfo("Éxito", resp.message)

    def _auditar_stock_ui(self):
        res = self.agent.execute("audit_inventory", {})
        if res.success:
            crit = res.data.get("critical_items", [])
            if crit:
                nombres = "\n".join([f"• {x['name']} (Stock: {x['current_stock']} / Mín: {x['min_stock']})" for x in crit])
                messagebox.showwarning("Alerta de Stock Crítico", f"Los siguientes insumos requieren reposición urgente:\n\n{nombres}")
            else:
                messagebox.showinfo("Auditoría Óptima", "Todos los suministros se encuentran por encima del umbral mínimo.")

    def _cargar_tabla_inventario(self):
        for it in self.tree_inv.get_children():
            self.tree_inv.delete(it)

        inv = self.agent._load_inventory()
        for r in inv:
            self.tree_inv.insert("", "end", values=(
                r.get("sku", ""),
                r.get("name", ""),
                r.get("category", ""),
                r.get("current_stock", 0),
                r.get("min_stock", 2),
                f"${float(r.get('cost_usd', 0.0)):,.2f}"
            ))
