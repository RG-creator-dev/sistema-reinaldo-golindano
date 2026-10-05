# Sistema de Gestión de Inversiones Reinaldo Golindano

Arquitectura modular y desacoplada en **Python** diseñada bajo estrictos patrones de ingeniería de software para la gestión integral de operaciones de servicio técnico, comercialización de insumos, auditoría de inventario, conciliación financiera y orquestación con Inteligencia Artificial.

---

## 🏛️ Estructura en 5 Departamentos Principales

La aplicación está organizada en 5 departamentos dentro del directorio `/modules/`:

```
Prueba_Antigravity/
├── config.py                                 # Configuración centralizada y gestión de claves API
├── requirements.txt                          # Dependencias oficiales del sistema
├── .env.example                              # Plantilla de variables de entorno
├── main.py                                   # Punto de entrada de la aplicación
│
├── core/                                     # Núcleo desacoplado y transversal
│   ├── base_agent.py                         # Clase abstracta BaseAgent y contratos de agentes
│   ├── event_bus.py                          # Bus de eventos asíncrono (Patrón Observer)
│   └── logger.py                             # Auditoría y registro unificado de eventos
│
├── modules/
│   ├── dept_01_direccion_general/            # 1. DIRECCIÓN GENERAL
│   │   ├── orchestrator_agent.py             # Agente Orquestador Central & Síntesis Ejecutiva
│   │   └── ui_view.py                        # Vista CustomTkinter del Directorio
│   │
│   ├── dept_02_comercio_ventas/              # 2. COMERCIO Y VENTAS
│   │   ├── b2b_marketing_agent.py            # Agente Publicitario B2B y Propuestas Corporativas
│   │   ├── quote_catalog_agent.py            # Procesador de pedidos (Telegram/Voz -> Items)
│   │   ├── pdf_generator.py                  # Generador de Presupuestos Formales con ReportLab
│   │   └── ui_view.py                        # Vista CustomTkinter de Cotizaciones y Marketing
│   │
│   ├── dept_03_compras_procura/              # 3. COMPRAS Y PROCURA
│   │   ├── supply_audit_agent.py             # Agente Analista de Suministros e Inventario Crítico
│   │   ├── ml_scraper.py                     # Rastreador Mercado Libre Venezuela (Desacoplado)
│   │   ├── web_scraper.py                    # Rastreador Web Global & Comparador de Costos
│   │   └── ui_view.py                        # Vista CustomTkinter de Stock y Rastreo Web
│   │
│   ├── dept_04_administracion_finanzas/      # 4. ADMINISTRACIÓN Y FINANZAS
│   │   ├── accounting_agent.py               # Agente Administrador y Contable (Libro Mayor)
│   │   ├── payment_gateways.py               # Pasarelas de Pago Cripto (Binance Pay & Cryptomus)
│   │   └── ui_view.py                        # Vista CustomTkinter de Balance y Cobros
│   │
│   └── dept_05_servicio_tecnico_taller/      # 5. SERVICIO TÉCNICO Y TALLER
│       ├── tech_diagnostics_agent.py         # Agente Diagnosticador Técnico Especialista Multimarca
│       └── ui_view.py                        # Vista CustomTkinter de Taller y Banco de Pruebas
│
└── ui/                                       # Capa Gráfica General
    ├── theme.py                              # Paleta corporativa Dark & estilos visuales
    └── main_window.py                        # Ventana CustomTkinter con Menú Lateral Navegable
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar o acceder al directorio del proyecto:
```bash
cd c:\Users\TRADING_PRO\Desktop\Prueba_Antigravity
```

### 2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### 3. Configuración de Credenciales (`.env`):
Crea tu archivo `.env` copiando el archivo de ejemplo:
```bash
copy .env.example .env
```
Edita `.env` para agregar tus credenciales:
- `GEMINI_API_KEY`: Tu clave de Google AI Studio.
- `TELEGRAM_BOT_TOKEN`: Token de bot de Telegram para recepción de notas de voz/pedidos.
- `BINANCE_API_KEY` / `BINANCE_SECRET_KEY`: Credenciales de Binance Pay.
- `CRYPTOMUS_API_KEY` / `CRYPTOMUS_MERCHANT_ID`: Credenciales de Cryptomus.

> **Nota de Resiliencia:** El sistema cuenta con **Modo Local Resiliente (Fallback)**. Si no ingresas claves API, la aplicación funcionará de forma íntegra para pruebas y demostración sin generar errores ni bloqueos.

### 4. Ejecutar la Aplicación:
```bash
python main.py
```

---

## 🔌 Conexión de Scripts Existentes de Scraping

Para conectar tus scripts previos de scraping de **Mercado Libre** o de búsqueda web global sin tocar la arquitectura:

```python
from modules.dept_03_compras_procura.ml_scraper import MercadoLibreTracker

def mi_scraper_personalizado(query: str):
    # Tu código existente de scraping aquí
    return [
        {
            "title": "Toner HP 85A Original",
            "price_usd": 19.5,
            "currency": "USD",
            "price_raw": 19.5,
            "seller": "MiProveedor",
            "permalink": "https://...",
            "source": "Mi Script Personalizado"
        }
    ]

# Enchufar el script al rastreador del sistema:
tracker = MercadoLibreTracker()
tracker.register_external_scraper(mi_scraper_personalizado)
```

---

## 📄 Generación de Presupuestos PDF con ReportLab
Los presupuestos generados en el módulo de **Comercio y Ventas** se guardan automáticamente en:
`exports/cotizaciones/Cotizacion_COT-XXXX_YYYYMMDD_HHMMSS.pdf`
Incluyen:
- Membrete legal de **Inversiones Reinaldo Golindano**.
- Desglose de repuestos, servicios técnicos y mano de obra con marcas (Epson, HP, Canon, Samsung).
- Cálculo automático de Subtotal, IVA (16%) y Total en USD.
- Cláusulas de garantía de 30 días y datos para transferencias, efectivo y pagos en **Binance Pay (USDT) / Cryptomus**.
