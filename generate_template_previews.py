"""
Generates beautiful, professional SVG resume preview cards for all 12 templates.
Saves them into frontend/public/templates/previews/{slug}.svg
"""
import os
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "frontend", "public", "templates", "previews")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATES = [
    {
        "slug": "ats-classic",
        "name": "ATS Classic",
        "category": "Classic",
        "theme": "#1e3a8a", # Navy
        "font": "Georgia, serif",
        "layout": "standard",
        "score": "99% ATS"
    },
    {
        "slug": "modern-single-column",
        "name": "Modern Single Column",
        "category": "Modern",
        "theme": "#0f766e", # Teal
        "font": "Inter, sans-serif",
        "layout": "modern_lines",
        "score": "97% ATS"
    },
    {
        "slug": "minimal-professional",
        "name": "Minimal Professional",
        "category": "Minimal",
        "theme": "#334155", # Slate
        "font": "system-ui, sans-serif",
        "layout": "minimalist",
        "score": "98% ATS"
    },
    {
        "slug": "software-engineer",
        "name": "Software Engineer",
        "category": "Technical",
        "theme": "#2563eb", # Blue
        "font": "Consolas, monospace",
        "layout": "tech_dense",
        "score": "96% ATS"
    },
    {
        "slug": "data-analyst",
        "name": "Data Analyst",
        "category": "Technical",
        "theme": "#4f46e5", # Indigo
        "font": "system-ui, sans-serif",
        "layout": "analytics",
        "score": "95% ATS"
    },
    {
        "slug": "data-scientist",
        "name": "Data Scientist",
        "category": "Technical",
        "theme": "#7c3aed", # Violet
        "font": "system-ui, sans-serif",
        "layout": "scientific",
        "score": "94% ATS"
    },
    {
        "slug": "product-business",
        "name": "Product / Business",
        "category": "Modern",
        "theme": "#b45309", # Amber/Bronze
        "font": "system-ui, sans-serif",
        "layout": "business",
        "score": "96% ATS"
    },
    {
        "slug": "academic-cv",
        "name": "Academic CV",
        "category": "Academic",
        "theme": "#1f2937", # Dark Charcoal
        "font": "Times New Roman, serif",
        "layout": "academic",
        "score": "93% ATS"
    },
    {
        "slug": "compact-one-page",
        "name": "Compact One Page",
        "category": "Minimal",
        "theme": "#047857", # Emerald
        "font": "system-ui, sans-serif",
        "layout": "compact",
        "score": "98% ATS"
    },
    {
        "slug": "two-column-modern",
        "name": "Two Column Modern",
        "category": "Modern",
        "theme": "#0284c7", # Sky/Ocean
        "font": "system-ui, sans-serif",
        "layout": "two_col",
        "score": "93% ATS"
    },
    {
        "slug": "fresher-resume",
        "name": "Fresher Resume",
        "category": "Classic",
        "theme": "#0d9488", # Teal
        "font": "system-ui, sans-serif",
        "layout": "fresher",
        "score": "98% ATS"
    },
    {
        "slug": "experienced-professional",
        "name": "Experienced Professional",
        "category": "Classic",
        "theme": "#1e293b", # Deep Slate
        "font": "Georgia, serif",
        "layout": "executive",
        "score": "97% ATS"
    }
]

