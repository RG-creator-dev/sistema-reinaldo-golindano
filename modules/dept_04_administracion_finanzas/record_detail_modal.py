"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: ADMINISTRACIÓN Y FINANZAS
Módulo: record_detail_modal.py
Descripción: Interfaz de visualización ampliada (Ventana Grande / Modal) para
             examinar en detalle cualquier registro contable del Libro Mayor o
             del módulo de Cuentas por Cobrar (CxC) y Cuentas por Pagar (CxP).
=============================================================================
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import Theme
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent


class RecordDetailModal(ctk.CTkToplevel):
    """
    Ventana flotante de gran tamaño que despliega la información completa,
    detallada y legible de un registro, eliminando restricciones de espacio
    y permitiendo acciones como liquidar en Libro Mayor o copiar datos.
    """

    def __init__(self, master, record: dict, record_type: str = "auto", agent: AccountingAgent = None, on_update_callback = None):
        super().__init__(master)
        self.record = dict(record)
        self.agent = agent or AccountingAgent()
        self.on_update_callback = on_update_callback

        # Auto-detectar tipo de registro si no se especifica
        if record_type == "auto":
            if "type" in self.record and self.record.get("type") in ("CxC", "CxP"):
                self.record_type = "cxc_cxp"
            elif "due_date" in self.record or "entity_name" in self.record:
                self.record_type = "cxc_cxp"
            else:
                self.record_type = "ledger"
        else:
            self.record_type = record_type

        # Configuración de ventana
        self.title("Ficha Técnica y Detalle Ampliado de Registro")
        self.geometry("720x640")
        self.minsize(640, 520)
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        # Centrar en pantalla o sobre la ventana padre
        self.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - 360
            y = master.winfo_rooty() + (master.winfo_height() // 2) - 320
            self.geometry(f"+{max(10, x)}+{max(10, y)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        for child in self.winfo_children():
            child.destroy()

        r = self.record
        rec_id = r.get("id", "N/A")

        # ── 1. Barra de Encabezado Superior ──
        header_frame = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        top_bar = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            top_bar,
            text="🔍 FICHA DE REGISTRO DETALLADA",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        id_box = ctk.CTkFrame(top_bar, fg_color=Theme.BG_DARK, corner_radius=6, border_width=1, border_color=Theme.CARD_BORDER)
        id_box.pack(side="right")
        ctk.CTkLabel(
            id_box,
            text=f"ID: {rec_id}",
            font=Theme.FONT_CODE,
            text_color=Theme.PRIMARY
        ).pack(side="left", padx=10, pady=4)

        # ── 2. Banner de Estado y Clasificación Visual ──
        tipo_str = r.get("type", "Operación")
        es_cxc_cxp = self.record_type == "cxc_cxp"

        if es_cxc_cxp:
            if tipo_str == "CxC":
                banner_color = "#0284c7"
                banner_title = "💰 CUENTA POR COBRAR (CxC) - Cobro Pendiente a Cliente"
            else:
                banner_color = "#f97316"
                banner_title = "🧾 CUENTA POR PAGAR (CxP) - Compromiso con Proveedor"
            status_val = r.get("status", "Pendiente")
        else:
            if tipo_str.lower() == "ingreso":
                banner_color = Theme.SUCCESS
                banner_title = "📈 MOVIMIENTO DE INGRESO - Entrada en Caja"
            else:
                banner_color = Theme.DANGER
                banner_title = "📉 MOVIMIENTO DE GASTO / EGRESO - Salida de Caja"
            status_val = "Asentado en Libro Mayor"

        banner_frame = ctk.CTkFrame(self, fg_color=banner_color, corner_radius=8)
        banner_frame.pack(fill="x", padx=16, pady=4)

        b_content = ctk.CTkFrame(banner_frame, fg_color="transparent")
        b_content.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(
            b_content,
            text=banner_title,
            font=Theme.FONT_BODY_BOLD,
            text_color="#ffffff"
        ).pack(side="left")

        # Badge de Estatus a la derecha
        badge_bg = "#ffffff"
        if status_val == "Pagado" or status_val == "Asentado en Libro Mayor":
            badge_fg = "#15803d"
        elif status_val == "Abonado":
            badge_fg = "#7c3aed"
        else:
            badge_fg = "#b45309"

        st_badge = ctk.CTkLabel(
            b_content,
            text=f"● {status_val.upper()}",
            font=("Segoe UI", 9, "bold"),
            text_color=badge_fg,
            fg_color=badge_bg,
            corner_radius=6,
            padx=10,
            pady=2
        )
        st_badge.pack(side="right")

        # ── 3. Caja de Montos Destacados ($ USD y Bolívares Bs a tasa BCV) ──
        amount_usd = float(r.get("amount_usd", 0.0))
        bcv_rate = float(r.get("bcv_rate", 0.0))
        amount_bs = float(r.get("amount_bs", 0.0))
        if amount_bs <= 0 and bcv_rate > 0:
            amount_bs = round(amount_usd * bcv_rate, 2)

        amounts_card = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        amounts_card.pack(fill="x", padx=16, pady=6)
        amounts_card.grid_columnconfigure((0, 1, 2), weight=1)

        # USD
        col_usd = ctk.CTkFrame(amounts_card, fg_color="transparent")
        col_usd.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        ctk.CTkLabel(col_usd, text="MONTO EN DÓLARES", font=("Segoe UI", 8, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(col_usd, text=f"${amount_usd:,.2f} USD", font=("Segoe UI", 16, "bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")

        # Bolívares
        col_bs = ctk.CTkFrame(amounts_card, fg_color="transparent")
        col_bs.grid(row=0, column=1, padx=12, pady=10, sticky="ew")
        ctk.CTkLabel(col_bs, text="MONTO EN BOLÍVARES (BCV)", font=("Segoe UI", 8, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(col_bs, text=f"{amount_bs:,.2f} Bs", font=("Segoe UI", 16, "bold"), text_color=Theme.SUCCESS).pack(anchor="w")

        # Tasa BCV
        col_bcv = ctk.CTkFrame(amounts_card, fg_color="transparent")
        col_bcv.grid(row=0, column=2, padx=12, pady=10, sticky="ew")
        ctk.CTkLabel(col_bcv, text="TASA OFICIAL BCV DEL DÍA", font=("Segoe UI", 8, "bold"), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        tasa_str = f"{bcv_rate:,.2f} Bs/USD" if bcv_rate > 0 else "Consultando tasa"
        ctk.CTkLabel(col_bcv, text=tasa_str, font=Theme.FONT_BODY_BOLD, text_color=Theme.PRIMARY).pack(anchor="w")

        # ── 4. Matriz de Datos Clave (Campos de entrada y detalles) ──
        body_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        body_scroll.pack(fill="both", expand=True, padx=16, pady=4)

        info_card = ctk.CTkFrame(body_scroll, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        info_card.pack(fill="x", pady=4)
        info_card.grid_columnconfigure((0, 1), weight=1)

        # Campos dinámicos según el tipo de registro
        if es_cxc_cxp:
            entity_label = "👤 Cliente:" if tipo_str == "CxC" else "🏢 Proveedor:"
            entity_val = r.get("entity_name", "Sin especificar")

            issue_dt = r.get("issue_date", "N/A")
            due_dt = r.get("due_date", "N/A")
            
            # Cálculo de estado de vencimiento
            vencimiento_extra = ""
            if status_val != "Pagado" and due_dt and due_dt != "N/A":
                try:
                    d_obj = datetime.strptime(str(due_dt)[:10], "%Y-%m-%d").date()
                    hoy = datetime.now().date()
                    delta = (d_obj - hoy).days
                    if delta < 0:
                        vencimiento_extra = f" (⚠️ ¡VENCIDA hace {abs(delta)} días!)"
                    elif delta == 0:
                        vencimiento_extra = " (⏰ ¡Vence hoy!)"
                    else:
                        vencimiento_extra = f" (⏳ Quedan {delta} días)"
                except Exception:
                    pass

            fields_left = [
                (entity_label, entity_val, Theme.TEXT_MAIN, True),
                ("📅 Fecha de Emisión:", str(issue_dt), Theme.TEXT_MAIN, False),
                ("⏰ Fecha de Vencimiento:", f"{due_dt}{vencimiento_extra}", Theme.DANGER if "VENCIDA" in vencimiento_extra else Theme.TEXT_MAIN, False)
            ]

            metodo = r.get("payment_method", "Pendiente")
            ledger_ref = r.get("ledger_trx_id") or "Sin asentar (Aún no pagada)"
            settled_dt = r.get("settled_at") or "Pendiente de liquidación"

            fields_right = [
                ("💳 Método de Pago:", metodo, Theme.TEXT_MAIN, False),
                ("🔗 Referencia Libro Mayor:", ledger_ref, Theme.SUCCESS if r.get("ledger_trx_id") else Theme.TEXT_MUTED, False),
                ("⏱️ Fecha de Liquidación:", settled_dt, Theme.TEXT_MAIN, False)
            ]
        else:
            fecha_op = r.get("date", "N/A")
            categoria = r.get("category", "General")
            metodo = r.get("method", "Pago Móvil")
            ref_code = r.get("ref_code", "") or "Sin N° Referencia"

            fields_left = [
                ("📅 Fecha y Hora de Operación:", str(fecha_op), Theme.TEXT_MAIN, False),
                ("🏷️ Categoría Financiera:", categoria, Theme.TEXT_MAIN, True),
                ("💳 Método de Pago:", metodo, Theme.TEXT_MAIN, False)
            ]

            fields_right = [
                ("🔢 N° de Referencia / Ticket:", ref_code, Theme.PRIMARY, True),
                ("🏛️ Fuente Tasa Cambiaria:", "Banco Central de Venezuela (BCV)", Theme.TEXT_MAIN, False),
                ("🛡️ Estado en Base de Datos:", "Sincronizado / Persistido", Theme.SUCCESS, False)
            ]

        # Renderizar campos izquierda
        for idx, (label, val, col, is_bold) in enumerate(fields_left):
            f_box = ctk.CTkFrame(info_card, fg_color="transparent")
            f_box.grid(row=idx, column=0, padx=14, pady=6, sticky="ew")
            ctk.CTkLabel(f_box, text=label, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(f_box, text=val, font=Theme.FONT_BODY_BOLD if is_bold else Theme.FONT_BODY, text_color=col, wraplength=280).pack(anchor="w")

        # Renderizar campos derecha
        for idx, (label, val, col, is_bold) in enumerate(fields_right):
            f_box = ctk.CTkFrame(info_card, fg_color="transparent")
            f_box.grid(row=idx, column=1, padx=14, pady=6, sticky="ew")
            ctk.CTkLabel(f_box, text=label, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(f_box, text=val, font=Theme.FONT_BODY_BOLD if is_bold else Theme.FONT_BODY, text_color=col, wraplength=280).pack(anchor="w")

        # ── 5. Área de Concepto / Descripción Completa (Sin recortes ni restricciones) ──
        desc_card = ctk.CTkFrame(body_scroll, fg_color=Theme.CARD_BG, corner_radius=10, border_width=1, border_color=Theme.CARD_BORDER)
        desc_card.pack(fill="x", pady=8)

        ctk.CTkLabel(
            desc_card,
            text="📝 Concepto / Descripción Completa de la Operación:",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=14, pady=(10, 4))

        full_desc = r.get("concept") or r.get("description") or "Sin descripción registrada"
        txt_box = ctk.CTkTextbox(
            desc_card,
            font=("Segoe UI", 10),
            height=75,
            fg_color=Theme.BG_DARK,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.CARD_BORDER
        )
        txt_box.pack(fill="x", padx=14, pady=(0, 10))
        txt_box.insert("1.0", full_desc)
        txt_box.configure(state="disabled")

        # Notas adicionales si existen
        notes = r.get("notes")
        if notes:
            ctk.CTkLabel(
                desc_card,
                text="📌 Observaciones / Notas Internas:",
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", padx=14, pady=(0, 2))
            
            txt_notes = ctk.CTkTextbox(
                desc_card,
                font=("Segoe UI", 9),
                height=45,
                fg_color=Theme.BG_DARK,
                text_color=Theme.TEXT_MUTED,
                border_width=1,
                border_color=Theme.CARD_BORDER
            )
            txt_notes.pack(fill="x", padx=14, pady=(0, 10))
            txt_notes.insert("1.0", notes)
            txt_notes.configure(state="disabled")

        # ── 6. Botones de Acción Inferiores ──
        footer = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, height=54, corner_radius=10)
        footer.pack(fill="x", padx=16, pady=(6, 16))

        footer_inner = ctk.CTkFrame(footer, fg_color="transparent")
        footer_inner.pack(fill="x", padx=14, pady=10)

        # Botón para Copiar Resumen
        btn_copy = ctk.CTkButton(
            footer_inner,
            text="📋 Copiar Datos",
            width=120,
            height=32,
            font=Theme.FONT_SMALL,
            fg_color=Theme.CARD_BORDER,
            hover_color=Theme.PRIMARY,
            command=self._copiar_al_portapapeles
        )
        btn_copy.pack(side="left")

        # Botón de Cerrar
        btn_close = ctk.CTkButton(
            footer_inner,
            text="Cerrar",
            width=100,
            height=32,
            font=Theme.FONT_BODY,
            fg_color=Theme.INPUT_BG,
            hover_color=Theme.CARD_BORDER,
            command=self.destroy
        )
        btn_close.pack(side="right", padx=(8, 0))

        # Si es CxC/CxP y no está pagada, ofrecer botón de liquidación directa
        if es_cxc_cxp and status_val != "Pagado":
            btn_liquidar = ctk.CTkButton(
                footer_inner,
                text="💳 Liquidar y Asentar en Libro Mayor",
                height=32,
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.SUCCESS,
                hover_color=Theme.SUCCESS_HOVER,
                command=self._liquidar_registro
            )
            btn_liquidar.pack(side="right")

    def _copiar_al_portapapeles(self):
        """Copia un resumen estructurado del registro al portapapeles del sistema."""
        r = self.record
        lines = [
            f"=== FICHA DE REGISTRO ({r.get('id', 'N/A')}) ===",
            f"Tipo: {r.get('type', 'Operación')}",
            f"Monto: ${float(r.get('amount_usd', 0.0)):,.2f} USD ({float(r.get('amount_bs', 0.0)):,.2f} Bs)",
            f"Tasa BCV: {float(r.get('bcv_rate', 0.0)):,.2f} Bs/USD",
            f"Cliente/Proveedor: {r.get('entity_name', 'N/A')}",
            f"Concepto: {r.get('concept') or r.get('description', '')}",
            f"Fecha Emisión: {r.get('issue_date') or r.get('date', '')}",
            f"Fecha Vencimiento: {r.get('due_date', 'N/A')}",
            f"Estatus: {r.get('status', 'Asentado')}",
            f"Método de Pago: {r.get('payment_method') or r.get('method', 'N/A')}"
        ]
        text_full = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text_full)
        messagebox.showinfo("Copiado", "Información detallada copiada al portapapeles.")

    def _liquidar_registro(self):
        """Abre un diálogo de liquidación para registrar automáticamente en el Libro Mayor."""
        rec_id = self.record.get("id")
        c_type = self.record.get("type", "CxC")
        entity_name = self.record.get("entity_name", "")
        amount_usd = float(self.record.get("amount_usd", 0.0))

        # Diálogo para seleccionar método de pago y categoría
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirmar Liquidación")
        dlg.geometry("380x320")
        dlg.resizable(False, False)
        dlg.grab_set()

        ctk.CTkLabel(
            dlg,
            text=f"Liquidar {rec_id}",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(15, 4))

        ctk.CTkLabel(
            dlg,
            text=f"{entity_name} • ${amount_usd:,.2f} USD",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Método de Pago
        ctk.CTkLabel(dlg, text="Método de Pago Utilizado:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(2, 0))
        combo_metodo = ctk.CTkComboBox(dlg, values=["Pago Móvil", "Transferencia Bancaria", "Binance USDT", "Efectivo USD", "Efectivo Bs"], state="readonly")
        combo_metodo.set("Pago Móvil")
        combo_metodo.pack(fill="x", padx=20, pady=2)

        # Categoría
        ctk.CTkLabel(dlg, text="Categoría en Libro Mayor:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(6, 0))
        default_cat = "Servicio Técnico" if c_type == "CxC" else "Mercancía"
        combo_cat = ctk.CTkComboBox(dlg, values=["Servicio Técnico", "Ventas / Facturación", "Mercancía", "Servicios", "Sueldos", "Oficina", "Otros"], state="readonly")
        combo_cat.set(default_cat)
        combo_cat.pack(fill="x", padx=20, pady=2)

        # Referencia bancaria
        ctk.CTkLabel(dlg, text="N° de Referencia de Pago:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(6, 0))
        entry_ref = ctk.CTkEntry(dlg, placeholder_text="Ej: 10560 o Ref Pago Móvil")
        entry_ref.pack(fill="x", padx=20, pady=2)

        def _confirmar():
            met = combo_metodo.get()
            cat = combo_cat.get()
            ref_c = entry_ref.get().strip() or rec_id

            resp = self.agent.settle_cxc_cxp({
                "cxc_cxp_id": rec_id,
                "payment_method": met,
                "category": cat,
                "ref_code": ref_c
            })

            dlg.destroy()
            if resp.success:
                messagebox.showinfo("Liquidación Exitosa", resp.message)
                # Actualizar el registro local en el modal y reconstruir
                self.record["status"] = "Pagado"
                self.record["payment_method"] = met
                self.record["ledger_trx_id"] = resp.data.get("ledger_transaction", {}).get("id")
                self.record["settled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._build_ui()
                if self.on_update_callback:
                    self.on_update_callback()
            else:
                messagebox.showerror("Error", resp.message)

        ctk.CTkButton(
            dlg,
            text="💾 Confirmar y Asentar",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            command=_confirmar
        ).pack(fill="x", padx=20, pady=(16, 12))
