"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: web_scraper.py
Descripción: Rastreador Web Global basado estrictamente en la lógica "madre" 
             exitosa, con soporte opcional limpio para Ámbito Internacional y Zoom.
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
    Rastreador Web Global adaptado de la lógica madre del sistema de escritorio.
    """

    def __init__(self):
        self.api_key = getattr(SystemConfig, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            app_logger.warning("No se encontró la GEMINI_API_KEY en la configuración.")

        # Compatibilidad de la librería Gemini
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
                self.model_old = genai_old.GenerativeModel("gemini-1.5-flash")
                self.usar_genai_nuevo = False
            except Exception:
                pass

        self.calc_zoom = CalculadoraImportacionZoom()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def buscar_sitios_web(self, busqueda: str, max_resultados: int = 20, ambito: str = "Nacional"):
        """
        Busca páginas web y grandes plataformas de comercio global o mercado nacional.
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
                        
                        snippet_text = snippets[i].get_text(strip=True) if i < len(snippets) else "Sin descripción"
                        
                        resultados.append({
                            "url": url_real,
                            "resumen": snippet_text
                        })
        except Exception as e:
            app_logger.warning(f"Error durante el rastreo web: {e}")

        # Respaldos limpios de la lógica madre
        if not resultados:
            encoded_term = urllib.parse.quote(busqueda)
            if ambito == "Internacional":
                resultados = [
                    {"url": f"https://www.amazon.com/s?k={encoded_term}", "resumen": f"Catálogo Amazon Global para '{busqueda}'"},
                    {"url": f"https://www.ebay.com/sch/i.html?_nkw={encoded_term}&_sop=12", "resumen": f"Catálogo eBay Global para '{busqueda}'"}
                ]
            else:
                resultados = [
                    {"url": "https://ioniashop.com", "resumen": f"IoniaShop Venezuela - Distribuidor de tóners e insumos para '{busqueda}'"},
                    {"url": "https://officenet.net.ve", "resumen": f"OfficeNet Venezuela - Proveedor corporativo de suministros"},
                    {"url": "https://compumall.com.ve", "resumen": f"CompuMall Venezuela - Tienda técnica de componentes"}
                ]

        return resultados

    def analizar_con_gemini_v2(self, producto: str, datos_extraidos: list, ambito: str = "Nacional", incluye_importacion: bool = False):
        if not datos_extraidos:
            return "No se encontraron tiendas o productos bajo los criterios estrictos solicitados."

        encoded_term = urllib.parse.quote(producto)
        estimacion = self.calc_zoom.estimar_peso_volumen(producto)
        peso_est = float(estimacion["peso_lb"])
        flete_aereo_est = max(peso_est * self.calc_zoom.tarifa_aerea_lb, 10.00)

        # SEPARACIÓN ABSOLUTA: Lógica Nacional intacta como el código madre, separada de la internacional
        if ambito != "Internacional":
            restriccion_geografica = "Ámbito Nacional de Venezuela."
            instruccion_ubicacion = "📍 **Ubicación Geográfica:** Indica la ciudad o estado del proveedor dentro de Venezuela."
            instruccion_zoom = "INSTRUCCIÓN LOGÍSTICA: Muestra únicamente los precios base de los proveedores locales sin fletes de casillero."
            
            prompt = f"""
            Eres un asistente analista de compras experto y estratega comercial para "Inversiones Reinaldo Golindano".
            El usuario está buscando: "{producto}".
            Ámbito seleccionado: Nacional de Venezuela.
            {restriccion_geografica}
            
            A continuación tienes una lista de resultados extraídos de la web abierta:
            {datos_extraidos}
            
            INSTRUCCIONES DE FORMATO Y ENLACES DIRECTOS:
            1. Analiza los resultados y selecciona las mejores opciones. ORDÉNALAS ESTRICTAMENTE DE MENOR A MAYOR PRECIO BASE (la más económica de primera como Opción 1).
            2. Presenta la información limpia y estructurada.
            3. Para CADA opción, detalla:
               - Nombre de la plataforma / Proveedor
               - Precio Base exacto estimado en USD
               - {instruccion_ubicacion}
               - Descripción analítica del valor para la competitividad del taller
               - **Enlace directo interactivo OBLIGATORIO:** Utiliza la URL limpia directa provista en los datos extraídos (ficha técnica o producto). Formato estricto: **Enlace:** [Texto descriptivo](URL)
               - {instruccion_zoom}
            """
        else:
            restriccion_geografica = (
                "REGLA CRÍTICA: ÁMBITO INTERNACIONAL EXCLUSIVO. Prohibido incluir proveedores de Venezuela. "
                "Prioriza hallazgos de plataformas globales como Amazon, AliExpress, eBay o Alibaba."
            )
            instruccion_ubicacion = (
                "🌍 **Ubicación Geográfica / Plataforma:** Indica claramente la tienda o plataforma global de origen (Ej: *Amazon - Estados Unidos*, *eBay - Estados Unidos* o *AliExpress - China*)."
            )

            if incluye_importacion:
                instruccion_zoom = (
                    f"INSTRUCCIÓN DE LOGÍSTICA ZOOM CASILLEROS (CASILLA TILDADA):\n"
                    f"Para CADA opción, incluye de forma integrada un desglose estimado de importación (peso est: ~{peso_est} lbs):\n"
                    f"- Flete aéreo estimado: ${(flete_aereo_est + 5):,.2f} USD Puesto en Taller."
                )
            else:
                instruccion_zoom = "INSTRUCCIÓN LOGÍSTICA: La casilla de cálculo de importación NO está tildada. Muestra únicamente los precios base de los proveedores."

            prompt = f"""
            Eres un asistente analista de compras experto y estratega comercial para "Inversiones Reinaldo Golindano".
            El usuario está buscando: "{producto}".
            Ámbito seleccionado: Internacional (Exclusivo).
            {restriccion_geografica}
            
            A continuación tienes una lista de resultados extraídos de la web abierta:
            {datos_extraidos}
            
            INSTRUCCIONES DE FORMATO Y ENLACES DIRECTOS:
            1. Analiza los resultados y selecciona las mejores opciones. ORDÉNALAS ESTRICTAMENTE DE MENOR A MAYOR PRECIO BASE (la más económica de primera como Opción 1).
            2. Presenta la información limpia y estructurada.
            3. Para CADA opción, detalla:
               - Nombre de la plataforma / Proveedor
               - Precio Base exacto estimado en USD
               - {instruccion_ubicacion}
               - Descripción analítica del valor para la competitividad del taller
               - **Enlace directo interactivo OBLIGATORIO:** Si la opción corresponde a Amazon, eBay, AliExpress o Alibaba, genera obligatoriamente una URL de búsqueda directa estructurada (ej. para Amazon: `https://www.amazon.com/s?k={encoded_term}`). Formato estricto: **Enlace:** [Texto descriptivo](URL)
               - {instruccion_zoom}
            """

        modelos = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-1.5-flash", "gemini-pro"]

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
                        time.sleep(2 * (intento + 1))
                    else:
                        break

        return "Los servidores de Google presentan alta demanda momentánea. Por favor, vuelve a presionar el botón de búsqueda en unos segundos."

    def analizar_con_gemini(self, producto: str, datos_extraidos: list):
        """Método de compatibilidad estándar."""
        return self.analizar_con_gemini_v2(producto, datos_extraidos, ambito="Nacional", incluye_importacion=False)


# Alias de compatibilidad
RastreadorWebGlobal = GlobalWebScraper