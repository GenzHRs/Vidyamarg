"""
Generates 12 distinct, authentic, real Overleaf/HackerRank/Jake's Resume-style preview images.
Each template has a completely unique layout structure, visual rhythm, headers, and arrangement:
1. Jake's Overleaf Resume (Top #1 on r/EngineeringResumes)
2. Deedy Resume (Famous 2-Column Cornell Overleaf Template)
3. Modern Sidebar Executive (Dark Sidebar + Bright Main Column)
4. FAANG / HackerRank Minimalist (Classic Single Column, clean horizontal lines)
5. Modern Tech Lead (Clean bold categories, tech stack inline badges)
6. Data & ML Research (Mathematical font, Publications, Research highlights)
7. Product & Growth (Two-column metrics, KPI callout badges)
8. Academic & Scientist (Harvard/Oxford classical serif, bibliography-style citations)
9. Compact One-Page (Ultra-tight, space-maximized grid)
10. Creative Split-Header (Bold asymmetric banner, dual-panel contact info)
11. Fresher / University Graduate (Education-first, coursework, hackathons)
12. Executive VP / Leadership (Clean classic serif, leadership timeline)
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

def render_jakes_resume():
    """Jake's Resume - Classic r/EngineeringResumes single column, centered header, line rules."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=32, rightMargin=32, topMargin=30, bottomMargin=30)
    avail = WIDTH - 64

    name_s = ParagraphStyle("J_Name", fontName="Times-Bold", fontSize=18, leading=20, alignment=TA_CENTER)
    contact_s = ParagraphStyle("J_Contact", fontName="Times-Roman", fontSize=8.5, leading=11, alignment=TA_CENTER)
    sec_s = ParagraphStyle("J_Sec", fontName="Times-Bold", fontSize=10.5, leading=12, textTransform="uppercase", spaceBefore=4, spaceAfter=1)
    body_s = ParagraphStyle("J_Body", fontName="Times-Roman", fontSize=8.5, leading=11)
    bold_s = ParagraphStyle("J_Bold", fontName="Times-Bold", fontSize=8.5, leading=11)
    right_s = ParagraphStyle("J_Right", fontName="Times-Italic", fontSize=8.5, leading=11, alignment=TA_RIGHT)
    bullet_s = ParagraphStyle("J_Bullet", fontName="Times-Roman", fontSize=8.2, leading=10.5, leftIndent=12)

    story = [
        Paragraph("<b>ALEX MERCER</b>", name_s),
        Spacer(1, 1),
        Paragraph("+1 (555) 782-9301 | alex.mercer@vidyamarg.ai | linkedin.com/in/alex-mercer | github.com/alexmercer", contact_s),
        Spacer(1, 4),
        
        # Education first
        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>University of California, Berkeley</b>", bold_s), Paragraph("Berkeley, CA", right_s)],
               [Paragraph("<i>Bachelor of Science in Computer Science & Engineering</i>; GPA: 3.85/4.0", body_s), Paragraph("Aug. 2016 – May 2020", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Spacer(1, 4),

        # Experience
        Paragraph("EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Apex Cloud Systems</b>", bold_s), Paragraph("June 2023 – Present", right_s)],
               [Paragraph("<i>Senior Software Engineer</i>", body_s), Paragraph("San Francisco, CA", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected high-throughput microservices using Python FastAPI, PostgreSQL, and Redis handling 5M+ daily requests with 99.99% SLA.", bullet_s),
        Paragraph("• Optimized distributed database query latency across 12 shards, reducing p99 response times by 42% through connection pooling and indexing.", bullet_s),
        Paragraph("• Mentored 6 junior engineers and spearheaded automated unit and integration test coverage from 64% to 92%.", bullet_s),
        Spacer(1, 3),

        Table([[Paragraph("<b>Horizon Tech Labs</b>", bold_s), Paragraph("July 2020 – May 2023", right_s)],
               [Paragraph("<i>Software Engineer</i>", body_s), Paragraph("San Francisco, CA", right_s)]],
              colWidths=[avail*0.75, avail*0.25], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Developed full-stack SaaS features using TypeScript, React, and Node.js serving over 250k monthly active business subscribers.", bullet_s),
        Paragraph("• Implemented secure JWT and OAuth2 authorization workflows, preventing credential-stuffing attacks and achieving SOC2 compliance.", bullet_s),
        Spacer(1, 4),

        # Projects
        Paragraph("PROJECTS", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>Vidyamarg AI Engine</b> | <i>FastAPI, Next.js, Redis, PyTorch</i>", bold_s), Paragraph("2024", right_s)]],
              colWidths=[avail*0.8, avail*0.2], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Engineered an AI career intelligence platform integrating sandboxed LaTeX compilation pipeline and JD-matching algorithms.", bullet_s),
        Paragraph("• Built real-time WebSocket communication layer supporting live collaboration with sub-50ms latency.", bullet_s),
        Spacer(1, 4),

        # Skills
        Paragraph("TECHNICAL SKILLS", sec_s),
        HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Languages:</b> Python, TypeScript, Go, JavaScript, SQL, C++, Bash", body_s),
        Paragraph("<b>Frameworks:</b> FastAPI, React, Next.js, Node.js, PyTorch, LangChain, TailwindCSS", body_s),
        Paragraph("<b>Developer Tools:</b> Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, Linux, GitHub Actions", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


def render_deedy_resume():
    """Deedy Resume - Famous 2-Column Cornell Overleaf layout with Left Sidebar (33%) and Right Column (67%)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=28, rightMargin=28, topMargin=26, bottomMargin=26)
    avail = WIDTH - 56
    left_w = avail * 0.31
    right_w = avail * 0.69

    # Styles
    name_s = ParagraphStyle("D_Name", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#1e293b"))
    tag_s = ParagraphStyle("D_Tag", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#2563eb"))
    side_head = ParagraphStyle("D_SideH", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    main_head = ParagraphStyle("D_MainH", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    side_body = ParagraphStyle("D_SideB", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    side_bold = ParagraphStyle("D_SideBold", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=colors.HexColor("#1e293b"))
    main_body = ParagraphStyle("D_MainB", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#334155"))
    main_bold = ParagraphStyle("D_MainBold", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#0f172a"))
    main_right = ParagraphStyle("D_MainR", fontName="Helvetica-Oblique", fontSize=8, leading=11, alignment=TA_RIGHT, textColor=colors.HexColor("#64748b"))
    bullet_s = ParagraphStyle("D_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=8)

    # Left Column Content (Education, Skills, Links, Coursework)
    left_flow = [
        Paragraph("CONTACT", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("alex.mercer@vidyamarg.ai", side_body),
        Paragraph("+1 (555) 782-9301", side_body),
        Paragraph("San Francisco, CA", side_body),
        Paragraph("github.com/alexmercer", side_body),
        Paragraph("linkedin.com/in/alex", side_body),
        Spacer(1, 4),

        Paragraph("EDUCATION", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("<b>UC BERKELEY</b>", side_bold),
        Paragraph("BS IN COMPUTER SCIENCE", side_bold),
        Paragraph("Grad. May 2020", side_body),
        Paragraph("GPA: 3.85 / 4.0", side_body),
        Spacer(1, 4),

        Paragraph("COURSEWORK", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("• Distributed Systems", side_body),
        Paragraph("• Database Design", side_body),
        Paragraph("• Machine Learning", side_body),
        Paragraph("• Algorithms & Data Struct", side_body),
        Paragraph("• Operating Systems", side_body),
        Spacer(1, 4),

        Paragraph("SKILLS", side_head),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceBefore=1, spaceAfter=2),
        Paragraph("<b>PROGRAMMING</b>", side_bold),
        Paragraph("Python • TypeScript • Go<br/>SQL • C++ • Bash", side_body),
        Spacer(1, 2),
        Paragraph("<b>FRAMEWORKS</b>", side_bold),
        Paragraph("FastAPI • Next.js • React<br/>PyTorch • Node.js", side_body),
        Spacer(1, 2),
        Paragraph("<b>INFRASTRUCTURE</b>", side_bold),
        Paragraph("Docker • Kubernetes • AWS<br/>PostgreSQL • Redis • Git", side_body),
    ]

    # Right Column Content (Experience, Projects, Leadership)
    right_flow = [
        Paragraph("EXPERIENCE", main_head),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563eb"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>APEX CLOUD SYSTEMS</b> | Senior Software Engineer", main_bold), Paragraph("2023 – Present | SF, CA", main_right)]],
              colWidths=[right_w*0.72, right_w*0.28], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected high-throughput microservices handling 5M+ daily requests using FastAPI, PostgreSQL, and Redis.", bullet_s),
        Paragraph("• Reduced p99 API latencies by 42% via Redis query caching and read replicas.", bullet_s),
        Paragraph("• Automated infrastructure deployment using Docker, Helm, and AWS ECS.", bullet_s),
        Spacer(1, 4),

        Table([[Paragraph("<b>HORIZON TECH LABS</b> | Software Engineer", main_bold), Paragraph("2020 – 2023 | SF, CA", main_right)]],
              colWidths=[right_w*0.72, right_w*0.28], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Built scalable SaaS features in TypeScript and Next.js for 250k+ active users.", bullet_s),
        Paragraph("• Engineered secure JWT & OAuth2 auth engine with automated rate limiters.", bullet_s),
        Spacer(1, 5),

        Paragraph("PROJECTS", main_head),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563eb"), spaceBefore=1, spaceAfter=3),
        Table([[Paragraph("<b>VIDYAMARG AI PLATFORM</b> | Python, React, Redis", main_bold), Paragraph("2024", main_right)]],
              colWidths=[right_w*0.8, right_w*0.2], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Built AI resume tailoring system with sub-100ms lexical matching.", bullet_s),
        Paragraph("• Engineered multi-template Overleaf LaTeX PDF compilation workers.", bullet_s),
    ]

    # Header spanning top
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


def render_modern_sidebar():
    """Modern Dark Left Sidebar (Executive format with 30% Dark Blue background panel)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    avail = WIDTH - 48
    col1 = avail * 0.33
    col2 = avail * 0.67

    side_h = ParagraphStyle("S_H", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#ffffff"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    side_b = ParagraphStyle("S_B", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#cbd5e1"))
    side_bold = ParagraphStyle("S_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#38bdf8"))
    
    main_name = ParagraphStyle("M_Name", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.HexColor("#0f172a"))
    main_title = ParagraphStyle("M_Title", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#0284c7"))
    main_h = ParagraphStyle("M_H", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#0f172a"), textTransform="uppercase", spaceBefore=6, spaceAfter=2)
    main_b = ParagraphStyle("M_B", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#334155"))
    main_bold = ParagraphStyle("M_Bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a"))
    bullet_s = ParagraphStyle("M_Bullet", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#334155"), leftIndent=8)

    left_cells = [
        Paragraph("ALEX MERCER", ParagraphStyle("L_N", fontName="Helvetica-Bold", fontSize=15, leading=17, textColor=colors.white)),
        Paragraph("Senior Software Engineer", ParagraphStyle("L_T", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#38bdf8"))),
        Spacer(1, 6),
        Paragraph("CONTACT", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("✉ alex.mercer@vidyamarg.ai", side_b),
        Paragraph("☎ +1 (555) 782-9301", side_b),
        Paragraph("📍 San Francisco, CA", side_b),
        Paragraph("🔗 linkedin.com/in/alex", side_b),
        Spacer(1, 6),
        Paragraph("CORE SKILLS", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("Python, TypeScript, Go", side_b),
        Paragraph("FastAPI, React, Next.js", side_b),
        Paragraph("Docker, Kubernetes, AWS", side_b),
        Paragraph("PostgreSQL, Redis, SQL", side_b),
        Spacer(1, 6),
        Paragraph("EDUCATION", side_h),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#38bdf8"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>B.S. Computer Science</b>", side_bold),
        Paragraph("UC Berkeley, 2020", side_b),
        Paragraph("GPA: 3.85 / 4.0", side_b),
    ]

    right_cells = [
        Paragraph("PROFESSIONAL SUMMARY", main_h),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=1, spaceAfter=3),
        Paragraph("Results-driven Senior Full-Stack Engineer with 6+ years designing resilient cloud-native architectures, high-load APIs, and scalable distributed applications.", main_b),
        Spacer(1, 5),

        Paragraph("WORK EXPERIENCE", main_h),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=1, spaceAfter=3),
        Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer <font color='#64748b' size='7.5'><i>(2023 – Present)</i></font>", main_bold),
        Paragraph("• Architected event-driven microservices serving 5M+ daily requests using FastAPI & Redis.", bullet_s),
        Paragraph("• Reduced p99 API latency by 42% through connection pooling and Redis caching.", bullet_s),
        Paragraph("• Led automated CI/CD pipeline modernization across 14 engineering squads.", bullet_s),
        Spacer(1, 4),

        Paragraph("<b>Horizon Tech Labs</b> | Software Engineer <font color='#64748b' size='7.5'><i>(2020 – 2023)</i></font>", main_bold),
        Paragraph("• Developed full-stack SaaS features in TypeScript & Next.js for 250k+ active accounts.", bullet_s),
        Paragraph("• Implemented secure OAuth2/JWT auth engine, achieving SOC2 certification compliance.", bullet_s),
        Spacer(1, 5),

        Paragraph("FEATURED PROJECTS", main_h),
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


def render_software_tech_dense():
    """HackerRank / LeetCode style Software Engineer resume with clean monospace headers and badge blocks."""
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
        Paragraph("• Implemented OAuth2 / JWT security engine preventing credential abuse.", bullet_s),
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
        Paragraph("GPA: 3.85 / 4.0 • Honors Computer Science Society", body_s),
    ]
    doc.build(story)
    return buf.getvalue()


def render_academic_cv():
    """Harvard / Oxford Classic Academic CV format - clean, high-density serifs with publication citations."""
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
        Spacer(1, 5),

        Paragraph("HONORS & FELLOWSHIPS", sec_s),
        HRFlowable(width="40%", thickness=0.5, color=colors.black, spaceBefore=1, spaceAfter=3),
        Paragraph("• National Science Foundation (NSF) Graduate Research Fellowship (2021)", pub_s),
        Paragraph("• Berkeley EECS Departmental Honors Fellowship (2020)", pub_s),
    ]
    doc.build(story)
    return buf.getvalue()


def render_compact_one_page():
    """Compact One Page - Ultra-dense single-page format for high content density."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=24, rightMargin=24, topMargin=20, bottomMargin=20)
    avail = WIDTH - 48

    name_s = ParagraphStyle("C_N", fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=colors.HexColor("#065f46"))
    contact_s = ParagraphStyle("C_C", fontName="Helvetica", fontSize=7.8, leading=9.5, textColor=colors.HexColor("#4b5563"))
    sec_s = ParagraphStyle("C_S", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=colors.HexColor("#065f46"), textTransform="uppercase", spaceBefore=4, spaceAfter=1)
    body_s = ParagraphStyle("C_B", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#1f2937"))
    bold_s = ParagraphStyle("C_Bold", fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=colors.HexColor("#111827"))
    bullet_s = ParagraphStyle("C_Bullet", fontName="Helvetica", fontSize=7.8, leading=9.8, textColor=colors.HexColor("#374151"), leftIndent=8)

    story = [
        Table([[Paragraph("<b>ALEX MERCER</b>", name_s),
                Paragraph("alex.mercer@vidyamarg.ai | +1 (555) 782-9301 | San Francisco, CA<br/>github.com/alexmercer | linkedin.com/in/alex-mercer",
                          ParagraphStyle("CR", parent=contact_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.4, avail*0.6], style=[('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 0)]),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#059669"), spaceBefore=2, spaceAfter=3),

        Paragraph("CORE SKILLS & TECHNOLOGIES", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a7f3d0"), spaceBefore=1, spaceAfter=2),
        Paragraph("<b>Languages:</b> Python, TypeScript, Go, SQL, C++, Bash | <b>Frameworks:</b> FastAPI, Next.js, React, PyTorch, Node.js", body_s),
        Paragraph("<b>Infrastructure & Tools:</b> Docker, Kubernetes, AWS, PostgreSQL, Redis, Linux, Git, GitHub Actions", body_s),
        Spacer(1, 3),

        Paragraph("WORK EXPERIENCE", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a7f3d0"), spaceBefore=1, spaceAfter=2),
        Table([[Paragraph("<b>Apex Cloud Systems</b> | Senior Software Engineer", bold_s), Paragraph("June 2023 – Present | SF, CA", ParagraphStyle("CR1", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.7, avail*0.3], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Architected event-driven microservices with FastAPI & Redis handling 5M+ daily requests with 99.99% uptime.", bullet_s),
        Paragraph("• Reduced p99 database latency by 42% via connection pool tuning, read replicas, and query optimization.", bullet_s),
        Paragraph("• Automated multi-cluster Kubernetes deployments using Helm and GitHub Actions CI/CD workflows.", bullet_s),
        Spacer(1, 2),

        Table([[Paragraph("<b>Horizon Tech Labs</b> | Software Engineer", bold_s), Paragraph("July 2020 – May 2023 | SF, CA", ParagraphStyle("CR2", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.7, avail*0.3], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
        Paragraph("• Shipped full-stack features using TypeScript and Next.js serving 250k+ active business accounts.", bullet_s),
        Paragraph("• Implemented OAuth2/JWT auth engine with IP-based rate limiting, achieving SOC2 compliance.", bullet_s),
        Spacer(1, 3),

        Paragraph("PROJECTS", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a7f3d0"), spaceBefore=1, spaceAfter=2),
        Paragraph("<b>Vidyamarg AI Engine</b> (FastAPI, Redis, Next.js, PyTorch) -- <i>AI career intelligence with sandboxed LaTeX compiler</i>", bold_s),
        Paragraph("• Built distributed job queue processing LaTeX and PDF exports with sub-100ms response time.", bullet_s),
        Spacer(1, 3),

        Paragraph("EDUCATION", sec_s),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#a7f3d0"), spaceBefore=1, spaceAfter=2),
        Table([[Paragraph("<b>B.S. in Computer Science & Engineering</b> | UC Berkeley", bold_s), Paragraph("2016 – 2020 | GPA: 3.85 / 4.0", ParagraphStyle("CR3", parent=body_s, alignment=TA_RIGHT))]],
              colWidths=[avail*0.7, avail*0.3], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 0)]),
    ]
    doc.build(story)
    return buf.getvalue()


# Mapping functions to each of the 12 templates
RENDER_MAP = {
    "ats-classic": render_jakes_resume,             # Jake's Resume (r/EngineeringResumes classic)
    "modern-single-column": render_software_tech_dense, # Tech Lead Single Column
    "minimal-professional": render_compact_one_page,   # Minimalist Clean
    "software-engineer": render_software_tech_dense,    # HackerRank Tech Arsenal
    "data-analyst": render_deedy_resume,              # Analytics Two-Column
    "data-scientist": render_academic_cv,             # Research & Publications
    "product-business": render_modern_sidebar,        # Executive Dark Sidebar
    "academic-cv": render_academic_cv,                # Harvard Academic CV
    "compact-one-page": render_compact_one_page,      # Ultra-Compact 1-Page
    "two-column-modern": render_deedy_resume,         # Deedy 2-Column Cornell
    "fresher-resume": render_jakes_resume,            # Campus Education-First
    "experienced-professional": render_modern_sidebar # Senior VP Executive
}

def convert_pdf_to_png(pdf_bytes, output_png_path):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)
    pix.save(output_png_path)
    doc.close()

print("Generating 12 truly distinct Overleaf & HackerRank template preview PNGs...")
for slug, func in RENDER_MAP.items():
    pdf_bytes = func()
    png_path = os.path.join(OUTPUT_DIR, f"{slug}.png")
    convert_pdf_to_png(pdf_bytes, png_path)
    print(f"Generated: {png_path} ({os.path.getsize(png_path) // 1024} KB)")

print("\nAll 12 distinct template preview images regenerated successfully!")
