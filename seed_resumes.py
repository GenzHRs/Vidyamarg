"""
Seed sample resumes for all candidate users who have none.
Run from the VidyamargAI directory:
  python seed_resumes.py
"""
import sys
sys.path.insert(0, 'backend')

from datetime import datetime
from app.core.database import SessionLocal
from app.models.models import User, Candidate
from app.models.resume_center_models import Resume, ResumeVersion, ResumeTemplate
from app.services.resume_templates_data import seed_resume_templates

CANDIDATES = [
    {
        'email': 'candidate@vidyamarg.ai',
        'full_name': 'Demo Candidate',
        'title': 'Senior Software Engineer',
        'skills_raw': 'Python, FastAPI, TypeScript, React, Next.js, PostgreSQL, Docker',
        'summary': 'Full-stack software engineer with 4 years of experience building modern web applications.',
        'phone': '+1 (555) 123-4567',
        'location': 'San Francisco, CA',
        'linkedin': 'https://linkedin.com/in/democandidate',
        'github': 'https://github.com/democandidate',
    },
    {
        'email': 'shiva@vidyamarg.ai',
        'full_name': 'Shiva Developer',
        'title': 'AI Engineer',
        'skills_raw': 'Python, Machine Learning, PyTorch, LangChain, React, FastAPI',
        'summary': 'AI Engineer specializing in LLM application architecture and agentic workflows.',
        'phone': '+1 (555) 234-5678',
        'location': 'Bangalore, India',
        'linkedin': 'https://linkedin.com/in/shivadev',
        'github': 'https://github.com/shivadev',
    },
    {
        'email': 'alex.swe@vidyamarg.ai',
        'full_name': 'Alex Chen',
        'title': 'Senior Backend Engineer',
        'skills_raw': 'Go, Java, Distributed Systems, Kubernetes, Cloud Architecture, Microservices',
        'summary': 'Senior Backend Engineer with 7+ years of distributed backend and cloud infrastructure experience.',
        'phone': '+1 (555) 345-6789',
        'location': 'New York, NY',
        'linkedin': 'https://linkedin.com/in/alexchen-swe',
        'github': 'https://github.com/alexchen-swe',
    },
    {
        'email': 'priya.data@vidyamarg.ai',
        'full_name': 'Priya Patel',
        'title': 'Data Scientist',
        'skills_raw': 'Python, SQL, Pandas, Tableau, Machine Learning, Scikit-Learn, BigQuery',
        'summary': 'Data Scientist experienced in predictive modeling, statistical analysis, and business intelligence.',
        'phone': '+1 (555) 456-7890',
        'location': 'Austin, TX',
        'linkedin': 'https://linkedin.com/in/priyapatel-ds',
        'github': 'https://github.com/priyapatel-ds',
    },
    {
        'email': 'rahul.fresher@vidyamarg.ai',
        'full_name': 'Rahul Verma',
        'title': 'Software Developer',
        'skills_raw': 'C++, Java, Python, HTML/CSS, JavaScript, Data Structures, Algorithms',
        'summary': 'Recent Computer Science Graduate eager to contribute to innovative software engineering teams.',
        'phone': '+1 (555) 567-8901',
        'location': 'Pune, India',
        'linkedin': 'https://linkedin.com/in/rahulverma-fresher',
        'github': 'https://github.com/rahulverma',
    },
]


def make_structured_data(item: dict) -> dict:
    skills_list = [s.strip() for s in item['skills_raw'].split(',')]
    skills_dict = {}
    if len(skills_list) > 3:
        skills_dict['Technical Skills'] = skills_list[:3]
        skills_dict['Frameworks & Tools'] = skills_list[3:]
    else:
        skills_dict['Skills'] = skills_list

    return {
        'personal_info': {
            'full_name': item['full_name'],
            'email': item['email'],
            'phone': item['phone'],
            'location': item['location'],
            'linkedin': item['linkedin'],
            'github': item['github'],
            'portfolio': '',
        },
        'summary': item['summary'],
        'experience': [
            {
                'title': item['title'],
                'company': 'VidyaMarg Technologies',
                'location': item['location'],
                'start_date': '2022',
                'end_date': 'Present',
                'bullets': [
                    'Designed and implemented scalable software solutions for production workloads.',
                    'Collaborated cross-functionally with product, design, and data teams.',
                    'Improved system performance and reliability through architectural best practices.',
                ],
            }
        ],
        'education': [
            {
                'degree': 'B.Tech in Computer Science & Engineering',
                'institution': 'State University of Technology',
                'location': item['location'],
                'graduation_year': '2022',
                'gpa': '3.7/4.0',
            }
        ],
        'skills': skills_dict,
        'projects': [
            {
                'name': 'Career Intelligence Platform',
                'tech_stack': ', '.join(skills_list[:3]),
                'bullets': [
                    'Built a full-stack career intelligence platform with AI-powered resume builder.',
                    'Integrated multi-format resume parsing and LaTeX compilation pipeline.',
                ],
            }
        ],
        'certifications': [
            'AWS Certified Cloud Practitioner',
        ],
    }


def seed_resumes():
    db = SessionLocal()
    try:
        # Ensure templates exist
        templates = db.query(ResumeTemplate).filter(ResumeTemplate.is_active == True).all()
        if not templates:
            print("Seeding templates first...")
            seed_resume_templates(db)
            templates = db.query(ResumeTemplate).filter(ResumeTemplate.is_active == True).all()
        
        # Use the ATS Classic template as default
        default_tmpl = next((t for t in templates if t.slug == 'ats-classic'), templates[0])
        print(f"Using template: {default_tmpl.name} (id={default_tmpl.id})")

        for item in CANDIDATES:
            user = db.query(User).filter(User.email == item['email']).first()
            if not user:
                print(f"  SKIP {item['email']}: user not found")
                continue

            # Get or create candidate profile
            cand = db.query(Candidate).filter(Candidate.user_id == user.id).first()
            if not cand:
                cand = Candidate(
                    user_id=user.id,
                    skills=item['skills_raw'],
                    summary=item['summary'],
                    phone=item['phone'],
                    linkedin=item['linkedin'],
                    github=item['github'],
                    status='Active',
                )
                db.add(cand)
                db.flush()
                print(f"  Created candidate profile for {item['email']}")

            # Check if candidate already has resumes
            existing_resumes = db.query(Resume).filter(
                Resume.candidate_id == cand.id,
                Resume.deleted_at == None
            ).count()

            if existing_resumes > 0:
                print(f"  SKIP {item['email']}: already has {existing_resumes} resume(s)")
                continue

            # Create sample resume
            structured_data = make_structured_data(item)
            resume = Resume(
                candidate_id=cand.id,
                title=f"{item['full_name']} - Master Resume",
                source_type='builder',
                template_id=default_tmpl.id,
                status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(resume)
            db.flush()

            version = ResumeVersion(
                resume_id=resume.id,
                version_number=1,
                structured_data=structured_data,
                change_summary='Initial resume — created by seed script',
                created_by=user.id,
                created_at=datetime.utcnow(),
            )
            db.add(version)
            db.flush()

            resume.current_version_id = version.id
            db.commit()
            print(f"  Created resume #{resume.id} for {item['email']}")

        db.commit()
        print("\nAll resumes seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_resumes()
