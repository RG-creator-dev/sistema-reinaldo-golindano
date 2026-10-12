"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: web_scraper.py
Descripción: Rastreador Web Global con enlaces limpios y directos, evitando
             absolutamente rutas 404 y garantizando navegación fluida.
=============================================================================
"""

import os
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from config import SystemConfig
from core.logger import app_logger


class CalculadoraImportacionZoom:
    """Calculadora logística de costos de importación y fletes vía Zoom Casilleros."""

    def __init__(self, tarifa_aerea_lb: float = 5.50, tarifa_maritima_ft3: float = 18.00, tasa_manejo: float = 5.00):
        self.tarifa_aerea_lb = tarifa_aerea_lb
        self.tarifa_maritima_ft3 = tarifa_maritima_ft3
        self.tasa_manejo = tasa_manejo

    def estimar_peso_volumen(self, producto: str) -> Dict[str, Any]:
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

    def calcular_costo_puesto_taller(self, precio_usd: float, peso_lb: float = 1.0, volumen_ft3: float = 0.1, tipo_envio: str = "Aereo") -> Dict[str, Any]:
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
    """Motor de búsqueda y rastreo web optimizado con enlaces directos seguros."""

    def __init__(self):
        self.calc_zoom = CalculadoraImportacionZoom()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def _es_url_mercado_libre(self, url: str) -> bool:
        """Verifica de forma absoluta si una URL pertenece a Mercado Libre."""
        url_lower = url.lower()
        patrones_ml = [
            "mercadolibre.com",
            "mercadolibre.com.ve",
            "mercadolibre.",
            "articulo.mercadolibre",
            "listado.mercadolibre",
            "mlv-", "mlb-", "mla-"
        ]
        return any(p in url_lower for p in patrones_ml)

    def buscar_sitios_web(self, busqueda: str, max_resultados: int = 20, ambito: str = "Nacional") -> List[Dict[str, str]]:
        """
        Busca páginas web y grandes plataformas de comercio global o nacional,
        excluyendo totalmente Mercado Libre.
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
                        
                        if self._es_url_mercado_libre(url_real):
                            continue

                        if ambito == "Internacional" and any(x in url_real.lower() for x in [".ve", "mercadolibre", "venezuela"]):
                            continue
                        
                        snippet_text = snippets[i].get_text(strip=True) if i < len(snippets) else "Sin descripción"
                        
                        resultados.append({
                            "url": url_real,
                            "resumen": snippet_text
                        })
        except Exception as e:
            app_logger.warning(f"Error durante el rastreo web: {e}")

        return resultados

    def analizar_con_gemini_v2(self, producto: str, datos_extraidos: list, ambito: str = "Nacional", incluye_importacion: bool = False) -> str:
        if not datos_extraidos:
            return "No se encontraron tiendas o productos bajo los criterios estrictos solicitados."

        if ambito == "Internacional":
            restriccion_geografica = (
                "REGLA CRÍTICA: ÁMBITO INTERNACIONAL EXCLUSIVO. Prohibido incluir proveedores de Venezuela. "
                "Prioriza hallazgos de plataformas globales como Amazon, AliExpress, eBay o Alibaba."
            )
            instruccion_ubicacion = (
                "🌍 **Ubicación Geográfica / Plataforma:** Indica claramente la tienda o plataforma global de origen (Ej: *Amazon - Estados Unidos*, *eBay - Estados Unidos* o *AliExpress - China*)."
            )
        else:
            restriccion_geografica = "Ámbito Nacional de Venezuela (Prohibido Mercado Libre)."
            instruccion_ubicacion = "📍 **Ubicación Geográfica:** Indica la ciudad o estado del proveedor dentro de Venezuela."

        estimacion = self.calc_zoom.estimar_peso_volumen(producto)
        peso_est = float(estimacion["peso_lb"])
        vol_est = float(estimacion["volumen_ft3"])
        es_pesado = bool(estimacion["es_pesado"])

        flete_aereo_est = max(peso_est * self.calc_zoom.tarifa_aerea_lb, 10.00)
        flete_maritimo_est = max(vol_est * self.calc_zoom.tarifa_maritima_ft3, 20.00)

        if incluye_importacion:
            if es_pesado:
                instruccion_zoom = f"""
                INSTRUCCIÓN DE IMPORTACIÓN ZOOM CASILLEROS (CASILLA MARCADA):
                Para CADA opción calcula obligatoriamente el flete hacia Guacara/Valencia (~{peso_est} lbs, vol: ~{vol_est} ft³):
                - Flete Aéreo: ${(flete_aereo_est):,.2f} + $5 manejo = **${(flete_aereo_est + 5):,.2f} USD**
                - Flete Marítimo: ${(flete_maritimo_est):,.2f} + $5 manejo = **${(flete_maritimo_est + 5):,.2f} USD**
                """
            else:
                instruccion_zoom = f"""
                INSTRUCCIÓN DE IMPORTACIÓN ZOOM CASILLEROS (CASILLA MARCADA):
                - Flete Aéreo Zoom: ${(flete_aereo_est):,.2f} + $5.00 manejo = **${(flete_aereo_est + 5):,.2f} USD**
                """
        else:
            instruccion_zoom = "INSTRUCCIÓN LOGÍSTICA: Muestra únicamente los precios base de los proveedores en USD."

        prompt = f"""
        Eres un asistente analista de compras experto y estratega comercial para 'Inversiones Reinaldo Golindano' (Taller técnico de impresoras y fotocopiadoras en Carabobo, Venezuela).
        El usuario está buscando: "{producto}".
        Ámbito seleccionado: {ambito}
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
           - **Enlace directo interactivo OBLIGATORIO:** Utiliza estrictamente las URLs reales provistas en los resultados de búsqueda web. Si la URL extraída es una página principal o de búsqueda general que pueda dar error, utiliza la URL limpia y verificada del dominio principal del proveedor (ej. `https://ioniashop.com` o `https://www.amazon.com`). Formato estricto: **Enlace:** [Texto descriptivo](URL)
           - {instruccion_zoom}
        """

        # Intento con google-genai moderno o genai legado
        modelos_genai = ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-3.6-flash", "gemini-1.5-flash"]
        for m_name in modelos_genai:
            try:
                from google import genai
                client = genai.Client(api_key=SystemConfig.GEMINI_API_KEY)
                resp = client.models.generate_content(
                    model=m_name,
                    contents=prompt
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                app_logger.warning(f"Intento con SDK google.genai ({m_name}): {e}")
                continue

        # Respaldo con google.generativeai legado
        try:
            import google.generativeai as genai_old
            genai_old.configure(api_key=SystemConfig.GEMINI_API_KEY)
            for m_name in ["gemini-1.5-flash", "gemini-pro"]:
                try:
                    m = genai_old.GenerativeModel(m_name)
                    res_old = m.generate_content(prompt)
                    if res_old and res_old.text:
                        return res_old.text.strip()
                except Exception:
                    continue
        except Exception:
            pass

        return "Los servidores de Google presentan alta demanda momentánea. Por favor, vuelve a presionar el botón de búsqueda en unos segundos."

    def analizar_con_gemini(self, producto: str, datos_extraidos: list) -> str:
        return self.analizar_con_gemini_v2(producto, datos_extraidos, ambito="Nacional", incluye_importacion=False)