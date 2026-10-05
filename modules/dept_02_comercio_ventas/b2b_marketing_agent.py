"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: b2b_marketing_agent.py
Descripción: Agente de Publicidad y Marketing Estratégico B2B.
             Generación de contenidos corporativos semanales con banco de
             105 temas no repetitivos para un horizonte de 100+ publicaciones.
             Estilo formal ejecutivo dirigido a gerentes y administradores.
=============================================================================
"""

import os
import json
import random
import datetime
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SystemConfig
from core.base_agent import BaseAgent, AgentResponse
from core.logger import app_logger

# Importar banco de temas corporativos
from modules.dept_02_comercio_ventas.banco_temas_b2b import (
    seleccionar_temas_para_lote,
    BANCO_TEMAS_B2B,
)


# ---------------------------------------------------------------------------
# INSTRUCCIÓN DE SISTEMA — ROL SENIOR B2B
# ---------------------------------------------------------------------------

INSTRUCCION_SISTEMA_B2B = """
Eres el Director de Marketing Estratégico Corporativo de 'Inversiones Reinaldo Golindano',
empresa especializada en gestión de flotas de impresión, servicio técnico de alta precisión
y procura de consumibles para el sector empresarial e industrial de Carabobo
(Valencia, Guacara, San Diego). Tu perfil: Especialista Senior con 15 años en marketing B2B.

PRINCIPIOS IRRENUNCIABLES DE ESTILO:
1. Tono: Formal, analítico, ejecutivo. Dirigido a Gerentes de Compras, Jefes de Sistemas
   y Administradores de empresas medianas y grandes de Carabobo.
2. Vocabulario: Corporativo, preciso y de alto valor consultivo. Sin lenguaje coloquial.
3. Emojis: PROHIBIDO el uso excesivo de emojis o iconografía infantil. Máximo 1 símbolo
   técnico por bloque de texto. NO usar: emojis festivos, caritas, fuegos, cohetes ni similares.