def generate_svg(tmpl):
    slug = tmpl["slug"]
    name = tmpl["name"]
    category = tmpl["category"]
    theme = tmpl["theme"]
    score = tmpl["score"]
    layout = tmpl["layout"]

    # Generate document preview lines according to layout
    if layout == "two_col":
        content_shapes = f"""
        <!-- Left Sidebar (35%) -->
        <rect x="25" y="90" width="85" height="270" rx="4" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
        <rect x="35" y="105" width="45" height="6" rx="2" fill="{theme}" />
        <rect x="35" y="120" width="65" height="3" rx="1.5" fill="#94a3b8" />
        <rect x="35" y="128" width="55" height="3" rx="1.5" fill="#94a3b8" />
        <rect x="35" y="136" width="60" height="3" rx="1.5" fill="#94a3b8" />
        
        <rect x="35" y="155" width="50" height="6" rx="2" fill="{theme}" />
        <rect x="35" y="170" width="65" height="3" rx="1.5" fill="#94a3b8" />
        <rect x="35" y="178" width="58" height="3" rx="1.5" fill="#94a3b8" />
        
        <rect x="35" y="200" width="45" height="6" rx="2" fill="{theme}" />
        <rect x="35" y="215" width="60" height="3" rx="1.5" fill="#94a3b8" />
        <rect x="35" y="223" width="50" height="3" rx="1.5" fill="#94a3b8" />

        <!-- Right Main (65%) -->
        <rect x="120" y="90" width="135" height="5" rx="2" fill="{theme}" />
        <line x1="120" y1="100" x2="255" y2="100" stroke="{theme}" stroke-width="1" stroke-opacity="0.3"/>
        <rect x="120" y="110" width="90" height="4" rx="2" fill="#334155" />
        <rect x="120" y="118" width="130" height="3" rx="1.5" fill="#64748b" />
        <rect x="120" y="125" width="125" height="3" rx="1.5" fill="#64748b" />
        <rect x="120" y="132" width="115" height="3" rx="1.5" fill="#64748b" />

        <rect x="120" y="150" width="95" height="4" rx="2" fill="#334155" />
        <rect x="120" y="158" width="130" height="3" rx="1.5" fill="#64748b" />
        <rect x="120" y="165" width="120" height="3" rx="1.5" fill="#64748b" />

        <rect x="120" y="185" width="80" height="5" rx="2" fill="{theme}" />
        <line x1="120" y1="195" x2="255" y2="195" stroke="{theme}" stroke-width="1" stroke-opacity="0.3"/>
        <rect x="120" y="205" width="130" height="3" rx="1.5" fill="#64748b" />
        <rect x="120" y="212" width="120" height="3" rx="1.5" fill="#64748b" />
        <rect x="120" y="219" width="110" height="3" rx="1.5" fill="#64748b" />
        """
    else:
        # Single column layout variations
        align_x = 30
        content_shapes = f"""
        <!-- Header -->
        <rect x="{align_x}" y="35" width="130" height="10" rx="3" fill="{theme}" />
        <rect x="{align_x}" y="50" width="190" height="4" rx="2" fill="#64748b" />
        <rect x="{align_x}" y="58" width="160" height="4" rx="2" fill="#94a3b8" />
        <line x1="{align_x}" y1="68" x2="250" y2="68" stroke="{theme}" stroke-width="1.5" stroke-opacity="0.4"/>

        <!-- Section 1: Experience -->
        <rect x="{align_x}" y="80" width="70" height="6" rx="2" fill="{theme}" />
        <line x1="{align_x}" y1="90" x2="250" y2="90" stroke="#cbd5e1" stroke-width="1"/>
        <rect x="{align_x}" y="98" width="90" height="4" rx="2" fill="#334155" />
        <rect x="210" y="98" width="40" height="4" rx="2" fill="#94a3b8" />
        <circle cx="{align_x + 5}" cy="108" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="106" width="205" height="3" rx="1.5" fill="#64748b" />
        <circle cx="{align_x + 5}" cy="116" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="114" width="195" height="3" rx="1.5" fill="#64748b" />
        <circle cx="{align_x + 5}" cy="124" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="122" width="180" height="3" rx="1.5" fill="#64748b" />

        <rect x="{align_x}" y="136" width="85" height="4" rx="2" fill="#334155" />
        <rect x="210" y="136" width="40" height="4" rx="2" fill="#94a3b8" />
        <circle cx="{align_x + 5}" cy="146" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="144" width="200" height="3" rx="1.5" fill="#64748b" />
        <circle cx="{align_x + 5}" cy="154" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="152" width="185" height="3" rx="1.5" fill="#64748b" />

        <!-- Section 2: Education -->
        <rect x="{align_x}" y="170" width="60" height="6" rx="2" fill="{theme}" />
        <line x1="{align_x}" y1="180" x2="250" y2="180" stroke="#cbd5e1" stroke-width="1"/>
        <rect x="{align_x}" y="188" width="110" height="4" rx="2" fill="#334155" />
        <rect x="215" y="188" width="35" height="4" rx="2" fill="#94a3b8" />
        <circle cx="{align_x + 5}" cy="198" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="196" width="190" height="3" rx="1.5" fill="#64748b" />

        <!-- Section 3: Skills -->
        <rect x="{align_x}" y="214" width="50" height="6" rx="2" fill="{theme}" />
        <line x1="{align_x}" y1="224" x2="250" y2="224" stroke="#cbd5e1" stroke-width="1"/>
        <rect x="{align_x}" y="232" width="220" height="3" rx="1.5" fill="#64748b" />
        <rect x="{align_x}" y="240" width="205" height="3" rx="1.5" fill="#64748b" />
        <rect x="{align_x}" y="248" width="190" height="3" rx="1.5" fill="#64748b" />

        <!-- Section 4: Projects -->
        <rect x="{align_x}" y="264" width="55" height="6" rx="2" fill="{theme}" />
        <line x1="{align_x}" y1="274" x2="250" y2="274" stroke="#cbd5e1" stroke-width="1"/>
        <rect x="{align_x}" y="282" width="95" height="4" rx="2" fill="#334155" />
        <circle cx="{align_x + 5}" cy="292" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="290" width="200" height="3" rx="1.5" fill="#64748b" />
        <circle cx="{align_x + 5}" cy="300" r="1.5" fill="{theme}"/>
        <rect x="{align_x + 12}" y="298" width="180" height="3" rx="1.5" fill="#64748b" />
        """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 380" width="280" height="380">
  <defs>
    <filter id="shadow" x="-5%" y="-3%" width="110%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.08"/>
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="280" height="380" fill="#f1f5f9"/>

  <!-- Resume Page (Sheet) -->
  <rect x="15" y="15" width="250" height="350" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" filter="url(#shadow)"/>

  {content_shapes}

  <!-- Bottom Accent / Brand Badge -->
  <rect x="15" y="342" width="250" height="23" rx="0" fill="{theme}" fill-opacity="0.05"/>
  <text x="25" y="357" font-family="Inter, system-ui, sans-serif" font-size="8.5" font-weight="700" fill="{theme}">{name}</text>
  <text x="255" y="357" text-anchor="end" font-family="Inter, system-ui, sans-serif" font-size="8" font-weight="700" fill="#10b981">{score}</text>
</svg>"""
    return svg

for tmpl in TEMPLATES:
    svg_content = generate_svg(tmpl)
    filepath = os.path.join(OUTPUT_DIR, f"{tmpl['slug']}.svg")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated: {filepath}")

print(f"\nAll {len(TEMPLATES)} SVG template previews generated successfully!")
