"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Módulo: banco_temas_b2b.py
Descripción: Banco maestro de 105 temas corporativos B2B no repetitivos
             para generación de contenido técnico, financiero y estratégico.
=============================================================================
"""

BANCO_TEMAS_B2B = [
    # -------------------------------------------------------------------------
    # PILAR 1: GESTIÓN DE FLOTAS Y ESTANDARIZACIÓN CORPORATIVA (FLEET MANAGEMENT)
    # -------------------------------------------------------------------------
    {
        "id": 1,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Estandarización de Flotas de Impresión: Reducción de Costos y Complejidad en Oficinas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["estandarización", "flota", "modelos dispares", "inventario consumibles"],
        "enfoque": "Impacto negativo de tener múltiples marcas y modelos dispares en oficinas de Carabobo. Beneficios financieros de estandarizar: reducción drástica de inventario de tóner, menor costo de soporte y eliminación de compras imprevistas de emergencia."
    },
    {
        "id": 2,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Auditoría de Volumen de Impresión Mensual: Detección de Equipos Sobrecargados",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["auditoría", "volumen mensual", "ciclo de trabajo", "sobrecarga"],
        "enfoque": "Riesgo operativo cuando impresoras departamentales pequeñas asumen cargas industriales en departamentos contables. Cómo dimensionar la flota según el ciclo de trabajo mensual real para evitar paradas prematuras."
    },
    {
        "id": 3,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Centralización vs. Descentralización de Centros de Copiado e Impresión en Plantas",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["centralización", "islas de impresión", "plantas industriales", "control de flujo"],
        "enfoque": "Análisis logístico para empresas de manufactura en Valencia y Guacara: cuándo conviene un centro de copiado centralizado de alta producción frente a puestos de impresión descentralizados por gerencia."
    },
    {
        "id": 4,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Dimensionamiento Técnico para Departamentos de Contabilidad y Facturación de Alto Flujo",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["contabilidad", "facturación masiva", "alto flujo", "resistencia térmica"],
        "enfoque": "Requerimientos de robustez mecánica y disipación térmica para equipos de facturación continua a fin de mes. Selección de unidades fusoras reforzadas para soportar jornadas ininterrumpidas de emisión de documentos."
    },
    {
        "id": 5,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Monitoreo del Ciclo de Vida y Contadores de Páginas para Mantenimiento Predictivo",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["ciclo de vida", "contadores", "mantenimiento predictivo", "desgaste preventivo"],
        "enfoque": "Uso inteligente de los contadores internos de páginas para programar la sustitución de tambores, cuchillas y rodillos antes de que fallen en plena jornada laboral, garantizando cero paradas imprevistas."
    },
    {
        "id": 6,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Estrategia de Flotas Híbridas: Láser Monocromático de Alta Velocidad e Inyección Continua Color",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["flotas híbridas", "inyección continua", "láser monocromático", "costo color"],
        "enfoque": "Optimización del presupuesto corporativo combinando tecnología láser para documentos legales y facturación con sistemas de inyección continua EcoTank de alta capacidad para gráficos y reportes internos."
    },
    {
        "id": 7,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Planificación Escalonada de Renovación de Equipos sin Descapitalizar la Organización",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["renovación escalonada", "descapitalización", "obsolescencia", "presupuesto capex"],
        "enfoque": "Estrategia financiera para gerentes de compras: cómo renovar equipos obsoletos por etapas, priorizando las áreas críticas de despacho y cobranza sin impactar severamente el flujo de caja."
    },
    {
        "id": 8,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Homogeneización de Consumibles: Cómo Reducir Códigos de Tóner a Estándares Corporativos",
        "categoria_imagen": "Toner",
        "palabras_clave": ["homogeneización", "códigos tóner", "reducción sku", "almacén insumos"],
        "enfoque": "Simplificación del almacén de suministros corporativos: cómo pasar de gestionar docenas de cartuchos diferentes a solo 2 o 3 referencias clave, eliminando consumibles obsoletos que quedan en el olvido."
    },
    {
        "id": 9,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Sobrecostos Ocultos por el Uso de Impresoras Domésticas en Entornos Corporativos",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["equipos domésticos", "sobrecostos", "fragilidad mecánica", "entorno corporativo"],
        "enfoque": "La trampa de comprar impresoras caseras baratas para uso empresarial: cartuchos pequeños de alto costo por página, fragilidad mecánica y constantes interrupciones administrativas."
    },
    {
        "id": 10,
        "pilar": "Gestión de Flotas",
        "titulo_sugerido": "Gestión Unificada de Impresión en Múltiples Sucursales bajo un Solo Aliado Técnico",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["múltiples sucursales", "aliado técnico único", "cobertura regional", "soporte unificado"],
        "enfoque": "Empresas con sedes en Valencia, Guacara y San Diego: ventajas operativas de centralizar el soporte técnico, mantenimiento y reposición de insumos con un proveedor local consolidado."
    },

    # -------------------------------------------------------------------------
    # PILAR 2: COSTOS OCULTOS, TCO Y EFICIENCIA FINANCIERA
    # -------------------------------------------------------------------------
    {
        "id": 11,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Costo Total de Propiedad (TCO): Por Qué el Precio de Compra es Solo el 15% del Gasto Real",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["tco", "costo total de propiedad", "gasto real", "análisis financiero"],
        "enfoque": "Análisis financiero profundo para gerentes de administración: el 85% del costo de una impresora durante su ciclo de vida corresponde a consumibles, repuestos, energía y tiempos de inactividad."
    },
    {
        "id": 12,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Cálculo del Costo Real por Página (CPP): Insumos de Alto Rendimiento vs. Cartuchos Estándar",
        "categoria_imagen": "Toner",
        "palabras_clave": ["costo por página", "cpp", "alto rendimiento", "rendimiento tóner"],
        "enfoque": "Metodología práctica para evaluar el rendimiento real de los cartuchos de tóner. Por qué los insumos High Yield generan ahorros operativos de hasta un 30% a mediano plazo."
    },
    {
        "id": 13,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "El Impacto Financiero del Downtime: Cuánto Pierde una Empresa por una Parada de Impresión",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["downtime", "tiempo inactividad", "pérdida financiera", "parada operativa"],
        "enfoque": "Cuantificación de las pérdidas invisibles generadas cuando una parada de impresión bloquea la facturación fiscal, la salida de camiones en despacho y la tramitación aduanal en Carabobo."
    },
    {
        "id": 14,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Presupuestos Anuales de Impresión: Cómo Prevenir Fugas de Capital con Mantenimiento Programado",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["presupuesto anual", "mantenimiento programado", "fugas de capital", "gasto predecible"],
        "enfoque": "Cómo convertir gastos imprevistos y emergencias técnicas costosas en una partida presupuestaria fija, controlada y predecible mediante planes de servicio programados."
    },
    {
        "id": 15,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Falsos Ahorros en Suministros: El Costo Real de un Tóner Defectuoso en Equipos Corporativos",
        "categoria_imagen": "Toner",
        "palabras_clave": ["falsos ahorros", "tóner defectuoso", "daño fusor", "polvillo residual"],
        "enfoque": "Riesgos del uso de consumibles de dudosa procedencia: derrame de polvillo en engranajes, ralladuras prematuras en el cilindro OPC y daño térmico al fusor que multiplican el costo final."
    },
    {
        "id": 16,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Deducción Fiscal y Tratamiento Contable de los Servicios de Mantenimiento Corporativo",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["deducción fiscal", "gasto operativo", "crédito fiscal", "seniat"],
        "enfoque": "Beneficios de contar con proveedores formales que emiten facturas legales con RIF e IVA: optimización contable y deducibilidad total como gasto operativo para empresas venezolanas."
    },
    {
        "id": 17,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Análisis de Rentabilidad: Reparación Mayor de Fusores y Tambores vs. Reposición de Equipos",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["rentabilidad", "reconstrucción fusor", "reposición equipo", "capex vs opex"],
        "enfoque": "Criterios técnicos para decidir cuándo la reconstrucción y cambio de película térmica de un fusor es una inversión inteligente que extiende la vida del equipo 3 años más a un tercio del costo de uno nuevo."
    },
    {
        "id": 18,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Eliminación de Costos por Reimpresión: Documentos Ilegibles, Manchas y Mermas de Papel",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["reimpresión", "merma papel", "documentos manchados", "eficiencia documental"],
        "enfoque": "El gasto silencioso de hojas desechadas por líneas negras o copias tenues. Cómo el mantenimiento preventivo del módulo de imagen devuelve nitidez del 100% y elimina el desperdicio de resmas."
    },
    {
        "id": 19,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Políticas de Impresión Corporativa para Mitigar el Desperdicio Administrativo Involuntario",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["políticas de impresión", "desperdicio involuntario", "impresión dúplex", "ahorro papel"],
        "enfoque": "Implementación de normativas internas sencillas: impresión a doble cara por defecto, modo borrador para notas internas y aprobación de impresiones a color para reducir hasta 20% el consumo."
    },
    {
        "id": 20,
        "pilar": "Costos Ocultos y TCO",
        "titulo_sugerido": "Gestión de Inventarios Críticos de Consumibles en Planta: Equilibrio Financiero y Operativo",
        "categoria_imagen": "Toner",
        "palabras_clave": ["inventario crítico", "stock mínimo", "capital de trabajo", "sin desabastecimiento"],
        "enfoque": "Estrategia de stock de seguridad para departamentos de compras: cómo mantener insumos de respaldo para cubrir picos de demanda sin congelar capital de trabajo innecesario en anaqueles."
    },

    # -------------------------------------------------------------------------
    # PILAR 3: CONTINUIDAD OPERATIVA Y LOGÍSTICA EN EL EJE INDUSTRIAL DE CARABOBO
    # -------------------------------------------------------------------------
    {
        "id": 21,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Continuidad en Despacho: Cero Interrupciones en Facturación y Guías de Entrega",
        "categoria_imagen": "Toner",
        "palabras_clave": ["despacho continuo", "guías de entrega", "cierre de facturación", "logística carabobo"],
        "enfoque": "Cómo blindar las estaciones de despacho en empresas de logística y distribución para que la salida de gandolas y fletes no sufra demoras por falta de documentos impresos."
    },
    {
        "id": 22,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Planes de Contingencia Inmediata ante Paradas de Impresión en la Zona Industrial de Valencia",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["zona industrial valencia", "contingencia inmediata", "parada técnica", "tiempo de respuesta"],
        "enfoque": "Protocolos de soporte de emergencia para plantas industriales en Valencia: diagnóstico técnico en sitio y resolución ágil de fallas mecánicas en equipos de control de producción."
    },
    {
        "id": 23,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "La Ventaja Estratégica del Soporte Técnico Local en Carabobo vs. Proveedores en Caracas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["soporte local", "carabobo vs caracas", "proximidad técnica", "disponibilidad inmediata"],
        "enfoque": "El riesgo de depender de proveedores en la capital: demoras de días en envíos de encomiendas y viáticos costosos frente a la agilidad de un aliado técnico local en Guacara, Valencia y San Diego."
    },
    {
        "id": 24,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Stock de Insumos y Repuestos Críticos en Consignación para Empresas de Manufactura",
        "categoria_imagen": "Toner",
        "palabras_clave": ["consignación", "stock de respaldo", "repuestos críticos", "manufactura"],
        "enfoque": "Modelos de abastecimiento colaborativo donde el cliente corporativo dispone de cartuchos y piezas de desgaste inmediato en sus instalaciones, facturados únicamente contra consumo."
    },
    {
        "id": 25,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Operaciones 24/7 en Centros de Distribución: Mantenimiento Continuo de Tiqueras y Guías",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["operaciones 24/7", "cedis", "tiqueras continuas", "etiquetas de despacho"],
        "enfoque": "Soporte preventivo especializado para impresoras de tickets y etiquetas en almacenes y centros de distribución con turnos nocturnos y fines de semana ininterrumpidos."
    },
    {
        "id": 26,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Protección de Fuentes de Poder y Tarjetas Lógicas contra Fluctuaciones Eléctricas Locales",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["fluctuaciones eléctricas", "fuentes de poder", "tarjetas lógicas", "protección sobretensión"],
        "enfoque": "Medidas de ingeniería y acondicionamiento eléctrico para salvaguardar tarjetas formateadoras y componentes sensibles ante bajas de tensión y cortes imprevistos en Carabobo."
    },
    {
        "id": 27,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Asistencia Técnica Prioritaria Durante Cierres Contables y Auditorías Fiscales",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["cierre contable", "auditoría fiscal", "asistencia prioritaria", "fin de mes"],
        "enfoque": "Guardias técnicas programadas y respuesta prioritaria para departamentos de finanzas en períodos de cierre mensual y preparación de balances donde el volumen de impresión se triplica."
    },
    {
        "id": 28,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Logística de Retiro, Reparación en Taller Especializado y Reinstalación sin Parar la Operación",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["retiro y entrega", "taller de precisión", "reinstalación en sitio", "cero fricción"],
        "enfoque": "El servicio integral puerta a puerta para empresas: retiro técnico del equipo, diagnóstico en banco de pruebas con instrumentación de precisión y retorno instalado y calibrado."
    },
    {
        "id": 29,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Robustecimiento de Equipos de Facturación en Puntos de Venta de Alto Tráfico en Guacara y San Diego",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["puntos de venta", "alto tráfico", "guacara y san diego", "mecanismo de corte"],
        "enfoque": "Alineación de cuchillas de corte y calibración de mecanismos de arrastre en tiqueras térmicas y fiscales de cadenas de supermercados, farmacias y comercios mayoristas."
    },
    {
        "id": 30,
        "pilar": "Continuidad Operativa",
        "titulo_sugerido": "Soporte Estratégico para Empresas Farmacéuticas y de Alimentos: Documentación de Lotes",
        "categoria_imagen": "Toner",
        "palabras_clave": ["farmacéutica", "alimentos", "control de lotes", "calidad documental"],
        "enfoque": "Cumplimiento de estándares de trazabilidad en industrias reguladas: impresión nítida e indeleble de certificados de análisis, fórmulas y rótulos de seguridad sin margen de error."
    },

    # -------------------------------------------------------------------------
    # PILAR 4: SEGURIDAD DOCUMENTAL, IT Y TRANSFORMACIÓN ADMINISTRATIVA
    # -------------------------------------------------------------------------
    {
        "id": 31,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Seguridad de Impresión y Confidencialidad en Recursos Humanos y Finanzas (PIN Printing)",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["seguridad de impresión", "pin printing", "confidencialidad", "recursos humanos"],
        "enfoque": "Configuración de impresión retenida por código de usuario para evitar que nóminas confidenciales o informes estratégicos queden expuestos en la bandeja de salida común."
    },
    {
        "id": 32,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Control de Accesos y Auditoría de Usuarios en Multifuncionales Corporativas Conectadas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["control de acceso", "auditoría de usuarios", "red corporativa", "cuotas de impresión"],
        "enfoque": "Cómo asignar perfiles de acceso y monitorear el consumo de copias por usuario o centro de costos para responsabilizar el uso de los recursos de la organización."
    },
    {
        "id": 33,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Flujos de Digitalización y Escaneo Directo a Servidores Seguros de Red (Scan to SMB/FTP)",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["escaneo a red", "scan to smb", "digitalización", "archivo digital"],
        "enfoque": "Modernización de la archivística física: configuración de rutas automáticas de escaneo directo hacia carpetas compartidas y respaldos en la nube, agilizando trámites internos."
    },
    {
        "id": 34,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Integración de Equipos de Impresión con Sistemas ERP Empresariales (SAP, Profit, Saint, A2)",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["erp", "profit plus", "saint", "a2 empresarial", "formatos de factura"],
        "enfoque": "Calibración precisa de emulaciones PCL y PostScript para que las órdenes de impresión generadas desde software contable y ERP se alineen con exactitud en formas continuas y membretes."
    },
    {
        "id": 35,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Prevención de Fugas de Información en Memorias y Discos Duros de Fotocopiadoras",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["fuga de información", "disco duro fotocopiadora", "borrado seguro", "ciberseguridad"],
        "enfoque": "Protocolos de borrado seguro y formateo de almacenamiento temporal en equipos corporativos antes de su mantenimiento mayor, descarte o reasignación de departamento."
    },
    {
        "id": 36,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Segmentación de Red y Asignación de VLANs Dedicadas para Dispositivos de Impresión",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["vlan", "segmentación de red", "seguridad perimetral", "infraestructura it"],
        "enfoque": "Recomendaciones para jefes de sistemas: aislar las impresoras en redes virtuales dedicadas para proteger los servidores principales ante intentos de intrusión lateral."
    },
    {
        "id": 37,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Descongestión del Personal de Sistemas Mediante Tercerización Especializada de Impresión",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["tercerización", "tickets de soporte", "departamento it", "foco estratégico"],
        "enfoque": "Por qué delegar atascos mecánicos y cambios de insumos en un servicio técnico externo permite al equipo de TI enfocarse en proyectos de ciberseguridad y valor para la empresa."
    },
    {
        "id": 38,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Configuración de Escaneo OCR para Recuperación Rápida de Archivos y Contratos Históricos",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["ocr", "reconocimiento óptico", "búsqueda documental", "contratos"],
        "enfoque": "Aprovechamiento de multifuncionales avanzadas para convertir documentos en PDF con texto seleccionable, ahorrando cientos de horas de búsqueda manual en archivos administrativos."
    },
    {
        "id": 39,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Estabilidad de Controladores y Drivers de Red ante Actualizaciones del Sistema Operativo",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["drivers de red", "controladores", "actualizaciones windows", "compatibilidad"],
        "enfoque": "Resolución de conflictos de impresión generados por parches de seguridad de Windows y distribución de controladores universales certificados en la red corporativa."
    },
    {
        "id": 40,
        "pilar": "Seguridad e IT",
        "titulo_sugerido": "Protocolos Seguros de Comunicación en Red para Dispositivos Multifuncionales (SNMPv3 y TLS)",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["snmpv3", "tls", "comunicación segura", "monitoreo de red"],
        "enfoque": "Blindaje en la transmisión de datos y comandos de monitoreo en red para evitar intercepciones de documentos sensibles en el trayecto entre la PC y la impresora."
    },

    # -------------------------------------------------------------------------
    # PILAR 5: MANTENIMIENTO PREVENTIVO ESTRATÉGICO VS. CORRECTIVO DE EMERGENCIA
    # -------------------------------------------------------------------------
    {
        "id": 41,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Mantenimiento Trimestral Programado: La Estrategia que Evita el 85% de las Paradas Críticas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["mantenimiento trimestral", "paradas críticas", "plan preventivo", "inspección periódica"],
        "enfoque": "Evidencia técnica de por qué una revisión periódica de limpieza interna, lubricación y ajuste mecánico es 5 veces más económica que atender fallas de emergencia."
    },
    {
        "id": 42,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Inspección Térmica y Lubricación de la Película Fusora (Fuser Film) para Evitar Atascos",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["fuser film", "grasa térmica", "atasco de salida", "fijación de tóner"],
        "enfoque": "Importancia de renovar la grasa de alta temperatura en fusores cerámicos antes de que la película se rasgue y cause atascamientos de papel arrugado y quemado."
    },
    {
        "id": 43,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Limpieza y Alineación del Sistema Óptico Láser para Nitidez Impecable en Códigos de Barra",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["óptico láser", "códigos de barra", "nitidez", "espejo poligonal"],
        "enfoque": "Cómo la acumulación de micropartículas de polvo en los espejos y prisma láser degrada la lectura de códigos QR y barras en despachos, y cómo se corrige con calibración óptica."
    },
    {
        "id": 44,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Reemplazo Predictivo de Gomas de Arrastre (Pickup Rollers) para Evitar Doble Alimentación",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["pickup rollers", "gomas de arrastre", "doble alimentación", "tracción de papel"],
        "enfoque": "La pérdida paulatina de porosidad en los rodillos de alimentación: causas de tomas múltiples de hojas y atascos en bandejas de entrada, y su solución económica oportuna."
    },
    {
        "id": 45,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Calibración de Solenoides y Embragues Electromagnéticos para Registro Milimétrico de Papel",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["solenoides", "embragues electromagnéticos", "registro de papel", "sincronización"],
        "enfoque": "Diagnóstico de almohadillas amortiguadoras pegajosas en solenoides que retrasan el paso de la hoja y generan falsas alarmas de atasco en el recorrido interno."
    },
    {
        "id": 46,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Mantenimiento Especializado para Impresoras Fiscales y Tiqueras Térmicas de Punto de Venta",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["impresoras fiscales", "tiqueras térmicas", "cabezal térmico", "residuos de papel"],
        "enfoque": "Descontaminación de residuos de papel químico y polvo térmico en los puntos calientes del cabezal de impresión para asegurar recibos nítidos y sin rayas blancas ilegibles."
    },
    {
        "id": 47,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Diagnóstico Térmico y Disipación en Fuentes de Alimentación y Transformadores de Alto Voltaje",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["fuente de alimentación", "disipación térmica", "alto voltaje", "ventiladores internos"],
        "enfoque": "Revisión de condensadores y ventiladores de enfriamiento en fuentes conmutadas para evitar reinicios intempestivos de los equipos durante jornadas intensas de trabajo."
    },
    {
        "id": 48,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Descontaminación de Polvillo de Tóner en Sensores de Paso y Duplexores de Fotocopiadoras",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["polvillo de tóner", "sensores ópticos", "duplexor", "atascos fantasma"],
        "enfoque": "Limpieza técnica de fotosensores infrarrojos cegados por polvo de tóner que generan avisos de atasco inexistentes y bloquean la impresión automática a doble cara."
    },
    {
        "id": 49,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Preservación y Reseteo Seguro de Sistemas de Bombeo y Depósitos de Tinta Residual",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["almohadillas de tinta", "reseteo técnico seguro", "bomba de purga", "depósito residual"],
        "enfoque": "Tratamiento profesional del ciclo de desecho de tinta en impresoras de inyección continua: sustitución física de absorbentes y ajuste de firmware sin riesgo de desbordamientos internos."
    },
    {
        "id": 50,
        "pilar": "Mantenimiento Preventivo",
        "titulo_sugerido": "Inspección y Rectificación de Bujes y Engranajes Mecánicos del Tren de Tracción de Papel",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["bujes", "engranajes desgastados", "tren de tracción", "ruidos mecánicos"],
        "enfoque": "Eliminación de ruidos estridentes y desgaste prematuro en los piñones principales del motor mediante lubricación con grasas sintéticas con teflón de alta viscosidad."
    },

    # -------------------------------------------------------------------------
    # PILAR 6: PROCURA INTELIGENTE DE INSUMOS Y CALIDAD DE CONSUMIBLES
    # -------------------------------------------------------------------------
    {
        "id": 51,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Selección Técnica de Cartuchos de Tóner High Yield para Reducir Frecuencia de Reposición",
        "categoria_imagen": "Toner",
        "palabras_clave": ["tóner high yield", "alta capacidad", "frecuencia de compra", "ahorro operativo"],
        "enfoque": "Guía para departamentos de compras: comparación del rendimiento de 1.500 páginas vs. versiones de 5.000 a 10.000 páginas y su impacto directo en costos logísticos."
    },
    {
        "id": 52,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "La Química del Polvo de Tóner: Punto de Fusión Adecuado para Hojas Membretadas y Gruesas",
        "categoria_imagen": "Toner",
        "palabras_clave": ["química de tóner", "punto de fusión", "hojas membretadas", "adherencia térmica"],
        "enfoque": "Por qué los tóners genéricos de baja calidad desprenden polvo al doblar las hojas o manchan sellos húmedos: la importancia del polímero y resina correctos en el polvo de tóner."
    },
    {
        "id": 53,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Vida Útil del Cilindro Fotoconductor (OPC Drum): Cómo Prevenir Surcos y Manchas de Fondo",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["cilindro opc", "tambor fotosensible", "surcos", "manchas de fondo"],
        "enfoque": "Factores que degradan la capa orgánica fotosensible del tambor: fricción de papel áspero, clips y grapas olvidadas, y cómo seleccionar cilindros con recubrimiento reforzado."
    },
    {
        "id": 54,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Sustitución Oportuna de la Cuchilla Dosificadora (Doctor Blade) para Impresión Homogénea",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["doctor blade", "cuchilla dosificadora", "impresión homogénea", "densidad de tóner"],
        "enfoque": "El rol fundamental de la lámina dosificadora en la formación de la capa electrostática de tóner: prevención de franjas claras alternadas y sombras indeseadas."
    },
    {
        "id": 55,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Tintas de Pigmento vs. Colorantes en Equipos Continuos: Resistencia al Agua en Archivos Legales",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["tinta de pigmento", "tinta colorante", "documentos legales", "resistencia humedad"],
        "enfoque": "Asesoría para departamentos legales y contables: por qué los documentos oficiales deben imprimirse con tintas pigmentadas para resistir humedad, luz solar y marcadores resaltadores."
    },
    {
        "id": 56,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Climatización y Almacenamiento de Resmas de Papel en Oficinas de Zonas Húmedas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["almacenamiento de papel", "humedad en resmas", "atasco de papel", "papel ondulado"],
        "enfoque": "El clima de Carabobo y su impacto en el papel: cómo la absorción de humedad ambiental genera curvaturas en el fusor y atascos continuos, y cómo solucionarlo con buenas prácticas de acopio."
    },
    {
        "id": 57,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Criterios para Auditar la Autenticidad y Rendimiento Real de Consumibles Adquiridos",
        "categoria_imagen": "Toner",
        "palabras_clave": ["auditoría de consumibles", "rendimiento real", "proveedores certificados", "pesaje de cartuchos"],
        "enfoque": "Técnicas sencillas para gerentes de compras: control de peso neto en cartuchos nuevos, sellos holográficos de seguridad y verificación de páginas rendidas mediante software."
    },
    {
        "id": 58,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "El Impacto del Polvo de Papel en los Cabezales de Impresión y Mecanismos de Arrastre",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["polvo de papel", "cabezal de impresión", "microobstrucciones", "papel económico"],
        "enfoque": "Los peligros de utilizar papeles de bajo gramaje con exceso de residuo mineral o celulosa suelta: obstrucción acelerada de inyectores y pérdida de tracción en rodillos de goma."
    },
    {
        "id": 59,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Diagnóstico de Rodillos de Transferencia y Rodillos de Carga Primaria (PCR) contra Efectos Fantasma",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["rodillo pcr", "efecto fantasma", "transferencia electrostática", "repetición de imagen"],
        "enfoque": "Causas técnicas de la repetición tenue de textos en la misma hoja (ghosting): desgaste o contaminación del rodillo PCR y métodos técnicos para restaurar el potencial de carga."
    },
    {
        "id": 60,
        "pilar": "Procura de Insumos",
        "titulo_sugerido": "Procedimientos Seguros para el Manejo y Disposición Responsable de Tóner Residual",
        "categoria_imagen": "Toner",
        "palabras_clave": ["tóner residual", "disposición responsable", "salud ocupacional", "medio ambiente"],
        "enfoque": "Protocolos de seguridad industrial para vaciar y descartar recipientes de tóner de desecho sin dispersar partículas microscópicas en el aire de las oficinas corporativas."
    },

    # -------------------------------------------------------------------------
    # PILAR 7: CONTRATOS CORPORATIVOS B2B Y ACUERDOS DE NIVEL DE SERVICIO (SLA)
    # -------------------------------------------------------------------------
    {
        "id": 61,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Contratos de Mantenimiento Corporativo Mensual: Tranquilidad con Costos Fijos y Predecibles",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["contrato corporativo", "mantenimiento mensual", "costos fijos", "sin sorpresas"],
        "enfoque": "Ventajas del esquema contractual B2B: revisiones preventivas periódicas programadas, soporte preferente en averías y tarifas preferenciales en repuestos originales."
    },
    {
        "id": 62,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Acuerdos de Nivel de Servicio (SLA): Tiempos de Respuesta de 4 a 24 Horas Garantizados",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["sla", "acuerdo de nivel de servicio", "tiempo de respuesta", "cobertura garantizada"],
        "enfoque": "Definición de compromisos formales de tiempo de atención ante fallas críticas en plantas de Carabobo, asegurando que ningún departamento clave permanezca detenido por días."
    },
    {
        "id": 63,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Informes Técnicos Ejecutivos Post-Servicio: Trazabilidad Total para la Gerencia General",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["informe técnico ejecutivo", "trazabilidad", "auditoría de mantenimiento", "transparencia"],
        "enfoque": "Entrega de reportes formales tras cada intervención técnica: estado de vida útil de componentes, mediciones de voltaje, contadores de páginas y recomendaciones operativas."
    },
    {
        "id": 64,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Equipos de Respaldo en Calidad de Préstamo (Standby Units) Durante Reparaciones Mayores",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["standby", "equipo de respaldo", "préstamo temporal", "continuidad absoluta"],
        "enfoque": "Garantía de continuidad para clientes corporativos: si una fotocopiadora o impresora de alta demanda requiere desarme completo en taller, se instala un equipo de respaldo equivalente."
    },
    {
        "id": 65,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Cumplimiento Fiscal y Legal Estricto: Facturación Formal con RIF y Solvencia Tributaria",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["cumplimiento fiscal", "factura legal", "retención de iva", "solvencia"],
        "enfoque": "Por qué las grandes corporaciones de Carabobo eligen proveedores que operan bajo estricto apego a las normas tributarias venezolanas, facilitando retenciones de IVA e ISLR."
    },
    {
        "id": 66,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Asignación de Técnico Especialista de Cabecera para Conocer el Historial de su Empresa",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["técnico asignado", "historial de flota", "atención personalizada", "confianza"],
        "enfoque": "El valor de contar con un especialista técnico familiarizado con las particularidades de su red, sus usuarios y el histórico de fallas de cada equipo en la sede."
    },
    {
        "id": 67,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Auditoría Inicial Sin Costo para Diagnosticar el Estado Real de su Parque de Impresión",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["auditoría inicial", "diagnóstico gratuito", "levantamiento técnico", "evaluación de parque"],
        "enfoque": "Propuesta de valor para empresas de Carabobo: levantamiento técnico detallado de cada equipo en planta para identificar vulnerabilidades mecánicas y oportunidades inmediatas de ahorro."
    },
    {
        "id": 68,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Condiciones Comerciales Flexibles y Crédito Corporativo Adaptado al Flujo de Caja Local",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["crédito corporativo", "condiciones de pago", "flujo de caja", "alianza b2b"],
        "enfoque": "Planes de facturación quincenales o mensuales que se acoplan al ciclo de pagos y cobranzas de empresas e industrias en el estado Carabobo."
    },
    {
        "id": 69,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Talleres de Capacitación al Personal Administrativo en Buenas Prácticas de Operación",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["capacitación de usuarios", "buenas prácticas", "cuidado de equipos", "reducción de atascos"],
        "enfoque": "Sesiones prácticas para usuarios de oficina: cómo alimentar papel correctamente, despejar atascos sencillos sin romper sensores y manipular tóner de forma higiénica."
    },
    {
        "id": 70,
        "pilar": "Contratos B2B & SLA",
        "titulo_sugerido": "Consolidación de Proveedores: Factura Unificada de Mantenimiento, Repuestos y Consumibles",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["consolidación de proveedores", "cuenta única", "simplificación administrativa", "procura integral"],
        "enfoque": "Ahorro de horas-hombre en el departamento de compras al gestionar un solo proveedor de confianza para todo el ciclo: diagnóstico, reparación, piezas y reposición continua de tóner."
    },

    # -------------------------------------------------------------------------
    # PILAR 8: DESAFÍOS INDUSTRIALES Y ENTORNOS EXIGENTES EN CARABOBO
    # -------------------------------------------------------------------------
    {
        "id": 71,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Operación de Impresoras en Ambientes con Polvo en Suspensión en Plantas de Manufactura",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["polvo en suspensión", "plantas de manufactura", "sellado mecánico", "zona industrial"],
        "enfoque": "Medidas de protección y filtros antipolvo para equipos ubicados en naves de producción química, textil o metalmecánica en Valencia y Guacara."
    },
    {
        "id": 72,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Impresión de Alto Volumen para Etiquetas de Empaque y Embalaje en Líneas de Producción",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["etiquetas de empaque", "línea de producción", "embalaje continuo", "cero retrasos"],
        "enfoque": "Calibración térmica de rodillos y cabezales para la impresión ininterrumpida de etiquetas adhesivas y códigos de despacho sin desprendimiento prematuro de adhesivo en los engranajes."
    },
    {
        "id": 73,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Mantenimiento Correctivo en Impresoras de Almacenes Sometidas a Variaciones Térmicas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["variaciones térmicas", "almacén industrial", "lubricación sintética", "galpones"],
        "enfoque": "Cómo las altas temperaturas dentro de galpones industriales resecan la grasa de los mecanismos y ablandan los rodillos de arrastre, y qué formulaciones sintéticas resuelven el problema."
    },
    {
        "id": 74,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Mitigación de Vibraciones Mecánicas Cercanas a Maquinaria Pesada en Oficinas de Planta",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["vibraciones mecánicas", "maquinaria pesada", "desalineación de espejos", "planta"],
        "enfoque": "Instalación de bases amortiguadoras y ajuste de fijaciones en impresoras situadas cerca de prensas, motores o líneas de ensamblaje para evitar descalibraciones del escáner y láser."
    },
    {
        "id": 75,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Descontaminación Preventiva de Contactos y Sensores en Áreas con Humedad Industrial",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["humedad industrial", "contactos eléctricos", "sulfatación", "limpieza dieléctrica"],
        "enfoque": "Aplicación de protectores dieléctricos y limpieza ultrasónica de terminales para evitar falsos contactos y cortocircuitos intermitentes en plantas de procesamiento de alimentos."
    },
    {
        "id": 76,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Selección de Consumibles de Alta Adherencia para Soportes Especiales: Polipropileno y Continuo",
        "categoria_imagen": "Toner",
        "palabras_clave": ["soportes especiales", "alta adherencia", "etiquetas sintéticas", "resistencia química"],
        "enfoque": "Asesoramiento en cintas térmicas y tóners de resina pura para imprimir etiquetas que deben soportar cámaras frigoríficas, manipulación con aceites y solventes industriales."
    },
    {
        "id": 77,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Optimización de Tiqueras en Básculas y Control de Pesaje de Gandolas en Romanas",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["báscula de gandolas", "romana industrial", "tiqueras de pesaje", "control de carga"],
        "enfoque": "Mantenimiento crítico de impresoras de tickets en casetas de romana: evitar que una falla en la impresión del ticket de tara y peso detenga la salida de transporte pesado."
    },
    {
        "id": 78,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Soluciones de Impresión para Laboratorios de Calidad: Trazabilidad y Certificados Técnicos",
        "categoria_imagen": "Toner",
        "palabras_clave": ["laboratorio de calidad", "trazabilidad", "certificados de análisis", "resolución gráfica"],
        "enfoque": "Configuración de máxima resolución en equipos láser para emitir curvas gráficas, cromatografías y especificaciones de control de calidad con absoluta definición visual."
    },
    {
        "id": 79,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Protocolos de Mantenimiento para Impresoras en Talleres y Concesionarios Automotrices",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["talleres automotrices", "concesionarios", "grasa y aceite", "órdenes de servicio"],
        "enfoque": "Blindaje de equipos en áreas de recepción de vehículos donde la presencia de lubricantes, grasas y hollín ambiental degrada rápidamente los rodillos de alimentación de papel."
    },
    {
        "id": 80,
        "pilar": "Entornos Industriales",
        "titulo_sugerido": "Prevención del Desgaste Prematuro de Engranajes por Operación Continua en Turnos Rotativos",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["turnos rotativos", "operación 24 horas", "desgaste de engranajes", "fatiga mecánica"],
        "enfoque": "Diagnóstico de fatiga térmica en piñones y bujes sometidos a ciclos de trabajo ininterrumpidos en fábricas que operan tres turnos de trabajo en Carabobo."
    },

    # -------------------------------------------------------------------------
    # PILAR 9: SOLUCIONES TÉCNICAS DE ALTA COMPLEJIDAD Y RECUPERACIÓN DE EQUIPOS
    # -------------------------------------------------------------------------
    {
        "id": 81,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Reconstrucción Integral de Unidades de Fusión para Fotocopiadoras Departamentales",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["reconstrucción fusor", "rodillo de presión", "termostato", "lámpara halógena"],
        "enfoque": "El proceso técnico de reemplazo de rodillo de presión, funda de teflón, termistores y rodamientos para recuperar un fusor de alto flujo a nuevo sin comprar la unidad entera."
    },
    {
        "id": 82,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Recuperación por Ultrasonido y Microfiltrado de Cabezales Piezoeléctricos Obstruidos",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["ultrasonido", "microfiltrado", "cabezal piezoeléctrico", "destape químico"],
        "enfoque": "Tecnología de laboratorio para salvar cabezales de impresión originales tapados por tintas secas o contaminación cruzada, evitando el costo de reemplazo del componente más costoso."
    },
    {
        "id": 83,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Diagnóstico y Reparación a Nivel de Componentes en Tarjetas Lógicas Principales",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["tarjeta lógica", "formatter board", "reparación electrónica", "microcomponentes"],
        "enfoque": "Capacidad de microelectrónica en taller: sustitución de reguladores de voltaje, diodos de protección y condensadores quemados sin tener que importar placas completas de fábrica."
    },
    {
        "id": 84,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Rectificación de Rodillos de Presión y Termistores para Control Térmico Milimétrico",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["rodillo de presión", "termistores", "control térmico", "código de error de temperatura"],
        "enfoque": "Eliminación de códigos de error de temperatura (falla de calentamiento del fusor) mediante la sustitución y calibración de resistencias térmicas de retroalimentación."
    },
    {
        "id": 85,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Sustitución de Fajas de Transferencia y Láminas de Limpieza en Sistemas Láser Color",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["faja de transferencia", "transfer belt", "láser color", "registro de cuatro colores"],
        "enfoque": "Ajuste milimétrico de la banda de transferencia de imagen para evitar desalineaciones cromáticas y manchas repetitivas en presentaciones ejecutivas y catálogos comerciales."
    },
    {
        "id": 86,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Calibración del Balance de Voltaje en Bloques de Alta Tensión para Eliminar Fondos Grises",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["alta tensión", "fondos grises", "potencial electrostático", "coronas de carga"],
        "enfoque": "Ajuste de fuentes de alto voltaje para restablecer el potencial de transferencia electrostática exacto, logrando blancos puros y negros sólidos en cada impresión."
    },
    {
        "id": 87,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Reparación y Calibración de Escáneres con Alimentador Automático (ADF) de Doble Pasada",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["adf", "escáner doble pasada", "rodillo de separación", "alineación de hojas"],
        "enfoque": "Mantenimiento preventivo en alimentadores automáticos de documentos: reemplazo de almohadillas de freno para evitar hojas torcidas y atascamientos en escaneos masivos."
    },
    {
        "id": 88,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Extracción Segura de Objetos Extraños en Conductos Internos de Papel sin Dañar Sensores",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["objetos extraños", "grapas y clips", "conductos de papel", "daño mecánico"],
        "enfoque": "Procedimientos para remover grapas, trozos de etiquetas autoadhesivas y restos de papel incrustados en guías plásticas sin romper actuadores de sensores ópticos."
    },
    {
        "id": 89,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Actualización y Restauración Segura de Firmware Corporativo sin Riesgo de Bloqueo",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["firmware corporativo", "restauración", "seguridad lógica", "anti-bloqueo"],
        "enfoque": "Procedimientos profesionales de flashing y recuperación de firmware en equipos que quedaron inoperativos tras cortes eléctricos o actualizaciones automáticas fallidas."
    },
    {
        "id": 90,
        "pilar": "Ingeniería Técnica",
        "titulo_sugerido": "Ajuste Micrométrico de Sincronización de Carro y Encoders Lineales para Tipografía Precisa",
        "categoria_imagen": "Epson EcoTank",
        "palabras_clave": ["encoder lineal", "sincronización de carro", "alineación tipográfica", "letras borrosas"],
        "enfoque": "Limpieza y lectura óptica de la cinta encoder milimétrica para eliminar desfasajes de líneas, textos dobles y distorsiones verticales en impresiones de alta definición."
    },

    # -------------------------------------------------------------------------
    # PILAR 10: ESTRATEGIA, FINANZAS Y LIDERAZGO ADMINISTRATIVO
    # -------------------------------------------------------------------------
    {
        "id": 91,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "El Rol del Gerente de Compras en la Optimización del Presupuesto Operativo de Oficina",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["gerente de compras", "presupuesto operativo", "negociación de insumos", "eficiencia"],
        "enfoque": "Cómo los líderes de abastecimiento pueden generar ahorros tangibles de dos dígitos renegociando esquemas de suministro continuo con aliados técnicos locales."
    },
    {
        "id": 92,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Cómo Justificar la Inversión en Mantenimiento Preventivo ante la Dirección General",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["justificación financiera", "dirección general", "retorno de inversión", "roi"],
        "enfoque": "Herramientas conceptuales y métricas de ROI para que administradores demuestren que el mantenimiento preventivo preserva los activos fijos de la compañía."
    },
    {
        "id": 93,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Indicadores Clave de Desempeño (KPIs) para la Gestión Eficiente de Impresión Corporativa",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["kpis de impresión", "mtbf", "tiempo medio entre fallas", "costo por página"],
        "enfoque": "Implementación de métricas de gestión: costo por usuario, tiempo medio entre fallas (MTBF) y tasa de resolución al primer contacto para una administración moderna."
    },
    {
        "id": 94,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Procedimientos Estandarizados para la Recepción de Calidad de Insumos en Almacén",
        "categoria_imagen": "Toner",
        "palabras_clave": ["recepción de insumos", "control de calidad", "almacén central", "criterios de rechazo"],
        "enfoque": "Lista de verificación para analistas de almacén: inspección visual de cajas, sellos de integridad, fechas de vencimiento y rechazo inmediato de lotes sospechosos."
    },
    {
        "id": 95,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Reducción de la Huella Ecológica y Consumo Energético en Oficinas Administrativas",
        "categoria_imagen": "Fusor",
        "palabras_clave": ["eficiencia energética", "modo sleep", "huella de carbono", "ahorro de electricidad"],
        "enfoque": "Configuración de modos de reposo inteligente y optimización térmica de fusores para reducir la factura eléctrica y promover prácticas sustentables en Carabobo."
    },
    {
        "id": 96,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Prevención de Compras Duplicadas Mediante el Control Centralizado de Suministros",
        "categoria_imagen": "Toner",
        "palabras_clave": ["compras duplicadas", "control centralizado", "orden de compra", "desperdicio de insumos"],
        "enfoque": "Estrategias para evitar que departamentos independientes compren cartuchos por separado a precios minoristas más caros y acumulen existencias descontroladas."
    },
    {
        "id": 97,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Planes de Contingencia ante Desabastecimiento de Insumos en Temporadas Festivas",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["temporadas festivas", "fin de año", "desabastecimiento", "plan de procura anticipada"],
        "enfoque": "Cómo anticipar la procura de insumos y mantenimiento antes de los cierres de fin de año o períodos vacacionales en los que las importaciones y transportes se retrasan."
    },
    {
        "id": 98,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "El Impacto de una Impresión Impecable en la Imagen Corporativa y Credibilidad Comercial",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["imagen corporativa", "credibilidad", "presentación de ofertas", "documentos nítidos"],
        "enfoque": "La impresión como carta de presentación física: por qué entregar una cotización formal o un contrato con manchas o texto desvanecido perjudica la percepción de calidad de su empresa."
    },
    {
        "id": 99,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Gestión Eficaz de Garantías Técnicas: Respaldo Real en Repuestos y Mano de Obra",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["garantías técnicas", "respaldo en repuestos", "mano de obra certificada", "confianza b2b"],
        "enfoque": "La importancia de exigir certificados de garantía por escrito en cada intervención técnica para proteger el patrimonio de la empresa ante repuestos defectuosos."
    },
    {
        "id": 100,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "La Sinergia entre Administración y Soporte Técnico Externo para Maximizar la Productividad",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["sinergia estratégica", "socio comercial", "productividad laboral", "soporte b2b"],
        "enfoque": "Cómo construir una relación de largo plazo con un proveedor técnico de confianza que conozca a fondo los procesos de su empresa y actúe como un brazo operativo de su equipo."
    },
    {
        "id": 101,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Digitalización Híbrida: Articulación entre Impresión Legal y Flujos de Aprobación en la Nube",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["digitalización híbrida", "firmas físicas vs digitales", "archivo legal", "flujos en la nube"],
        "enfoque": "Estrategia documental moderna: cómo conviven las facturas e informes impresos de respaldo legal con repositorios digitales seguros para aprobaciones rápidas."
    },
    {
        "id": 102,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Auditoría de Compatibilidad de Consumibles: Evitar Daños Irreversibles en Tambores",
        "categoria_imagen": "Modulo de Imagen",
        "palabras_clave": ["compatibilidad consumibles", "daño en tambor", "auditoría técnica", "proveedor confiable"],
        "enfoque": "Verificación técnica de tolerancias mecánicas y voltajes de polarización en cartuchos genéricos para evitar perforaciones prematuras en el tambor fotoconductor."
    },
    {
        "id": 103,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Rendimiento por Turno: Estrategias para Eliminar Cuellos de Botella en Horas Pico de Cobranza",
        "categoria_imagen": "Tiqueras Epson",
        "palabras_clave": ["horas pico", "cuellos de botella", "cobranza y facturación", "velocidad de impresión"],
        "enfoque": "Ajuste de velocidades de puerto y buffer de memoria en tiqueras e impresoras de mostrador para atender filas rápidas de clientes sin pausas entre comprobantes."
    },
    {
        "id": 104,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Protección de Equipos Críticos Mediante Sistemas de Alimentación Ininterrumpida (UPS)",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["ups", "respaldo de energía", "protección eléctrica", "apagados controlados"],
        "enfoque": "Criterios para seleccionar UPS y estabilizadores de voltaje adecuados para impresoras láser y fotocopiadoras, considerando sus picos de consumo térmico durante el encendido."
    },
    {
        "id": 105,
        "pilar": "Estrategia Administrativa",
        "titulo_sugerido": "Transformando el Centro de Impresión: De un Gasto Inevitable a una Ventaja Competitiva",
        "categoria_imagen": "Reparaciones",
        "palabras_clave": ["ventaja competitiva", "eficiencia de costos", "transformación operativa", "excelencia"],
        "enfoque": "Conclusión ejecutiva: cómo las empresas líderes de Carabobo convierten un área tradicionalmente descuidada en un modelo de eficiencia de costos, orden administrativo y continuidad de negocio."
    }
]


def obtener_tema_por_id(tema_id: int):
    """Retorna el tema con el ID especificado (1 a 105)."""
    for t in BANCO_TEMAS_B2B:
        if t["id"] == tema_id:
            return t
    idx = (tema_id - 1) % len(BANCO_TEMAS_B2B)
    return BANCO_TEMAS_B2B[idx]


def seleccionar_temas_para_lote(siguiente_id: int, textos_historicos: list = None, cantidad: int = 3):
    """
    Selecciona 'cantidad' temas únicos y no repetidos para el próximo lote semanal.
    Revisa tanto el avance correlativo como el historial de textos previos para
    evitar duplicidad en un horizonte de al menos 100 publicaciones.
    """
    if textos_historicos is None:
        textos_historicos = []

    # Concatenar todo el historial previo en minúsculas para búsqueda de coincidencias
    historial_unificado = " ".join([str(t).lower() for t in textos_historicos if t])

    temas_seleccionados = []
    total_temas = len(BANCO_TEMAS_B2B)
    indice_inicio = (siguiente_id - 1) % total_temas

    intentos = 0
    paso = 0

    while len(temas_seleccionados) < cantidad and intentos < total_temas * 2:
        idx_evaluar = (indice_inicio + paso) % total_temas
        candidato = BANCO_TEMAS_B2B[idx_evaluar]
        paso += 1
        intentos += 1

        # Verificar si ya lo seleccionamos en este mismo lote
        if any(t["id"] == candidato["id"] for t in temas_seleccionados):
            continue

        # Verificar si el tema ya fue cubierto en publicaciones recientes
        # (usamos sus palabras clave para detectar si ya se generó recientemente)
        coincidencias = 0
        for kw in candidato["palabras_clave"]:
            if kw.lower() in historial_unificado:
                coincidencias += 1

        # Si más de la mitad de las palabras clave están en el historial muy reciente,
        # pero aún tenemos temas sin explorar, preferimos explorar otros temas.
        if coincidencias >= 2 and intentos < total_temas:
            continue

        temas_seleccionados.append(candidato)

    # Si por algún motivo de historial muy denso no se completan, completar secuencialmente
    while len(temas_seleccionados) < cantidad:
        idx_fallback = (indice_inicio + len(temas_seleccionados)) % total_temas
        candidato = BANCO_TEMAS_B2B[idx_fallback]
        if not any(t["id"] == candidato["id"] for t in temas_seleccionados):
            temas_seleccionados.append(candidato)

    return temas_seleccionados
