from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
from datetime import datetime
import io

def generar_reporte_pdf(usuario, productos):
    """Genera un PDF con el reporte de inventario"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1a4d8c'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    story = []
    story.append(Paragraph("📦 REPORTE DE INVENTARIO", titulo_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Generado por: {usuario}", styles['Normal']))
    story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    if productos:
        data = [["ID", "Producto", "Categoría", "Cantidad", "Precio Unit.", "Valor Total"]]
        total_general = 0
        for p in productos:
            valor = p.cantidad * p.precio
            total_general += valor
            data.append([
                str(p.id), p.nombre, p.categoria, str(p.cantidad),
                f"${p.precio:,.2f}", f"${valor:,.2f}"
            ])
        data.append(["", "", "", "", "TOTAL GENERAL:", f"${total_general:,.2f}"])
        
        table = Table(data, colWidths=[0.6*inch, 2*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d8c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (1, 1), (-1, -2), 9),
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),
            ('ALIGN', (5, 1), (5, -2), 'RIGHT'),
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
    
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", 
                          styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_inventario_{timestamp}.pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response