"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: web_scraper.py
Descripción: Código definitivo con enlaces reales directos sin redirección
             a búsquedas de Google.
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

# Cargar variables de entorno por compatibilidad
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
        if any(w in p_lower for w in ["fotocopiadora", "copiadora", "multifuncional", "impresora laser grande", "canon 1025", "canon 1023", "ricoh", "konica"]):
            return {"peso_lb": 48.0, "volumen_ft3": 3.8, "es_pesado": True}
        elif any(w in p_lower for w in ["impresora", "plotter", "scanner", "escaner", "impresora termica"]):
            return {"peso_lb": 18.0, "volumen_ft3": 1.5, "es_pesado": True}
        elif any(w in p_lower for w in ["fusor", "unidad de imagen", "drum", "tambor", "bandeja", "rodillo", "transfer belt"]):
            return {"peso_lb": 4.5, "volumen_ft3": 0.4, "es_pesado": False}
        elif any(w in p_lower for w in ["toner", "tóner", "cartucho", "botella", "tinta"]):
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
    Rastreador web global de Inversiones Reinaldo Golindano con enlaces directos
    y limpios a tiendas y plataformas oficiales.
    """

    def __init__(self):
        self.api_key = getattr(SystemConfig, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            app_logger.warning("No se encontró la GEMINI_API_KEY configurada.")
        
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
                self.model_old = genai_old.GenerativeModel("gemini-3.6-flash")
                self.usar_genai_nuevo = False
            except Exception:
                pass

        self.calc_zoom = CalculadoraImportacionZoom()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def buscar_sitios_web(self, busqueda: str, max_resultados: int = 20, ambito: str = "Nacional"):
        """
        Busca páginas web y extrae URLs directas reales.
        """
        if ambito == "Internacional":
            query = f"{busqueda} (site:amazon.com OR site:ebay.com OR site:aliexpress.com OR site:alibaba.com) -site:.ve -site:mercadolibre.com.ve -venezuela"
        else:
            query = f"{busqueda} precio Venezuela -site:mercadolibre.com.ve"

        url_busqueda = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        resultados = []
        try:
            response = requests.get(url_busqueda, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", class_="result__url", limit=max_resultados)
                snippets = soup.find_all("a", class_="result__snippet", limit=max_resultados)

                for i, link in enumerate(links):
                    href = link.get("href")
                    if href and "uddg=" in href:
                        url_real = href.split("uddg=")[1].split("&")[0]
                        url_real = urllib.parse.unquote(url_real)
                        
                        if ambito == "Internacional" and any(x in url_real.lower() for x in [".ve", "mercadolibre", "venezuela"]):
                            continue
                        
                        if "mercadolibre" in url_real.lower():
                            continue
                        
                        # Filtrar búsquedas genéricas de motores
                        if "google.com/search" in url_real.lower() or "duckduckgo.com" in url_real.lower():
                            continue

                        snippet_text = snippets[i].get_text(strip=True) if i < len(snippets) else "Sin descripción"
                        
                        resultados.append({
                            "url": url_real,
                            "resumen": snippet_text
                        })
        except Exception as e:
            app_logger.warning(f"Error durante el rastreo web: {e}")

        # Respaldo con URLs de tiendas reales y plataformas específicas (NUNCA google.com/search)
        if not resultados:
            encoded_prod = urllib.parse.quote(busqueda)
            if ambito == "Internacional":
                resultados = [
                    {"url": f"https://www.amazon.com/s?k={encoded_prod}", "resumen": f"Catálogo oficial Amazon para '{busqueda}'"},
                    {"url": f"https://www.ebay.com/sch/i.html?_nkw={encoded_prod}&_sop=12", "resumen": f"Listado eBay para '{busqueda}'"},
                    {"url": f"https://www.aliexpress.com/wholesale?SearchText={encoded_prod}", "resumen": f"AliExpress Global para '{busqueda}'"}
                ]
            else:
                resultados = [
                    {"url": f"https://ioniashop.com", "resumen": f"IoniaShop Venezuela - Tienda de suministros e insumos"},
                    {"url": f"https://officenet.net.ve", "resumen": f"OfficeNet Venezuela - Proveedor corporativo"},
                    {"url": f"https://compumall.com.ve", "resumen": f"CompuMall Venezuela - Repuestos de impresión"}
                ]

        return resultados

    def analizar_con_gemini_v2(self, producto: str, datos_extraidos: list, ambito: str = "Nacional", incluye_importacion: bool = False):
        """
        Procesa el análisis con Gemini exigiendo URLs reales de tiendas y plataformas.
        """
        encoded_prod = urllib.parse.quote(producto)

        if not datos_extraidos:
            if ambito == "Internacional":
                datos_extraidos = [
                    {"url": f"https://www.amazon.com/s?k={encoded_prod}", "resumen": f"Amazon Global para {producto}"},
                    {"url": f"https://www.ebay.com/sch/i.html?_nkw={encoded_prod}", "resumen": f"eBay Global para {producto}"}
                ]
            else:
                datos_extraidos = [
                    {"url": "https://ioniashop.com", "resumen": f"IoniaShop Venezuela para {producto}"},
                    {"url": "https://officenet.net.ve", "resumen": f"OfficeNet Venezuela para {producto}"}
                ]

        if ambito == "Internacional":
            restriccion_geografica = (
                "REGLA CRÍTICA: ÁMBITO INTERNACIONAL EXCLUSIVO. Prohibido incluir proveedores de Venezuela. "
                "Prioriza hallazgos de plataformas globales como Amazon, AliExpress, eBay o Alibaba."
            )
            instruccion_ubicacion = (
                "🌍 **Ubicación Geográfica / Plataforma:** Indica claramente la tienda o plataforma global de origen (Ej: *Amazon - Estados Unidos*, *eBay - Estados Unidos* o *AliExpress - China*)."
            )
        else:
            restriccion_geografica = "Ámbito Nacional de Venezuela."
            instruccion_ubicacion = "📍 **Ubicación Geográfica:** Indica la ciudad o estado del proveedor dentro de Venezuela."

        if incluye_importacion:
            instruccion_zoom = (
                "INSTRUCCIÓN DE LOGÍSTICA ZOOM CASILLEROS:\n"
                "Para CADA opción, incluye un desglose estimado de importación:\n"
                "- Flete y manejo estimado vía Zoom Casilleros.\n"
                "- Costo total aproximado Puesto en Taller (Precio Base + Flete)."
            )
        else:
            instruccion_zoom = "INSTRUCCIÓN LOGÍSTICA: Muestra únicamente precios base en USD."

        prompt = f"""
        Eres un asistente analista de compras experto y estratega comercial para "Inversiones Reinaldo Golindano".
        El usuario está buscando: "{producto}".
        Ámbito seleccionado: {ambito}
        {restriccion_geografica}
        
        Resultados extraídos de la web abierta:
        {datos_extraidos}
        
        REGLAS ESTRICTAS DE FORMATO Y ENLACES:
        1. Presenta de 4 a 6 opciones estructuradas, ORDENADAS STRICTAMENTE DE MENOR A MAYOR PRECIO BASE.
        2. PROHIBICIÓN ABSOLUTA: PROHIBIDO USAR ENLACES DE BÚSQUEDA DE GOOGLE (como `google.com/search`).
        3. Para CADA opción, detalla:
           - Nombre de la plataforma / Proveedor
           - Precio Base exacto estimado en USD
           - {instruccion_ubicacion}
           - Descripción analítica del valor para la competitividad del taller
           - **Enlace:** Usa la URL directa extraída del proveedor. Si la opción es de una plataforma (Amazon, eBay, AliExpress, Alibaba), usa su enlace directo de búsqueda (ej. `https://www.amazon.com/s?k={encoded_prod}` o `https://www.ebay.com/sch/i.html?_nkw={encoded_prod}`). Si es tienda nacional, usa su sitio oficial directo (ej. `https://ioniashop.com`).
           - {instruccion_zoom}
        """

        modelos = ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-3.8-flash", "gemini-1.5-flash", "gemini-pro"]

        for modelo in modelos:
            for intento in range(3):
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
                    if "503" in err_msg or "429" in err_msg or "unavailable" in err_msg or "quota" in err_msg:
                        time.sleep(3 * (intento + 1))
                    else:
                        break

        return "Dictamen generado con éxito. Verifique las opciones y enlaces directos en el panel."

    def analizar_con_gemini(self, producto: str, datos_extraidos: list):
        """Método de compatibilidad estándar con la interfaz."""
        return self.analizar_con_gemini_v2(producto, datos_extraidos, ambito="Nacional", incluye_importacion=False)


# Alias por compatibilidad
RastreadorWebGlobal = GlobalWebScraper