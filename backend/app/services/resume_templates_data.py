"""
15 Truly Distinct Overleaf-Inspired Resume Templates:
1. Classic ATS Resume (Classic) - Single column, monochrome, simple headings, traditional professional layout.
2. Modern Corporate (Classic) - Strong typography, colored section headings, balanced spacing, clean corporate style.
3. Executive Resume (Classic) - Large name header, elegant typography, leadership summary, achievement-focused sections.
4. Modern Two-Column (Creative) - Narrow left sidebar for skills & contact details, wide right column for experience.
5. Color Sidebar (Creative) - Full-height colored sidebar, profile details, skill indicators, main content on the right.
6. Minimalist Elegant (Creative) - Lots of white space, thin dividers, subtle typography, premium minimalist appearance.
7. Bold Creative (Creative) - Large typography, geometric accents, asymmetrical sections, distinctive visual hierarchy.
8. Software Engineer (Technical) - Technical skills, work experience, projects, GitHub and technology-focused sections.
9. AI/ML Engineer (Technical) - Machine learning skills, models, frameworks, research, projects, and measurable results.
10. Data Scientist (Technical) - Data tools, analytics projects, technical achievements, and research highlights.
11. Developer Portfolio (Technical) - Project-focused design, prominent GitHub & portfolio links, technology tags.
12. Graduate / Fresher (Academic) - Education & projects appear first, with compact skills and no placeholder experience.
13. Academic CV (Academic) - Research interests, publications, education, teaching, projects, and academic achievements.
14. Timeline Resume (Specialized) - Clear vertical timeline for education & employment, dates separated from descriptions.
15. Infographic Resume (Specialized) - Distinctive visual sections, graphical skill summaries, structured layout (Non-ATS creative).
"""
from typing import List, Dict, Any

RESUME_TEMPLATES: List[Dict[str, Any]] = [
    # ── 1. Classic ATS Resume ──────────────────────────────────────────────────
    {
        "id": 1,
        "name": "Classic ATS Resume",
        "slug": "classic-ats",
        "description": "Ultra-clean single column layout, black and white, simple headings, traditional professional ATS standard.",
        "category": "Classic",
        "ats_score": 99,
        "page_format": "A4 / 1-Page Optimized",
        "font_info": "Times-Roman / Computer Modern",
        "best_use_case": "Conservative industries, enterprise recruiting, ATS scanners, government & banking.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/classic-ats.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.65in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

\hypersetup{colorlinks=false, pdfborder={0 0 0}}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}
\setlist[itemize]{leftmargin=1.5em, itemsep=2pt, parsep=0pt, topsep=2pt}

\begin{document}

\begin{center}
    {\LARGE \textbf{<VAR:FULL_NAME>}} \\ \vspace{4pt}
    <VAR:EMAIL> \ \textbar \ <VAR:PHONE> \ \textbar \ <VAR:LOCATION> \\
    <VAR:LINKS>
\end{center}

<BLOCK:SUMMARY>
\section{Professional Summary}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:SKILLS>
\section{Technical Skills}
\begin{itemize}
    <LOOP:SKILLS_CATEGORIES>
    \item \textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS>
    </LOOP:SKILLS_CATEGORIES>
\end{itemize}
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Work Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} \hfill <VAR:JOB_DATES> \\
\textit{<VAR:JOB_COMPANY>} \hfill \textit{<VAR:JOB_LOCATION>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\vspace{3pt}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Key Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \ \textbar \ \textit{<VAR:PROJECT_TECH>} \hfill <VAR:PROJECT_DATES> \\
<VAR:PROJECT_LINK>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
\vspace{3pt}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>} \hfill <VAR:EDU_DATES> \\
\textit{<VAR:INSTITUTION>} \hfill \textit{<VAR:EDU_LOCATION>}
<VAR:EDU_DETAILS>
\vspace{2pt}
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

<BLOCK:CERTIFICATIONS>
\section{Certifications}
\begin{itemize}
    <LOOP:CERTIFICATIONS>
    \item \textbf{<VAR:CERT_NAME>}
    </LOOP:CERTIFICATIONS>
