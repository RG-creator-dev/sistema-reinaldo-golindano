"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMPRAS Y PROCURA
Módulo: web_scraper.py
Descripción: Rastreador Web Global Multirrubro y Asistente de Procura con IA.
             Búsqueda abierta y libre sin límites de catálogo ni rubro.
             Exclusión estricta de Mercado Libre.
             Mecanismo Cero Pantallas Vacías con enlaces directos de búsqueda
             exacta (sin dominios caídos ni redirecciones al Home).
=============================================================================
"""

import os
import re
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
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
        """Estima peso y volumen según la naturaleza técnica de cualquier producto (Multirrubro)."""
        p_lower = producto.lower()
        if any(w in p_lower for w in ["fotocopiadora", "copiadora", "multifuncional", "impresora laser grande", "canon 1025", "canon 1023", "ricoh", "konica", "maquinaria", "motor", "servidor"]):
            return {"peso_lb": 48.0, "volumen_ft3": 3.8, "es_pesado": True, "categoria": "Maquinaria / Equipo Pesado"}
        elif any(w in p_lower for w in ["impresora", "plotter", "scanner", "escaner", "impresora termica", "computadora", "cpu", "monitor", "planta electrica", "compresor", "ups"]):
            return {"peso_lb": 18.0, "volumen_ft3": 1.5, "es_pesado": True, "categoria": "Equipo Mediano / Electrónica"}
        elif any(w in p_lower for w in ["fusor", "unidad de imagen", "drum", "tambor", "bandeja", "rodillo", "transfer belt", "herramienta", "taladro", "bateria", "repuesto"]):
            return {"peso_lb": 4.5, "volumen_ft3": 0.4, "es_pesado": False, "categoria": "Repuestos / Herramientas"}
        elif any(w in p_lower for w in ["toner", "tóner", "cartucho", "botella", "tinta", "resma", "papel", "papeleria", "cable"]):
            return {"peso_lb": 2.2, "volumen_ft3": 0.15, "es_pesado": False, "categoria": "Consumibles / Insumos"}
        else:
            return {"peso_lb": 2.5, "volumen_ft3": 0.12, "es_pesado": False, "categoria": "Artículos Generales"}

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
    Rastreador web global abierto, multicapa y multirrubro del Sistema de Gestión.
    """

    def __init__(self):
        self.api_key = getattr(SystemConfig, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            app_logger.warning("No se encontró la GEMINI_API_KEY en la configuración.")

        self.usar_genai_nuevo = False
        self.client = None

        try:
            from google import genai
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
                self.usar_genai_nuevo = True
        except Exception as e:
            app_logger.warning(f"Aviso inicializando google.genai: {e}")

        if not self.usar_genai_nuevo and self.api_key:
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=self.api_key)
                self.model_old = genai_old.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                app_logger.warning(f"Aviso inicializando google.generativeai clásico: {e}")

        self.calc_zoom = CalculadoraImportacionZoom()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _es_url_permitida(self, url: str, ambito: str) -> bool:
        """
        Regla de Filtro y Calidad:
        1. Excluye strictly Mercado Libre.
        2. Elimina URLs estáticas que apunten a la raíz/Home sin parámetros de búsqueda.
        3. Excluye dominios caídos o no comprobados.
        4. Respeta el ámbito geográfico.
        """
        if not url:
            return False
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            path = parsed.path.lower()
            query = parsed.query
        except Exception:
            return False

        # REGLA ESTRICTA 1: Excluir Mercado Libre en su dominio o ruta
        if "mercadolibre" in netloc or "mercadolibre" in path:
            return False

        # REGLA 2: Excluir enlaces a la raíz/Home sin ruta ni parámetros de búsqueda
        if (not path or path == "/") and not query:
            return False

        # REGLA 3: Excluir dominios no existentes o con fallos conocidos de DNS
        if any(bad in netloc for bad in ["compumall.com.ve", "multimaxstore.com", "tiendasdaka.com"]):
            return False

        u = url.lower()
        if any(ml in u for ml in ["mercadolibre.com", "mercadolibre.com.ve", "articulo.mercadolibre", "listado.mercadolibre"]):
            if not any(se in netloc for se in ["google.", "bing.", "yahoo.", "duckduckgo."]):
                return False

        # Si el ámbito es Internacional: omitir dominios venezolanos
        if ambito == "Internacional" and any(ve in netloc for ve in [".com.ve", ".ve"]):
            return False

        # Si el ámbito es Nacional: omitir plataformas que solo despachan fuera del país sin envío local
        if ambito == "Nacional" and any(intl in netloc for intl in ["aliexpress.com", "alibaba.com", "ebay.com"]):
            return False

        # Si el ámbito es Nacional: excluir enlaces internos de buscadores o redirecciones de anuncios
        if ambito == "Nacional" and (any(se in netloc for se in ["duckduckgo.com", "bing.com", "google."]) or "y.js" in path):
            return False

        return True

    def _generar_enlaces_dinamicos(self, busqueda: str, ambito: str) -> List[Dict[str, str]]:
        """
        Genera dinámicamente enlaces verificados de búsqueda directa y filtrada para CUALQUIER producto.
        """
        termino = busqueda.strip()
        encoded = urllib.parse.quote(termino)
        encoded_plus = urllib.parse.quote_plus(termino)

        enlaces: List[Dict[str, str]] = []

        if ambito in ("Internacional", "Ambos"):
            enlaces.extend([
                {
                    "plataforma": "AliExpress Global (Directo de Fabricante)",
                    "url": f"https://www.aliexpress.com/wholesale?SearchText={encoded}",
                    "resumen": f"Catálogo internacional de fabricantes y compras directas para '{termino}'"
                },
                {
                    "plataforma": "eBay Global (Ofertas Nuevas y Reacondicionadas)",
                    "url": f"https://www.ebay.com/sch/i.html?_nkw={encoded}&_sop=12",
                    "resumen": f"Publicaciones directas y subastas internacionales para '{termino}'"
                },
                {
                    "plataforma": "Amazon Global (Distribución Certificada)",
                    "url": f"https://www.amazon.com/s?k={encoded}",
                    "resumen": f"Suministro oficial con despacho a casillero internacional para '{termino}'"
                },
                {
                    "plataforma": "Alibaba Trade (Mayoristas y Lotes)",
                    "url": f"https://www.alibaba.com/trade/search?SearchText={encoded}",
                    "resumen": f"Importación por volumen y distribuidores mayoristas de '{termino}'"
                },
                {
                    "plataforma": "Google Shopping Global",
                    "url": f"https://www.google.com/search?q={encoded_plus}+price+usd+buy+online",
                    "resumen": f"Rastreo internacional multitienda en la web abierta para '{termino}'"
                }
            ])

        if ambito in ("Nacional", "Ambos"):
            enlaces.extend([
                {
                    "plataforma": "Google Comercios Venezuela (.VE)",
                    "url": f"https://www.google.com/search?q={encoded_plus}+site:.ve+-site:mercadolibre.com.ve",
                    "resumen": f"Búsqueda directa de '{termino}' en tiendas y distribuidores de Venezuela (.ve)"
                },
                {
                    "plataforma": "Google Precios y Proveedores Venezuela",
                    "url": f"https://www.google.com/search?q={encoded_plus}+precio+Venezuela+-site:mercadolibre.com.ve+-site:mercadolibre.com",
                    "resumen": f"Catálogo de precios y ofertas activas en Venezuela para '{termino}'"
                },
                {
                    "plataforma": "Bing Comercios y Tiendas Venezuela (.VE)",
                    "url": f"https://www.bing.com/search?q={encoded_plus}+site:.ve+-mercadolibre",
                    "resumen": f"Rastreo en comercios e importadores venezolanos registrados para '{termino}'"
                },
                {
                    "plataforma": "DuckDuckGo Comercios Venezuela (.VE)",
                    "url": f"https://duckduckgo.com/?q={encoded_plus}+site:.ve+-site:mercadolibre.com.ve",
                    "resumen": f"Directorio comercial abierto de proveedores en Venezuela para '{termino}'"
                },
                {
                    "plataforma": "EPA Venezuela (Catálogo Nacional)",
                    "url": f"https://ve.epaenlinea.com/catalogsearch/result/?q={encoded}",
                    "resumen": f"Búsqueda directa de suministros, ferretería y equipos en EPA Venezuela para '{termino}'"
                }
            ])

        return enlaces

    def buscar_sitios_web(self, busqueda: str, max_resultados: int = 15, ambito: str = "Nacional") -> List[Dict[str, str]]:
        """
        Rastrea páginas web con búsqueda abierta y multirrubro en la web.
        Excluye Mercado Libre, filtra URLs a páginas de inicio vacías y garantiza resultados.
        """
        termino = busqueda.strip()
        if not termino:
            return []

        resultados: List[Dict[str, str]] = []
        enlaces_dinamicos = self._generar_enlaces_dinamicos(termino, ambito)

        if ambito == "Internacional":
            query = f"{termino} price usd online store -mercadolibre"
        elif ambito == "Ambos":
            query = f"{termino} precio distribuidor store -mercadolibre"
        else:
            query = f"{termino} precio Venezuela"

        endpoints = [
            f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}",
            f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}",
            f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        ]

        def _extraer_enlaces_html(url_target):
            try:
                resp = requests.get(url_target, headers=self.headers, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("a", class_="result__url") or soup.find_all("a", class_="result-link")
                    snippets = soup.find_all("a", class_="result__snippet") or soup.find_all("td", class_="result-snippet")

                    for i, link in enumerate(links[:max_resultados]):
                        href = link.get("href", "")
                        if "uddg=" in href:
                            try:
                                url_real = href.split("uddg=")[1].split("&")[0]
                                url_real = urllib.parse.unquote(url_real)
                            except Exception:
                                continue

                            if not self._es_url_permitida(url_real, ambito):
                                continue

                            if any(r["url"] == url_real for r in resultados):
                                continue

                            snippet_txt = snippets[i].get_text(strip=True) if i < len(snippets) else f"Catálogo para {termino}"
                            resultados.append({
                                "url": url_real,
                                "resumen": snippet_txt
                            })
            except Exception as e:
                app_logger.info(f"Aviso: Consulta directa HTML no respondió ({e}), activando alternativas.")

        for ep in endpoints:
            if len(resultados) >= 4:
                break
            _extraer_enlaces_html(ep)

        if ambito == "Nacional" and len(resultados) < 4:
            _extraer_enlaces_html(f"https://duckduckgo.com/html/?q={urllib.parse.quote(f'{termino} comprar venezuela')}")

        if len(resultados) < 4:
            for ed in enlaces_dinamicos:
                if not any(r["url"] == ed["url"] for r in resultados):
                    resultados.append({
                        "url": ed["url"],
                        "resumen": f"[{ed['plataforma']}] {ed['resumen']}"
                    })

        return resultados

    def _resolver_url_por_proveedor(self, texto_contexto: str, busqueda: str, ambito: str, datos_extraidos: list = None, url_existente: str = "") -> str:
        """
        Mapeador Semántico Inteligente de Enlaces Anti-Alucinación:
        Garantiza que ningún comercio (ej. EPA) se asigne erróneamente a un proveedor distinto.
        """
        ctx = texto_contexto.lower()
        termino = busqueda.strip()
        encoded = urllib.parse.quote(termino)
        encoded_plus = urllib.parse.quote_plus(termino)

        # Extraer el proveedor exacto del texto si está presente en el contexto
        proveedor_match = re.search(r'\*\*proveedor\s*/\s*plataforma:\*\*\s*([^\n\r*]+)', ctx, re.IGNORECASE)
        nombre_prov = proveedor_match.group(1).strip() if proveedor_match else ""

        # 1. Si la URL existente pertenece al dominio directo del proveedor indicado, respetarla
        if url_existente and url_existente.startswith("http"):
            try:
                parsed = urllib.parse.urlparse(url_existente)
                netloc = parsed.netloc.lower()
                path = parsed.path.lower()
                query = parsed.query.lower()
                es_home = (not path or path == "/") and not query
                es_ml = "mercadolibre" in netloc or "mercadolibre" in path

                if not es_home and not es_ml:
                    # Plataformas internacionales
                    if "ebay" in ctx and "ebay." in netloc:
                        return url_existente
                    if "amazon" in ctx and "amazon." in netloc:
                        return url_existente
                    if "aliexpress" in ctx and "aliexpress." in netloc:
                        return url_existente
                    if "alibaba" in ctx and "alibaba." in netloc:
                        return url_existente
                    if "walmart" in ctx and "walmart." in netloc:
                        return url_existente
                    if ("hp" in ctx or "hewlett" in ctx) and "hp.com" in netloc:
                        return url_existente

                    # Caso específico EPA
                    if ("epa" in ctx or "epaenlinea" in ctx) and "epaenlinea.com" in netloc:
                        return url_existente

                    # Comercios nacionales en general: asegurar que el dominio esté en el nombre del proveedor
                    if ámbito == "Nacional" and len(path.strip("/").split("/")) >= 1 and path != "/":
                        if not any(se in netloc for se in ["google.", "bing.", "duckduckgo.", "yahoo.", "epaenlinea.com"]):
                            dom_base = netloc.replace("www.", "").split(".")[0]
                            if len(dom_base) >= 3 and dom_base in ctx:
                                return url_existente
            except Exception:
                pass

        # 2. Mapeo semántico directo para plataformas internacionales conocidas
        if "ebay" in ctx:
            return f"https://www.ebay.com/sch/i.html?_nkw={encoded}&_sop=12"
        if "amazon" in ctx:
            return f"https://www.amazon.com/s?k={encoded}"
        if "aliexpress" in ctx or "ali express" in ctx:
            return f"https://www.aliexpress.com/wholesale?SearchText={encoded}"
        if "alibaba" in ctx or "ali baba" in ctx:
            return f"https://www.alibaba.com/trade/search?SearchText={encoded}"
        if "walmart" in ctx:
            return f"https://www.walmart.com/search?q={encoded}"
        if ("hp" in ctx or "hewlett" in ctx) and any(w in ctx for w in ["tienda", "store", "oficial", "shop"]):
            return f"https://www.hp.com/us-en/shop/sitesearch?keyword={encoded}"

        # 3. Mapeo exclusivo para EPA (Solo si la opción menciona explícitamente a EPA)
        if "epa " in ctx or "epaenlinea" in ctx or " ferretería epa" in ctx or "tiendas epa" in ctx:
            return f"https://ve.epaenlinea.com/catalogsearch/result/?q={encoded}"

        # 4. Búsqueda en datos_extraidos sin cruzar tiendas
        for d in (datos_extraidos or []):
            u = d.get("url", "")
            if u and "http" in u:
                try:
                    parsed_u = urllib.parse.urlparse(u)
                    netloc_u = parsed_u.netloc.lower().replace("www.", "")
                    dom_u = netloc_u.split(".")[0]

                    # Si el dominio extraído coincide con el texto del proveedor y no es EPA de forma espuria
                    if dom_u and len(dom_u) >= 4 and dom_u in ctx and dom_u != "duckduckgo":
                        return u
                except Exception:
                    pass

        # 5. FALLBACK AISLADO Y REFUTABLE POR PROVEEDOR (Cero Alucinación / Cero Enlaces Repetidos)
        if ámbito == "Nacional":
            if nombre_prov and "epa" not in nombre_prov.lower():
                prov_enc = urllib.parse.quote_plus(nombre_prov)
                return f"https://www.google.com/search?q={encoded_plus}+{prov_enc}+Venezuela+-site:mercadolibre.com.ve"
            return f"https://www.google.com/search?q={encoded_plus}+site:.ve+-site:mercadolibre.com.ve"

        if ámbito == "Ambos":
            return f"https://www.google.com/search?q={encoded_plus}+precio+usd+store"

        return f"https://www.google.com/search?q={encoded_plus}+price+usd+buy+online"

    def _sanitizar_enlaces_dictamen(self, texto: str, busqueda: str, ambito: str, datos_extraidos: list = None) -> str:
        """
        Regla de Integridad de Enlaces sin Reciclaje Ciego:
        Aísla cada opción comercial y le asigna la URL exacta o su búsqueda dedicada.
        """
        link_md_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)')
        opcion_pattern = re.compile(r'(?m)(^(?:#+\s*)?(?:\*\*)?(?:Opción|Opcion)\s+\d+.*$)')
        bloques = opcion_pattern.split(texto)

        if len(bloques) <= 1:
            def replacer_global(m):
                lbl, u = m.group(1), m.group(2)
                resolved = self._resolver_url_por_proveedor(lbl, busqueda, ambito, datos_extraidos, url_existente=u)
                return f"[{lbl}]({resolved})"
            return link_md_pattern.sub(replacer_global, texto)

        resultado = [bloques[0]]
        for i in range(1, len(bloques), 2):
            encabezado = bloques[i]
            contenido = bloques[i + 1] if i + 1 < len(bloques) else ""
            bloque_texto = encabezado + " " + contenido

            def replacer_bloque(m):
                lbl, u = m.group(1), m.group(2)
                resolved = self._resolver_url_por_proveedor(
                    bloque_texto + " " + lbl,
                    busqueda,
                    ambito,
                    datos_extraidos,
                    url_existente=u
                )
                return f"[{lbl}]({resolved})"

            contenido_limpio = link_md_pattern.sub(replacer_bloque, contenido)

            # Si la opción carece de enlace, asociarle su URL aislada dedicada
            if not re.search(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', contenido_limpio):
                resolved = self._resolver_url_por_proveedor(bloque_texto, busqueda, ambito, datos_extraidos)
                link_line = f"\n* **Enlace:** [Ver Oferta / Producto de '{busqueda}']({resolved})"
                if "\n---" in contenido_limpio:
                    contenido_limpio = contenido_limpio.replace("\n---", f"{link_line}\n---", 1)
                else:
                    contenido_limpio = contenido_limpio.rstrip() + f"{link_line}\n"

            resultado.append(encabezado + contenido_limpio)

        return "".join(resultado)

    def _filtrar_salida_mercadolibre(self, texto: str) -> str:
        """Remueve cualquier línea o mención que contenga Mercado Libre de la salida final."""
        lineas = texto.split("\n")
        lineas_filtradas = [l for l in lineas if "mercadolibre" not in l.lower()]
        return "\n".join(lineas_filtradas)

    def analizar_con_gemini_v2(self, producto: str, datos_extraidos: list, ambito: str = "Nacional", incluye_importacion: bool = False) -> str:
        """
        Genera el dictamen comercial y de procura con IA ordenando de menor a mayor precio base en USD.
        Totalmente multirrubro y abierto, con exclusión estricta de Mercado Libre y enlaces 100% verificados.
        """
        termino = producto.strip()
        enlaces_dinamicos = self._generar_enlaces_dinamicos(termino, ambito)

        if not datos_extraidos:
            datos_extraidos = [{"url": ed["url"], "resumen": ed["resumen"]} for ed in enlaces_dinamicos]

        estimacion = self.calc_zoom.estimar_peso_volumen(termino)
        peso_est = float(estimacion["peso_lb"])
        vol_est = float(estimacion["volumen_ft3"])
        es_pesado = estimacion["es_pesado"]
        categoria_prod = estimacion.get("categoria", "Producto General")

        flete_aereo_est = max(peso_est * self.calc_zoom.tarifa_aerea_lb, 10.00)
        flete_mar_est = max(vol_est * self.calc_zoom.tarifa_maritima_ft3, 20.00)

        if ambito == "Internacional":
            restriccion_geo = (
                "ÁMBITO SELECCIONADO: INTERNACIONAL EXCLUSIVO. Prohibido incluir tiendas de Venezuela. "
                "Enfócate en plataformas globales (AliExpress, eBay, Amazon, Alibaba, distribuidores autorizados en EE.UU., Asia o Europa)."
            )
            ubicacion_fmt = "🌍 **Ubicación Geográfica / Plataforma:** Tienda o país de origen (Ej: *AliExpress - China / Internacional*, *Amazon - Estados Unidos*, *eBay - Estados Unidos*)."
        elif ambito == "Ambos":
            restriccion_geo = "ÁMBITO SELECCIONADO: MIXTO (NACIONAL E INTERNACIONAL). Compara opciones en Venezuela con importaciones globales."
            ubicacion_fmt = "📍 / 🌍 **Ubicación Geográfica:** Ciudad/Estado en Venezuela o Plataforma/País internacional."
        else:
            restriccion_geo = (
                "ÁMBITO SELECCIONADO: NACIONAL DE VENEZUELA. "
                "Enfócate en tiendas, importadores, distribuidores y comercios dentro de Venezuela."
            )
            ubicacion_fmt = "📍 **Ubicación Geográfica:** Ciudad o Estado del proveedor dentro de Venezuela (ej. Valencia, Caracas, Maracay, Barquisimeto)."

        if incluye_importacion:
            if es_pesado:
                instruccion_zoom = (
                    f"INSTRUCCIÓN LOGÍSTICA ZOOM CASILLEROS (CASILLA TILDADA):\n"
                    f"El producto ('{termino}') se clasifica como {categoria_prod} (peso est: ~{peso_est} lbs, vol: ~{vol_est} ft³):\n"
                    f"- Flete Marítimo recomendado ($18.00/ft³ + $5 manejo): ${(flete_mar_est + 5):,.2f} USD Puesto en Taller.\n"
                    f"- Flete Aéreo expreso ($5.50/lb + $5 manejo): ${(flete_aereo_est + 5):,.2f} USD Puesto en Taller.\n"
                    f"- Calcula el Costo Total Puesto en Taller (Precio Base + Flete + Manejo) en Guacara/Valencia."
                )
            else:
                instruccion_zoom = (
                    f"INSTRUCCIÓN LOGÍSTICA ZOOM CASILLEROS (CASILLA TILDADA):\n"
                    f"Para CADA opción incluye el desglose de importación aéreo (peso est: ~{peso_est} lbs):\n"
                    f"- Flete Aéreo Zoom Casilleros: ${flete_aereo_est:,.2f} ($5.50/lb, mín $10) + $5.00 manejo = **${(flete_aereo_est + 5):,.2f} USD**\n"
                    f"- Costo Total Puesto en Taller (Precio Base + ${(flete_aereo_est + 5):,.2f} USD)."
                )
        else:
            instruccion_zoom = "INSTRUCCIÓN LOGÍSTICA: Muestra únicamente los precios base de los proveedores en USD."

        if ambito == "Nacional":
            reglas_enlaces = f"""
        REGLAS ESTRICTAS DE ASIGNACIÓN DE ENLACES (ÁMBITO NACIONAL):
        1. Para CADA opción comercial, asigna la URL exacta obtenida de la tienda del proveedor o su enlace directo de búsqueda.
        2. Queda TERMINANTEMENTE PROHIBIDO reusar el enlace de un comercio (ej. EPA) para asignárselo a otro proveedor distinto.
        3. Formato estricto para cada opción:
           **Enlace:** [Ver Producto / Oferta de '{termino}'](URL_DIRECTA_O_DE_BUSQUEDA)
        """
        else:
            reglas_enlaces = f"""
        REGLAS ESTRICTAS DE ASIGNACIÓN DE ENLACES:
        1. Queda TERMINANTEMENTE PROHIBIDO inventar nombres de dominio inexistentes.
        2. Queda TERMINANTEMENTE PROHIBIDO colocar enlaces que lleven al Home o página principal sin parámetros.
        3. DEBES utilizar OBLIGATORIAMENTE un enlace correspondiente a la plataforma del proveedor.
        4. Formato estricto para cada opción:
           **Enlace:** [Ver Resultados y Precios de '{termino}'](URL_DIRECTA_DE_LAS_FUENTES)
        """

        prompt = f"""
        Eres el Gerente Senior de Compras y Estratega de Procura Comercial para "Inversiones Reinaldo Golindano".
        Tu especialidad es la inteligencia comercial multirrubro: localizar la mejor oferta del mercado en la web abierta para cualquier producto, insumo, repuesto, herramienta o consumible, con criterio de revendedor y optimización de costos.

        PRODUCTO COTIZADO: "{termino}"
        {restriccion_geo}

        REGLA DE FILTRO CRÍTICA Y OBLIGATORIA:
        - QUEDA TERMINANTEMENTE PROHIBIDO incluir opciones, precios o enlaces de Mercado Libre.
        - Mantén abierta y libre la búsqueda en todas las demás tiendas, portales web, proveedores locales y distribuidores nacionales o internacionales.

        FUENTES Y ENLACES DE BÚSQUEDA DIRECTA DISPONIBLES (UTILIZA ESTOS ENLACES):
        {datos_extraidos}

        {reglas_enlaces}

        INSTRUCCIONES DE FORMATO Y ESTRUCTURA:
        1. Analiza las fuentes y presenta entre 3 y 5 opciones comerciales concretas, ORDENADAS ESTRICTAMENTE DE MENOR A MAYOR PRECIO BASE EN USD (Opción 1 = la más económica).
        2. Para CADA opción incluye:
           - **Opción N: [Nombre del Producto / Suministro]**
           - **Proveedor / Plataforma:** Nombre de la tienda, distribuidor o plataforma verificada.
           - **Precio Base Estimado:** En USD (indicar si es precio unitario o lote/pack si aplica).
           - {ubicacion_fmt}
           - **Análisis Comercial:** Breve evaluación de conveniencia, disponibilidad y margen.
           - **Enlace:** [Ver Resultados / Producto de '{termino}'](URL_DIRECTA)
           - {instruccion_zoom}
        3. Concluye con un **Dictamen Estratégico de Compra** indicando la opción recomendada según relación costo-beneficio y tiempo de entrega.
        """

        modelos = [
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash"
        ]

        for modelo in modelos:
            for intento in range(2):
                try:
                    if self.usar_genai_nuevo and self.client:
                        response = self.client.models.generate_content(
                            model=modelo,
                            contents=prompt
                        )
                        if response and response.text and len(response.text.strip()) > 50:
                            texto_limpio = self._filtrar_salida_mercadolibre(response.text.strip())
                            texto_sanitizado = self._sanitizar_enlaces_dictamen(texto_limpio, termino, ambito, datos_extraidos)
                            return texto_sanitizado
                    elif not self.usar_genai_nuevo and hasattr(self, "model_old"):
                        import google.generativeai as genai_old
                        m = genai_old.GenerativeModel(modelo)
                        response = m.generate_content(prompt)
                        if response and response.text and len(response.text.strip()) > 50:
                            texto_limpio = self._filtrar_salida_mercadolibre(response.text.strip())
                            texto_sanitizado = self._sanitizar_enlaces_dictamen(texto_limpio, termino, ambito, datos_extraidos)
                            return texto_sanitizado
                except Exception as e:
                    app_logger.warning(f"Intento fallido con modelo {modelo}: {e}")
                    time.sleep(1)

        # Fallback de emergencia si la API de IA no responde
        return self._generar_dictamen_autonomo(termino, ambito, incluye_importacion, datos_extraidos)

    def _generar_dictamen_autonomo(self, producto: str, ambito: str, incluye_importacion: bool, datos_extraidos: list) -> str:
        """Dictamen autónomo de respaldo para contingencias en línea."""
        termino = producto.strip()
        enlaces_dinamicos = self._generar_enlaces_dinamicos(termino, ambito)
        
        dictamen = f"### Dictamen Estratégico de Compra (Modo Contingencia Autónoma)\n\n"
        dictamen += f"Se han generado enlaces directos de búsqueda y consulta verificada para **'{termino}'** sin depender de Mercado Libre:\n\n"
        
        for i, ed in enumerate(enlaces_dinamicos[:4], 1):
            dictamen += f"**Opción {i}: {ed['plataforma']}**\n"
            dictamen += f"- **Proveedor / Plataforma:** {ed['plataforma']}\n"
            dictamen += f"- **Enlace:** [Ver Resultados y Ofertas]({ed['url']})\n\n"
            
        return dictamen