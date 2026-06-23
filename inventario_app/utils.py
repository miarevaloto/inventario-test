from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
from django.db.models import Sum, Count
from datetime import datetime
import io

def generar_reporte_pdf(usuario, productos, inventario_nombre=None, estadisticas=None):
    """Genera un PDF con el reporte de inventario mejorado"""
    
    if estadisticas is None:
        estadisticas = {}
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # ========== ESTILOS ==========
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1a4d8c'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#6c757d'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    seccion_style = ParagraphStyle(
        'SeccionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a4d8c'),
        spaceAfter=8,
        spaceBefore=15
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT
    )
    
    story = []
    
    # ========== 1. TÍTULO Y ENCABEZADO ==========
    story.append(Paragraph("📦 REPORTE DE INVENTARIO", titulo_style))
    story.append(Paragraph("Sistema de Gestión de Inventarios", subtitulo_style))
    story.append(Spacer(1, 10))
    
    # ========== 2. INFORMACIÓN DEL USUARIO Y FECHA ==========
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    info_data = [
        ["Generado por:", usuario],
        ["Fecha:", fecha_actual],
        ["Inventario:", inventario_nombre or "General"],
    ]
    
    if estadisticas.get('total_productos') is not None:
        info_data.append(["Total Productos:", str(estadisticas.get('total_productos', 0))])
    if estadisticas.get('stock_total') is not None:
        info_data.append(["Stock Total:", str(estadisticas.get('stock_total', 0))])
    if estadisticas.get('valor_total') is not None:
        info_data.append(["Valor Total:", f"${estadisticas.get('valor_total', 0):,.2f}"])
    
    info_table = Table(info_data, colWidths=[1.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # ========== 3. PRODUCTOS CON STOCK BAJO (si existen) ==========
    productos_bajo_stock = [p for p in productos if p.cantidad < 5]
    
    if productos_bajo_stock:
        story.append(Paragraph("⚠️ PRODUCTOS CON STOCK CRÍTICO", seccion_style))
        
        bajo_data = [["Producto", "Categoría", "Stock", "Estado"]]
        for p in productos_bajo_stock[:10]:  # Máximo 10 productos
            if p.cantidad == 0:
                estado = "🔴 AGOTADO"
            elif p.cantidad < 3:
                estado = "🟠 CRÍTICO"
            else:
                estado = "🟡 BAJO"
            bajo_data.append([p.nombre, p.categoria, str(p.cantidad), estado])
        
        bajo_table = Table(bajo_data, colWidths=[2.2*inch, 1.5*inch, 0.8*inch, 1.2*inch])
        bajo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3cd')]),
        ]))
        story.append(bajo_table)
        story.append(Spacer(1, 15))
    
    # ========== 4. RESUMEN POR CATEGORÍA ==========
    categorias = {}
    for p in productos:
        if p.categoria not in categorias:
            categorias[p.categoria] = {"cantidad": 0, "valor": 0, "count": 0}
        categorias[p.categoria]["cantidad"] += p.cantidad
        categorias[p.categoria]["valor"] += p.cantidad * p.precio
        categorias[p.categoria]["count"] += 1
    
    if categorias:
        story.append(Paragraph("📊 RESUMEN POR CATEGORÍA", seccion_style))
        
        cat_data = [["Categoría", "Productos", "Stock Total", "Valor Total"]]
        for cat, data in categorias.items():
            cat_data.append([
                cat,
                str(data["count"]),
                str(data["cantidad"]),
                f"${data['valor']:,.2f}"
            ])
        
        cat_table = Table(cat_data, colWidths=[2*inch, 1*inch, 1.2*inch, 1.8*inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 15))
    
    # ========== 5. LISTA COMPLETA DE PRODUCTOS ==========
    story.append(Paragraph("📋 LISTADO DE PRODUCTOS", seccion_style))
    
    if productos:
        data = [["ID", "Producto", "Categoría", "Cantidad", "Precio Unit.", "Valor Total"]]
        total_general = 0
        for p in productos:
            valor = p.cantidad * p.precio
            total_general += valor
            # Resaltar productos con stock bajo
            if p.cantidad < 5:
                data.append([
                    str(p.id),
                    f"⚠️ {p.nombre}",
                    p.categoria,
                    f"**{p.cantidad}**",
                    f"${p.precio:,.2f}",
                    f"${valor:,.2f}"
                ])
            else:
                data.append([
                    str(p.id),
                    p.nombre,
                    p.categoria,
                    str(p.cantidad),
                    f"${p.precio:,.2f}",
                    f"${valor:,.2f}"
                ])
        data.append(["", "", "", "", "TOTAL GENERAL:", f"${total_general:,.2f}"])
        
        table = Table(data, colWidths=[0.6*inch, 2*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (1, 1), (-1, -2), 9),
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (-1, -2), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0fe')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (4, -1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a4d8c')),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No hay productos en este inventario", styles['Normal']))
    
    # ========== 6. PIE DE PÁGINA ==========
    story.append(Spacer(1, 30))
    story.append(Paragraph("-" * 80, styles['Normal']))
    story.append(Paragraph(
        f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}",
        styles['Normal']
    ))
    story.append(Paragraph(
        "Este documento es confidencial y de uso exclusivo de la empresa.",
        styles['Normal']
    ))
    story.append(Paragraph(
        "MotoStock PRO - Sistema de Gestión de Inventarios v1.0",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_inventario_{timestamp}.pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
