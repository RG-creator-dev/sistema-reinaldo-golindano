"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: web_scraper.py
Descripción: Rastreador Web y Agente de Procura Multisectorial basado en la
             arquitectura modular de eslabones y el Prompt Madre.
=============================================================================
"""

import os
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from config import SystemConfig
from core.logger import app_logger

# Cargar variables de entorno
load_dotenv()


class CalculadoraImportacionZoom:
    """Calculadora logística de costos de importación y fletes vía Zoom Casilleros."""

    def __init__(self, tarifa_aerea_lb: float = 5.50, tarifa_maritima_ft3: float = 18.00, tasa_manejo: float = 5.00):
        self.tarifa_aerea_lb = tarifa_aerea_lb
        self.tarifa_maritima_ft3 = tarifa_maritima_ft3
        self.tasa_manejo = tasa_manejo

    def estimar_peso_volumen(self, producto: str) -> dict:
        """Estima peso y volumen según la naturaleza técnica del producto."""
        p_lower = producto.lower()
        if any(w in p_lower for w in ["fotocopiadora", "copiadora", "multifuncional", "maquinaria", "generador", "compresor"]):
            return {"peso_lb": 48.0, "volumen_ft3": 3.8, "es_pesado": True}
        elif any(w in p_lower for w in ["impresora", "escaner", "laptop", "herramienta electrica", "caja de herramientas"]):
            return {"peso_lb": 18.0, "volumen_ft3": 1.5, "es_pesado": True}
        elif any(w in p_lower for w in ["fusor", "tambor", "repuesto automotriz", "alternador", "bomba", "taladro"]):
            return {"peso_lb": 4.5, "volumen_ft3": 0.4, "es_pesado": False}
        elif any(w in p_lower for w in ["toner", "tinta", "filtro", "aceite", "lubricante", "destornillador"]):
            return {"peso_lb": 2.2, "volumen_ft3": 0.15, "es_pesado": False}
        else:
            return {"peso_lb": 1.2, "volumen_ft3": 0.08, "es_pesado": False}

    def calcular_costo_puesto_taller(self, precio_usd: float, peso_lb: float = 1.0, volumen_ft3: float = 0.1, tipo_envio: str = "Aereo") -> dict:
        """Calcula el costo final puesto en taller en Guacara/Valencia."""
        if tipo_envio.lower() == "aereo":
            flete = max(peso_lb * self.tarifa_aerea_lb, 10.00)
        else:
            flete = max(volumen_ft3 * self.tarifa_maritima_ft3, 20.00)

        costo_total = precio_usd + flete + self.tasa_manejo

        return {
            "precio_base_usd": round(precio_usd, 2),
            "flete_estimado_usd": round(flete, 2),
            "gastos_manejo_usd": self.tasa_manejo,
            "costo_total_puesto_ve": round(costo_total, 2),
            "modalidad": tipo_envio
        }


class GlobalWebScraper:
    """
    Agente de Procura y Rastreador Web Multisectorial para Inversiones Reinaldo Golindano.
    """

    def __init__(self):
        self.api_key = getattr(SystemConfig, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            app_logger.warning("No se encontró la GEMINI_API_KEY en la configuración.")

        # Configuración del cliente oficial de Google GenAI
        self.usar_genai_nuevo = False
        try:
            from google import genai
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
                self.usar_genai_nuevo = True
        except Exception:
            pass

        if not self.usar_genai_nuevo and self.api_key:
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=self.api_key)
                self.usar_genai_nuevo = False
            except Exception:
                pass

        self.calc_zoom = CalculadoraImportacionZoom()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def buscar_sitios_web(self, busqueda: str, max_resultados: int = 15, ambito: str = "Nacional") -> list:
        """
        ESLABÓN 1: Extracción limpia de la web abierta excluyendo Mercado Libre.
        """
        encoded_term = urllib.parse.quote(busqueda)
        
        # Construcción de querys optimizadas con exclusión estricta de Mercado Libre
        if ambito == "Internacional":
            query = f"{busqueda} (site:amazon.com OR site:ebay.com OR site:aliexpress.com OR site:alibaba.com) -site:.ve -site:mercadolibre.com -mercadolibre"
        elif ambito == "Ambos":
            query = f"{busqueda} precio -site:mercadolibre.com -site:mercadolibre.com.ve -mercadolibre"
        else:  # Nacional
            query = f"{busqueda} precio Venezuela -site:mercadolibre.com.ve -site:mercadolibre.com -mercadolibre"

        url_busqueda = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        resultados = []

        try:
            response = requests.get(url_busqueda, headers=self.headers, timeout=8)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", class_="result__url", limit=max_resultados)
                snippets = soup.find_all("a", class_="result__snippet", limit=max_resultados)

                for i, link in enumerate(links):
                    href = link.get("href")
                    if href and "uddg=" in href:
                        url_real = href.split("uddg=")[1].split("&")[0]
                        url_real = urllib.parse.unquote(url_real)
                        
                        # FILTRO DURO: Exclusión absoluta de Mercado Libre
                        if "mercadolibre" in url_real.lower():
                            continue

                        # Filtro de coherencia geográfica para búsquedas nacionales
                        if ambito == "Nacional" and any(x in url_real.lower() for x in ["amazon.com", "ebay.com", "aliexpress.com", "alibaba.com"]):
                            continue

                        snippet_text = snippets[i].get_text(strip=True) if i < len(snippets) else "Sin descripción disponible"

                        resultados.append({
                            "url": url_real,
                            "resumen": snippet_text
                        })
        except Exception as e:
            app_logger.warning(f"Error durante la extracción del Eslabón 1: {e}")

        return resultados

    def analizar_con_gemini_v2(self, producto: str, datos_extraidos: list, ambito: str = "Nacional", incluye_importacion: bool = False) -> str:
        """
        ESLABÓN 2 Y 3: Inteligencia Comercial con Gemini aplicando el PROMPT MADRE MULTISECTORIAL.
        """
        if not datos_extraidos:
            return "⚠️ No se encontraron ofertas reales en la web abierta bajo los criterios solicitados. Intenta ajustar el término de búsqueda."

        estimacion = self.calc_zoom.estimar_peso_volumen(producto)
        peso_est = float(estimacion["peso_lb"])
        flete_aereo_est = max(peso_est * self.calc_zoom.tarifa_aerea_lb, 10.00)

        # Instrucciones logísticas según ámbito
        if ambito == "Nacional":
            regla_geografica = "ÁMBITO NACIONAL: Limítate estrictamente a tiendas o distribuidores ubicados en Venezuela."
            instruccion_zoom = "No incluir cálculo de fletes internacionales."
        elif ambito == "Internacional":
            regla_geografica = "ÁMBITO INTERNACIONAL EXCLUSIVO: Prohibido incluir tiendas de Venezuela. Prioriza tiendas o plataformas globales (Amazon, eBay, AliExpress, Alibaba)."
            if incluye_importacion:
                instruccion_zoom = f"Incluir estimación de flete aéreo Zoom Casillero puesto en taller (Peso est: ~{peso_est} lbs, Flete est: ${(flete_aereo_est + 5):,.2f} USD)."
            else:
                instruccion_zoom = "Muestra únicamente el precio base del proveedor internacional."
        else:  # Ambos
            regla_geografica = "ÁMBITO COMBINADO (AMBOS): Puedes comparar opciones nacionales e internacionales."
            instruccion_zoom = f"Para opciones internacionales, indica el flete estimado Zoom Casillero (Aprox: ${(flete_aereo_est + 5):,.2f} USD)."

        # PROMPT MADRE INTEGRADO
        prompt = f"""
