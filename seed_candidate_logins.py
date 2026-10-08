import sys
sys.path.insert(0, 'backend')
from app.core.database import SessionLocal
from app.models.models import User, Candidate
from app.models.resume_center_models import Resume, ResumeVersion, ResumeTemplate
from app.core.security import get_password_hash

def seed_candidates():
    db = SessionLocal()
    try:
        candidates_data = [
            {
                'email': 'candidate@vidyamarg.ai',
                'full_name': 'Demo Candidate',
                'role': 'candidate',
                'skills': 'Python, FastAPI, TypeScript, React, Next.js, PostgreSQL, Docker',
                'summary': 'Full-stack software engineer with 4 years of experience building modern web applications.',
                'phone': '+1 (555) 123-4567',
                'linkedin': 'https://linkedin.com/in/democandidate',
                'github': 'https://github.com/democandidate'
            },
            {
                'email': 'shiva@vidyamarg.ai',
                'full_name': 'Shiva Developer',
                'role': 'candidate',
                'skills': 'Python, Machine Learning, PyTorch, LangChain, React, FastAPI',
                'summary': 'AI Engineer specializing in LLM application architecture and agentic workflows.',
                'phone': '+1 (555) 234-5678',
                'linkedin': 'https://linkedin.com/in/shivadev',
                'github': 'https://github.com/shivadev'
            },
            {
                'email': 'alex.swe@vidyamarg.ai',
                'full_name': 'Alex Chen',
                'role': 'candidate',
                'skills': 'Go, Java, Distributed Systems, Kubernetes, Cloud Architecture, Microservices',
                'summary': 'Senior Backend Engineer with 7+ years of distributed backend and cloud infrastructure experience.',
                'phone': '+1 (555) 345-6789',
                'linkedin': 'https://linkedin.com/in/alexchen-swe',
                'github': 'https://github.com/alexchen-swe'
            },
            {
                'email': 'priya.data@vidyamarg.ai',
                'full_name': 'Priya Patel',
                'role': 'candidate',
                'skills': 'Python, SQL, Pandas, Tableau, Machine Learning, Scikit-Learn, BigQuery',
                'summary': 'Data Scientist experienced in predictive modeling, statistical analysis, and business intelligence.',
                'phone': '+1 (555) 456-7890',
                'linkedin': 'https://linkedin.com/in/priyapatel-ds',
                'github': 'https://github.com/priyapatel-ds'
            },
            {
                'email': 'rahul.fresher@vidyamarg.ai',
                'full_name': 'Rahul Verma',
                'role': 'candidate',
                'skills': 'C++, Java, Python, HTML/CSS, JavaScript, Data Structures, Algorithms',
                'summary': 'Recent Computer Science Graduate eager to contribute to innovative software engineering teams.',
                'phone': '+1 (555) 567-8901',
                'linkedin': 'https://linkedin.com/in/rahulverma-fresher',
                'github': 'https://github.com/rahulverma'
            }
        ]

        software_template = db.query(ResumeTemplate).filter(ResumeTemplate.slug == 'software-engineer').first()
        template_id = software_template.id if software_template else None

        for item in candidates_data:
            existing = db.query(User).filter(User.email == item['email']).first()
            if not existing:
                user = User(
                    email=item['email'],
                    password_hash=get_password_hash('Password123!'),
                    full_name=item['full_name'],
                    role=item['role']
                )
                db.add(user)
                db.flush()
                cand = Candidate(
                    user_id=user.id,
                    skills=item['skills'],
                    summary=item['summary'],
                    phone=item['phone'],
                    linkedin=item['linkedin'],
                    github=item['github']
                )
                db.add(cand)
                db.flush()

                # Create sample resume for this candidate
                resume = Resume(
                    candidate_id=cand.id,
                    title=f"{item['full_name']} - Master Resume",
                    source_type='builder',
                    template_id=template_id,
                    status='active'
                )
                db.add(resume)
                db.flush()

                sample_struct = {
                    'basics': {
                        'name': item['full_name'],
                        'email': item['email'],
                        'phone': item['phone'],
                        'summary': item['summary'],
                        'links': {'linkedin': item['linkedin'], 'github': item['github']}
                    },
                    'skills': [s.strip() for s in item['skills'].split(',')],
                    'experience': [
                        {
                            'company': 'Tech Solutions',
                            'position': item['skills'].split(',')[0].strip() + ' Specialist',
                            'startDate': '2022-01',
                            'endDate': 'Present',
                            'highlights': ['Designed system architectures', 'Collaborated on high-impact projects']
                        }
                    ],
                    'education': [
                        {
                            'institution': 'University Institute of Technology',
                            'degree': 'Bachelor of Technology in Computer Science',
                            'graduationDate': '2022'
                        }
                    ]
                }

                version = ResumeVersion(
                    resume_id=resume.id,
                    version_number=1,
                    structured_data=sample_struct,
                    change_summary='Initial resume version',
                    created_by=user.id
                )
                db.add(version)
                db.flush()
                resume.current_version_id = version.id
                print(f"Created candidate: {item['email']}")
            else:
                # Update existing candidate password to make sure it's Password123!
                existing.password_hash = get_password_hash('Password123!')
                print(f"Updated candidate password: {item['email']}")

        db.commit()
        print('All candidate accounts ready!')
    finally:
        db.close()

if __name__ == '__main__':
    seed_candidates()
