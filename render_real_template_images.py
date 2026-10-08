"""
Render real resume sample PDFs using ReportLab with custom styles for all 12 templates,
and convert page 1 of each into high-resolution PNG images using PyMuPDF (fitz).
Output: frontend/public/templates/previews/{slug}.png
"""
import os
import io
import pymupdf as fitz
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "frontend", "public", "templates", "previews")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SAMPLE_RESUME = {
    "name": "Alex Mercer",
    "title": "Senior Full-Stack & AI Engineer",
    "email": "alex.mercer@vidyamarg.ai",
    "phone": "+1 (555) 782-9301",
    "location": "San Francisco, CA",
    "linkedin": "linkedin.com/in/alex-mercer",
    "github": "github.com/alexmercer",
    "summary": "Innovative Full-Stack & AI Software Engineer with 6+ years of experience architecting distributed cloud systems, real-time microservices, and LLM applications. Proven record delivering high-throughput platforms serving 5M+ daily requests with 99.99% uptime.",
    "experience": [
        {
            "role": "Senior Software Engineer",
            "company": "Apex Cloud Systems",
            "dates": "2023 - Present",
            "bullets": [
                "Architected event-driven microservices using Python FastAPI, PostgreSQL, and Redis handling 5M+ daily API transactions.",
                "Engineered agentic AI workflows and semantic search pipelines, boosting query accuracy by 38% while reducing p99 latency by 45%.",
                "Led infrastructure migration to Docker & Kubernetes, standardizing CI/CD pipelines across 14 distributed engineering teams."
            ]
        },
        {
            "role": "Software Engineer",
            "company": "Horizon Tech Labs",
            "dates": "2020 - 2023",
            "bullets": [
                "Developed scalable full-stack web applications using TypeScript, Next.js, and Node.js with 99.95% availability.",
                "Implemented secure OAuth2, JWT authentication, and automated rate-limiting guards against credential stuffing.",
                "Optimized complex SQL queries and indexed database tables, reducing median query execution time from 420ms to 65ms."
            ]
        }
    ],
    "education": [
        {
            "degree": "B.S. in Computer Science & Engineering",
            "school": "University of California, Berkeley",
            "dates": "2016 - 2020",
            "gpa": "GPA: 3.85 / 4.0"
        }
    ],
    "skills": {
        "Languages": "Python, TypeScript, Go, JavaScript, SQL, C++",
        "Frameworks": "FastAPI, Next.js, React, PyTorch, LangChain, TailwindCSS",
        "Cloud & DevOps": "Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, Linux"
    },
    "projects": [
        {
            "name": "Vidyamarg AI Engine",
            "tech": "FastAPI, Next.js, Redis, PyTorch",
            "dates": "2024",
            "bullets": [
                "Engineered career intelligence engine with zero-hallucination tailoring and Overleaf-grade LaTeX compilation pipeline.",
                "Scaled distributed background job workers processing concurrent PDF compilations with 99.9% reliability."
            ]
        }
    ]
}

