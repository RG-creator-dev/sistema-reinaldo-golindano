"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: ui/main_window.py
Descripción: Ventana principal CustomTkinter con menú lateral navegable,
             conexión de los 5 departamentos y orquestación unificada de agentes.
=============================================================================
"""

import os
import customtkinter as ctk
from config import SystemConfig
from core.logger import app_logger
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
        self.geometry("1280x800")
        self.minsize(1100, 700)
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

        # Layout general (Sidebar a la izquierda, Contenedor a la derecha)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_container()

        # Cargar Dirección General por defecto
        self.navigate_to("dept_01")

    def _start_telegram_daemon(self):
        """Inicia el bot de Telegram en un hilo secundario dedicado de forma concurrente."""
        try:
            telegram_controller.start()
            app_logger.info("Servicio concurrente del Bot de Telegram (@InversionesRG_bot) activado en segundo plano permanente.")
        except Exception as e:
            app_logger.error(f"Error iniciando bot de Telegram en segundo plano: {e}", exc_info=True)

    def _on_close(self):
        """Detiene de forma ordenada los servicios en segundo plano antes de destruir la ventana."""
        app_logger.info("Cerrando aplicación y finalizando servicios en segundo plano...")
        try:
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
        """Construye el menú de navegación lateral con los 5 departamentos."""
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

        # Footer de la Barra Lateral (Tasa BCV y Versión)
        footer = ctk.CTkFrame(self.sidebar, fg_color=Theme.CARD_BG, corner_radius=8)
        footer.pack(side="bottom", fill="x", padx=12, pady=15)

        bcv = BCVExchangeRateProvider.get_official_rate()
        self.lbl_sidebar_bcv = ctk.CTkLabel(
            footer,
            text=f"💵 BCV: {bcv['rate']:,.2f} Bs",
            font=Theme.FONT_SMALL,
            text_color=Theme.SUCCESS
        )
        self.lbl_sidebar_bcv.pack(pady=(6, 2))

        ctk.CTkLabel(
            footer,
            text=f"v{SystemConfig.APP_VERSION} • Producción",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_DIM
        ).pack(pady=(0, 6))

    def _build_container(self):
        """Contenedor dinámico donde se alojan las vistas departamentales."""
        self.container = ctk.CTkFrame(self, fg_color=Theme.BG_DARK, corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def navigate_to(self, dept_code: str, factory=None):
        """Cambia fluidamente entre las vistas de los 5 departamentos."""
        # Limpiar contenedor
        for child in self.container.winfo_children():
            child.destroy()

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
                view = factory()
                view.pack(fill="both", expand=True)
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
