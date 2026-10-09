"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: ui/main_window.py
Descripción: Ventana principal CustomTkinter con menú lateral navegable,
             widgets de control cambiario BCV (esquina inferior izquierda y
             esquina superior derecha con botón de actualización), orquestación
             unificada y sincronización automática en la nube (Render).
=============================================================================
"""

import os
import threading
from datetime import datetime
import customtkinter as ctk
from config import SystemConfig
from core.logger import app_logger
from core.cloud_sync import cloud_sync
from core.event_bus import event_bus
from ui.theme import Theme

# Importación de Agentes Centrales
from modules.dept_01_direccion_general.orchestrator_agent import OrchestratorAgent
from modules.dept_02_comercio_ventas.quote_catalog_agent import QuoteCatalogAgent
from modules.dept_02_comercio_ventas.b2b_marketing_agent import B2BMarketingAgent
from modules.dept_03_compras_procura.supply_audit_agent import SupplyAuditAgent
from modules.dept_04_administracion_finanzas.accounting_agent import AccountingAgent
from modules.dept_05_servicio_tecnico_taller.tech_diagnostics_agent import TechDiagnosticsAgent
from modules.dept_04_administracion_finanzas.payment_gateways import BCVExchangeRateProvider

# Importación de Vistas Departamentales
from modules.dept_01_direccion_general.ui_view import DireccionGeneralView
from modules.dept_02_comercio_ventas.ui_view import ComercioVentasView
from modules.dept_03_compras_procura.ui_view import ComprasProcuraView
from modules.dept_04_administracion_finanzas.ui_view import AdminFinanzasView
from modules.dept_05_servicio_tecnico_taller.ui_view import ServicioTecnicoView
from modules.dept_02_comercio_ventas.telegram_voice_bot import telegram_controller


class MainWindow(ctk.CTk):
    """Ventana Maestra del Sistema de Gestión de Inversiones Reinaldo Golindano."""

    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Inversiones Reinaldo Golindano")
        self.geometry("1280x820")
        self.minsize(1100, 720)
        ctk.set_appearance_mode("dark")

        # Icono de la aplicación
        icon_path = os.path.join(SystemConfig.BASE_DIR, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Inicializar y orquestar agentes departamentales
        self._init_agents()

        # Iniciar servicio concurrente del Bot de Telegram en hilo secundario permanente
        self._start_telegram_daemon()

        # Configurar cierre seguro de hilos
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Layout general (Sidebar a la izquierda, Panel Central a la derecha)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_dept_code = "dept_01"
        self.current_view = None

        self._build_sidebar()
        self._build_main_area()

        # Cargar Dirección General por defecto
        self.navigate_to("dept_01")

        # Iniciar sincronización automática con Render en segundo plano
        if getattr(SystemConfig, "AUTO_SYNC_ON_STARTUP", True):
            self._start_cloud_sync_daemon()

        # Suscribir eventos del EventBus
        event_bus.subscribe("cloud_sync_completed", self._on_cloud_sync_completed_event)

    def _start_telegram_daemon(self):
        """Inicia el bot de Telegram en modo local únicamente si está habilitado expresamente en la configuración."""
        if getattr(SystemConfig, "ENABLE_LOCAL_TELEGRAM_POLLING", False):
            try:
                telegram_controller.start()
                app_logger.info("Servicio local del Bot de Telegram (@InversionesRG_bot) activado para pruebas locales.")
            except Exception as e:
                app_logger.error(f"Error iniciando bot de Telegram en modo local: {e}", exc_info=True)
        else:
            app_logger.info("Bot de Telegram operando centralmente en la Nube (Render). Escucha local desactivada para evitar conflicto 409.")

    def _on_close(self):
        """Detiene de forma ordenada los servicios en segundo plano antes de destruir la ventana."""
        app_logger.info("Cerrando aplicación y finalizando servicios en segundo plano...")
        try:
            if telegram_controller.is_active:
                telegram_controller.stop()
        except Exception as e:
            app_logger.warning(f"Aviso al detener bot en cierre: {e}")
        self.destroy()

    def _init_agents(self):
        """Instancia los agentes y los enlaza al Orquestador Central."""
        self.orchestrator = OrchestratorAgent()
        self.quote_agent = QuoteCatalogAgent()
        self.b2b_agent = B2BMarketingAgent()
        self.supply_agent = SupplyAuditAgent()
        self.accounting_agent = AccountingAgent()
        self.tech_agent = TechDiagnosticsAgent()

        # Registrar agentes en Dirección General
        self.orchestrator.register_agent("b2b_marketing", self.b2b_agent)
        self.orchestrator.register_agent("quote_catalog", self.quote_agent)
        self.orchestrator.register_agent("supply_audit", self.supply_agent)
        self.orchestrator.register_agent("accounting", self.accounting_agent)
        self.orchestrator.register_agent("tech_diagnostics", self.tech_agent)

        app_logger.info("Todos los agentes departamentales han sido enlazados con el Orquestador Central.")

    def _build_sidebar(self):
        """Construye el menú de navegación lateral con los 5 departamentos y el indicador BCV inferior izquierdo."""
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=Theme.SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Encabezado de Marca
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=15, pady=(20, 15))

        ctk.CTkLabel(
            brand_frame,
            text="INVERSIONES\nREINALDO GOLINDANO",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
            justify="center"
        ).pack(fill="x")

        ctk.CTkLabel(
            brand_frame,
            text="Sistema Integral de Gestión",
            font=Theme.FONT_SMALL,
            text_color=Theme.PRIMARY,
            justify="center"
        ).pack(fill="x", pady=(2, 0))

        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=Theme.CARD_BORDER)
        sep.pack(fill="x", padx=15, pady=5)

        # Botones de Navegación para los 5 Departamentos
        self.nav_buttons = {}
        dept_specs = [
            ("dept_01", "👑 Dirección General", lambda: DireccionGeneralView(self.container, self.orchestrator)),
            ("dept_02", "💼 Comercio y Ventas", lambda: ComercioVentasView(self.container, self.quote_agent)),
            ("dept_03", "📦 Compras y Procura", lambda: ComprasProcuraView(self.container, self.supply_agent)),
            ("dept_04", "🏛️ Adm. y Finanzas", lambda: AdminFinanzasView(self.container, self.accounting_agent)),
            ("dept_05", "🛠️ Servicio Técnico", lambda: ServicioTecnicoView(self.container, self.tech_agent))
        ]

        for code, label, factory in dept_specs:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=Theme.FONT_BODY_BOLD,
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=Theme.TEXT_MUTED,
                hover_color=Theme.CARD_BG,
                command=lambda c=code, f=factory: self.navigate_to(c, f)
            )
            btn.pack(pady=4, padx=12, fill="x")
            self.nav_buttons[code] = (btn, factory)

        # ---------------------------------------------------------------------
        # FOOTER INFERIOR IZQUIERDO: Ventana indicadora de Tasa BCV y Versión
        # ---------------------------------------------------------------------
        footer = ctk.CTkFrame(self.sidebar, fg_color=Theme.CARD_BG, corner_radius=8, border_width=1, border_color=Theme.CARD_BORDER)
        footer.pack(side="bottom", fill="x", padx=12, pady=15)

        bcv = BCVExchangeRateProvider.get_official_rate()
        self.lbl_sidebar_bcv = ctk.CTkLabel(
            footer,
            text=f"💵 BCV: {bcv['rate']:,.2f} Bs",
            font=Theme.FONT_SMALL,
            text_color=Theme.SUCCESS
        )
        self.lbl_sidebar_bcv.pack(pady=(6, 2))

        self.lbl_sidebar_source = ctk.CTkLabel(
            footer,
            text=f"🏛️ {bcv.get('fuente', 'Oficial')}",
            font=("Segoe UI", 8),
            text_color=Theme.TEXT_DIM
        )
        self.lbl_sidebar_source.pack(pady=(0, 2))

        ctk.CTkLabel(
            footer,
            text=f"v{SystemConfig.APP_VERSION} • Producción",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_DIM
        ).pack(pady=(0, 6))

    def _build_main_area(self):
        """Construye el área principal con la barra superior de control cambiario/sincronización y el contenedor."""
        self.main_area = ctk.CTkFrame(self, fg_color=Theme.BG_DARK, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Barra Superior Maestra
        self._build_top_bar()

        # Contenedor dinámico de vistas departamentales
        self.container = ctk.CTkFrame(self.main_area, fg_color=Theme.BG_DARK, corner_radius=0)
        self.container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _build_top_bar(self):
        """
        Construye la barra superior fija que incluye:
        - Título / Módulo activo y estado del sistema.
        - Botón de Sincronización en la Nube con Render.
        - VENTANA INDICADORA BCV SUPERIOR DERECHA con botón interactivo de actualización ('Actualizar').
        """
        self.top_bar = ctk.CTkFrame(self.main_area, fg_color=Theme.CARD_BG, height=58, corner_radius=0, border_width=1, border_color=Theme.CARD_BORDER)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar.grid_propagate(False)

        # Lado Izquierdo: Título y Estado
        left_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        left_box.pack(side="left", padx=15, pady=8)

        self.lbl_top_title = ctk.CTkLabel(
            left_box,
            text="👑 DIRECCIÓN GENERAL",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_top_title.pack(side="left", padx=(0, 10))

        self.lbl_cloud_status = ctk.CTkLabel(
            left_box,
            text="☁️ Render: Listo",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_cloud_status.pack(side="left")

        # Lado Derecho: Sincronización Render y Widget BCV Superior Derecho
        right_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        right_box.pack(side="right", padx=15, pady=6)

        # Botón de Sincronización con Render
        self.btn_sync_render = ctk.CTkButton(
            right_box,
            text="☁️ Sincronizar",
            width=105,
            height=32,
            font=Theme.FONT_SMALL,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.forzar_sincronizacion_render
        )
        self.btn_sync_render.pack(side="left", padx=(0, 12))

        # ---------------------------------------------------------------------
        # WIDGET INDICADOR DE CONTROL CAMBIARIO (BCV) - ESQUINA SUPERIOR DERECHA
        # ---------------------------------------------------------------------
        self.bcv_top_box = ctk.CTkFrame(
            right_box,
            fg_color=Theme.BG_DARK,
            corner_radius=8,
            border_width=1,
            border_color=Theme.CARD_BORDER
        )
        self.bcv_top_box.pack(side="left")

        bcv = BCVExchangeRateProvider.get_official_rate()

        bcv_labels_frame = ctk.CTkFrame(self.bcv_top_box, fg_color="transparent")
        bcv_labels_frame.pack(side="left", padx=(10, 8), pady=4)

        self.lbl_top_bcv = ctk.CTkLabel(
            bcv_labels_frame,
            text=f"💵 BCV Oficial: {bcv['rate']:,.2f} Bs/USD",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.SUCCESS
        )
        self.lbl_top_bcv.pack(anchor="w")

        self.lbl_top_bcv_date = ctk.CTkLabel(
            bcv_labels_frame,
            text=f"📅 {bcv.get('fecha', 'Hoy')} • Banco Central de Venezuela",
            font=("Segoe UI", 8),
            text_color=Theme.TEXT_DIM
        )
        self.lbl_top_bcv_date.pack(anchor="w")

        # Botón Interactivo de Actualización BCV
        self.btn_refresh_bcv = ctk.CTkButton(
            self.bcv_top_box,
            text="🔄 Actualizar",
            width=88,
            height=30,
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=lambda: self.actualizar_tasa_bcv(force_refresh=True)
        )
        self.btn_refresh_bcv.pack(side="left", padx=(0, 8), pady=4)

    def actualizar_tasa_bcv(self, force_refresh: bool = True):
        """
        Consulta en segundo plano la tasa oficial más reciente del BCV y actualiza
        instantáneamente tanto el widget superior derecho como el inferior izquierdo.
        """
        self.btn_refresh_bcv.configure(state="disabled", text="⏳...")
        self.lbl_top_bcv.configure(text="💵 BCV: Consultando...", text_color=Theme.PRIMARY)

        def _task():
            bcv_info = BCVExchangeRateProvider.get_official_rate(force_refresh=force_refresh)
            self.after(0, self._render_bcv_actualizado, bcv_info)

        threading.Thread(target=_task, daemon=True).start()

    def _render_bcv_actualizado(self, bcv_info: dict):
        self.btn_refresh_bcv.configure(state="normal", text="🔄 Actualizar")
        rate = bcv_info.get("rate", 0.0)
        fecha = bcv_info.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        fuente = bcv_info.get("fuente", "Oficial")

        # Actualizar Widget Superior Derecho
        self.lbl_top_bcv.configure(text=f"💵 BCV Oficial: {rate:,.2f} Bs/USD", text_color=Theme.SUCCESS)
        self.lbl_top_bcv_date.configure(text=f"📅 {fecha} • {fuente}")

        # Actualizar Widget Inferior Izquierdo
        self.lbl_sidebar_bcv.configure(text=f"💵 BCV: {rate:,.2f} Bs")
        self.lbl_sidebar_source.configure(text=f"🏛️ {fuente}")

        # Si la vista actual es Finanzas o Dirección, refrescar sus datos
        self._refrescar_vista_activa()

    def _start_cloud_sync_daemon(self):
        """Lanza la sincronización automática en segundo plano con el servidor Render."""
        self.lbl_cloud_status.configure(text="☁️ Render: Sincronizando...", text_color=Theme.PRIMARY)

        def _task():
            res = cloud_sync.sync_from_cloud()
            self.after(0, self._render_cloud_sync_result, res)

        threading.Thread(target=_task, daemon=True, name="RenderAutoSyncThread").start()

    def forzar_sincronizacion_render(self):
        """Permite al usuario sincronizar manualmente en cualquier momento con un clic."""
        self.btn_sync_render.configure(state="disabled", text="⏳ Sincronizando...")
        self.lbl_cloud_status.configure(text="☁️ Conectando a Render...", text_color=Theme.PRIMARY)

        def _task():
            res = cloud_sync.sync_from_cloud()
            self.after(0, self._render_cloud_sync_result, res, True)

        threading.Thread(target=_task, daemon=True).start()

    def _render_cloud_sync_result(self, res: dict, is_manual: bool = False):
        self.btn_sync_render.configure(state="normal", text="☁️ Sincronizar")
        
        if res.get("success"):
            new_trx = res.get("new_transactions", 0)
            new_q = res.get("new_quotes", 0)
            new_w = res.get("new_workshop", 0)
            status_txt = f"☁️ Render: Sincronizado (+{new_trx} trx, +{new_q} cot)" if (new_trx or new_q) else "☁️ Render: Sincronizado (Al día)"
            self.lbl_cloud_status.configure(
                text=status_txt,
                text_color=Theme.SUCCESS
            )
            self._refrescar_vista_activa()
            if is_manual:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Sincronización en la Nube (Render)",
                    f"¡Sincronización completada con éxito!\n\n"
                    f"• Transacciones / Comprobantes nuevos: {new_trx}\n"
                    f"• Cotizaciones remotas integradas: {new_q}\n"
                    f"• Órdenes de taller actualizadas: {new_w}\n\n"
                    f"Todos los registros creados remotamente se han volcado en la base local del escritorio."
                )
        else:
            msg = res.get("message", "Sin conexión")
            self.lbl_cloud_status.configure(
                text=f"☁️ Render: {msg[:30]}",
                text_color=Theme.WARNING
            )
            if is_manual:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Aviso de Sincronización",
                    f"No se pudo completar la consulta al servidor de Render:\n\n{msg}\n\n"
                    f"Verifique la conexión a internet o que el servicio de Render se encuentre activo."
                )

    def _on_cloud_sync_completed_event(self, data: dict):
        """Manejador de evento de sincronización completada."""
        self._refrescar_vista_activa()

    def _refrescar_vista_activa(self):
        """Notifica a la vista activa que refresque sus tablas, KPIs o balances."""
        try:
            if self.current_view:
                if hasattr(self.current_view, "actualizar_kpis"):
                    self.current_view.actualizar_kpis()
                elif hasattr(self.current_view, "actualizar_balance"):
                    self.current_view.actualizar_balance()
                elif hasattr(self.current_view, "_cargar_historial_cotizaciones"):
                    self.current_view._cargar_historial_cotizaciones()
        except Exception as e:
            app_logger.warning(f"Aviso actualizando vista activa: {e}")

    def navigate_to(self, dept_code: str, factory=None):
        """Cambia fluidamente entre las vistas de los 5 departamentos."""
        self.current_dept_code = dept_code

        # Limpiar contenedor
        for child in self.container.winfo_children():
            child.destroy()

        dept_titles = {
            "dept_01": "👑 DIRECCIÓN GENERAL",
            "dept_02": "💼 COMERCIO Y VENTAS",
            "dept_03": "📦 COMPRAS Y PROCURA",
            "dept_04": "🏛️ ADMINISTRACIÓN Y FINANZAS",
            "dept_05": "🛠️ SERVICIO TÉCNICO Y TALLER"
        }
        self.lbl_top_title.configure(text=dept_titles.get(dept_code, "SISTEMA INTEGRAL"))

        # Actualizar estilos de botones
        for code, (btn, fac) in self.nav_buttons.items():
            if code == dept_code:
                btn.configure(fg_color=Theme.PRIMARY, text_color=Theme.TEXT_MAIN)
                if factory is None:
                    factory = fac
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_MUTED)

        # Instanciar y mostrar vista
        if factory:
            try:
                self.current_view = factory()
                self.current_view.pack(fill="both", expand=True)
                app_logger.info(f"Navegación exitosa a departamento: {dept_code}")
            except Exception as e:
                app_logger.error(f"Error cargando departamento {dept_code}: {e}", exc_info=True)
                err_label = ctk.CTkLabel(
                    self.container,
                    text=f"Error cargando el departamento:\n{e}",
                    text_color=Theme.DANGER,
                    font=Theme.FONT_TITLE
                )
                err_label.pack(expand=True)
