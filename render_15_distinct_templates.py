"""
Renders 15 completely unique, genuine Overleaf-inspired resume PDF previews and PNG images.
Each template uses its distinct layout function, structure, typography, and page design.
Output: frontend/public/templates/previews/{slug}.png
"""

import os
import io
import pymupdf as fitz
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "frontend", "public", "templates", "previews")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH, HEIGHT = letter

# ─────────────────────────────────────────────────────────────────────────────
# 1. Classic ATS Resume (Jake's Resume / Monochrome / Centered Header)
# ─────────────────────────────────────────────────────────────────────────────
def render_classic_ats():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=30, bottomMargin=30)
    avail = WIDTH - 64

    name_s = ParagraphStyle("ATS_Name", fontName="Times-Bold", fontSize=18, leading=20, alignment=TA_CENTER)
    contact_s = ParagraphStyle("ATS_Contact", fontName="Times-Roman", fontSize=8.5, leading=11, alignment=TA_CENTER)
    sec_s = ParagraphStyle("ATS_Sec", fontName="Times-Bold", fontSize=10.5, leading=12, textTransform="uppercase", spaceBefore=4, spaceAfter=1)
    body_s = ParagraphStyle("ATS_Body", fontName="Times-Roman", fontSize=8.5, leading=11)
    bold_s = ParagraphStyle("ATS_Bold", fontName="Times-Bold", fontSize=8.5, leading=11)
    right_s = ParagraphStyle("ATS_Right", fontName="Times-Italic", fontSize=8.5, leading=11, alignment=TA_RIGHT)
    bullet_s = ParagraphStyle("ATS_Bullet", fontName="Times-Roman", fontSize=8.2, leading=10.5, leftIndent=12)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Spacer(1, 1),
        Paragraph("+1 (555) 782-9301 | alex.mercer@vidyamarg.ai | linkedin.com/in/alex-mercer | github.com/alexmercer", contact_s),
        Spacer(1, 4),

        Paragraph("PROFESSIONAL SUMMARY", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("Full-Stack & Cloud Systems Software Engineer with 6+ years of experience architecting resilient distributed backends, microservices, and AI pipelines handling 5M+ daily API transactions.", body_s),
        Spacer(1, 4),

        Paragraph("WORK EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b>", bold_s), Paragraph("June 2023 – Present", right_s)],
               [Paragraph("<i>Senior Software Engineer</i>", body_s), Paragraph("San Francisco, CA", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected high-throughput microservices using Python FastAPI, PostgreSQL, and Redis handling 5M+ daily requests with 99.99% SLA.", bullet_s),
        Paragraph("• Optimized distributed database latency across 12 shards, cutting p99 response times by 42% through connection pooling.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b>", bold_s), Paragraph("July 2020 – May 2023", right_s)],
               [Paragraph("<i>Software Engineer</i>", body_s), Paragraph("San Francisco, CA", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Built full-stack SaaS features using TypeScript and Next.js for 250k+ active business accounts.", bullet_s),
        Paragraph("• Implemented OAuth2 and JWT authorization workflows, reducing credential stuffing vulnerability to zero.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>University of California, Berkeley</b>", bold_s), Paragraph("Berkeley, CA", right_s)],
               [Paragraph("<i>Bachelor of Science in Computer Science & Engineering</i>; GPA: 3.85/4.0", body_s), Paragraph("Aug. 2016 – May 2020", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Spacer(1, 4),

        Paragraph("TECHNICAL SKILLS", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Languages:</b> Python, TypeScript, Go, JavaScript, SQL, C++, Bash", body_s),
        Paragraph("<b>Frameworks & Tools:</b> FastAPI, React, Next.js, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Modern Corporate (Left Header / Navy Rules / Corporate Hierarchy)
# ─────────────────────────────────────────────────────────────────────────────
def render_modern_corporate():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=28, bottomMargin=28)
    avail = WIDTH - 64

    name_s = ParagraphStyle("Corp_N", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#1e40af"))
    contact_s = ParagraphStyle("Corp_C", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569"))
    sec_s = ParagraphStyle("Corp_Sec", fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#1e40af"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("Corp_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("Corp_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("Corp_Bullet", fontName="Helvetica", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("alex.mercer@vidyamarg.ai  •  +1 (555) 782-9301  •  San Francisco, CA  •  linkedin.com/in/alex-mercer", contact_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e40af"), spaceBefore=3, spaceAfter=5),

        Paragraph("EXECUTIVE PROFILE", sec_s),
        Paragraph("Senior Software Engineer with 6+ years driving technical modernization and building high-concurrency cloud services in fast-paced corporate environments.", body_s),
        Spacer(1, 4),

        Paragraph("PROFESSIONAL EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#93c5fd"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected event-driven microservices processing 5M+ daily API transactions with 99.99% uptime.", bullet_s),
        Paragraph("• Reduced p99 latency by 42% through distributed caching, connection pooling, and query plan tuning.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Shipped multi-tenant SaaS features in TypeScript & Next.js for 250k+ active corporate clients.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION & CREDENTIALS", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#93c5fd"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>University of California, Berkeley</b> -- B.S. in Computer Science & Engineering (GPA: 3.85 / 4.0)", body_s),
        Spacer(1, 4),

        Paragraph("CORE SKILLS & TECHNOLOGIES", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#93c5fd"), spaceBefore=1, spaceAfter=3),
        Paragraph("Python, TypeScript, Go, FastAPI, Next.js, PostgreSQL, Redis, Docker, Kubernetes, AWS, Git", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Executive Resume (Deep Navy / Classic Serif / Leadership Focus)
# ─────────────────────────────────────────────────────────────────────────────
def render_executive_resume():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=32, bottomMargin=32)
    avail = WIDTH - 72

    name_s = ParagraphStyle("Exec_N", fontName="Times-Bold", fontSize=22, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#14234b"))
    sub_s = ParagraphStyle("Exec_Sub", fontName="Times-Italic", fontSize=10, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#1e3a8a"))
    contact_s = ParagraphStyle("Exec_C", fontName="Times-Roman", fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#334155"))
    sec_s = ParagraphStyle("Exec_Sec", fontName="Times-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#14234b"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("Exec_B", fontName="Times-Roman", fontSize=8.8, leading=12, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("Exec_Bold", fontName="Times-Bold", fontSize=8.8, leading=12, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("Exec_Bullet", fontName="Times-Roman", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155"), leftIndent=12)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("Engineering Leadership & Cloud Systems Architecture", sub_s),
        Spacer(1, 2),
        Paragraph("alex.mercer@vidyamarg.ai  |  +1 (555) 782-9301  |  San Francisco, CA  |  linkedin.com/in/alex-mercer", contact_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#14234b"), spaceBefore=3, spaceAfter=6),

        Paragraph("LEADERSHIP PROFILE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=3),
        Paragraph("Accomplished engineering leader with 6+ years driving distributed systems architecture, team mentorship, and high-stakes product delivery. Proven ability to bridge engineering execution with business ROI.", body_s),
        Spacer(1, 5),

        Paragraph("EXECUTIVE EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Directed microservices architecture servicing 5M+ daily transactions, delivering 99.99% uptime SLA.", bullet_s),
        Paragraph("• Spearheaded automated CI/CD and observability pipelines across 14 distributed engineering squads.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Championed core SaaS features for 250k+ active clients, boosting annual enterprise renewals by 24%.", bullet_s),
        Spacer(1, 5),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. in Computer Science & Engineering</b>, University of California, Berkeley (GPA: 3.85 / 4.0)", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Modern Two-Column (Deedy Cornell Overleaf 32% / 68% Split)
# ─────────────────────────────────────────────────────────────────────────────
def render_modern_two_column():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=28, rightMargin=28, topMargin=26, bottomMargin=26)
    avail = WIDTH - 56
    left_w = avail * 0.31
    right_w = avail * 0.69

    name_s = ParagraphStyle("D_N", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#1e293b"))
    tag_s = ParagraphStyle("D_T", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#2563eb"))
    side_head = ParagraphStyle("D_SH", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    side_body = ParagraphStyle("D_SB", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    main_head = ParagraphStyle("D_MH", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    main_body = ParagraphStyle("D_MB", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#334155"))
    main_bold = ParagraphStyle("D_MBold", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("D_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=8)

    left_flow = [
        Paragraph("CONTACT", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("alex.mercer@vidyamarg.ai<br/>+1 (555) 782-9301<br/>San Francisco, CA<br/>github.com/alexmercer", side_body),
        Spacer(1, 4),
        Paragraph("EDUCATION", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("<b>UC BERKELEY</b><br/>BS Computer Science<br/>Grad. 2020<br/>GPA: 3.85 / 4.0", side_body),
        Spacer(1, 4),
        Paragraph("SKILLS", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("Python • TypeScript • Go<br/>FastAPI • React • Next.js<br/>Docker • Kubernetes<br/>PostgreSQL • Redis • AWS", side_body),
    ]

    right_flow = [
        Paragraph("EXPERIENCE", main_head),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563eb"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>APEX CLOUD SYSTEMS</b> | Senior Software Engineer <font color='#64748b' size='7.5'><i>(2023 – Present)</i></font>", main_bold),
        Paragraph("• Architected high-throughput microservices handling 5M+ daily requests using FastAPI & Redis.", bullet_s),
        Paragraph("• Reduced p99 API latencies by 42% via connection pool tuning and query optimization.", bullet_s),
        Spacer(1, 4),

        Paragraph("<b>HORIZON TECH LABS</b> | Software Engineer <font color='#64748b' size='7.5'><i>(2020 – 2023)</i></font>", main_bold),
        Paragraph("• Built scalable SaaS features in TypeScript and Next.js for 250k+ active business accounts.", bullet_s),
        Paragraph("• Engineered secure JWT & OAuth2 auth engine with automated rate limiters.", bullet_s),
        Spacer(1, 5),

        Paragraph("PROJECTS", main_head),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563eb"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>VIDYAMARG AI PLATFORM</b> | Python, React, Redis", main_bold),
        Paragraph("• Built AI resume tailoring system with sub-100ms lexical matching and LaTeX compile pipeline.", bullet_s),
    ]

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("Senior Software Engineer & Distributed Systems Specialist", tag_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=3, spaceAfter=6),
        Table([[left_flow, right_flow]], colWidths=[left_w, right_w], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('RIGHTPADDING', (0,0), (0,0), 10),
            ('LEFTPADDING', (1,0), (1,0), 10),
            ('LINEAFTER', (0,0), (0,0), 0.5, colors.HexColor("#cbd5e1")),
        ])
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Color Sidebar (Full-Height Dark Panel on Left)
# ─────────────────────────────────────────────────────────────────────────────
def render_color_sidebar():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    avail = WIDTH - 48
    col1 = avail * 0.33
    col2 = avail * 0.67

    side_h = ParagraphStyle("S_H", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#ffffff"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    side_b = ParagraphStyle("S_B", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#cbd5e1"))
    side_bold = ParagraphStyle("S_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#38bdf8"))
    
    main_h = ParagraphStyle("M_H", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    main_b = ParagraphStyle("M_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#334155"))
    main_bold = ParagraphStyle("M_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("M_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=8)

    left_cells = [
        Paragraph("ALEX MERCER", ParagraphStyle("L_N", fontName="Helvetica-Bold", fontSize=15, leading=17, textColor=colors.white)),
        Paragraph("Full-Stack Engineer", ParagraphStyle("L_T", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#38bdf8"))),
        Spacer(1, 6),
        Paragraph("CONTACT", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("✉ alex.mercer@vidyamarg.ai<br/>☎ +1 (555) 782-9301<br/>📍 San Francisco, CA", side_b),
        Spacer(1, 6),
        Paragraph("CORE SKILLS", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("Python, TypeScript, Go<br/>FastAPI, Next.js, React<br/>Docker, Kubernetes, AWS<br/>PostgreSQL, Redis", side_b),
        Spacer(1, 6),
        Paragraph("EDUCATION", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. Computer Science</b>", side_bold),
        Paragraph("UC Berkeley, 2020", side_b),
    ]

    right_cells = [
        Paragraph("PROFESSIONAL SUMMARY", main_h),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=1, spaceAfter=3),
        Paragraph("Creative Full-Stack Software Engineer with 6+ years building microservices, cloud applications, and real-time platforms.", main_b),
        Spacer(1, 5),

        Paragraph("WORK EXPERIENCE", main_h),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer <font color='#64748b' size='7.5'><i>(2023 – Present)</i></font>", main_bold),
        Paragraph("• Architected event-driven microservices serving 5M+ daily requests using FastAPI & Redis.", bullet_s),
        Paragraph("• Reduced p99 API latency by 42% through connection pooling and caching.", bullet_s),
        Spacer(1, 4),

        Paragraph("<b>Horizon Tech Labs</b> | Software Engineer <font color='#64748b' size='7.5'><i>(2020 – 2023)</i></font>", main_bold),
        Paragraph("• Developed full-stack SaaS features in TypeScript & Next.js for 250k+ active accounts.", bullet_s),
        Spacer(1, 5),

        Paragraph("KEY PROJECTS", main_h),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Vidyamarg AI Engine</b> (FastAPI, Redis, Next.js)", main_bold),
        Paragraph("• Built high-performance LaTeX compilation pipeline with live preview rendering.", bullet_s),
    ]

    t = Table([[left_cells, right_cells]], colWidths=[col1, col2], style=[
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#0f172a")),
        ('TOPPADDING', (0,0), (0,0), 16),
        ('BOTTOMPADDING', (0,0), (0,0), 16),
        ('LEFTPADDING', (0,0), (0,0), 12),
        ('RIGHTPADDING', (0,0), (0,0), 12),
        ('TOPPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (1,0), (1,0), 14),
        ('RIGHTPADDING', (1,0), (1,0), 8),
    ])
    doc.build([t])
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Minimalist Elegant (Muted Slate / Generous Whitespace / Subtle Lines)
# ─────────────────────────────────────────────────────────────────────────────
def render_minimalist_elegant():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=34, bottomMargin=34)
    avail = WIDTH - 72

    name_s = ParagraphStyle("Min_N", fontName="Times-Roman", fontSize=18, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#1e293b"))
    contact_s = ParagraphStyle("Min_C", fontName="Times-Roman", fontSize=8, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#64748b"))
    sec_s = ParagraphStyle("Min_S", fontName="Times-Roman", fontSize=9.5, leading=12, alignment=TA_CENTER, textTransform="uppercase", spaceBefore=7, spaceAfter=2)
    body_s = ParagraphStyle("Min_B", fontName="Times-Roman", fontSize=8.2, leading=11.5, textColor=colors.HexColor("#334155"))
    bold_s = ParagraphStyle("Min_Bold", fontName="Times-Bold", fontSize=8.2, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("Min_Bullet", fontName="Times-Roman", fontSize=8, leading=10.5, textColor=colors.HexColor("#475569"), leftIndent=10)

    story = [
        Paragraph("A L E X &nbsp; M E R C E R", name_s),
        Spacer(1, 2),
        Paragraph("alex.mercer@vidyamarg.ai &nbsp; • &nbsp; +1 (555) 782-9301 &nbsp; • &nbsp; San Francisco, CA &nbsp; • &nbsp; linkedin.com/in/alex", contact_s),
        Spacer(1, 4),
        HRFlowable(width="60%", thickness=0.4, color=colors.HexColor("#94a3b8"), spaceBefore=2, spaceAfter=5),

        Paragraph("P R O F I L E", sec_s),
        Paragraph("Software engineer specializing in distributed backend systems, low-latency APIs, and scalable infrastructure.", body_s),
        Spacer(1, 4),

        Paragraph("E X P E R I E N C E", sec_s),
        Table([[Paragraph("<b>Apex Cloud Systems</b> -- Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected high-throughput microservices handling 5M+ daily requests using FastAPI.", bullet_s),
        Paragraph("• Reduced p99 database latency by 42% through connection pooling and indexing.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> -- Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Shipped scalable SaaS features serving 250k+ active business subscribers.", bullet_s),
        Spacer(1, 4),

        Paragraph("E D U C A T I O N", sec_s),
        Table([[Paragraph("<b>University of California, Berkeley</b> -- B.S. in Computer Science", bold_s), Paragraph("2016 – 2020", ParagraphStyle("R3", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.8, avail*0.2], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Spacer(1, 4),

        Paragraph("S K I L L S", sec_s),
        Paragraph("Python, TypeScript, Go, FastAPI, React, Next.js, Docker, Kubernetes, PostgreSQL, Redis", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Bold Creative (Asymmetric Header / Red Accent / Punchy Typography)
# ─────────────────────────────────────────────────────────────────────────────
def render_bold_creative():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=26, bottomMargin=26)
    avail = WIDTH - 60

    name_s = ParagraphStyle("B_N", fontName="Helvetica-Bold", fontSize=24, leading=26, textColor=colors.HexColor("#b91c1c"))
    title_s = ParagraphStyle("B_T", fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#0f172a"))
    contact_s = ParagraphStyle("B_C", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b"))
    sec_s = ParagraphStyle("B_S", fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#b91c1c"), spaceBefore=6, spaceAfter=2)
    body_s = ParagraphStyle("B_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("B_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("B_Bullet", fontName="Helvetica", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("ALEX MERCER", name_s),
        Paragraph("SENIOR FULL-STACK & SYSTEMS ENGINEER", title_s),
        Paragraph("alex.mercer@vidyamarg.ai | +1 (555) 782-9301 | San Francisco, CA", contact_s),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#b91c1c"), spaceBefore=3, spaceAfter=5),

        Paragraph("EXPERIENCE", sec_s),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected high-throughput microservices using Python FastAPI, PostgreSQL, and Redis handling 5M+ daily requests.", bullet_s),
        Paragraph("• Optimized distributed database latency across 12 shards, reducing p99 response times by 42%.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Developed full-stack SaaS features using TypeScript and Next.js for 250k+ active clients.", bullet_s),
        Spacer(1, 4),

        Paragraph("PROJECTS", sec_s),
        Paragraph("<b>Vidyamarg AI Engine</b> -- Career intelligence platform with real-time LaTeX PDF compilation pipeline.", body_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        Paragraph("<b>B.S. in Computer Science & Engineering</b>, UC Berkeley (GPA: 3.85 / 4.0)", body_s),
        Spacer(1, 4),

        Paragraph("TECHNICAL SKILLS", sec_s),
        Paragraph("Python, TypeScript, Go, FastAPI, React, Next.js, Docker, Kubernetes, AWS, PostgreSQL, Redis", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Software Engineer (HackerRank / Monospace Code Badges / Technical Arsenal)
# ─────────────────────────────────────────────────────────────────────────────
def render_software_engineer():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=26, bottomMargin=26)
    avail = WIDTH - 60

    name_s = ParagraphStyle("S_N", fontName="Helvetica-Bold", fontSize=18, leading=20, alignment=TA_LEFT, textColor=colors.HexColor("#0f172a"))
    contact_s = ParagraphStyle("S_C", fontName="Courier", fontSize=8, leading=10, textColor=colors.HexColor("#0369a1"))
    sec_s = ParagraphStyle("S_S", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("S_B", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155"))
    bold_s = ParagraphStyle("S_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a"))
    mono_tag = ParagraphStyle("S_Mono", fontName="Courier-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#0284c7"))
    bullet_s = ParagraphStyle("S_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("github.com/alexmercer | alex.mercer@vidyamarg.ai | +1 (555) 782-9301 | San Francisco, CA", contact_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=3, spaceAfter=4),

        Paragraph("TECHNICAL ARSENAL", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=1, spaceAfter=3),
        Table([
            [Paragraph("<b>Languages</b>", bold_s), Paragraph("Python, TypeScript, Go, JavaScript, SQL, C++, Bash", body_s)],
            [Paragraph("<b>Frameworks</b>", bold_s), Paragraph("FastAPI, Next.js, React, Node.js, PyTorch, LangChain", body_s)],
            [Paragraph("<b>Cloud & Ops</b>", bold_s), Paragraph("Docker, Kubernetes, AWS, PostgreSQL, Redis, Linux, GitHub Actions", body_s)],
        ], colWidths=[avail*0.2, avail*0.8], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 1)]),
        Spacer(1, 4),

        Paragraph("EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> -- Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=bold_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("Stack: <code>Python, FastAPI, Redis, PostgreSQL, Docker, AWS</code>", mono_tag),
        Paragraph("• Architected microservice fleet handling 5M+ daily requests with 99.99% uptime.", bullet_s),
        Paragraph("• Built distributed Redis caching tier dropping p99 API latencies by 42%.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> -- Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=bold_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("Stack: <code>TypeScript, Next.js, Node.js, PostgreSQL, Docker</code>", mono_tag),
        Paragraph("• Shipped mission-critical SaaS apps serving 250k+ active business accounts.", bullet_s),
        Spacer(1, 4),

        Paragraph("FEATURED PROJECTS", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Vidyamarg AI Engine</b> | <i>FastAPI, Next.js, Redis, PyTorch</i>", bold_s),
        Paragraph("• Career intelligence engine featuring sub-50ms resume parser & sandboxed LaTeX compiler.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>B.S. in Computer Science & Engineering</b> | UC Berkeley", bold_s), Paragraph("2016 – 2020", ParagraphStyle("R3", parent=bold_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.8, avail*0.2], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 9. AI/ML Engineer (Violet Theme / Models & Benchmarks / Research Emphasis)
# ─────────────────────────────────────────────────────────────────────────────
def render_aiml_engineer():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=28, bottomMargin=28)
    avail = WIDTH - 64

    name_s = ParagraphStyle("AI_N", fontName="Helvetica-Bold", fontSize=19, leading=21, textColor=colors.HexColor("#6d28d9"))
    sub_s = ParagraphStyle("AI_Sub", fontName="Helvetica", fontSize=9.5, leading=12, textColor=colors.HexColor("#475569"))
    sec_s = ParagraphStyle("AI_S", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#6d28d9"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("AI_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("AI_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("AI_Bullet", fontName="Helvetica", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("AI & Machine Learning Engineer | Deep Learning & LLM Systems", sub_s),
        Paragraph("alex.mercer@vidyamarg.ai | +1 (555) 782-9301 | San Francisco, CA | github.com/alexmercer", ParagraphStyle("C", parent=sub_s, fontSize=8, textColor=colors.HexColor("#64748b"))),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6d28d9"), spaceBefore=3, spaceAfter=5),

        Paragraph("AI / ML MODELS & ARCHITECTURES", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c4b5fd"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Frameworks:</b> PyTorch, TensorFlow, HuggingFace Transformers, LangChain, vLLM", body_s),
        Paragraph("<b>Specialties:</b> RAG Pipelines, Fine-tuning (LoRA, QLoRA), Vector Search (FAISS, Milvus)", body_s),
        Spacer(1, 4),

        Paragraph("MACHINE LEARNING EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c4b5fd"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> -- Senior AI Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected multi-model agentic RAG pipeline boosting domain query accuracy by 38%.", bullet_s),
        Paragraph("• Optimized inference latency from 450ms to 95ms using TensorRT-LLM and KV caching.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> -- ML Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Deployed predictive recommendation models serving 250k+ daily users on AWS SageMaker.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c4b5fd"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. in Computer Science & Engineering</b>, UC Berkeley (GPA: 3.85 / 4.0)", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 10. Data Scientist (Indigo / Statistical Metrics / Mathematical Computing)
# ─────────────────────────────────────────────────────────────────────────────
def render_data_scientist():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=28, bottomMargin=28)
    avail = WIDTH - 64

    name_s = ParagraphStyle("DS_N", fontName="Helvetica-Bold", fontSize=19, leading=21, textColor=colors.HexColor("#4338ca"))
    sub_s = ParagraphStyle("DS_Sub", fontName="Helvetica", fontSize=9, leading=11, textColor=colors.HexColor("#64748b"))
    sec_s = ParagraphStyle("DS_S", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#4338ca"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("DS_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("DS_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("DS_Bullet", fontName="Helvetica", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Paragraph("Data Scientist & Quantitative Analytics Specialist | alex.mercer@vidyamarg.ai", sub_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4338ca"), spaceBefore=3, spaceAfter=5),

        Paragraph("ANALYTICS & COMPUTATIONAL SKILLS", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a5b4fc"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Languages & Tools:</b> Python, R, SQL, Pandas, NumPy, Scikit-Learn, PyTorch, BigQuery", body_s),
        Paragraph("<b>Methods:</b> Causal Inference, A/B Testing, Time Series Forecasting, Bayesian Analysis", body_s),
        Spacer(1, 4),

        Paragraph("DATA SCIENCE EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a5b4fc"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> -- Senior Data Scientist", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Engineered churn prediction algorithms lowering annual enterprise subscriber turnover by 18%.", bullet_s),
        Paragraph("• Built real-time anomaly detection pipeline flagging fraudulent transactions with 99.4% precision.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> -- Data Analyst & Scientist", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Spearheaded centralized BI metrics dashboards tracking $45M+ in ARR across product lines.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a5b4fc"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. in Computer Science & Statistics</b>, UC Berkeley (GPA: 3.85 / 4.0)", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 11. Developer Portfolio (Cyan Theme / Project Cards / Live Demo URLs)
# ─────────────────────────────────────────────────────────────────────────────
def render_developer_portfolio():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=26, bottomMargin=26)
    avail = WIDTH - 60

    name_s = ParagraphStyle("Port_N", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#0e7490"))
    sub_s = ParagraphStyle("Port_Sub", fontName="Courier", fontSize=8.5, leading=11, textColor=colors.HexColor("#0891b2"))
    sec_s = ParagraphStyle("Port_S", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#0e7490"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("Port_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bold_s = ParagraphStyle("Port_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("Port_Bullet", fontName="Helvetica", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=10)

    story = [
        Paragraph("ALEX MERCER", name_s),
        Paragraph("github.com/alexmercer | alex.mercer@vidyamarg.ai | portfolio.alexmercer.dev", sub_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0e7490"), spaceBefore=3, spaceAfter=5),

        Paragraph("FEATURED PROJECTS & OPEN-SOURCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#67e8f9"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Vidyamarg AI Engine</b> -- <i>FastAPI, Next.js, Redis, PyTorch</i> [github.com/alexmercer/vidyamarg]", bold_s),
        Paragraph("• Career intelligence engine featuring sandboxed Overleaf LaTeX compilation pipeline.", bullet_s),
        Paragraph("• Implemented zero-hallucination semantic skill matching with sub-50ms response times.", bullet_s),
        Spacer(1, 3),

        Paragraph("<b>CloudScale Microservices</b> -- <i>Go, Kubernetes, Redis, Docker</i> [live: demo.cloudscale.io]", bold_s),
        Paragraph("• Distributed event mesh handling 5M+ daily requests with real-time WebSocket metrics.", bullet_s),
        Spacer(1, 4),

        Paragraph("ENGINEERING EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#67e8f9"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", bold_s), Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Optimized distributed database query latency across 12 shards, reducing p99 by 42%.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", bold_s), Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Built full-stack SaaS features in TypeScript & Next.js for 250k+ active accounts.", bullet_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        Paragraph("<b>B.S. Computer Science & Engineering</b>, UC Berkeley (GPA: 3.85 / 4.0)", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 12. Graduate / Fresher (Education First / Campus Coursework & Hackathons)
# ─────────────────────────────────────────────────────────────────────────────
def render_graduate_fresher():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=30, bottomMargin=30)
    avail = WIDTH - 64

    name_s = ParagraphStyle("F_N", fontName="Times-Bold", fontSize=18, leading=20, alignment=TA_CENTER)
    contact_s = ParagraphStyle("F_C", fontName="Times-Roman", fontSize=8.5, leading=11, alignment=TA_CENTER)
    sec_s = ParagraphStyle("F_S", fontName="Times-Bold", fontSize=10.5, leading=12, textTransform="uppercase", spaceBefore=4, spaceAfter=1)
    body_s = ParagraphStyle("F_B", fontName="Times-Roman", fontSize=8.5, leading=11)
    bold_s = ParagraphStyle("F_Bold", fontName="Times-Bold", fontSize=8.5, leading=11)
    right_s = ParagraphStyle("F_R", fontName="Times-Italic", fontSize=8.5, leading=11, alignment=TA_RIGHT)
    bullet_s = ParagraphStyle("F_Bullet", fontName="Times-Roman", fontSize=8.2, leading=10.5, leftIndent=12)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Spacer(1, 1),
        Paragraph("alex.mercer@vidyamarg.ai | +1 (555) 782-9301 | San Francisco, CA | github.com/alexmercer", contact_s),
        Spacer(1, 4),

        # Education First for New Grads
        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>University of California, Berkeley</b>", bold_s), Paragraph("Berkeley, CA", right_s)],
               [Paragraph("<i>B.S. in Computer Science & Engineering</i>; GPA: 3.85 / 4.0 (Dean's Honors List)", body_s), Paragraph("Graduated May 2020", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("Relevant Coursework: Distributed Systems, Database Management, Algorithms, Operating Systems, Machine Learning", body_s),
        Spacer(1, 4),

        Paragraph("ACADEMIC & CAPSTONE PROJECTS", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Vidyamarg Career Platform</b> | <i>FastAPI, Next.js, Redis, PostgreSQL</i>", bold_s),
        Paragraph("• Built distributed real-time platform with automated LaTeX compiling engine and ATS resume checker.", bullet_s),
        Paragraph("• Implemented token bucket rate limiter handling 10k requests/min with sub-10ms response overhead.", bullet_s),
        Spacer(1, 3),

        Paragraph("<b>Distributed Key-Value Store</b> | <i>Go, Raft Consensus, Docker</i>", bold_s),
        Paragraph("• Engineered fault-tolerant distributed key-value cluster implementing the Raft consensus algorithm.", bullet_s),
        Spacer(1, 4),

        Paragraph("TECHNICAL SKILLS", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Languages:</b> Python, TypeScript, Go, Java, C++, SQL, Bash", body_s),
        Paragraph("<b>Tools & Systems:</b> FastAPI, Next.js, Docker, Kubernetes, PostgreSQL, Redis, Git, Linux", body_s),
        Spacer(1, 4),

        Paragraph("INTERNSHIP EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> -- Software Engineering Intern", bold_s), Paragraph("Summer 2019", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Contributed to backend microservices, optimizing SQL queries and adding automated integration tests.", bullet_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 13. Academic CV (Harvard / Oxford Formal Serifs / Citation Publications)
# ─────────────────────────────────────────────────────────────────────────────
def render_academic_cv():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=38, rightMargin=38, topMargin=34, bottomMargin=34)
    avail = WIDTH - 76

    name_s = ParagraphStyle("A_N", fontName="Times-Bold", fontSize=17, leading=19, alignment=TA_CENTER)
    contact_s = ParagraphStyle("A_C", fontName="Times-Italic", fontSize=8.5, leading=11, alignment=TA_CENTER)
    sec_s = ParagraphStyle("A_S", fontName="Times-Bold", fontSize=10, leading=13, alignment=TA_CENTER, textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    body_s = ParagraphStyle("A_B", fontName="Times-Roman", fontSize=8.5, leading=11.5)
    bold_s = ParagraphStyle("A_Bold", fontName="Times-Bold", fontSize=8.5, leading=11.5)
    pub_s = ParagraphStyle("A_Pub", fontName="Times-Roman", fontSize=8, leading=10.5, leftIndent=14)

    story = [
        Paragraph("ALEX MERCER, Ph.D. Candidate", name_s),
        Paragraph("Department of Electrical Engineering & Computer Sciences | University of California, Berkeley", contact_s),
        Paragraph("alex.mercer@berkeley.edu | (555) 782-9301 | https://eecs.berkeley.edu/~mercer", contact_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#475569"), spaceBefore=3, spaceAfter=6),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="40%", thickness=0.5, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>University of California, Berkeley</b>", bold_s), Paragraph("Berkeley, CA", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))],
               [Paragraph("Ph.D. in Computer Science (Advisor: Prof. J. Patterson)", body_s), Paragraph("2020 – Present", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))],
               [Paragraph("B.S. in Computer Science, Magna Cum Laude", body_s), Paragraph("2016 – 2020", ParagraphStyle("R3", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Spacer(1, 5),

        Paragraph("RESEARCH PUBLICATIONS", sec_s),
        HRFlowable(width="40%", thickness=0.5, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("[1] <b>A. Mercer</b>, R. Chen, and K. Zhang. <i>\"Distributed Cache Invalidation in Low-Latency Microservices.\"</i> ACM Symposium on Cloud Computing (SoCC), 2023.", pub_s),
        Spacer(1, 2),
        Paragraph("[2] <b>A. Mercer</b> and L. Davis. <i>\"Zero-Hallucination Retrieval Augmented Generation in Career Domain Systems.\"</i> IEEE Transactions on Knowledge Discovery, 2024.", pub_s),
        Spacer(1, 5),

        Paragraph("ACADEMIC APPOINTMENTS & TEACHING", sec_s),
        HRFlowable(width="40%", thickness=0.5, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Graduate Student Instructor</b> -- CS162 Operating Systems", bold_s), Paragraph("Fall 2022, Spring 2023", ParagraphStyle("R4", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.7, avail*0.3], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("Led weekly discussion sections for 80+ students; authored auto-graders for multi-threaded file systems.", pub_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 14. Timeline Resume (Vertical Timeline Column with Clear Date Separators)
# ─────────────────────────────────────────────────────────────────────────────
def render_timeline_resume():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=26, bottomMargin=26)
    avail = WIDTH - 60

    name_s = ParagraphStyle("T_N", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#0369a1"))
    contact_s = ParagraphStyle("T_C", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569"))
    sec_s = ParagraphStyle("T_S", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#0369a1"), spaceBefore=5, spaceAfter=2)
    time_badge = ParagraphStyle("T_Badge", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#0284c7"))
    body_s = ParagraphStyle("T_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bullet_s = ParagraphStyle("T_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=6)

    story = [
        Paragraph("ALEX MERCER", name_s),
        Paragraph("alex.mercer@vidyamarg.ai  •  +1 (555) 782-9301  •  San Francisco, CA", contact_s),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0369a1"), spaceBefore=3, spaceAfter=5),

        Paragraph("CAREER TIMELINE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#7dd3fc"), spaceBefore=1, spaceAfter=3),

        # 2023 - Present
        Table([
            [Paragraph("<b>[ 2023 – Present ]</b>", time_badge),
             Paragraph("<b>Apex Cloud Systems</b> -- Senior Software Engineer<br/>• Architected microservices fleet handling 5M+ daily requests.<br/>• Cut p99 latency by 42% through connection pooling.", body_s)]
        ], colWidths=[avail*0.25, avail*0.75], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 2)]),
        Spacer(1, 3),

        # 2020 - 2023
        Table([
            [Paragraph("<b>[ 2020 – 2023 ]</b>", time_badge),
             Paragraph("<b>Horizon Tech Labs</b> -- Software Engineer<br/>• Shipped full-stack SaaS features in TypeScript & Next.js for 250k+ active accounts.", body_s)]
        ], colWidths=[avail*0.25, avail*0.75], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 2)]),
        Spacer(1, 3),

        # 2016 - 2020
        Table([
            [Paragraph("<b>[ 2016 – 2020 ]</b>", time_badge),
             Paragraph("<b>UC Berkeley</b> -- B.S. in Computer Science & Engineering (GPA: 3.85 / 4.0)", body_s)]
        ], colWidths=[avail*0.25, avail*0.75], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 2)]),
        Spacer(1, 4),

        Paragraph("CORE SKILLS", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#7dd3fc"), spaceBefore=1, spaceAfter=3),
        Paragraph("Python, TypeScript, Go, FastAPI, Next.js, Docker, Kubernetes, AWS, PostgreSQL, Redis", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 15. Infographic Resume (Visual Metric Panels / Dual Graphic Sections / Creative)
# ─────────────────────────────────────────────────────────────────────────────
def render_infographic_resume():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=28, rightMargin=28, topMargin=24, bottomMargin=24)
    avail = WIDTH - 56

    name_s = ParagraphStyle("Info_N", fontName="Helvetica-Bold", fontSize=22, leading=24, textColor=colors.HexColor("#5b21b6"))
    contact_s = ParagraphStyle("Info_C", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b"))
    sec_s = ParagraphStyle("Info_S", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#5b21b6"), spaceBefore=5, spaceAfter=2)
    body_s = ParagraphStyle("Info_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#1e293b"))
    bullet_s = ParagraphStyle("Info_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=8)

    # Metric callout boxes
    m1 = Paragraph("<b>5M+</b><br/><font size='7' color='#475569'>Daily Requests</font>", ParagraphStyle("M1", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#5b21b6")))
    m2 = Paragraph("<b>42%</b><br/><font size='7' color='#475569'>Latency Drop</font>", ParagraphStyle("M2", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#5b21b6")))
    m3 = Paragraph("<b>99.99%</b><br/><font size='7' color='#475569'>Service Uptime</font>", ParagraphStyle("M3", fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#5b21b6")))

    metrics_table = Table([[m1, m2, m3]], colWidths=[avail/3, avail/3, avail/3], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f5f3ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#ddd6fe")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ddd6fe")),
        ('PADDING', (0,0), (-1,-1), 6),
    ])

    story = [
        Paragraph("ALEX MERCER", name_s),
        Paragraph("alex.mercer@vidyamarg.ai  •  +1 (555) 782-9301  •  San Francisco, CA", contact_s),
        Spacer(1, 4),
        metrics_table,
        Spacer(1, 5),

        Paragraph("CAREER ACHIEVEMENTS", sec_s),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#5b21b6"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", ParagraphStyle("B", parent=body_s, fontName="Helvetica-Bold")),
                Paragraph("2023 – Present", ParagraphStyle("R", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected event-driven microservices handling 5M+ daily requests with 99.99% SLA.", bullet_s),
        Paragraph("• Reduced p99 database latency by 42% via connection pool tuning and query optimization.", bullet_s),
        Spacer(1, 4),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", ParagraphStyle("B2", parent=body_s, fontName="Helvetica-Bold")),
                Paragraph("2020 – 2023", ParagraphStyle("R2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Shipped multi-tenant SaaS features in TypeScript & Next.js for 250k+ active accounts.", bullet_s),
        Spacer(1, 4),

        Paragraph("CORE SKILLS & CAPABILITIES", sec_s),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#5b21b6"), spaceBefore=1, spaceAfter=3),
        Paragraph("Python, TypeScript, Go, FastAPI, Next.js, Docker, Kubernetes, AWS, PostgreSQL, Redis", body_s),
        Spacer(1, 4),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#5b21b6"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. in Computer Science & Engineering</b>, UC Berkeley (GPA: 3.85 / 4.0)", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 15 Independent Mapping Configuration
# ─────────────────────────────────────────────────────────────────────────────
RENDER_15_MAP = {
    "classic-ats": render_classic_ats,
    "modern-corporate": render_modern_corporate,
    "executive-resume": render_executive_resume,
    "modern-two-column": render_modern_two_column,
    "color-sidebar": render_color_sidebar,
    "minimalist-elegant": render_minimalist_elegant,
    "bold-creative": render_bold_creative,
    "software-engineer": render_software_engineer,
    "ai-ml-engineer": render_aiml_engineer,
    "data-scientist": render_data_scientist,
    "developer-portfolio": render_developer_portfolio,
    "graduate-fresher": render_graduate_fresher,
    "academic-cv": render_academic_cv,
    "timeline-resume": render_timeline_resume,
    "infographic-resume": render_infographic_resume,
}

def convert_pdf_to_png(pdf_bytes, output_png_path):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)
    pix.save(output_png_path)
    doc.close()

print(f"Rendering all {len(RENDER_15_MAP)} genuinely distinct resume templates...")
for slug, func in RENDER_15_MAP.items():
    pdf_bytes = func()
    png_path = os.path.join(OUTPUT_DIR, f"{slug}.png")
    convert_pdf_to_png(pdf_bytes, png_path)
    print(f"Generated distinct preview: {png_path} ({os.path.getsize(png_path) // 1024} KB)")

print(f"\nAll {len(RENDER_15_MAP)} distinct template preview images generated successfully!")
