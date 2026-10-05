"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: SERVICIO TÉCNICO Y TALLER
Módulo: ui_view.py
Descripción: Interfaz gráfica CustomTkinter para Banco de Pruebas,
             Diagnósticos Guiados por IA y Órdenes de Servicio Técnico.
=============================================================================
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_05_servicio_tecnico_taller.tech_diagnostics_agent import TechDiagnosticsAgent


class ServicioTecnicoView(ctk.CTkFrame):
    """Panel unificado del Departamento de Servicio Técnico y Taller."""

    def __init__(self, master, agent: TechDiagnosticsAgent = None):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.agent = agent or TechDiagnosticsAgent()

        self._init_ui()
        self._cargar_ordenes_taller()

    def _init_ui(self):
        # 1. Cabecera Departamental
        header = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="🛠️ SERVICIO TÉCNICO Y TALLER", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Banco de Pruebas Especializado (Epson, HP, Canon, Samsung) y Órdenes de Reparación", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # 2. Pestañas
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_DARK, segmented_button_selected_color=Theme.PRIMARY)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_diag = self.tabview.add("🩺 Estación de Diagnóstico IA")
        self.tab_ordenes = self.tabview.add("📋 Órdenes de Taller y Banco de Pruebas")

        self._build_tab_diagnostico()
        self._build_tab_ordenes()

    # -------------------------------------------------------------------------
    # PESTAÑA 1: DIAGNÓSTICO TÉCNICO ASISTIDO POR IA
    # -------------------------------------------------------------------------
    def _build_tab_diagnostico(self):
        tab = self.tab_diag
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)

        # Panel Izquierdo: Formulario de Entrada de Síntomas
        left_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        left_box.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(left_box, text="Datos del Equipo y Falla", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(left_box, text="Marca del Equipo:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.combo_marca = ctk.CTkComboBox(left_box, values=["Epson", "HP", "Canon", "Samsung", "Otra Marca"], state="readonly")
        self.combo_marca.set("Epson")
        self.combo_marca.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left_box, text="Modelo Específico:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_modelo = ctk.CTkEntry(left_box, placeholder_text="Ej: EcoTank L3250 / LaserJet M141w")
        self.entry_modelo.pack(fill="x", padx=15, pady=3)
        self.entry_modelo.insert(0, "EcoTank L3250")

        ctk.CTkLabel(left_box, text="Síntomas Reportados o Código de Error:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.txt_sintomas = ctk.CTkTextbox(left_box, height=100, font=Theme.FONT_BODY, fg_color=Theme.INPUT_BG)
        self.txt_sintomas.pack(fill="x", padx=15, pady=3)
        self.txt_sintomas.insert("1.0", "Luces de tinta y papel parpadean alternadas. El software indica que una almohadilla de tinta ha llegado al final de su vida útil.")

        self.btn_ejecutar_diag = ctk.CTkButton(
            left_box,
            text="🩺 Ejecutar Diagnóstico de Alta Precisión",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PURPLE,
            hover_color=Theme.PURPLE_HOVER,
            command=self._iniciar_diagnostico_thread
        )
        self.btn_ejecutar_diag.pack(fill="x", padx=15, pady=(15, 10))

        # Panel Derecho: Procedimiento y Dictamen de Taller
        right_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        right_box.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        ctk.CTkLabel(right_box, text="Dictamen Técnico, Procedimiento Paso a Paso y Repuestos", font=Theme.FONT_SUBTITLE, text_color=Theme.PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))

        self.txt_diag_output = ctk.CTkTextbox(right_box, font=Theme.FONT_BODY, fg_color=Theme.INPUT_BG)
        self.txt_diag_output.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.txt_diag_output.insert("1.0", "Selecciona el equipo, describe los síntomas y presiona 'Ejecutar Diagnóstico'.\nEl sistema elaborará la causa raíz, pasos de desarmado/calibración y lista de piezas requeridas.")

    def _iniciar_diagnostico_thread(self):
        marca = self.combo_marca.get()
        modelo = self.entry_modelo.get().strip()
        sintomas = self.txt_sintomas.get("1.0", "end").strip()

        if not modelo or not sintomas:
            messagebox.showwarning("Atención", "Por favor completa el modelo y los síntomas de la falla.")
            return

        self.btn_ejecutar_diag.configure(state="disabled")
        self.txt_diag_output.delete("1.0", "end")
        self.txt_diag_output.insert("1.0", "Analizando tolerancias mecánicas, circuito y banco de pruebas con IA...\n")

        def _task():
            res = self.agent.execute("diagnose_equipment", {
                "brand": marca,
                "model": modelo,
                "symptoms": sintomas
            })
            self.after(0, self._render_diagnostico, res)

        threading.Thread(target=_task, daemon=True).start()

    def _render_diagnostico(self, res):
        self.btn_ejecutar_diag.configure(state="normal")
        self.txt_diag_output.delete("1.0", "end")
        if res.success:
            self.txt_diag_output.insert("1.0", res.data.get("diagnosis_text", ""))
        else:
            self.txt_diag_output.insert("1.0", f"Error: {res.message}")

    # -------------------------------------------------------------------------
    # PESTAÑA 2: ÓRDENES DE TALLER
    # -------------------------------------------------------------------------
    def _build_tab_ordenes(self):
        tab = self.tab_ordenes
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)

        # Formulario de Ingreso a Taller
        left_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        left_box.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="nsew")

        ctk.CTkLabel(left_box, text="Ingreso de Equipo a Taller", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(left_box, text="Nombre del Cliente:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_job_client = ctk.CTkEntry(left_box, placeholder_text="Nombre / Razón Social")
        self.entry_job_client.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(left_box, text="Teléfono:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_job_phone = ctk.CTkEntry(left_box, placeholder_text="0424-XXXXXXX")
        self.entry_job_phone.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(left_box, text="Equipo / Modelo:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_job_equip = ctk.CTkEntry(left_box, placeholder_text="Ej: Epson L3110 o HP LaserJet 107w")
        self.entry_job_equip.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(left_box, text="Falla Reportada:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_job_falla = ctk.CTkEntry(left_box, placeholder_text="Ej: No toma papel / Rayas negras")
        self.entry_job_falla.pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(left_box, text="Costo Estimado Presupuestado ($):", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=15, pady=(4, 0))
        self.entry_job_cost = ctk.CTkEntry(left_box, placeholder_text="25.00")
        self.entry_job_cost.pack(fill="x", padx=15, pady=2)

        btn_ingresar_taller = ctk.CTkButton(
            left_box,
            text="📥 Registrar Entrada a Taller",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=self._registrar_orden_ui
        )
        btn_ingresar_taller.pack(fill="x", padx=15, pady=(12, 10))

        # Tabla de Órdenes en Taller
        right_box = ctk.CTkFrame(tab, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        right_box.grid(row=0, column=1, padx=(8, 0), pady=5, sticky="nsew")

        top_ctrl = ctk.CTkFrame(right_box, fg_color="transparent")
        top_ctrl.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(top_ctrl, text="Equipos en Banco de Pruebas y Taller", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(side="left")

        btn_cambiar_estado = ctk.CTkButton(
            top_ctrl,
            text="✅ Cambiar Estado a Reparado",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._marcar_reparado_ui
        )
        btn_cambiar_estado.pack(side="right")

        scroll = ttk.Scrollbar(right_box, orient="vertical")
        cols = ("id", "fecha", "cliente", "equipo", "costo", "estado")
        self.tree_jobs = ttk.Treeview(right_box, columns=cols, show="headings", yscrollcommand=scroll.set)
        scroll.config(command=self.tree_jobs.yview)

        self.tree_jobs.heading("id", text="N° Orden")
        self.tree_jobs.heading("fecha", text="Fecha")
        self.tree_jobs.heading("cliente", text="Cliente")
        self.tree_jobs.heading("equipo", text="Equipo")
        self.tree_jobs.heading("costo", text="Costo ($)")
        self.tree_jobs.heading("estado", text="Estado")

        self.tree_jobs.column("id", width=80, anchor="center")
        self.tree_jobs.column("fecha", width=115, anchor="center")
        self.tree_jobs.column("cliente", width=120)
        self.tree_jobs.column("equipo", width=130)
        self.tree_jobs.column("costo", width=70, anchor="e")
        self.tree_jobs.column("estado", width=120, anchor="center")

        self.tree_jobs.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    def _registrar_orden_ui(self):
        cli = self.entry_job_client.get().strip()
        tel = self.entry_job_phone.get().strip()
        eq = self.entry_job_equip.get().strip()
        falla = self.entry_job_falla.get().strip()
        cost_str = self.entry_job_cost.get().strip()

        if not cli or not eq:
            messagebox.showwarning("Atención", "Por favor ingresa al menos el cliente y el equipo.")
            return

        try:
            cost = float(cost_str.replace(",", ".")) if cost_str else 0.0
        except ValueError:
            cost = 0.0

        resp = self.agent.execute("register_repair_job", {
            "client_name": cli,
            "client_phone": tel,
            "brand": eq,
            "symptoms": falla,
            "cost_usd": cost
        })

        if resp.success:
            self.entry_job_client.delete(0, "end")
            self.entry_job_phone.delete(0, "end")
            self.entry_job_equip.delete(0, "end")
            self.entry_job_falla.delete(0, "end")
            self.entry_job_cost.delete(0, "end")
            self._cargar_ordenes_taller()
            messagebox.showinfo("Éxito", resp.message)

    def _marcar_reparado_ui(self):
        sel = self.tree_jobs.selection()
        if not sel:
            messagebox.showinfo("Información", "Selecciona una orden de la lista para actualizar su estado.")
            return

        vals = self.tree_jobs.item(sel[0], "values")
        if vals:
            job_id = vals[0]
            self.agent.execute("update_job_status", {"job_id": job_id, "status": "Reparado - Listo para Entrega"})
            self._cargar_ordenes_taller()
            messagebox.showinfo("Actualizado", f"La orden {job_id} ha sido marcada como Reparada.")

    def _cargar_ordenes_taller(self):
        for it in self.tree_jobs.get_children():
            self.tree_jobs.delete(it)

        jobs = self.agent._load_workshop_jobs()
        for j in reversed(jobs):
            self.tree_jobs.insert("", "end", values=(
                j.get("job_id", ""),
                j.get("created_at", ""),
                j.get("client_name", ""),
                j.get("equipment", ""),
                f"${float(j.get('estimated_cost_usd', 0.0)):,.2f}",
                j.get("status", "")
            ))