TEMPLATES_CONFIG = [
    {
        "slug": "ats-classic",
        "primary": colors.HexColor("#0f172a"), # Black/Dark Slate
        "accent": colors.HexColor("#1e3a8a"),  # Navy
        "font_name": "Times-Roman",
        "font_bold": "Times-Bold",
        "font_italic": "Times-Italic",
        "center_header": True,
        "divider_style": "full",
        "margins": 36
    },
    {
        "slug": "modern-single-column",
        "primary": colors.HexColor("#1e40af"), # Royal Blue
        "accent": colors.HexColor("#3b82f6"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "colored",
        "margins": 34
    },
    {
        "slug": "minimal-professional",
        "primary": colors.HexColor("#334155"), # Muted Slate
        "accent": colors.HexColor("#64748b"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "subtle",
        "margins": 38
    },
    {
        "slug": "software-engineer",
        "primary": colors.HexColor("#0284c7"), # Sky/Cyan
        "accent": colors.HexColor("#0369a1"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": True,
        "divider_style": "full",
        "margins": 32
    },
    {
        "slug": "data-analyst",
        "primary": colors.HexColor("#4338ca"), # Indigo
        "accent": colors.HexColor("#6366f1"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "colored",
        "margins": 34
    },
    {
        "slug": "data-scientist",
        "primary": colors.HexColor("#6d28d9"), # Purple
        "accent": colors.HexColor("#8b5cf6"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "colored",
        "margins": 34
    },
    {
        "slug": "product-business",
        "primary": colors.HexColor("#92400e"), # Amber/Bronze
        "accent": colors.HexColor("#b45309"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": True,
        "divider_style": "full",
        "margins": 36
    },
    {
        "slug": "academic-cv",
        "primary": colors.HexColor("#111827"), # Pure Dark
        "accent": colors.HexColor("#374151"),
        "font_name": "Times-Roman",
        "font_bold": "Times-Bold",
        "font_italic": "Times-Italic",
        "center_header": True,
        "divider_style": "classic",
        "margins": 38
    },
    {
        "slug": "compact-one-page",
        "primary": colors.HexColor("#065f46"), # Emerald
        "accent": colors.HexColor("#059669"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "subtle",
        "margins": 28
    },
    {
        "slug": "two-column-modern",
        "primary": colors.HexColor("#0f766e"), # Teal
        "accent": colors.HexColor("#14b8a6"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": False,
        "divider_style": "colored",
        "margins": 32
    },
    {
        "slug": "fresher-resume",
        "primary": colors.HexColor("#2563eb"), # Fresh Blue
        "accent": colors.HexColor("#3b82f6"),
        "font_name": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "center_header": True,
        "divider_style": "colored",
        "margins": 35
    },
    {
        "slug": "experienced-professional",
        "primary": colors.HexColor("#1e293b"), # Slate
        "accent": colors.HexColor("#475569"),
        "font_name": "Times-Roman",
        "font_bold": "Times-Bold",
        "font_italic": "Times-Italic",
        "center_header": False,
        "divider_style": "full",
        "margins": 36
    }
]

def render_template_pdf(config):
    buffer = io.BytesIO()
    margin = config["margins"]
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()
    primary = config["primary"]
    accent = config["accent"]
    font_base = config["font_name"]
    font_bold = config["font_bold"]
    font_italic = config["font_italic"]

    # Custom styles
    name_align = TA_CENTER if config["center_header"] else TA_LEFT
    name_style = ParagraphStyle(
        "T_Name",
        fontName=font_bold,
        fontSize=18,
        leading=21,
        textColor=primary,
        alignment=name_align
    )
    title_style = ParagraphStyle(
        "T_Title",
        fontName=font_bold,
        fontSize=10,
        leading=13,
        textColor=accent,
        alignment=name_align
    )
    contact_style = ParagraphStyle(
        "T_Contact",
        fontName=font_base,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4b5563"),
        alignment=name_align
    )
    section_style = ParagraphStyle(
        "T_Section",
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=primary,
        spaceBefore=7,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        "T_Body",
        fontName=font_base,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1f2937")
    )
    bold_style = ParagraphStyle(
        "T_Bold",
        fontName=font_bold,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#111827")
    )
    italic_style = ParagraphStyle(
        "T_Italic",
        fontName=font_italic,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#4b5563")
    )
    bullet_style = ParagraphStyle(
        "T_Bullet",
        fontName=font_base,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#374151"),
        leftIndent=10
    )

    story = []

    # 1. Header
    story.append(Paragraph(SAMPLE_RESUME["name"].upper(), name_style))
    story.append(Spacer(1, 1))
    story.append(Paragraph(SAMPLE_RESUME["title"], title_style))
    story.append(Spacer(1, 2))
    contacts = f"{SAMPLE_RESUME['email']}  •  {SAMPLE_RESUME['phone']}  •  {SAMPLE_RESUME['location']}  •  {SAMPLE_RESUME['linkedin']}"
    story.append(Paragraph(contacts, contact_style))
    story.append(Spacer(1, 4))

    # Divider below header
    hr_color = primary if config["divider_style"] == "colored" else colors.HexColor("#cbd5e1")
    story.append(HRFlowable(width="100%", thickness=1.5, color=hr_color, spaceBefore=2, spaceAfter=4))

    # 2. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=hr_color, spaceBefore=1, spaceAfter=3))
    story.append(Paragraph(SAMPLE_RESUME["summary"], body_style))
    story.append(Spacer(1, 4))

    # 3. Technical Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=hr_color, spaceBefore=1, spaceAfter=3))
    for cat, items in SAMPLE_RESUME["skills"].items():
        skill_text = f"<b>{cat}:</b> {items}"
        story.append(Paragraph(skill_text, body_style))
    story.append(Spacer(1, 4))

    # 4. Work Experience
    story.append(Paragraph("WORK EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=hr_color, spaceBefore=1, spaceAfter=3))
    avail_width = letter[0] - 2 * margin
    for exp in SAMPLE_RESUME["experience"]:
        left_cell = Paragraph(f"<b>{exp['role']}</b> | <i>{exp['company']}</i>", body_style)
        right_cell = Paragraph(f"<i>{exp['dates']}</i>", ParagraphStyle("Right", parent=body_style, alignment=TA_RIGHT))
        row_table = Table([[left_cell, right_cell]], colWidths=[avail_width * 0.72, avail_width * 0.28])
        row_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(row_table)
        for bullet in exp["bullets"]:
            story.append(Paragraph(f"• {bullet}", bullet_style))
        story.append(Spacer(1, 3))

    # 5. Key Projects
    story.append(Paragraph("KEY PROJECTS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=hr_color, spaceBefore=1, spaceAfter=3))
    for proj in SAMPLE_RESUME["projects"]:
        left_p = Paragraph(f"<b>{proj['name']}</b> ({proj['tech']})", body_style)
        right_p = Paragraph(f"<i>{proj['dates']}</i>", ParagraphStyle("RightP", parent=body_style, alignment=TA_RIGHT))
        proj_table = Table([[left_p, right_p]], colWidths=[avail_width * 0.75, avail_width * 0.25])
        proj_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(proj_table)
        for b in proj["bullets"]:
            story.append(Paragraph(f"• {b}", bullet_style))
        story.append(Spacer(1, 3))

    # 6. Education
    story.append(Paragraph("EDUCATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.75, color=hr_color, spaceBefore=1, spaceAfter=3))
    for edu in SAMPLE_RESUME["education"]:
        left_e = Paragraph(f"<b>{edu['degree']}</b> | {edu['school']}", body_style)
        right_e = Paragraph(f"<i>{edu['dates']}</i>", ParagraphStyle("RightE", parent=body_style, alignment=TA_RIGHT))
        edu_table = Table([[left_e, right_e]], colWidths=[avail_width * 0.75, avail_width * 0.25])
        edu_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(edu_table)
        story.append(Paragraph(f"• {edu['gpa']}", bullet_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def convert_pdf_to_png(pdf_bytes, output_png_path):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    # 2x scale for sharp preview
    pix = page.get_pixmap(dpi=150)
    pix.save(output_png_path)
    doc.close()

print(f"Generating realistic preview images for {len(TEMPLATES_CONFIG)} templates...")
for cfg in TEMPLATES_CONFIG:
    pdf_data = render_template_pdf(cfg)
    png_path = os.path.join(OUTPUT_DIR, f"{cfg['slug']}.png")
    convert_pdf_to_png(pdf_data, png_path)
    print(f"Rendered: {png_path} ({os.path.getsize(png_path) // 1024} KB)")

print("\nAll 12 real resume preview images generated successfully!")