\end{itemize}
</BLOCK:CERTIFICATIONS>

\end{document}
"""
    },

    # ── 2. Modern Corporate ────────────────────────────────────────────────────
    {
        "id": 2,
        "name": "Modern Corporate",
        "slug": "modern-corporate",
        "description": "Strong contemporary typography, navy blue accent bars, balanced corporate layout with modern hierarchy.",
        "category": "Classic",
        "ats_score": 97,
        "page_format": "A4 / Corporate Standard",
        "font_info": "Helvetica / Latin Modern Sans",
        "best_use_case": "Tech corporate, consulting firms, mid-to-large enterprises, product organizations.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/modern-corporate.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{primary}{RGB}{30, 64, 175}
\definecolor{subtext}{RGB}{75, 85, 99}

\hypersetup{colorlinks=true, linkcolor=primary, urlcolor=primary}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{}[\vspace{1pt}\color{primary}\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt, topsep=1pt}

\begin{document}

{\LARGE \textbf{\color{primary}<VAR:FULL_NAME>}} \\ \vspace{2pt}
{\small \color{subtext} <VAR:EMAIL> \ $\cdot$ \ <VAR:PHONE> \ $\cdot$ \ <VAR:LOCATION> \ $\cdot$ \ <VAR:LINKS>}
\vspace{4pt}

<BLOCK:SUMMARY>
\section{Executive Profile}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:SKILLS>
\section{Skills \& Competencies}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Professional Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} $\cdot$ \textit{<VAR:JOB_COMPANY>} \hfill <VAR:JOB_DATES> \\
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\vspace{2pt}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Key Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \textbar \ \textit{<VAR:PROJECT_TECH>} \hfill <VAR:PROJECT_DATES> \\
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
\vspace{2pt}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES> \\
<VAR:EDU_DETAILS>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 3. Executive Resume ────────────────────────────────────────────────────
    {
        "id": 3,
        "name": "Executive Resume",
        "slug": "executive-resume",
        "description": "Large elegant name header, leadership summary, deep slate tones, achievement-focused layout for senior roles.",
        "category": "Classic",
        "ats_score": 97,
        "page_format": "A4 / Leadership Executive",
        "font_info": "Latin Modern Roman",
        "best_use_case": "VP, Directors, Heads of Engineering, Senior Product Managers, Executive Leadership.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/executive-resume.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.6in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{brandnavy}{RGB}{20, 35, 75}
\hypersetup{colorlinks=true, urlcolor=brandnavy}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{brandnavy}}{}{0em}{}[\vspace{1pt}\color{brandnavy}\titlerule]
\titlespacing*{\section}{0pt}{8pt}{3pt}
\setlist[itemize]{leftmargin=1.3em, itemsep=1.5pt, parsep=0pt}

\begin{document}

\begin{center}
    {\huge \textbf{\color{brandnavy}<VAR:FULL_NAME>}} \\ \vspace{2pt}
    Executive Leadership \& Strategic Management \\
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:SUMMARY>
\section{Executive Profile}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:SKILLS>
\section{Leadership Competencies}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Executive Experience \& Leadership}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} \hfill <VAR:JOB_DATES> \\
\textit{<VAR:JOB_COMPANY>} \hfill \textit{<VAR:JOB_LOCATION>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\vspace{2pt}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Key Strategic Initiatives}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \hfill <VAR:PROJECT_DATES> \\
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>} \hfill <VAR:EDU_DATES> \\
\textit{<VAR:INSTITUTION>} \hfill \textit{<VAR:EDU_LOCATION>}
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 4. Modern Two-Column ───────────────────────────────────────────────────
    {
        "id": 4,
        "name": "Modern Two-Column",
        "slug": "modern-two-column",
        "description": "Iconic Deedy Overleaf 2-column layout: Left column for contact, skills, and coursework; Right column for career history.",
        "category": "Creative",
        "ats_score": 94,
        "page_format": "A4 / 2-Column Split",
        "font_info": "Helvetica / Latin Modern",
        "best_use_case": "Tech startups, web developers, modern software engineering, product design.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/modern-two-column.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{paracol}
\usepackage{xcolor}

\definecolor{primary}{RGB}{37, 99, 235}
\hypersetup{colorlinks=true, urlcolor=primary}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{6pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt}

\begin{document}

{\huge \textbf{<VAR:FULL_NAME>}} \\
<VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\vspace{4pt}
\hrule
\vspace{6pt}

\columnratio{0.32}
\begin{paracol}{2}
% Left Column
\section{Skills}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} \\
<VAR:CATEGORY_ITEMS> \vspace{3pt} \\
</LOOP:SKILLS_CATEGORIES>

\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>} \\
\textit{<VAR:INSTITUTION>} \\
<VAR:EDU_DATES> \vspace{3pt} \\
</LOOP:EDUCATION>

\switchcolumn
% Right Column
<BLOCK:SUMMARY>
\section{Summary}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} -- \textit{<VAR:JOB_COMPANY>} \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\vspace{2pt}
</LOOP:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} (\textit{<VAR:PROJECT_TECH>}) \hfill <VAR:PROJECT_DATES>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

\end{paracol}
\end{document}
"""
    },

    # ── 5. Color Sidebar ───────────────────────────────────────────────────────
    {
        "id": 5,
        "name": "Color Sidebar",
        "slug": "color-sidebar",
        "description": "Full-height dark navy sidebar containing profile details, contacts, and skills with an open white main area for experience.",
        "category": "Creative",
        "ats_score": 93,
        "page_format": "A4 / Colored Sidebar",
        "font_info": "Helvetica / Latin Modern Sans",
        "best_use_case": "Full-stack designers, creative technologists, frontend architects, digital consulting.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/color-sidebar.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.4in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{sidebg}{RGB}{15, 23, 42}
\definecolor{mainblue}{RGB}{2, 132, 199}

\pagestyle{empty}
\titleformat{\section}{\large\bfseries\color{mainblue}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{6pt}{3pt}
\setlist[itemize]{leftmargin=1.1em, itemsep=1.5pt, parsep=0pt}

\begin{document}
{\LARGE \textbf{<VAR:FULL_NAME>}} \\
<VAR:EMAIL> $\cdot$ <VAR:PHONE> $\cdot$ <VAR:LOCATION> $\cdot$ <VAR:LINKS>
\vspace{4pt}
\hrule

<BLOCK:SUMMARY>
\section{Profile}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:EXPERIENCE>
\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} -- \textit{<VAR:JOB_COMPANY>} \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \hfill <VAR:PROJECT_DATES>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 6. Minimalist Elegant ──────────────────────────────────────────────────
    {
        "id": 6,
        "name": "Minimalist Elegant",
        "slug": "minimalist-elegant",
        "description": "Distraction-free typography, generous whitespace, thin dividing rules, and understated minimalist elegance.",
        "category": "Creative",
        "ats_score": 98,
        "page_format": "A4 / Minimal Clean",
        "font_info": "Latin Modern Roman",
        "best_use_case": "Architects, senior consultants, executive managers, minimalist portfolios.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/minimalist-elegant.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.6in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

\pagestyle{empty}
\hypersetup{colorlinks=false, pdfborder={0 0 0}}

\titleformat{\section}{\normalsize\bfseries\uppercase}{}{0em}{}[\vspace{1pt}\hrule]
\titlespacing*{\section}{0pt}{10pt}{4pt}
\setlist[itemize]{leftmargin=1.4em, itemsep=2pt, parsep=0pt}

\begin{document}

\begin{center}
    {\Large \textbf{<VAR:FULL_NAME>}} \\ \vspace{3pt}
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:SUMMARY>
\section{Profile}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:EXPERIENCE>
\section{Professional Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_COMPANY>} \hfill <VAR:JOB_LOCATION> \\
\textit{<VAR:JOB_TITLE>} \hfill \textit{<VAR:JOB_DATES>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\vspace{3pt}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:SKILLS>
\section{Core Skills}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:INSTITUTION>} \hfill <VAR:EDU_LOCATION> \\
\textit{<VAR:DEGREE>} \hfill \textit{<VAR:EDU_DATES>}
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 7. Bold Creative ───────────────────────────────────────────────────────
    {
        "id": 7,
        "name": "Bold Creative",
        "slug": "bold-creative",
        "description": "Large typography, bold geometric banner accents, asymmetric sections, and distinctive visual punch.",
        "category": "Creative",
        "ats_score": 94,
        "page_format": "A4 / Bold Creative",
        "font_info": "Helvetica-Bold / Sans Serif",
        "best_use_case": "Design engineers, UI/UX developers, creative agency leads, product innovators.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/bold-creative.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{boldred}{RGB}{185, 28, 28}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{boldred}}{}{0em}{}[\vspace{1pt}\color{boldred}\titlerule]
\titlespacing*{\section}{0pt}{8pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt}

\begin{document}

{\Huge \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
{\small \textbf{<VAR:EMAIL>} $\bullet$ <VAR:PHONE> $\bullet$ <VAR:LOCATION> $\bullet$ <VAR:LINKS>}
\vspace{4pt}

<BLOCK:SUMMARY>
\section{Overview}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:EXPERIENCE>
\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} $\mid$ <VAR:JOB_COMPANY> \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:SKILLS>
\section{Skills}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 8. Software Engineer ───────────────────────────────────────────────────
    {
        "id": 8,
        "name": "Software Engineer",
        "slug": "software-engineer",
        "description": "Jake's Resume / HackerRank favorite: technical arsenal table, open-source projects, and monospaced tech stack tags.",
        "category": "Technical",
        "ats_score": 98,
        "page_format": "A4 / 1-Page Tech Standard",
        "font_info": "Latin Modern Sans / Monospace badges",
        "best_use_case": "Backend, Frontend, Full-Stack, DevOps, Cloud Infrastructure Engineers.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/software-engineer.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{accent}{RGB}{15, 23, 42}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\vspace{1pt}\titlerule]
\titlespacing*{\section}{0pt}{6pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1pt, parsep=0pt, topsep=1pt}

\begin{document}

\begin{center}
    {\huge \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
    \textbf{<VAR:EMAIL>} $\cdot$ <VAR:PHONE> $\cdot$ <VAR:LOCATION> $\cdot$ <VAR:LINKS>
\end{center}

<BLOCK:SKILLS>
\section{Technical Arsenal}
\begin{itemize}[leftmargin=0em, label={}]
    <LOOP:SKILLS_CATEGORIES>
    \item \textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS>
    </LOOP:SKILLS_CATEGORIES>
\end{itemize}
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} \hfill <VAR:JOB_DATES> \\
\textit{<VAR:JOB_COMPANY>} \hfill \textit{<VAR:JOB_LOCATION>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Featured Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \textbar \ \texttt{<VAR:PROJECT_TECH>} \hfill <VAR:PROJECT_DATES> \\
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>} \hfill <VAR:EDU_DATES> \\
\textit{<VAR:INSTITUTION>} \hfill \textit{<VAR:EDU_LOCATION>}
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 9. AI/ML Engineer ──────────────────────────────────────────────────────
    {
        "id": 9,
        "name": "AI/ML Engineer",
        "slug": "ai-ml-engineer",
        "description": "Tailored for AI engineers, LLM architectures, neural frameworks, model training benchmarks, and measurable metrics.",
        "category": "Technical",
        "ats_score": 97,
        "page_format": "A4 / AI & Machine Learning",
        "font_info": "Latin Modern / PyTorch & Model Stacks",
        "best_use_case": "AI Engineers, LLM Specialists, Deep Learning Engineers, Computer Vision & NLP Researchers.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/ai-ml-engineer.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{aimlpurple}{RGB}{109, 40, 217}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{aimlpurple}}{}{0em}{}[\vspace{1pt}\color{aimlpurple}\titlerule]
\titlespacing*{\section}{0pt}{6pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt}

\begin{document}

\begin{center}
    {\huge \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
    AI \& Machine Learning Engineer \\
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:SKILLS>
\section{AI / ML Models \& Frameworks}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Engineering Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} -- \textit{<VAR:JOB_COMPANY>} \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{AI Deployments \& Benchmarks}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} (\textit{<VAR:PROJECT_TECH>}) \hfill <VAR:PROJECT_DATES>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 10. Data Scientist ─────────────────────────────────────────────────────
    {
        "id": 10,
        "name": "Data Scientist",
        "slug": "data-scientist",
        "description": "Emphasizes SQL pipelines, predictive modeling, statistical testing, BI visualizations, and quantified business impact.",
        "category": "Technical",
        "ats_score": 97,
        "page_format": "A4 / Data Science",
        "font_info": "Latin Modern Roman",
        "best_use_case": "Data Scientists, Quantitative Researchers, Applied Statisticians, Analytics Leads.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/data-scientist.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

\pagestyle{empty}
\hypersetup{colorlinks=true, urlcolor=blue}

\titleformat{\section}{\large\bfseries\scshape}{}{0em}{}[\vspace{1pt}\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}
\setlist[itemize]{leftmargin=1.3em, itemsep=1.5pt, parsep=0pt}

\begin{document}

\begin{center}
    {\LARGE \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
    Data Science \& Predictive Modeling \\
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:SUMMARY>
\section{Research \& Focus}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:SKILLS>
\section{Data Tools \& Mathematical Computing}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} \hfill <VAR:JOB_DATES> \\
\textit{<VAR:JOB_COMPANY>} \hfill \textit{<VAR:JOB_LOCATION>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Machine Learning Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \hfill <VAR:PROJECT_DATES> \\
\textit{Stack: <VAR:PROJECT_TECH>}
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>} \hfill <VAR:EDU_DATES> \\
<VAR:INSTITUTION>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 11. Developer Portfolio ────────────────────────────────────────────────
    {
        "id": 11,
        "name": "Developer Portfolio",
        "slug": "developer-portfolio",
        "description": "Project-first design showcasing demo URLs, GitHub repositories, software architectures, and active tech stacks.",
        "category": "Technical",
        "ats_score": 96,
        "page_format": "A4 / Project-First Layout",
        "font_info": "Helvetica / Monospace tags",
        "best_use_case": "Open-source contributors, independent developers, hackathon winners, portfolio builders.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/developer-portfolio.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{portcyan}{RGB}{14, 116, 144}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{portcyan}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{6pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt}

\begin{document}

{\LARGE \textbf{<VAR:FULL_NAME>}} \\
<VAR:EMAIL> $\cdot$ <VAR:PHONE> $\cdot$ <VAR:LOCATION> $\cdot$ <VAR:LINKS>
\vspace{4pt}

<BLOCK:PROJECTS>
\section{Featured Projects \& Repositories}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \textbar \ \texttt{<VAR:PROJECT_TECH>} \hfill <VAR:PROJECT_DATES> \\
<VAR:PROJECT_LINK>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:SKILLS>
\section{Technologies \& Stacks}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} -- <VAR:JOB_COMPANY> \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    },

    # ── 12. Graduate / Fresher ─────────────────────────────────────────────────
    {
        "id": 12,
        "name": "Graduate / Fresher",
        "slug": "graduate-fresher",
        "description": "Education-first layout with college projects, coursework, and honors at top; no awkward empty experience gaps.",
        "category": "Academic",
        "ats_score": 98,
        "page_format": "A4 / Campus & New Grad",
        "font_info": "Times-Roman / University Standard",
        "best_use_case": "College graduates, campus placements, interns, entry-level software developers.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/graduate-fresher.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.6in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

\hypersetup{colorlinks=false, pdfborder={0 0 0}}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{3pt}
\setlist[itemize]{leftmargin=1.3em, itemsep=1.5pt, parsep=0pt}

\begin{document}

\begin{center}
    {\huge \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:INSTITUTION>} \hfill <VAR:EDU_LOCATION> \\
\textit{<VAR:DEGREE>} \hfill <VAR:EDU_DATES> \\
<VAR:EDU_DETAILS> \vspace{2pt} \\
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

<BLOCK:PROJECTS>
\section{Academic \& Capstone Projects}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \textbar \ \textit{<VAR:PROJECT_TECH>} \hfill <VAR:PROJECT_DATES> \\
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
\end{LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:SKILLS>
\section{Technical Skills}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Internships \& Experience}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} -- <VAR:JOB_COMPANY> \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

\end{document}
"""
    },

    # ── 13. Academic CV ────────────────────────────────────────────────────────
    {
        "id": 13,
        "name": "Academic CV",
        "slug": "academic-cv",
        "description": "Harvard / Oxford standard: formal academic serifs, research publications citations ([1], [2]), and teaching appointments.",
        "category": "Academic",
        "ats_score": 93,
        "page_format": "A4 / Multi-Page Scholar CV",
        "font_info": "Latin Modern Roman / Formal Serifs",
        "best_use_case": "Ph.D. candidates, university researchers, professors, fellows, postdoc appointments.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/academic-cv.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.65in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}

\pagestyle{empty}
\titleformat{\section}{\large\bfseries\scshape\centering}{}{0em}{}[\vspace{1pt}\hrule]
\titlespacing*{\section}{0pt}{10pt}{4pt}
\setlist[itemize]{leftmargin=1.5em, itemsep=2pt, parsep=0pt}

\begin{document}

\begin{center}
    {\huge \textbf{<VAR:FULL_NAME>}} \\ \vspace{2pt}
    Academic Curriculum Vitae \\
    <VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\end{center}

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:INSTITUTION>}, <VAR:EDU_LOCATION> \hfill <VAR:EDU_DATES> \\
\textit{<VAR:DEGREE>} \\
<VAR:EDU_DETAILS> \vspace{2pt} \\
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

<BLOCK:EXPERIENCE>
\section{Academic Appointments \& Research}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>}, <VAR:JOB_COMPANY> \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Research Projects \& Publications}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \hfill <VAR:PROJECT_DATES> \\
\textit{Focus: <VAR:PROJECT_TECH>}
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:SKILLS>
\section{Methodologies \& Tools}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

\end{document}
"""
    },

    # ── 14. Timeline Resume ────────────────────────────────────────────────────
    {
        "id": 14,
        "name": "Timeline Resume",
        "slug": "timeline-resume",
        "description": "Clear visual timeline structure: dates positioned in dedicated left timeline column beside role descriptions.",
        "category": "Specialized",
        "ats_score": 94,
        "page_format": "A4 / Vertical Timeline",
        "font_info": "Helvetica / Timeline Markers",
        "best_use_case": "Career changers, diverse multi-role professionals, contract engineers with clear year milestones.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/timeline-resume.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{timeblue}{RGB}{3, 105, 161}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{timeblue}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{3pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1.5pt, parsep=0pt}

\begin{document}

{\huge \textbf{<VAR:FULL_NAME>}} \\
<VAR:EMAIL> $\cdot$ <VAR:PHONE> $\cdot$ <VAR:LOCATION> $\cdot$ <VAR:LINKS>
\vspace{4pt}

<BLOCK:EXPERIENCE>
\section{Career Timeline}
<LOOP:EXPERIENCE>
\textbf{[<VAR:JOB_DATES>]} \textbf{<VAR:JOB_TITLE>} -- \textit{<VAR:JOB_COMPANY>}
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
\end{LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:EDUCATION>
\section{Education Timeline}
<LOOP:EDUCATION>
\textbf{[<VAR:EDU_DATES>]} \textbf{<VAR:DEGREE>}, <VAR:INSTITUTION>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

<BLOCK:SKILLS>
\section{Core Skills}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

\end{document}
"""
    },

    # ── 15. Infographic Resume ─────────────────────────────────────────────────
    {
        "id": 15,
        "name": "Infographic Resume",
        "slug": "infographic-resume",
        "description": "Creative visual layout with structured visual metric boxes, pill badges, and dual columns. (Creative / Non-ATS).",
        "category": "Specialized",
        "ats_score": 88,
        "page_format": "A4 / Infographic Visual",
        "font_info": "Helvetica-Bold / Graphic Panels",
        "best_use_case": "Creative portfolios, startup pitch decks, networking resumes, visual design leaders.",
        "license_name": "MIT License",
        "license_url": "https://opensource.org/licenses/MIT",
        "preview_image": "/templates/previews/infographic-resume.png",
        "is_active": True,
        "latex_template": r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.45in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

\definecolor{infopurple}{RGB}{91, 33, 182}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries\color{infopurple}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{6pt}{2pt}
\setlist[itemize]{leftmargin=1.1em, itemsep=1pt, parsep=0pt}

\begin{document}

{\Huge \textbf{\color{infopurple}<VAR:FULL_NAME>}} \\
<VAR:EMAIL> $\mid$ <VAR:PHONE> $\mid$ <VAR:LOCATION> $\mid$ <VAR:LINKS>
\vspace{3pt}

<BLOCK:SUMMARY>
\section{Profile \& Value Proposition}
<VAR:SUMMARY_TEXT>
</BLOCK:SUMMARY>

<BLOCK:SKILLS>
\section{Skills \& Capabilities}
<LOOP:SKILLS_CATEGORIES>
\textbf{<VAR:CATEGORY_NAME>:} <VAR:CATEGORY_ITEMS> \\
</LOOP:SKILLS_CATEGORIES>
</BLOCK:SKILLS>

<BLOCK:EXPERIENCE>
\section{Career History}
<LOOP:EXPERIENCE>
\textbf{<VAR:JOB_TITLE>} $\cdot$ <VAR:JOB_COMPANY> \hfill <VAR:JOB_DATES>
\begin{itemize}
    <LOOP:JOB_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:JOB_BULLETS>
\end{itemize}
</LOOP:EXPERIENCE>
</BLOCK:EXPERIENCE>

<BLOCK:PROJECTS>
\section{Key Deliverables}
<LOOP:PROJECTS>
\textbf{<VAR:PROJECT_NAME>} \hfill <VAR:PROJECT_DATES>
\begin{itemize}
    <LOOP:PROJECT_BULLETS>
    \item <VAR:BULLET_TEXT>
    </LOOP:PROJECT_BULLETS>
\end{itemize}
</LOOP:PROJECTS>
</BLOCK:PROJECTS>

<BLOCK:EDUCATION>
\section{Education}
<LOOP:EDUCATION>
\textbf{<VAR:DEGREE>}, <VAR:INSTITUTION> \hfill <VAR:EDU_DATES>
</LOOP:EDUCATION>
</BLOCK:EDUCATION>

\end{document}
"""
    }
]


def seed_resume_templates(db_session):
    """Inserts or updates the 15 distinct templates in the database."""
    from app.models.resume_center_models import ResumeTemplate

    for t_data in RESUME_TEMPLATES:
        existing = db_session.query(ResumeTemplate).filter_by(slug=t_data["slug"]).first()
        if existing:
            existing.name = t_data["name"]
            existing.description = t_data["description"]
            existing.category = t_data["category"]
            existing.ats_score = t_data["ats_score"]
            existing.latex_template = t_data["latex_template"]
            existing.license_name = t_data["license_name"]
            existing.license_url = t_data["license_url"]
            existing.preview_image = t_data["preview_image"]
            existing.is_active = t_data["is_active"]
        else:
            tmpl = ResumeTemplate(
                name=t_data["name"],
                slug=t_data["slug"],
                description=t_data["description"],
                category=t_data["category"],
                ats_score=t_data["ats_score"],
                latex_template=t_data["latex_template"],
                license_name=t_data["license_name"],
                license_url=t_data["license_url"],
                preview_image=t_data["preview_image"],
                is_active=t_data["is_active"]
            )
            db_session.add(tmpl)
    db_session.commit()
