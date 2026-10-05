"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: ml_scraper.py
Descripción: Rastreador de Mercado Libre Venezuela con motor de extracción Selenium
             (paridad total con Escaneador de Oportunidades v2.2), métricas de precios
             y dictamen de oportunidades con IA.
=============================================================================
"""

import os
import csv
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Any, Optional
from config import SystemConfig
from core.logger import app_logger

try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class MercadoLibreTracker:
    """Rastreador y Analizador de Mercado Libre Venezuela con paridad de motor Selenium."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def _obtener_datos_selenium(self, query: str, max_items: int = 60) -> List[Tuple[str, str, str, str]]:
        """Extrae publicaciones dinámicas de Mercado Libre Venezuela usando Selenium Edge headless."""
        query_encoded = urllib.parse.quote(query.strip())
        url = f"https://listado.mercadolibre.com.ve/{query_encoded}_SortOrder_PRICE*ASC"

        os.environ['WDM_LOG'] = '0'
        options = webdriver.EdgeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-position=-32000,-32000")
        options.add_argument("--window-size=1200,900")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(EdgeChromiumDriverManager().install(), log_output=os.devnull)
        driver = webdriver.Edge(service=service, options=options)
        resultados: List[Tuple[str, str, str, str]] = []

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 8)
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ui-search-layout__item")))
            except Exception:
                pass

            # Scroll progresivo para hidratar las cards dinámicas
            for scroll in range(1, 5):
                driver.execute_script(f"window.scrollTo(0, {scroll * 900});")
                time.sleep(0.5)

            items = driver.find_elements(By.CLASS_NAME, "ui-search-layout__item")

            for item in items[:max_items]:
                try:
                    # 1. Título
                    titulo = ""
                    for sel_t in ["h2", ".poly-component__title", ".ui-search-item__title", "h3"]:
                        try:
                            elem = item.find_element(By.CSS_SELECTOR, sel_t)
                            t_text = elem.text.strip()
                            if t_text:
                                titulo = t_text
                                break
                        except Exception:
                            continue

                    # 2. Precio
                    precio = "N/A"
                    try:
                        frac_elem = item.find_element(By.CLASS_NAME, "andes-money-amount__fraction")
                        try:
                            sym_elem = item.find_element(By.CLASS_NAME, "andes-money-amount__currency-symbol")
                            simbolo = sym_elem.text.strip()
                        except Exception:
                            simbolo = "$"
                        precio = f"{simbolo}{frac_elem.text.strip()}"
                    except Exception:
                        pass

                    # 3. Ubicación
                    ubicacion = "Venezuela"
                    for sel_ub in [".poly-component__location", ".ui-search-item__location"]:
                        try:
                            elem_ub = item.find_element(By.CSS_SELECTOR, sel_ub)
                            ub_text = elem_ub.text.strip()
                            if ub_text:
                                ubicacion = ub_text
                                break
                        except Exception:
                            continue

                    # 4. Enlace
                    link = ""
                    try:
                        link = item.find_element(By.TAG_NAME, "a").get_attribute("href") or ""
                        # Limpiar parámetros de tracking excesivos
                        if "#" in link:
                            link = link.split("#")[0]
                    except Exception:
                        pass

                    if titulo and link:
                        resultados.append((titulo, precio, ubicacion, link))
                except Exception:
                    continue

        except Exception as e:
            app_logger.error(f"Error en extracción Selenium Mercado Libre: {e}")
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        return resultados

    def _obtener_datos_fallback_requests(self, query: str) -> List[Tuple[str, str, str, str]]:
        """Fallback secundario basado en HTML directo."""
        query_encoded = urllib.parse.quote(query.strip())
        url = f"https://listado.mercadolibre.com.ve/{query_encoded}_SortOrder_PRICE*ASC"
        resultados = []

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.find_all(["li", "div"], class_=re.compile(r"ui-search-layout__item|poly-card"))
                for item in items[:40]:
                    try:
                        title_el = item.find(["h2", "h3", "a"], class_=re.compile(r"ui-search-item__title|poly-component__title"))
                        titulo = title_el.get_text(strip=True) if title_el else ""

                        link_el = item.find("a", href=True)
                        link = link_el["href"] if link_el else ""

                        frac_el = item.find(class_=re.compile(r"andes-money-amount__fraction"))
                        sim_el = item.find(class_=re.compile(r"andes-money-amount__currency-symbol"))
                        simbolo = sim_el.get_text(strip=True) if sim_el else "$"
                        precio = f"{simbolo}{frac_el.get_text(strip=True)}" if frac_el else "N/A"

                        loc_el = item.find(class_=re.compile(r"ui-search-item__location|poly-component__location"))
                        ubicacion = loc_el.get_text(strip=True) if loc_el else "Venezuela"

                        if titulo and link:
                            resultados.append((titulo, precio, ubicacion, link))
                    except Exception:
                        continue
        except Exception as e:
            app_logger.warning(f"Fallback requests HTML falló: {e}")

        return resultados

    def buscar_mercado_libre(self, query: str, max_items: int = 60) -> List[Tuple[str, str, str, str]]:
        """
        Rastrea publicaciones en Mercado Libre Venezuela ordenadas por menor precio.
        Utiliza el motor de Selenium para paridad idéntica con el Escaneador de Oportunidades v2.2.
        """
        resultados = []
        if SELENIUM_AVAILABLE:
            try:
                resultados = self._obtener_datos_selenium(query, max_items=max_items)
            except Exception as e:
                app_logger.error(f"Falla inicializando Selenium: {e}")

        if not resultados:
            app_logger.info("Activando fallback secundario para Mercado Libre...")
            resultados = self._obtener_datos_fallback_requests(query)

        return resultados

    @classmethod
    def calcular_metricas(cls, resultados: List[Tuple[str, str, str, str]]) -> Dict[str, float]:
        """Calcula precio mínimo, promedio y máximo a partir de los datos capturados."""
        precios_num = []
        for row in resultados:
            precio_raw = row[1]
            # Extraer dígitos y separadores
            num_str = "".join([c for c in precio_raw if c.isdigit() or c in ".,"])
            if not num_str:
                continue
            # Normalizar formatos: 1.250,50 o 12.50
            if "," in num_str and "." in num_str:
                num_str = num_str.replace(".", "").replace(",", ".")
            elif "," in num_str:
                num_str = num_str.replace(",", ".")

            try:
                val = float(num_str)
                if val > 0:
                    precios_num.append(val)
            except ValueError:
                continue

        if precios_num:
            return {
                "min": round(min(precios_num), 2),
                "avg": round(sum(precios_num) / len(precios_num), 2),
                "max": round(max(precios_num), 2),
                "count": len(precios_num)
            }
        return {"min": 0.0, "avg": 0.0, "max": 0.0, "count": 0}

    def analizar_con_ia(self, query: str, resultados: List[Tuple[str, str, str, str]]) -> str:
        """Sintetiza y dictamina con Gemini AI las mejores opciones de compra con enlaces directos."""
        if not resultados:
            return "No hay publicaciones de Mercado Libre cargadas para analizar."

        top_15 = resultados[:15]
        lista_texto = "\n".join([f"- {r[0]} | Precio: {r[1]} | Ubicación: {r[2]} | Enlace: {r[3]}" for r in top_15])

        prompt = f"""
        Actúa como un experto analista senior de compras, negocios e inversiones en Venezuela para 'Inversiones Reinaldo Golindano' (taller especializado en fotocopiadoras, impresoras y consumibles en Carabobo/Venezuela).
        El usuario busca adquirir o monitorear: "{query}"

        A continuación tienes la selección de las publicaciones reales ordenadas por menor precio capturadas de Mercado Libre Venezuela:
        {lista_texto}

        ESTRUCTURA OBLIGATORIA DEL DICTAMEN:
        Organiza tu respuesta de forma ejecutiva, técnica y limpia, agrupando las recomendaciones en las siguientes categorías de compra:

        1. **Opción 1: Ahorro Máximo (Menor Precio / Rentabilidad para Taller)**
           - Título de la publicación: [Título exacto]
           - Precio de compra: [Precio capturado]
           - 📍 Ubicación del vendedor: [Ciudad o estado]
           - Justificación técnica: Por qué representa la alternativa de costo más bajo y su conveniencia económica.
           - **Enlace:** [Ver Publicación en Mercado Libre](URL)

        2. **Opción 2: Calidad de Marca (Original / Producto Certificado)**
           - Título de la publicación: [Título exacto de la opción de mayor respaldo/marca original]
           - Precio de compra: [Precio capturado]
           - 📍 Ubicación del vendedor: [Ciudad o estado]
           - Justificación técnica: Ventajas en durabilidad, garantía y cero riesgo para los equipos de los clientes.
           - **Enlace:** [Ver Publicación en Mercado Libre](URL)

        3. **Opción 3: Mayor Conveniencia (Logística / Reputación / Disponibilidad)**
           - Título de la publicación: [Título exacto]
           - Precio de compra: [Precio capturado]
           - 📍 Ubicación del vendedor: [Ciudad o estado]
           - Justificación técnica: Balance óptimo entre tiempo de entrega, reputación del vendedor y precio unitario.
           - **Enlace:** [Ver Publicación en Mercado Libre](URL)

        4. **Dictamen de Compra y Recomendación Estratégica:**
           - Veredicto ejecutivo recomendando cuál de las opciones adquirir según la urgencia del taller y margen comercial.

        REGLA ESTRICTA DE ENLACES:
        Cada una de las opciones recomendadas DEBE incluir obligatoriamente su enlace interactivo completo con formato:
        **Enlace:** [Ver Publicación en Mercado Libre](URL)
        """

        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                from google import genai
                client = genai.Client(api_key=SystemConfig.GEMINI_API_KEY)
                resp = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                err_msg = str(e)
                app_logger.warning(f"Intento {intento}/{max_intentos} dictamen ML con Gemini: {err_msg}")
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                    time.sleep(2 * intento)
                else:
                    break

        # Fallback estructurado en caso de congestión de la API de IA
        return self._generar_dictamen_ml_fallback(query, top_15)

    def _generar_dictamen_ml_fallback(self, query: str, top_items: List[Tuple[str, str, str, str]]) -> str:
        """Dictamen estructurado autónomo para Mercado Libre cuando la API de IA presenta alta demanda."""
        if not top_items:
            return "No se encontraron publicaciones disponibles para generar el dictamen."

        # Buscar la mejor opción económica (Ahorro Máximo)
        item_ahorro = top_items[0]

        # Buscar opción de calidad / original
        item_marca = None
        for it in top_items:
            if any(w in it[0].lower() for w in ["original", "sellado", "genuino", "canon", "hp", "epson"]):
                item_marca = it
                break
        if not item_marca:
            item_marca = top_items[1] if len(top_items) > 1 else item_ahorro

        # Buscar opción balanceada
        item_conveniencia = top_items[2] if len(top_items) > 2 else (top_items[1] if len(top_items) > 1 else item_ahorro)

        lineas = [
            f"### Dictamen de Oportunidades Nacionales: '{query}'\n",
            "Evaluación de compras para Inversiones Reinaldo Golindano basada en las mejores ofertas capturadas en Mercado Libre Venezuela:\n",
            "#### 1. Opción 1: Ahorro Máximo (Menor Precio)",
            f"- **Publicación:** {item_ahorro[0]}",
            f"- **Precio:** {item_ahorro[1]}",
            f"- 📍 **Ubicación:** {item_ahorro[2]}",
            "- **Análisis:** Opción de costo mínimo para maximizar margen operativo del taller.",
            f"- **Enlace:** [Ver Publicación en Mercado Libre]({item_ahorro[3]})\n",
            "#### 2. Opción 2: Calidad de Marca (Original / Garantizada)",
            f"- **Publicación:** {item_marca[0]}",
            f"- **Precio:** {item_marca[1]}",
            f"- 📍 **Ubicación:** {item_marca[2]}",
            "- **Análisis:** Insumo o repuesto con respaldo de marca, ideal para clientes corporativos de alta exigencia.",
            f"- **Enlace:** [Ver Publicación en Mercado Libre]({item_marca[3]})\n",
            "#### 3. Opción 3: Mayor Conveniencia (Balance Precio / Ubicación)",
            f"- **Publicación:** {item_conveniencia[0]}",
            f"- **Precio:** {item_conveniencia[1]}",
            f"- 📍 **Ubicación:** {item_conveniencia[2]}",
            "- **Análisis:** Excelente alternativa intermedia con despacho rápido y disponibilidad inmediata.",
            f"- **Enlace:** [Ver Publicación en Mercado Libre]({item_conveniencia[3]})\n",
            "#### 4. Dictamen de Compra",
            "💡 **Recomendación:** Se sugiere proceder con la **Opción 1: Ahorro Máximo** para recargas o servicios estándar del taller, reservando la **Opción 2: Calidad de Marca** para ventas directas a empresas o contratos corporativos."
        ]
        return "\n".join(lineas)

    @classmethod
    def exportar_csv(cls, filepath: str, resultados: List[Tuple[str, str, str, str]]) -> bool:
        """Exporta los hallazgos a formato CSV compatible con Google Sheets y Excel."""
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerow(["Publicación", "Precio", "Ubicación", "Enlace URL"])
                for row in resultados:
                    writer.writerow(row)
            return True
        except Exception as e:
            app_logger.error(f"Error exportando CSV: {e}")
            return False