4. Estructura: Párrafos completos y bien argumentados. NO listas de emojis.
5. Foco: Continuidad operativa, impacto financiero, reducción de costos ocultos, SLA.
6. Cierre: Llamada a la acción formal y directa hacia WhatsApp corporativo.
7. Formato: Texto limpio para LinkedIn, Instagram empresarial y WhatsApp corporativo.
"""


class B2BMarketingAgent(BaseAgent):
    """
    Agente de Marketing B2B y Publicidad Estratégica.
    Genera publicaciones corporativas formales para gerentes de Carabobo
    utilizando un banco de 105 temas con memoria anti-repetición integrada.
    """

    # Mapeo de carpetas de fotos reales en modo solo lectura
    MAPEO_CARPETAS = {
        "Epson EcoTank":    os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Epson eco Tank"),
        "Fusor":            os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Fusor"),
        "Modulo de Imagen": os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Modulo de imagen"),
        "Reparaciones":     os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Reparaciones"),
        "Tiqueras Epson":   os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Tikeras epson"),
        "Toner":            os.path.join(SystemConfig.RUTA_PUBLICIDAD_IMAGENES, "Toner"),
    }

    def __init__(self):
        super().__init__(
            agent_id="publicitario_b2b",
            name="Agente Publicitario B2B Senior",
            department="Comercio y Ventas",
            description=(
                "Genera contenido corporativo formal B2B utilizando un banco de 105 temas "
                "estratégicos no repetitivos. Estilo ejecutivo para gerentes de Carabobo."
            ),
        )

    # ------------------------------------------------------------------
    # Conexión exacta a Google Sheets (idéntica al app.py del escritorio)
    # ------------------------------------------------------------------

    def _conectar_google_sheets(self):
        """Conecta con la matriz de Google Sheets usando la misma lógica del ejecutable."""
        posibles_rutas = [
            os.path.join(getattr(SystemConfig, "BASE_DIR", "."), "service_account.json"),
            "service_account.json",
            os.path.join(r"C:\Users\TRADING_PRO\Desktop\Prueba_Antigravity", "service_account.json"),
            os.path.join(r"C:\Users\TRADING_PRO\Desktop\publicidad\Ejecutable publicidad", "service_account.json")
        ]
        
        path_creds = None
        for r in posibles_rutas:
            if os.path.exists(r):
                path_creds = r
                break

        if not path_creds:
            raise FileNotFoundError("No se encontró el archivo 'service_account.json' en ninguna de las rutas de respaldo.")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(path_creds, scope)
        gc = gspread.authorize(creds)
        return gc.open("Matriz_Contenido_Marketing_V3").sheet1

    def _obtener_siguiente_id(self, sheet) -> int:
        """Lee la columna A, ignora encabezados no numéricos y retorna el próximo ID."""
        columna_a = sheet.col_values(1)
        numeros = [int(v.strip()) for v in columna_a if str(v).strip().isdigit()]
        return (max(numeros) + 1) if numeros else 1

    def seleccionar_foto_real(self, categoria: str) -> Optional[str]:
        """Selecciona una fotografía real de la subcarpeta correspondiente (solo lectura)."""
        carpeta = self.MAPEO_CARPETAS.get(categoria, self.MAPEO_CARPETAS["Reparaciones"])

        if not os.path.exists(carpeta):
            carpeta = self.MAPEO_CARPETAS["Reparaciones"]

        if not os.path.exists(carpeta):
            return None

        exts = (".jpg", ".jpeg", ".png", ".webp")
        archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(exts)]

        if not archivos and carpeta != self.MAPEO_CARPETAS["Reparaciones"]:
            carpeta = self.MAPEO_CARPETAS["Reparaciones"]
            if os.path.exists(carpeta):
                archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(exts)]

        if archivos:
            return os.path.join(carpeta, random.choice(archivos))
        return None

    def subir_imagen_a_imgbb(self, ruta_imagen: str) -> str:
        """Sube la imagen seleccionada al CDN público de ImgBB."""
        url = "https://api.imgbb.com/1/upload"
        imgbb_key = "b9b7b0521bf51fd400cb94e23b1f49d1"
        with open(ruta_imagen, "rb") as f:
            resp = requests.post(url, data={"key": imgbb_key}, files={"image": f})
        if resp.status_code != 200:
            raise Exception(f"Error HTTP {resp.status_code} al subir a ImgBB: {resp.text}")
        res = resp.json()
        if res.get("success"):
            return res["data"]["url"]
        raise Exception(f"Error ImgBB: {res}")

    def generar_enlace_whatsapp(self, tema: str = "asistencia técnica") -> str:
        """Crea el enlace de WhatsApp corporativo limpio y directo."""
        num = SystemConfig.EMISOR_TELEFONO.replace("-", "").replace(".", "").replace(" ", "")
        if num.startswith("0"):
            num = "58" + num[1:]
        elif not num.startswith("58"):
            num = "58" + num

        # Retorna únicamente el enlace base limpio sin texto codificado kilométrico
        return f"https://wa.me/{num}"

    def calcular_proximas_fechas_l_m_v(self, cantidad: int = 3) -> List[str]:
        """Calcula las próximas fechas para Lunes, Miércoles y Viernes."""
        fechas = []
        hoy = datetime.date.today()
        dias_objetivo = [0, 2, 4]
        contador = 1
        while len(fechas) < cantidad:
            dia = hoy + datetime.timedelta(days=contador)
            if dia.weekday() in dias_objetivo:
                fechas.append(dia.strftime("%Y-%m-%d"))
            contador += 1
        return fechas

    def _construir_prompt_corporativo(self, tema: dict, historial_titulos: list) -> str:
        """Construye el prompt de redacción para un tema del banco corporativo."""
        historial_str = (
            "\n".join([f"- {t}" for t in historial_titulos[-15:] if t])
            if historial_titulos
            else "Sin historial previo."
        )

        return f"""
Redacta una publicación corporativa B2B completa para 'Inversiones Reinaldo Golindano'.
Contacto directo WhatsApp empresarial: {self.generar_enlace_whatsapp(tema.get('titulo_sugerido',''))}

TEMA ASIGNADO DEL BANCO ESTRATÉGICO:
Pilar temático: {tema['pilar']}
Título orientativo: {tema['titulo_sugerido']}
Enfoque de contenido: {tema['enfoque']}
Palabras clave a trabajar: {', '.join(tema['palabras_clave'])}

