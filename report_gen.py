from fpdf import FPDF
import datetime
from PIL import Image, ImageDraw, ImageFont
import os

def generate_logo(path='outputs/tc_logo.png', size=200):
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, size, size], fill=(0, 120, 60))
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    text = "TC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2),
        text,
        fill="white",
        font=font
    )
    img.save(path)
    return path

class AuditReport(FPDF):
    def header(self):
        logo_path = generate_logo()
        self.image(logo_path, 10, 8, 25)
        self.set_font('helvetica', 'B', 15)
        self.cell(80)
        self.cell(100, 10, 'ENVIRONMENTAL COMPLIANCE CERTIFICATE', border=0, ln=0, align='R')
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 5, 'DISCLAIMER: This is a preliminary remote sensing audit based on satellite imagery.', 0, 1, 'C')
        self.cell(0, 5, 'Final EUDR compliance remains the responsibility of the operator.', 0, 0, 'C')

def create_pdf_report(audit_id, supplier_name, verdict, area_lost, map_path):
    os.makedirs('outputs', exist_ok=True)
    pdf = AuditReport()
    pdf.add_page()

    # Supplier Summary Block
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'Supplier: {supplier_name}', ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 10, f'Audit ID: {audit_id}', ln=True)
    pdf.cell(0, 10, f'Date: {datetime.date.today()}', ln=True)

    # Verdict Highlight
    if verdict == "NON_COMPLIANT":
        color = (200, 0, 0)
    elif verdict == "LEGALLY_INCOMPLETE":
        color = (204, 102, 0)
    elif verdict == "DATA_GAP":
        color = (100, 100, 100)
    else:
        color = (0, 128, 0)

    pdf.set_text_color(*color)
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 15, f'VERDICT: {verdict}', ln=True)
    pdf.set_text_color(0, 0, 0)

    # Landscape context note
    pdf.set_font('helvetica', 'I', 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, 'Map shows 5km landscape buffer. Red = forest loss post-2020 (Hansen GFC v1.13). Green = tree cover baseline.', ln=True)
    pdf.cell(0, 6, 'Loss shown is regional context - not confined to the audited plot boundary.', ln=True)
    pdf.set_text_color(0, 0, 0)

    # Evidence Map — fixed height to ensure footer always renders
    if map_path and os.path.exists(map_path):
        pdf.image(map_path, x=10, w=190, h=130)
    else:
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, '[Satellite map unavailable]', ln=True)

    # Deforestation area figure below map
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    if area_lost == 0:
        loss_text = 'Total forest loss detected in buffer zone: 0 sq m (Note: Hansen GFC coverage may be limited in boreal regions)'
    else:
        loss_text = f'Total forest loss detected in buffer zone: {area_lost:,.0f} sq m'
    pdf.cell(0, 8, loss_text, ln=True)
    pdf.set_text_color(0, 0, 0)

    report_name = f"outputs/certificate_{audit_id}.pdf"
    pdf.output(report_name)
    print(f"📄 Certificate generated: {report_name}")