Eres el Gerente de Compras y Procura Senior para 'Inversiones Reinaldo Golindano'. Tu función es actuar como un agente de búsqueda y localización multisectorial para cualquier tipo de producto, insumo, repuesto, herramienta o bien de consumo que requiera la empresa o sus clientes. Tu especialidad es la inteligencia comercial: encontrar la mejor oferta del mercado con criterio de revendedor, optimizando costos y garantizando la viabilidad de entrega.

PRODUCTO SOLICITADO: "{producto}"
ÁMBITO CONFIGURADO: {ambito}
{regla_geografica}

DATOS EXTRAÍDOS DE LA WEB ABIERTA:
{datos_extraidos}

REGLAS CRÍTICAS DE PROCURA:
1. Enfoque de Costo-Beneficio y Reventa: Busca la opción que ofrezca la mejor relación calidad-precio razonable. Evita marcas de lujo o precios inflados a menos que el usuario lo pida explícitamente. Prioriza costos competitivos que permitan margen de ganancia.
2. Exclusión Estricta de Plataformas: Está terminantemente prohibido incluir o procesar opciones de Mercado Libre.
3. Formato y Presentación de Opciones:
   - Selecciona las 4 mejores opciones reales encontradas.
   - ORDÉNALAS ESTRICTAMENTE DE MENOR A MAYOR PRECIO BASE EN USD (Opción 1 es la más económica).
   - Para CADA opción detalla:
     * Nombre de la Tienda / Proveedor.
     * Ubicación Geográfica (Ciudad/Estado en VE o País/Plataforma en Internacional).
     * Precio Base en USD y presentación del producto (unidad, caja, kit, etc.).
     * Razón Comercial: Breve explicación de por qué conviene para el negocio.
     * Enlace Directo Interactivo: Formato estricto **Enlace:** [Ver producto o tienda](URL)
     * Logística Zoom: {instruccion_zoom}

4. Cero Falsificaciones: Prohibido inventar datos o usar opciones de relleno si la red no aportó información real.
"""

        # Modelos Gemini disponibles por orden de prioridad
        modelos = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

        for modelo in modelos:
            for intento in range(2):
                try:
                    if self.usar_genai_nuevo:
                        response = self.client.models.generate_content(
                            model=modelo,
                            contents=prompt
                        )
                        if response and response.text:
                            return response.text.strip()
                    else:
                        import google.generativeai as genai_old
                        m = genai_old.GenerativeModel(modelo)
                        response = m.generate_content(prompt)
                        if response and response.text:
                            return response.text.strip()
                except Exception as e:
                    err_msg = str(e).lower()
                    if any(code in err_msg for code in ["503", "429", "unavailable", "quota"]):
                        time.sleep(1.5 * (intento + 1))
                    else:
                        break

        return "⚠️ Los servidores de IA presentan alta demanda momentánea. Por favor, reintenta tu búsqueda en unos segundos."

    def analizar_con_gemini(self, producto: str, datos_extraidos: list) -> str:
        """Método de compatibilidad estándar."""
        return self.analizar_con_gemini_v2(producto, datos_extraidos, ambito="Nacional", incluye_importacion=False)


# Alias de compatibilidad
RastreadorWebGlobal = GlobalWebScraper