HISTORIAL DE TITULOS RECIENTES (NO repetir estos enfoques):
{historial_str}

ESTRUCTURA REQUERIDA DEL COPY:
1. Párrafo de apertura: Plantear el problema o contexto financiero/operativo que enfrenta la empresa objetivo.
2. Párrafo de desarrollo: Explicar el impacto de no atender este problema y la solución especializada que ofrece Inversiones Reinaldo Golindano.
3. Párrafo de cierre con llamada a la acción formal hacia WhatsApp: {self.generar_enlace_whatsapp(tema.get('titulo_sugerido',''))}
4. Hashtags profesionales B2B (máximo 6): etiquetas del sector industrial de Carabobo.

REGLAS ADICIONALES:
- Longitud: Entre 180 y 320 palabras. Denso en información de valor, sin relleno.
- El texto debe sonar como un artículo de consultoría industrial, no como publicidad agresiva.
- NO incluir saludo de apertura del tipo "¡Hola!" o "Buenos días".
- Mención geográfica obligatoria: Valencia, Guacara o San Diego (Carabobo).

Devuelve ÚNICAMENTE el texto del copy. Sin explicaciones, sin prefijos, sin bloques de código.
"""

    def execute(self, task_type: str, payload: Dict[str, Any]) -> AgentResponse:
        app_logger.info(f"Agente B2B ejecutando tarea: {task_type}")

        if task_type == "generate_weekly_batch":
            id_inicio = payload.get("siguiente_id", 1)
            historial = payload.get("historial_copys", [])
            return self.generar_lote_semanal(id_inicio=id_inicio, historial_copys=historial)
        elif task_type == "generate_campaign_copy":
            tema = payload.get("topic", "Auditoría de flota de impresión en Carabobo")
            canal = payload.get("channel", "WhatsApp / LinkedIn Empresarial")
            return self.generar_copy_especifico(tema, canal)
        elif task_type == "generate_proposal":
            return self.generar_propuesta_corporativa(payload)
        else:
            return AgentResponse(success=False, message=f"Tarea '{task_type}' desconocida.")

    # ------------------------------------------------------------------
    # Generación del lote semanal con escritura directa en Google Sheets
    # ------------------------------------------------------------------

    def generar_lote_semanal(
        self, id_inicio: int = 1, historial_copys: list = None
    ) -> AgentResponse:
        """
        Genera 3 publicaciones B2B, sube a ImgBB y hace append_row directo en Google Sheets.
        """
        if historial_copys is None:
            historial_copys = []

        # 1. CONEXIÓN DIRECTA Y OBTENCIÓN DEL SIGUIENTE ID DESDE LA NUBE
        try:
            sheet = self._conectar_google_sheets()
            id_correlativo = self._obtener_siguiente_id(sheet)
            app_logger.info(f"[B2B] Conectado a Google Sheets con éxito. Próximo ID: {id_correlativo}")
        except Exception as e:
            app_logger.error(f"[B2B] Error conectando a Google Sheets: {e}")
            return AgentResponse(
                success=False,
                message=f"Error de conexión con Google Sheets: {str(e)}"
            )

        # Extraer títulos del historial para contexto anti-repetición
        historial_titulos = []
        for copy in historial_copys:
            primera_linea = str(copy).split("\n")[0].strip()[:100]
            if primera_linea:
                historial_titulos.append(primera_linea)

        # Seleccionar 3 temas únicos del banco utilizando el ID real de la nube
        temas_del_lote = seleccionar_temas_para_lote(
            siguiente_id=id_correlativo,
            textos_historicos=historial_copys,
            cantidad=3,
        )

        fechas = self.calcular_proximas_fechas_l_m_v(3)
        dias_semana = ["Lunes", "Miércoles", "Viernes"]

        try:
            lote_resultado = []

            for i, tema in enumerate(temas_del_lote):
                id_actual = id_correlativo + i
                fecha_actual = fechas[i]
                
                prompt = self._construir_prompt_corporativo(tema, historial_titulos)

                copy_text = self.call_gemini(
                    prompt=prompt,
                    system_instruction=INSTRUCCION_SISTEMA_B2B,
                    model_name="gemini-3-flash-preview",
                )

                primera_linea = copy_text.split("\n")[0].strip()[:100]
                historial_titulos.append(primera_linea)

                cat = tema["categoria_imagen"]
                foto = self.seleccionar_foto_real(cat)
                
                # Subir a ImgBB
                url_publica_img = "https://i.ibb.co/Placeholder/default.jpg"
                if foto and os.path.exists(foto):
                    try:
                        url_publica_img = self.subir_imagen_a_imgbb(foto)
                    except Exception as img_err:
                        app_logger.error(f"Error subiendo imagen a ImgBB: {img_err}")

                wa_link = self.generar_enlace_whatsapp(tema["titulo_sugerido"])

                # ESCRIBIR DIRECTAMENTE EN GOOGLE SHEETS
                nueva_fila = [
                    id_actual,              # A: ID_Post
                    copy_text,              # B: Texto_Publicacion
                    url_publica_img,        # C: URL_Imagen
                    "Todas",                # D: Plataforma
                    fecha_actual,           # E: Fecha_Programada
                    "Pendiente",            # F: Estado
                ]
                sheet.append_row(nueva_fila, value_input_option="USER_ENTERED")
                app_logger.info(f"[B2B] Fila registrada en Google Sheets para ID {id_actual}")

                lote_resultado.append({
                    "fecha_programada":  fecha_actual,
                    "dia_semana":        dias_semana[i],
                    "banco_tema_id":     tema["id"],
                    "pilar":             tema["pilar"],
                    "titulo_orientativo": tema["titulo_sugerido"],
                    "categoria":         cat,
                    "foto_asignada":     os.path.basename(foto) if foto else "Sin foto local",
                    "ruta_foto":         foto,
                    "url_imagen":        url_publica_img,
                    "copy":              copy_text,
                    "whatsapp_url":      wa_link,
                })

            self.emit_event(
                "weekly_campaign_generated",
                {
                    "posts_count": len(lote_resultado),
                    "temas_ids": [t["id"] for t in temas_del_lote],
                    "fechas": fechas,
                },
            )

            return AgentResponse(
                success=True,
                data=lote_resultado,
                message=(
                    f"Lote semanal de 3 publicaciones generado y sincronizado "
                    f"exitosamente con Google Sheets (IDs: {id_correlativo} al {id_correlativo+2} enlaces limpios)."
                ),
            )

        except Exception as e:
            app_logger.error(f"Error crítico en la generación o registro de campaña B2B: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                message=f"Error durante el proceso: {str(e)}",
            )

    def generar_copy_especifico(self, tema: str, canal: str) -> AgentResponse:
        prompt = (
            f"Redacta un artículo corporativo B2B formal sobre: '{tema}' "
            f"para {canal}, dirigido a empresas de Carabobo (Valencia, Guacara, San Diego). "
            f"Tono analítico y ejecutivo. Sin emojis excesivos. "
            f"Cierre con llamada a la acción hacia WhatsApp: {self.generar_enlace_whatsapp(tema)}"
        )
        copy_text = self.call_gemini(
            prompt=prompt,
            system_instruction=INSTRUCCION_SISTEMA_B2B,
            model_name="gemini-3-flash-preview",
        )
        return AgentResponse(success=True, data={"copy": copy_text})

    def generar_propuesta_corporativa(self, payload: Dict[str, Any]) -> AgentResponse:
        cliente = payload.get("client_name", "Empresa Cliente")
        flota = payload.get("fleet_details", "Impresoras láser y inyección continua corporativas")
        prompt = (
            f"Redacta una propuesta corporativa formal de servicio de mantenimiento preventivo "
            f"y correctivo para la empresa '{cliente}', con flota: {flota}, "
            f"con cobertura en Carabobo (Valencia, Guacara, San Diego). "
            f"Incluye: alcance del servicio, SLA propuesto, ventajas del contrato mensual y "
            f"datos de contacto de Inversiones Reinaldo Golindano. "
            f"Tono ejecutivo y formal, sin emojis."
        )
        propuesta = self.call_gemini(
            prompt=prompt,
            system_instruction=INSTRUCCION_SISTEMA_B2B,
            model_name="gemini-3-flash-preview",
        )
        return AgentResponse(success=True, data={"proposal": propuesta})
