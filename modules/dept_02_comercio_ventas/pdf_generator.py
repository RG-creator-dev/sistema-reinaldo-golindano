"""
=============================================================================
SISTEMA DE GESTIÓN DE INVERSIONES REINALDO GOLINDANO
Departamento: COMERCIO Y VENTAS
Módulo: pdf_generator.py
Descripción: Generador de Presupuestos y Cotizaciones Formales en PDF con ReportLab.
             Cumple con diseño para técnico de alta precisión, tasa oficial BCV,
             cálculo de IVA (16% por defecto / sin IVA) y cláusulas comerciales.
=============================================================================
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from config import SystemConfig
from core.logger import app_logger


class PDFQuoteGenerator:
    """Genera documentos PDF de presupuestos técnicos con acabado estético e institucional."""

    @classmethod
    def generate(
        cls,
        quote_id: str,
        client_name: str,
        client_rif: str = "N/A",
        client_phone: str = "N/A",
        client_company: str = "Particular",
        items: Optional[List[Dict[str, Any]]] = None,
        tax_percent: float = 16.0,
        bcv_rate: float = 849.56,
        notes: str = ""
    ) -> str:
        """
        Construye el PDF formal de la cotización y devuelve su ruta absoluta.
        """
        SystemConfig.ensure_directories()
        items = items or []

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Cotizacion_{quote_id}_{timestamp_str}.pdf"
        output_path = os.path.join(SystemConfig.QUOTES_DIR, filename)

        # Configuración de página Letter
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Paleta de Colores ReportLab
        primary_color = colors.HexColor("#0f172a")     # Slate 900
        accent_color = colors.HexColor("#2563eb")      # Blue 600
        text_dark = colors.HexColor("#1e293b")         # Slate 800
        text_muted = colors.HexColor("#64748b")        # Slate 500
        bg_table_header = colors.HexColor("#0f172a")
        bg_alt_row = colors.HexColor("#f8fafc")
        border_color = colors.HexColor("#cbd5e1")

        # Estilos Tipográficos
        title_style = ParagraphStyle(
            'CompanyTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=primary_color
        )
        subtitle_style = ParagraphStyle(
            'CompanySubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=text_muted
        )
        quote_title_style = ParagraphStyle(
            'QuoteTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=18,
            alignment=2,  # Derecha
            textColor=accent_color
        )
        quote_meta_style = ParagraphStyle(
            'QuoteMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=text_dark
        )
        client_label_style = ParagraphStyle(
            'ClientLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=accent_color
        )
        client_val_style = ParagraphStyle(
            'ClientVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=text_dark
        )
        cell_header_style = ParagraphStyle(
            'CellHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
            alignment=1
        )
        cell_text_style = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=text_dark
        )
        cell_text_bold = ParagraphStyle(
            'CellTextBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=text_dark
        )
        cell_num_style = ParagraphStyle(
            'CellNum',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=text_dark,
            alignment=2
        )
        terms_title_style = ParagraphStyle(
            'TermsTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=primary_color
        )
        terms_text_style = ParagraphStyle(
            'TermsText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7,
            leading=9.5,
            textColor=text_muted
        )

        story = []

        # 1. ENCABEZADO INSTITUCIONAL
        company_info = [
            Paragraph(f"<b>{SystemConfig.EMISOR_NOMBRE.upper()}</b>", title_style),
            Paragraph(f"<b>RIF:</b> {SystemConfig.EMISOR_RIF}", subtitle_style),
            Paragraph(f"<b>Dirección:</b> {SystemConfig.EMISOR_DIRECCION}", subtitle_style),
            Paragraph(f"<b>Contacto:</b> {SystemConfig.EMISOR_TELEFONO} | <b>Email:</b> {SystemConfig.EMISOR_EMAIL}", subtitle_style),
            Paragraph(f"<b>Especialidad:</b> {SystemConfig.EMISOR_DESCRIPCION}", subtitle_style),
        ]

        fecha_emision = datetime.now().strftime("%d/%m/%Y")
        quote_meta = [
            Paragraph("PRESUPUESTO FORMAL", quote_title_style),
            Paragraph(f"<b>N° Control:</b> {quote_id}", quote_meta_style),
            Paragraph(f"<b>Fecha:</b> {fecha_emision}", quote_meta_style),
            Paragraph(f"<b>Validez de la oferta:</b> 5 días continuos", quote_meta_style),
            Paragraph(f"<b>Tasa BCV del Día:</b> {bcv_rate:,.2f} Bs/USD", quote_meta_style),
        ]

        header_table = Table(
            [[company_info, quote_meta]],
            colWidths=[360, 180]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=0, spaceAfter=8))

        # 2. CUADRO DE DATOS DEL CLIENTE
        client_data = [
            [
                Paragraph("DATOS DEL CLIENTE / RECEPTOR", client_label_style),
                Paragraph("", client_label_style)
            ],
            [
                Paragraph(f"<b>Cliente / Razón Social:</b> {client_name}", client_val_style),
                Paragraph(f"<b>RIF / C.I.:</b> {client_rif}", client_val_style)
            ],
            [
                Paragraph(f"<b>Empresa / Organización:</b> {client_company}", client_val_style),
                Paragraph(f"<b>Teléfono de Contacto:</b> {client_phone}", client_val_style)
            ]
        ]
        client_table = Table(client_data, colWidths=[340, 200])
        client_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 12))

        # 3. TABLA DETALLADA DE ÍTEMS Y ESPECIFICACIONES TÉCNICAS
        table_rows = [
            [
                Paragraph("ÍTEM", cell_header_style),
                Paragraph("DESCRIPCIÓN Y ESPECIFICACIONES TÉCNICAS", cell_header_style),
                Paragraph("CANT.", cell_header_style),
                Paragraph("PRECIO ($)", cell_header_style),
                Paragraph("TOTAL ($)", cell_header_style),
            ]
        ]

        subtotal_usd = 0.0
        for idx, itm in enumerate(items, start=1):
            desc = itm.get("description", "Servicio Técnico / Insumo")
            specs = itm.get("specs", "")
            full_desc = f"<b>{desc}</b>"
            if specs:
                full_desc += f"<br/><font color='#64748b'><i>{specs}</i></font>"

            qty = float(itm.get("qty", 1))
            price = float(itm.get("price_usd", 0.0))
            line_total = qty * price
            subtotal_usd += line_total

            table_rows.append([
                Paragraph(str(idx), cell_text_bold),
                Paragraph(full_desc, cell_text_style),
                Paragraph(f"{qty:.0f}" if qty.is_integer() else f"{qty:.2f}", cell_num_style),
                Paragraph(f"${price:,.2f}", cell_num_style),
                Paragraph(f"${line_total:,.2f}", cell_num_style),
            ])

        # Totales
        is_exempt = (tax_percent <= 0.0)
        tax_amount_usd = round(subtotal_usd * (tax_percent / 100.0), 2) if not is_exempt else 0.0
        total_usd = subtotal_usd + tax_amount_usd
        total_bs = round(total_usd * bcv_rate, 2)
        subtotal_bs = round(subtotal_usd * bcv_rate, 2)

        items_table = Table(
            table_rows,
            colWidths=[35, 305, 50, 75, 75]
        )
        items_style = [
            ('BACKGROUND', (0, 0), (-1, 0), bg_table_header),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        # Filas alternadas
        for r_idx in range(1, len(table_rows)):
            if r_idx % 2 == 0:
                items_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_alt_row))

        items_table.setStyle(TableStyle(items_style))
        story.append(items_table)
        story.append(Spacer(1, 8))

        # 4. CUADRO DE LIQUIDACIÓN Y TOTALES
        iva_label = "IVA (16%):" if not is_exempt else "IVA (EXENTO / SIN IVA):"
        iva_val_str = f"${tax_amount_usd:,.2f}" if not is_exempt else "$0.00"

        totals_data = [
            [Paragraph("<b>SUBTOTAL:</b>", cell_num_style), Paragraph(f"${subtotal_usd:,.2f}", cell_num_style)],
            [Paragraph(f"<b>{iva_label}</b>", cell_num_style), Paragraph(iva_val_str, cell_num_style)],
            [Paragraph("<b>TOTAL GENERAL (USD):</b>", ParagraphStyle('TTotal', parent=cell_num_style, fontName='Helvetica-Bold', textColor=accent_color)),
             Paragraph(f"<b>${total_usd:,.2f}</b>", ParagraphStyle('TTotalVal', parent=cell_num_style, fontName='Helvetica-Bold', textColor=accent_color))],
            [Paragraph(f"<b>TOTAL EQUIVALENTE EN BOLÍVARES (BCV {bcv_rate:,.2f}):</b>", ParagraphStyle('TBs', parent=cell_num_style, fontName='Helvetica-Bold', textColor=primary_color)),
             Paragraph(f"<b>{total_bs:,.2f} Bs</b>", ParagraphStyle('TBsVal', parent=cell_num_style, fontName='Helvetica-Bold', textColor=primary_color))]
        ]

        totals_table = Table(totals_data, colWidths=[360, 180])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 2), (1, 2), 1, accent_color),
            ('BACKGROUND', (0, 3), (1, 3), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 3), (1, 3), 0.5, border_color),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 10))

        # 5. CONDICIONES COMERCIALES OBLIGATORIAS (PIE DE PÁGINA REQUERIDO)
        condiciones_comerciales = [
            Paragraph("<b>CONDICIONES COMERCIALES Y MÉTODOS DE PAGO:</b>", terms_title_style),
            Paragraph("1. <b>Moneda y Tasa de Cambio:</b> Los precios están reflejados en dólares americanos (USD). Para pagos en moneda nacional (Bolívares), la tasa aplicable es la oficial publicada por el <b>Banco Central de Venezuela (BCV)</b> para la fecha de la transacción.", terms_text_style),
            Paragraph(f"2. <b>Manejo del IVA:</b> {'Por disposición legal, la cotización incluye el cálculo del IVA (16%).' if not is_exempt else 'Emisión especial libre de IVA acordada con el cliente.'}", terms_text_style),
            Paragraph("3. <b>Métodos de Pago Aceptados:</b> Transferencias bancarias electrónicas (Banesco, Banco Mercantil, Banco de Venezuela, Banco Provincial), Pago Móvil interbancario y USDT en Binance (Binance Pay / UID institucional).", terms_text_style),
            Paragraph("4. <b>Garantía Técnica:</b> Treinta (30) días continuos en componentes reemplazados y mano de obra especializada bajo condiciones operativas normales.", terms_text_style),
            Paragraph("5. <b>Taller y Recepción:</b> Guacara, Edo. Carabobo. Contacto técnico directo: 0424-494.91.35 | inversionesreinaldog@gmail.com", terms_text_style),
        ]

        if notes:
            condiciones_comerciales.insert(1, Paragraph(f"<b>Observaciones técnicas:</b> {notes}", terms_text_style))

        terms_table = Table([[condiciones_comerciales]], colWidths=[540])
        terms_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(terms_table)

        # Construir documento PDF
        doc.build(story)
        app_logger.info(f"Cotización PDF creada exitosamente: {output_path}")
        return output_path
