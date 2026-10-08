import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def test_pdf():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('ResumeTitle', parent=styles['Normal'], fontSize=20, leading=24, fontName='Helvetica-Bold', alignment=1, textColor=colors.HexColor('#0f172a'))
    contact_style = ParagraphStyle('ResumeContact', parent=styles['Normal'], fontSize=9, leading=12, fontName='Helvetica', alignment=1, textColor=colors.HexColor('#334155'))
    section_style = ParagraphStyle('ResumeSection', parent=styles['Normal'], fontSize=11, leading=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e40af'), spaceBefore=8, spaceAfter=3)
    body_style = ParagraphStyle('ResumeBody', parent=styles['Normal'], fontSize=9.5, leading=13, fontName='Helvetica', textColor=colors.HexColor('#1e293b'))
    bullet_style = ParagraphStyle('ResumeBullet', parent=body_style, leftIndent=12, bulletIndent=4)
    job_header_style = ParagraphStyle('JobHeader', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f172a'))

    story = []
    story.append(Paragraph('Shiva Developer', title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph('shiva@vidyamarg.ai | +1 (555) 234-5678 | New York, NY', contact_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=6))

    story.append(Paragraph('PROFESSIONAL SUMMARY', section_style))
    story.append(Paragraph('AI Engineer specializing in LLM application architecture and agentic workflows.', body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('TECHNICAL SKILLS', section_style))
    story.append(Paragraph('<b>Languages &amp; Frameworks:</b> Python, PyTorch, LangChain, React, FastAPI', body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('WORK EXPERIENCE', section_style))
    story.append(Paragraph('<b>Senior AI Engineer</b> &mdash; <i>Tech Solutions</i> <font color="#64748b">(2022 &ndash; Present)</font>', job_header_style))
    story.append(Paragraph('&bull; Designed system architectures handling 5M+ daily requests.', bullet_style))
    story.append(Paragraph('&bull; Collaborated on high-impact agentic projects with 99.9% uptime.', bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('EDUCATION', section_style))
    story.append(Paragraph('<b>B.Tech in Computer Science</b> &mdash; <i>University Institute of Technology</i> <font color="#64748b">(2022)</font>', job_header_style))

    doc.build(story)
    pdf = buf.getvalue()
    assert pdf.startswith(b'%PDF'), 'Invalid PDF'
    print('PDF generated successfully! Size:', len(pdf))

if __name__ == '__main__':
    test_pdf()
