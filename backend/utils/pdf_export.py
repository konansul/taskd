"""
PDF export functionality for presentations.
Converts presentation slides to PDF format.
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from typing import List, Dict
import os
from PIL import Image as PILImage
import tempfile


def create_pdf_from_slides(slides: List[Dict], output_path: str, template_info: Dict = None):
    """
    Create a PDF presentation from slides data.
    
    Args:
        slides: List of slide dictionaries
        output_path: Path where PDF will be saved
        template_info: Optional template information (colors, fonts, etc.)
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Build story (content)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading2'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=12,
        alignment=TA_LEFT,
        leading=18,
        fontName='Helvetica'
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        alignment=TA_LEFT,
        leading=18,
        leftIndent=20,
        fontName='Helvetica'
    )
    
    for slide in slides:
        slide_type = slide.get('type', '')
        
        if slide_type == 'title':
            # Title slide
            title = slide.get('title', 'Presentation')
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5*inch))
            
        elif slide_type == 'intro':
            # Introduction slide
            story.append(Paragraph("Giriş", slide_title_style))
            story.append(Spacer(1, 0.2*inch))
            
            aim = slide.get('aim', '')
            if aim:
                story.append(Paragraph(f"<b>Məqsəd:</b> {aim}", content_style))
                story.append(Spacer(1, 0.15*inch))
            
            summary = slide.get('summary', '')
            if summary:
                story.append(Paragraph(f"<b>Xülasə:</b> {summary}", content_style))
            
        elif slide_type == 'main':
            # Main content slide
            title = slide.get('title', '')
            if title:
                story.append(Paragraph(title, slide_title_style))
                story.append(Spacer(1, 0.2*inch))
            
            # Add bullet points
            for i in range(1, 5):
                point = slide.get(f'point{i}', '')
                if point:
                    story.append(Paragraph(f"• {point}", bullet_style))
            
            # Handle visual if present
            visual = slide.get('visual', {})
            if visual and visual.get('type') == 'image':
                image_path = visual.get('image_path')
                if image_path and os.path.exists(image_path):
                    try:
                        # Add image to PDF
                        img = Image(image_path, width=5*inch, height=3*inch)
                        story.append(Spacer(1, 0.2*inch))
                        story.append(img)
                    except Exception as e:
                        # Fallback to description if image can't be loaded
                        description = visual.get('description', 'Image')
                        story.append(Spacer(1, 0.2*inch))
                        story.append(Paragraph(f"<i>[Vizual: {description}]</i>", content_style))
                elif visual.get('description'):
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph(f"<i>[Vizual: {visual['description']}]</i>", content_style))
        
        elif slide_type == 'recommendation':
            # Recommendations slide
            story.append(Paragraph("Tövsiyələr", slide_title_style))
            story.append(Spacer(1, 0.2*inch))
            
            for i in range(1, 6):
                rec = slide.get(f'recommendation{i}', '')
                if rec:
                    story.append(Paragraph(f"• {rec}", bullet_style))
        
        # Add page break between slides (except for the last one)
        if slide != slides[-1]:
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    return output_path

