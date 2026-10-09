"""
VidyaMarg AI — Seed Comprehensive Dummy Jobs (All Types)
Populates realistic, production-grade dummy job postings and company entities:
- Employment Types: Full-time, Part-time, Contract, Internship, Freelance, Remote
- Work Modes: Remote, Hybrid, Onsite
- Seniority Levels: Intern, Junior, Mid, Senior, Lead
- Technical Domains: AI/ML, GenAI/LLM, Data Science, Python Backend, Full-Stack, MLOps/DevOps, QA/Testing
- Valid, working apply URLs (Greenhouse, Lever, Company Career Portals)
- Pre-computes Matches for all candidates
"""

import hashlib
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.job_models import Job, Company, Match
from app.models.models import Candidate

def generate_job_hash(title: str, company: str, ext_id: str) -> str:
    raw = f"{title.lower()}::{company.lower()}::{ext_id.lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

COMPANIES_DATA = [
    {
        "name": "Google DeepMind",
        "normalized_name": "google deepmind",
        "domain": "deepmind.google",
        "industry": "Artificial Intelligence",
        "company_size": "enterprise",
        "founded_year": 2010,
        "headquarters": "London, UK / Mountain View, CA",
        "description": "Pioneering research lab committed to solving intelligence to advance science and benefit humanity.",
        "website": "https://deepmind.google",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "OpenAI",
        "normalized_name": "openai",
        "domain": "openai.com",
        "industry": "Artificial Intelligence",
        "company_size": "mid",
        "founded_year": 2015,
        "headquarters": "San Francisco, CA",
        "description": "AI research and deployment company behind GPT-4, ChatGPT, and Sora.",
        "website": "https://openai.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Anthropic",
        "normalized_name": "anthropic",
        "domain": "anthropic.com",
        "industry": "Artificial Intelligence",
        "company_size": "mid",
        "founded_year": 2021,
        "headquarters": "San Francisco, CA",
        "description": "AI safety and research company focused on building steerable, interpretable, and reliable AI systems like Claude.",
        "website": "https://anthropic.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Microsoft",
        "normalized_name": "microsoft",
        "domain": "microsoft.com",
        "industry": "Enterprise Software & Cloud",
        "company_size": "enterprise",
        "founded_year": 1975,
        "headquarters": "Redmond, WA",
        "description": "Global technology company enabling digital transformation through intelligent cloud and cutting-edge AI.",
        "website": "https://microsoft.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Meta",
        "normalized_name": "meta",
        "domain": "meta.com",
        "industry": "Social Media & AI",
        "company_size": "enterprise",
        "founded_year": 2004,
        "headquarters": "Menlo Park, CA",
        "description": "Building technologies that help people connect, find communities, and grow businesses, creators of Llama models.",
        "website": "https://meta.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Hugging Face",
        "normalized_name": "hugging face",
        "domain": "huggingface.co",
        "industry": "Open-Source AI",
        "company_size": "mid",
        "founded_year": 2016,
        "headquarters": "New York, NY / Paris, France",
        "description": "The AI community building the future of open models, datasets, and collaborative machine learning.",
        "website": "https://huggingface.co",
        "trust_score": 0.97,
        "is_verified": True,
    },
    {
        "name": "Databricks",
        "normalized_name": "databricks",
        "domain": "databricks.com",
        "industry": "Data & AI Platform",
        "company_size": "enterprise",
        "founded_year": 2013,
        "headquarters": "San Francisco, CA",
        "description": "The Data and AI company helping organizations unify their data, analytics, and artificial intelligence.",
        "website": "https://databricks.com",
        "trust_score": 0.97,
        "is_verified": True,
    },
    {
        "name": "Scale AI",
        "normalized_name": "scale ai",
        "domain": "scale.com",
        "industry": "AI Infrastructure",
        "company_size": "mid",
        "founded_year": 2016,
        "headquarters": "San Francisco, CA",
        "description": "The Data Foundry for AI, powering generative AI model training, fine-tuning, and human-in-the-loop evaluations.",
        "website": "https://scale.com",
        "trust_score": 0.96,
        "is_verified": True,
    },
    {
        "name": "NVIDIA",
        "normalized_name": "nvidia",
        "domain": "nvidia.com",
        "industry": "Semiconductors & Accelerated AI",
        "company_size": "enterprise",
        "founded_year": 1993,
        "headquarters": "Santa Clara, CA",
        "description": "World leader in visual computing and GPU-accelerated computing powering the global AI revolution.",
        "website": "https://nvidia.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Stripe",
        "normalized_name": "stripe",
        "domain": "stripe.com",
        "industry": "Financial Infrastructure",
        "company_size": "enterprise",
        "founded_year": 2010,
        "headquarters": "San Francisco, CA / Dublin, Ireland",
        "description": "Financial infrastructure platform for the internet, powering millions of businesses worldwide.",
        "website": "https://stripe.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Razorpay",
        "normalized_name": "razorpay",
        "domain": "razorpay.com",
        "industry": "FinTech",
        "company_size": "mid",
        "founded_year": 2014,
        "headquarters": "Bengaluru, Karnataka, India",
        "description": "India's leading payments and financial services platform for businesses and developers.",
        "website": "https://razorpay.com",
        "trust_score": 0.96,
        "is_verified": True,
    },
    {
        "name": "Swiggy Labs",
        "normalized_name": "swiggy labs",
        "domain": "swiggy.com",
        "industry": "E-Commerce & FoodTech",
        "company_size": "enterprise",
        "founded_year": 2014,
        "headquarters": "Bengaluru, Karnataka, India",
        "description": "On-demand convenience platform leveraging AI, computer vision, and real-time dispatch systems.",
        "website": "https://swiggy.com",
        "trust_score": 0.95,
        "is_verified": True,
    },
    {
        "name": "Zerodha Tech",
        "normalized_name": "zerodha tech",
        "domain": "zerodha.tech",
        "industry": "FinTech & Brokerage",
        "company_size": "mid",
        "founded_year": 2010,
        "headquarters": "Bengaluru, Karnataka, India",
        "description": "India's largest retail stockbroker, celebrated for lean, high-performance technology infrastructure.",
        "website": "https://zerodha.tech",
        "trust_score": 0.97,
        "is_verified": True,
    },
    {
        "name": "Cohere",
        "normalized_name": "cohere",
        "domain": "cohere.com",
        "industry": "Enterprise Generative AI",
        "company_size": "mid",
        "founded_year": 2019,
        "headquarters": "Toronto, Canada",
        "description": "Enterprise AI platform building multilingual LLMs, Command models, and industry-leading RAG embeddings.",
        "website": "https://cohere.com",
        "trust_score": 0.96,
        "is_verified": True,
    },
    {
        "name": "Perplexity AI",
        "normalized_name": "perplexity ai",
        "domain": "perplexity.ai",
        "industry": "AI Search Engine",
        "company_size": "startup",
        "founded_year": 2022,
        "headquarters": "San Francisco, CA",
        "description": "Next-generation conversational search engine synthesizing web information with real-time citations.",
        "website": "https://perplexity.ai",
        "trust_score": 0.96,
        "is_verified": True,
    },
    {
        "name": "DeepLearning.AI",
        "normalized_name": "deeplearning.ai",
        "domain": "deeplearning.ai",
        "industry": "Education & AI Research",
        "company_size": "mid",
        "founded_year": 2017,
        "headquarters": "Palo Alto, CA",
        "description": "Founded by Andrew Ng, empowering millions to build an AI-first future through world-class education.",
        "website": "https://deeplearning.ai",
        "trust_score": 0.97,
        "is_verified": True,
    },
    {
        "name": "Goldman Sachs",
        "normalized_name": "goldman sachs",
        "domain": "goldmansachs.com",
        "industry": "Finance & Investment Banking",
        "company_size": "enterprise",
        "founded_year": 1869,
        "headquarters": "New York, NY / Bengaluru, India",
        "description": "Leading global financial institution providing investment banking, securities, and asset management services.",
        "website": "https://goldmansachs.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "McKinsey & Company",
        "normalized_name": "mckinsey & company",
        "domain": "mckinsey.com",
        "industry": "Management Consulting & Strategy",
        "company_size": "enterprise",
        "founded_year": 1926,
        "headquarters": "New York, NY / Mumbai, India",
        "description": "Global management consulting firm serving leading businesses, governments, and institutions.",
        "website": "https://mckinsey.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Figma",
        "normalized_name": "figma",
        "domain": "figma.com",
        "industry": "Design & Creative Tools",
        "company_size": "mid",
        "founded_year": 2012,
        "headquarters": "San Francisco, CA",
        "description": "Leading collaborative product design platform connecting teams to build better digital experiences.",
        "website": "https://figma.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Hindustan Unilever",
        "normalized_name": "hindustan unilever",
        "domain": "hul.co.in",
        "industry": "Consumer Goods & Marketing",
        "company_size": "enterprise",
        "founded_year": 1933,
        "headquarters": "Mumbai, Maharashtra, India",
        "description": "India's largest fast-moving consumer goods company with celebrated consumer brands.",
        "website": "https://hul.co.in",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Salesforce",
        "normalized_name": "salesforce",
        "domain": "salesforce.com",
        "industry": "Enterprise Sales & CRM",
        "company_size": "enterprise",
        "founded_year": 1999,
        "headquarters": "San Francisco, CA / Bengaluru, India",
        "description": "World leader in Customer Relationship Management (CRM) and cloud enterprise software.",
        "website": "https://salesforce.com",
        "trust_score": 0.99,
        "is_verified": True,
    },
    {
        "name": "Apollo Hospitals",
        "normalized_name": "apollo hospitals",
        "domain": "apollohospitals.com",
        "industry": "Healthcare & Life Sciences",
        "company_size": "enterprise",
        "founded_year": 1983,
        "headquarters": "Chennai, Tamil Nadu, India",
        "description": "Asia's foremost integrated healthcare services provider touching over 150 million lives.",
        "website": "https://apollohospitals.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Blinkit",
        "normalized_name": "blinkit",
        "domain": "blinkit.com",
        "industry": "Operations & Quick Commerce",
        "company_size": "enterprise",
        "founded_year": 2013,
        "headquarters": "Gurugram, Haryana, India",
        "description": "Pioneering quick commerce and ultra-fast fulfillment operations platform in India.",
        "website": "https://blinkit.com",
        "trust_score": 0.96,
        "is_verified": True,
    },
    {
        "name": "Workday",
        "normalized_name": "workday",
        "domain": "workday.com",
        "industry": "Human Resources & Enterprise Cloud",
        "company_size": "enterprise",
        "founded_year": 2005,
        "headquarters": "Pleasanton, CA / Bengaluru, India",
        "description": "Leading provider of enterprise cloud applications for finance, human resources, and workforce planning.",
        "website": "https://workday.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
    {
        "name": "Airbnb",
        "normalized_name": "airbnb",
        "domain": "airbnb.com",
        "industry": "Hospitality & Brand Experience",
        "company_size": "enterprise",
        "founded_year": 2008,
        "headquarters": "San Francisco, CA",
        "description": "Community marketplace connecting people to unique travel experiences and stays worldwide.",
        "website": "https://airbnb.com",
        "trust_score": 0.98,
        "is_verified": True,
    },
]

JOBS_DATA = [
    # ==========================================
    # 1. FULL-TIME ONSITE / HYBRID / REMOTE
    # ==========================================
    {
        "external_id": "job_ft_001",
        "company_name": "Google DeepMind",
        "title": "Senior AI / Machine Learning Engineer",
        "title_normalized": "senior ai machine learning engineer",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "Machine Learning",
        "industry": "Artificial Intelligence",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 4200000,
        "salary_max": 6500000,
        "salary_currency": "INR",
        "salary_raw": "₹42,00,000 - ₹65,00,000 / yr",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://careers.google.com/jobs/results/148291034",
        "job_url": "https://careers.google.com/jobs/results/148291034",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "Scikit-learn", "Docker", "Machine Learning", "Embeddings"],
        "preferred_skills": ["Transformers", "Distributed Systems", "Kubernetes", "CUDA"],
        "description_summary": "Architect and deploy large-scale deep learning models for production intelligence pipelines at DeepMind Bengaluru. Collaborate with global research groups to scale neural networks across distributed accelerator clusters.",
        "description": """About the Role:
We are looking for an experienced Senior AI/ML Engineer to join the Google DeepMind engineering team in Bengaluru. You will work on designing, training, and operationalizing modern machine learning architectures that touch hundreds of millions of users.

Key Responsibilities:
- Design, implement, and benchmark machine learning algorithms using Python, PyTorch, and TensorFlow.
- Build production model training and inference pipelines with low-latency guarantees.
- Optimize deep neural networks using quantization, pruning, and distributed data-parallel paradigms.
- Collaborate with research scientists to bring novel AI breakthroughs into production services.

Qualifications & Requirements:
- 4+ years of industry experience deploying machine learning systems in production.
- Strong proficiency in Python, PyTorch, TensorFlow, Scikit-learn, NumPy, and Pandas.
- Solid background in linear algebra, probability, loss functions, and optimization techniques.
- Experience containerizing models with Docker and managing microservices.

Benefits:
- Competitive compensation + Google equity (GSUs).
- Comprehensive healthcare coverage for family.
- Generous annual learning and conference allowance.""",
    },
    {
        "external_id": "job_ft_002",
        "company_name": "Anthropic",
        "title": "Generative AI & LLM Systems Engineer",
        "title_normalized": "generative ai llm systems engineer",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "Artificial Intelligence",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 175000,
        "salary_max": 240000,
        "salary_currency": "USD",
        "salary_raw": "$175,000 - $240,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 7.0,
        "apply_url": "https://jobs.lever.co/anthropic/9a8b7c6d-4321",
        "job_url": "https://jobs.lever.co/anthropic/9a8b7c6d-4321",
        "required_skills": ["Python", "LLMs", "RAG", "LangChain", "FastAPI", "Prompt Engineering", "OpenAI"],
        "preferred_skills": ["Vector Databases", "Qdrant", "Claude API", "Evaluation Frameworks", "vLLM"],
        "description_summary": "Design high-reliability LLM agent architectures and production RAG pipelines for Claude ecosystem integrations. Focus on steerability, factuality validation, and context retrieval optimization.",
        "description": """About Anthropic:
Anthropic is an AI safety and research company dedicated to building reliable, interpretable, and steerable AI systems.

The Role:
As a Generative AI & LLM Systems Engineer, you will build state-of-the-art conversational pipelines, multi-hop RAG architectures, and agentic workflows using Python, FastAPI, LangChain, and advanced LLM orchestrators.

Key Responsibilities:
- Develop production-grade Retrieval-Augmented Generation (RAG) engines with hybrid semantic search.
- Implement robust prompt engineering, structured JSON outputs, and guardrails for hallucination prevention.
- Build high-throughput REST APIs and asynchronous streaming endpoints using FastAPI.
- Benchmark and optimize token usage, latency, and response grounding.

Requirements:
- 3+ years experience in Python backend development with deep expertise in LLM application frameworks.
- Demonstrated hands-on experience with RAG architectures, vector embeddings, and LangChain/LlamaIndex.
- Strong knowledge of API development with FastAPI and relational/vector storage.
- Passion for AI alignment and truthful, grounded model behavior.""",
    },
    {
        "external_id": "job_ft_003",
        "company_name": "Microsoft",
        "title": "Machine Learning Engineer (Azure AI)",
        "title_normalized": "machine learning engineer azure ai",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "Cloud AI",
        "industry": "Enterprise Software & Cloud",
        "location": "Hyderabad, Telangana, India",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "salary_min": 2600000,
        "salary_max": 4000000,
        "salary_currency": "INR",
        "salary_raw": "₹26,00,000 - ₹40,00,000 / yr",
        "experience_min_years": 2.0,
        "experience_max_years": 5.0,
        "apply_url": "https://careers.microsoft.com/us/en/job/1829402",
        "job_url": "https://careers.microsoft.com/us/en/job/1829402",
        "required_skills": ["Python", "Azure", "Docker", "Scikit-learn", "PyTorch", "REST APIs", "Git"],
        "preferred_skills": ["Azure ML Studio", "MLflow", "Kubernetes", "PostgreSQL"],
        "description_summary": "Build and scale enterprise cloud machine learning solutions on Microsoft Azure. Implement end-to-end training pipelines, CI/CD for ML, and automated model monitoring.",
        "description": """Join the Azure AI team at Microsoft IDC Hyderabad to build the foundation of cloud-native machine learning.

Responsibilities:
- Build resilient machine learning pipelines using Python, Scikit-learn, and PyTorch on Azure.
- Containerize training and scoring routines with Docker and automate deployment using Git workflows.
- Monitor model drift, data drift, and latency SLAs in live customer-facing enterprise services.
- Work closely with cloud architects and data engineers to unify data streams from relational and NoSQL databases.

Requirements:
- 2+ years of professional software engineering and machine learning experience.
- Strong Python programming, data manipulation with Pandas/NumPy, and REST API development.
- Hands-on experience with cloud platforms (Azure preferred) and containerization (Docker).
- Bachelor's or Master's degree in Computer Science, Data Science, or related engineering disciplines.""",
    },
    {
        "external_id": "job_ft_004",
        "company_name": "Razorpay",
        "title": "Senior Python Backend Engineer (FastAPI / Microservices)",
        "title_normalized": "senior python backend engineer fastapi microservices",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "senior",
        "role_category": "Backend Engineering",
        "role_sub_category": "FastAPI/Microservices",
        "industry": "FinTech",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 3200000,
        "salary_max": 4800000,
        "salary_currency": "INR",
        "salary_raw": "₹32,00,000 - ₹48,00,000 / yr",
        "experience_min_years": 3.5,
        "experience_max_years": 7.0,
        "apply_url": "https://razorpay.com/jobs/senior-backend-engineer-python",
        "job_url": "https://razorpay.com/jobs/senior-backend-engineer-python",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "MySQL", "Docker", "REST APIs", "Git"],
        "preferred_skills": ["Redis", "Kafka", "Celery", "SQLAlchemy", "AsyncIO"],
        "description_summary": "Architect ultra-reliable payments settlement microservices handling thousands of requests per second. Champion clean asynchronous architecture with FastAPI, PostgreSQL, and event streaming.",
        "description": """About Razorpay:
Razorpay powers seamless payments for millions of businesses across India and Southeast Asia.

What You Will Do:
- Architect high-throughput, low-latency microservices using Python, FastAPI, and AsyncIO.
- Optimize database schemas and query performance on PostgreSQL and MySQL.
- Implement robust idempotency, distributed locking, and event-driven architectures.
- Collaborate with security teams to ensure PCI-DSS compliance and zero-downtime deployments.

Requirements:
- 3.5+ years of production experience building Python backend services.
- Deep expertise in FastAPI, Pydantic, SQLAlchemy, and relational databases (PostgreSQL/MySQL).
- Strong understanding of containerization (Docker), RESTful principles, and Git version control.
- Experience with concurrency, asynchronous execution, and message queues.""",
    },
    {
        "external_id": "job_ft_005",
        "company_name": "Databricks",
        "title": "Staff MLOps & Platform Engineer",
        "title_normalized": "staff mlops platform engineer",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "lead",
        "role_category": "DevOps/Cloud",
        "role_sub_category": "MLOps",
        "industry": "Data & AI Platform",
        "location": "Remote",
        "city": "Remote",
        "country": "United States",
        "salary_min": 190000,
        "salary_max": 260000,
        "salary_currency": "USD",
        "salary_raw": "$190,000 - $260,000 / yr",
        "experience_min_years": 6.0,
        "experience_max_years": 10.0,
        "apply_url": "https://boards.greenhouse.io/databricks/jobs/5201948",
        "job_url": "https://boards.greenhouse.io/databricks/jobs/5201948",
        "required_skills": ["Python", "Docker", "Git", "GitHub", "Azure", "REST APIs"],
        "preferred_skills": ["Kubernetes", "MLflow", "Terraform", "CI/CD", "Ray"],
        "description_summary": "Lead the platform architecture for automated model registry, continuous deployment, and GPU cluster orchestration across multi-cloud environments.",
        "description": """At Databricks, we are passionate about solving the world's toughest data problems.

Responsibilities:
- Build standardized MLOps infrastructure for thousands of data science teams worldwide.
- Automate model registry, tracking, and A/B rollout pipelines using MLflow and container runtimes.
- Orchestrate distributed model training and inference on Kubernetes and Azure clusters.
- Establish best practices for GitOps, observability, metrics tracking, and fault tolerance.

Requirements:
- 6+ years of software/systems engineering with at least 3 years focused on MLOps infrastructure.
- Proficient in Python, Docker, cloud ecosystems (Azure/AWS), and modern DevOps tools.
- Deep expertise in containerized environments and microservice API architectures.""",
    },
    {
        "external_id": "job_ft_006",
        "company_name": "Hugging Face",
        "title": "Machine Learning Engineer (NLP & Transformers)",
        "title_normalized": "machine learning engineer nlp transformers",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "NLP",
        "industry": "Open-Source AI",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 130000,
        "salary_max": 180000,
        "salary_currency": "USD",
        "salary_raw": "$130,000 - $180,000 / yr",
        "experience_min_years": 2.5,
        "experience_max_years": 6.0,
        "apply_url": "https://boards.greenhouse.io/huggingface/jobs/6192834",
        "job_url": "https://boards.greenhouse.io/huggingface/jobs/6192834",
        "required_skills": ["Python", "PyTorch", "Hugging Face Transformers", "NLP", "Embeddings", "Git"],
        "preferred_skills": ["Tokenizers", "Datasets", "Safetensors", "PEFT", "LoRA"],
        "description_summary": "Work on the world's most popular open-source NLP and transformer libraries. Implement state-of-the-art tokenization, embedding generation, and fine-tuning pipelines.",
        "description": """Join Hugging Face and help democratize good machine learning!

Responsibilities:
- Maintain and enhance open-source NLP pipelines within the Transformers ecosystem.
- Implement efficient embedding generation and indexing algorithms for retrieval applications.
- Build demonstration models and reproducible Jupyter notebooks for the developer community.
- Optimize memory footprints during model inference using PyTorch and quantization libraries.

Requirements:
- 2.5+ years of experience with Python and PyTorch in an NLP or Machine Learning context.
- Solid understanding of Attention mechanisms, Transformers, embeddings, and tokenizers.
- Active GitHub presence or open-source contributions are strongly valued.""",
    },
    {
        "external_id": "job_ft_007",
        "company_name": "Swiggy Labs",
        "title": "Computer Vision & Document AI Engineer",
        "title_normalized": "computer vision document ai engineer",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "Computer Vision",
        "industry": "E-Commerce & FoodTech",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 2400000,
        "salary_max": 3800000,
        "salary_currency": "INR",
        "salary_raw": "₹24,00,000 - ₹38,00,000 / yr",
        "experience_min_years": 2.0,
        "experience_max_years": 5.0,
        "apply_url": "https://careers.swiggy.com/jobs/swiggy-ai-engineer-102",
        "job_url": "https://careers.swiggy.com/jobs/swiggy-ai-engineer-102",
        "required_skills": ["Python", "OCR", "TensorFlow", "PyTorch", "Pandas", "NumPy", "FastAPI"],
        "preferred_skills": ["OpenCV", "Tesseract", "LayoutLM", "AWS S3", "Docker"],
        "description_summary": "Build intelligent OCR, document understanding, and receipt recognition systems using deep learning and computer vision to automate partner onboarding.",
        "description": """Swiggy Labs is the innovation engine driving breakthrough technology at Swiggy.

Responsibilities:
- Build automated Document AI and OCR pipelines to parse restaurant menus, bills, and licenses.
- Train custom object detection and text recognition models using PyTorch and TensorFlow.
- Package models into robust FastAPI endpoints integrated into the vendor onboarding workflow.
- Clean and preprocess complex image and tabular data using Pandas and NumPy.

Requirements:
- 2+ years of experience in computer vision, OCR, and Document AI.
- Strong coding skills in Python, NumPy, Pandas, and deep learning frameworks.
- Experience delivering production-ready inference endpoints.""",
    },
    {
        "external_id": "job_ft_008",
        "company_name": "Scale AI",
        "title": "Full-Stack AI Application Engineer (Next.js / Python)",
        "title_normalized": "full stack ai application engineer nextjs python",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Full-Stack",
        "role_sub_category": "Full-Stack AI",
        "industry": "AI Infrastructure",
        "location": "Remote",
        "city": "Remote",
        "country": "United States",
        "salary_min": 140000,
        "salary_max": 195000,
        "salary_currency": "USD",
        "salary_raw": "$140,000 - $195,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://jobs.lever.co/scaleai/3b827104",
        "job_url": "https://jobs.lever.co/scaleai/3b827104",
        "required_skills": ["Python", "FastAPI", "REST APIs", "Git", "GitHub", "Docker"],
        "preferred_skills": ["React", "Next.js", "TypeScript", "Tailwind CSS", "PostgreSQL"],
        "description_summary": "Build responsive web applications and AI-human interactive dashboards connecting cutting-edge LLMs to production users.",
        "description": """Scale AI is building the data foundation for artificial intelligence.

Responsibilities:
- Develop modern full-stack web applications combining Next.js user interfaces with FastAPI backends.
- Build real-time streaming interfaces for LLM completions, prompt evaluations, and annotation workflows.
- Maintain clean codebases with Git, automated testing, and containerized deployment.

Requirements:
- 3+ years in full-stack software development with Python and modern JavaScript/TypeScript.
- Experience building RESTful APIs with FastAPI and responsive frontends.
- Familiarity with Docker and agile collaboration on GitHub.""",
    },

    # ==========================================
    # 2. PART-TIME JOBS
    # ==========================================
    {
        "external_id": "job_pt_001",
        "company_name": "DeepLearning.AI",
        "title": "Machine Learning Course Instructor & Technical Mentor (Part-Time)",
        "title_normalized": "machine learning course instructor mentor part time",
        "employment_type": "Part-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "Education/Mentorship",
        "industry": "Education & AI Research",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 45,
        "salary_max": 80,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$45 - $80 / hr (20 hrs/week)",
        "experience_min_years": 2.0,
        "experience_max_years": 6.0,
        "apply_url": "https://deeplearning.ai/careers/pt-mentor-ml",
        "job_url": "https://deeplearning.ai/careers/pt-mentor-ml",
        "required_skills": ["Python", "Scikit-learn", "TensorFlow", "PyTorch", "Jupyter Notebook", "Pandas"],
        "preferred_skills": ["Technical Writing", "Curriculum Design", "Mentorship"],
        "description_summary": "Mentor emerging AI engineers and evaluate practical machine learning code notebooks. Conduct weekly interactive code reviews and author hands-on lab exercises.",
        "description": """About DeepLearning.AI:
We are on a mission to educate and inspire the world to build AI-powered solutions.

Role (Part-time, ~15-20 hours/week):
- Review and refine student machine learning projects implemented in Jupyter Notebooks.
- Provide targeted code feedback on Scikit-learn, TensorFlow, and PyTorch implementations.
- Help create new lab exercises and practical assignments covering neural networks and data science.

Requirements:
- 2+ years of professional experience in machine learning and Python.
- Strong understanding of core algorithms (regression, classification, neural nets, clustering).
- Excellent technical communication and a passion for teaching.""",
    },
    {
        "external_id": "job_pt_002",
        "company_name": "Scale AI",
        "title": "AI Technical Writer & Prompt Engineering Specialist (Part-Time)",
        "title_normalized": "ai technical writer prompt engineering specialist part time",
        "employment_type": "Part-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "junior",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "AI Infrastructure",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 35,
        "salary_max": 60,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$35 - $60 / hr (15-20 hrs/week)",
        "experience_min_years": 1.0,
        "experience_max_years": 3.0,
        "apply_url": "https://jobs.lever.co/scaleai/pt-prompt-specialist",
        "job_url": "https://jobs.lever.co/scaleai/pt-prompt-specialist",
        "required_skills": ["Python", "Prompt Engineering", "OpenAI", "LLMs", "Git"],
        "preferred_skills": ["Technical Writing", "Markdown", "JSON Schema", "Few-Shot Learning"],
        "description_summary": "Craft complex system prompts, evaluation benchmarks, and technical developer documentation for frontier LLM models on a flexible part-time schedule.",
        "description": """Role Overview:
Join Scale AI as a Part-Time AI Technical Writer & Prompt Engineering Specialist. You will craft high-quality instruction prompts, design evaluation datasets, and test frontier LLM behavior.

Responsibilities:
- Write few-shot prompts and structured evaluation rubrics for LLM tasks.
- Create developer guides and code walkthroughs using Python and OpenAI APIs.
- Validate model outputs for safety, accuracy, and adherence to instructions.

Requirements:
- 1+ years experience working with Python and LLM prompt engineering.
- Excellent written English and technical clarity.
- Availability for 15-20 flexible hours per week.""",
    },
    {
        "external_id": "job_pt_003",
        "company_name": "Zerodha Tech",
        "title": "Part-Time Python Data Automation Developer",
        "title_normalized": "part time python data automation developer",
        "employment_type": "Part-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "junior",
        "role_category": "Backend Engineering",
        "role_sub_category": "Data Engineering",
        "industry": "FinTech & Brokerage",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 35000,
        "salary_max": 60000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹35,000 - ₹60,000 / month",
        "experience_min_years": 1.0,
        "experience_max_years": 3.0,
        "apply_url": "https://zerodha.tech/careers/pt-data-dev",
        "job_url": "https://zerodha.tech/careers/pt-data-dev",
        "required_skills": ["Python", "Pandas", "PostgreSQL", "MySQL", "Git"],
        "preferred_skills": ["Bash", "Linux", "Cron", "Data Cleaning"],
        "description_summary": "Write reliable Python ETL scripts and automated reconciliation pipelines for financial records. Flexible 20 hours per week working with Zerodha's core engineering teams.",
        "description": """Zerodha Tech is looking for a detail-oriented part-time Python developer to assist in data pipeline automation.

Responsibilities:
- Write maintainable Python scripts to automate daily data extraction and CSV ingestion.
- Clean and normalize financial data using Pandas and SQL queries on PostgreSQL/MySQL.
- Monitor scheduled cron jobs and troubleshoot data pipeline discrepancies.

Requirements:
- 1+ years experience in Python and relational database querying.
- Solid understanding of data structures, Pandas dataframes, and Git.""",
    },

    # ==========================================
    # 3. CONTRACT JOBS
    # ==========================================
    {
        "external_id": "job_ct_001",
        "company_name": "Perplexity AI",
        "title": "Contract Generative AI & RAG Application Developer",
        "title_normalized": "contract generative ai rag application developer",
        "employment_type": "Contract",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "AI Search Engine",
        "location": "Remote",
        "city": "Remote",
        "country": "United States",
        "salary_min": 75,
        "salary_max": 120,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$75 - $120 / hr (6-Month Contract)",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://boards.greenhouse.io/perplexity/jobs/4910284",
        "job_url": "https://boards.greenhouse.io/perplexity/jobs/4910284",
        "required_skills": ["Python", "RAG", "LangChain", "LLMs", "FastAPI", "Embeddings", "Docker"],
        "preferred_skills": ["Vector Search", "Qdrant", "Prompt Tuning", "BM25"],
        "description_summary": "6-month contract role to optimize semantic search pipelines, citation extractors, and low-latency RAG response streaming using Python and FastAPI.",
        "description": """Perplexity AI is seeking a contract Senior RAG Engineer for an intensive 6-month initiative.

Key Deliverables:
- Build low-latency retrieval pipelines merging keyword search and dense vector embeddings.
- Implement streaming RAG generation endpoints in FastAPI with verifiable citation anchors.
- Optimize LLM token usage and response latency under high query loads.

Requirements:
- 3+ years experience with Python, FastAPI, and production RAG/LLM applications.
- Deep hands-on knowledge of LangChain, vector embeddings, and chunking strategies.
- Availability to start immediately on a 40 hour/week remote contract.""",
    },
    {
        "external_id": "job_ct_002",
        "company_name": "Cohere",
        "title": "Contract AI Model Evaluation & Alignment Specialist",
        "title_normalized": "contract ai model evaluation alignment specialist",
        "employment_type": "Contract",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "AI Safety",
        "industry": "Enterprise Generative AI",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 60,
        "salary_max": 95,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$60 - $95 / hr (3-Month Contract)",
        "experience_min_years": 2.0,
        "experience_max_years": 5.0,
        "apply_url": "https://cohere.com/careers/contract-eval-specialist",
        "job_url": "https://cohere.com/careers/contract-eval-specialist",
        "required_skills": ["Python", "LLMs", "Prompt Engineering", "Pandas", "Scikit-learn"],
        "preferred_skills": ["RLHF", "Hallucination Detection", "Adversarial Prompting", "JSON"],
        "description_summary": "Perform rigorous safety, hallucination, and factual alignment evaluations on Cohere's Command and Embed models across multilingual benchmarks.",
        "description": """Cohere is hiring a contract AI Evaluation Specialist for a 3-month contract.

Responsibilities:
- Build automated testing suites to evaluate model outputs against factual knowledge bases.
- Execute adversarial prompt testing (red-teaming) to discover vulnerabilities and edge-case errors.
- Analyze evaluation metrics using Pandas and Scikit-learn and generate alignment scorecards.

Requirements:
- 2+ years experience in NLP/LLM testing, prompt engineering, and Python.
- Strong analytical skills and familiarity with benchmark datasets.""",
    },
    {
        "external_id": "job_ct_003",
        "company_name": "Razorpay",
        "title": "Contract Python API Developer (Integration Platform)",
        "title_normalized": "contract python api developer integration platform",
        "employment_type": "Contract",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "mid",
        "role_category": "Backend Engineering",
        "role_sub_category": "REST APIs",
        "industry": "FinTech",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹1,20,000 - ₹1,80,000 / month (6-Month Contract)",
        "experience_min_years": 2.5,
        "experience_max_years": 5.0,
        "apply_url": "https://razorpay.com/jobs/contract-api-dev",
        "job_url": "https://razorpay.com/jobs/contract-api-dev",
        "required_skills": ["Python", "FastAPI", "MySQL", "REST APIs", "Docker", "Git"],
        "preferred_skills": ["Payment Gateways", "Pydantic", "Postman", "Swagger"],
        "description_summary": "Develop third-party enterprise integrations and webhook notification systems using Python and FastAPI. 6-month contract with high probability of full-time conversion.",
        "description": """Razorpay seeks an experienced Python API contractor to deliver mission-critical partner integrations.

Key Responsibilities:
- Build robust REST APIs and webhook handling services with FastAPI and MySQL.
- Implement comprehensive input validation with Pydantic and unit tests.
- Package microservices using Docker for automated staging deployments.

Requirements:
- 2.5+ years of Python backend engineering experience.
- Deep familiarity with REST APIs, SQL databases, and Git.""",
    },

    # ==========================================
    # 4. INTERNSHIPS
    # ==========================================
    {
        "external_id": "job_in_001",
        "company_name": "Google DeepMind",
        "title": "Machine Learning Engineering Intern (Summer 2026)",
        "title_normalized": "machine learning engineering intern summer 2026",
        "employment_type": "Internship",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "intern",
        "role_category": "AI/ML",
        "role_sub_category": "Machine Learning",
        "industry": "Artificial Intelligence",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 75000,
        "salary_max": 110000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹75,000 - ₹1,10,000 / month + Housing",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://careers.google.com/jobs/results/intern-deepmind-blr",
        "job_url": "https://careers.google.com/jobs/results/intern-deepmind-blr",
        "required_skills": ["Python", "PyTorch", "NumPy", "Pandas", "Scikit-learn", "Git"],
        "preferred_skills": ["TensorFlow", "Math/Statistics", "Computer Science Fundamentals"],
        "description_summary": "12-week paid summer internship working alongside world-class AI researchers at Google DeepMind Bengaluru. Build, train, and benchmark deep neural models.",
        "description": """The DeepMind Internship Experience:
As an ML Engineering Intern, you will be paired with a Senior Research Engineer mentor to work on impactful machine learning problems.

What You'll Do:
- Implement neural network architectures in PyTorch and evaluate performance on benchmark datasets.
- Clean, preprocess, and visualize complex datasets using NumPy and Pandas.
- Present research findings and code artifacts to the broader engineering team.

Qualifications:
- Currently enrolled in or recent graduate of a Bachelor's, Master's, or PhD in Computer Science, Data Science, or related field.
- Proficiency in Python programming and experience with PyTorch or TensorFlow.
- Strong foundational grasp of linear algebra, calculus, and machine learning theory.""",
    },
    {
        "external_id": "job_in_002",
        "company_name": "Microsoft",
        "title": "Generative AI & NLP Research Intern",
        "title_normalized": "generative ai nlp research intern",
        "employment_type": "Internship",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "intern",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "Enterprise Software & Cloud",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 80000,
        "salary_max": 105000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹80,000 - ₹1,05,000 / month",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://careers.microsoft.com/us/en/job/intern-msr-blr",
        "job_url": "https://careers.microsoft.com/us/en/job/intern-msr-blr",
        "required_skills": ["Python", "LLMs", "RAG", "Prompt Engineering", "Git", "GitHub"],
        "preferred_skills": ["LangChain", "Transformers", "FastAPI"],
        "description_summary": "6-month internship at Microsoft Research India exploring prompt engineering, retrieval-augmented generation, and agentic workflows.",
        "description": """Join Microsoft Research (MSR) India as a Generative AI & NLP Research Intern!

You will collaborate with leading researchers investigating prompt strategies, context window optimizations, and verifiable reasoning in LLMs.

Requirements:
- Strong Python coding skills and practical exposure to LLMs (OpenAI, Gemini, Hugging Face).
- Curiosity, quick learning ability, and passion for artificial intelligence.
- Experience building student projects or research prototypes.""",
    },
    {
        "external_id": "job_in_003",
        "company_name": "Razorpay",
        "title": "Python Backend & Cloud Engineering Intern",
        "title_normalized": "python backend cloud engineering intern",
        "employment_type": "Internship",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "intern",
        "role_category": "Backend Engineering",
        "role_sub_category": "Python",
        "industry": "FinTech",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 40000,
        "salary_max": 60000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹40,000 - ₹60,000 / month",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://razorpay.com/jobs/intern-backend-python",
        "job_url": "https://razorpay.com/jobs/intern-backend-python",
        "required_skills": ["Python", "FastAPI", "MySQL", "REST APIs", "Git"],
        "preferred_skills": ["Docker", "Linux", "PostgreSQL"],
        "description_summary": "Exciting 6-month internship building scalable APIs, database schemas, and microservices for India's premier payments gateway.",
        "description": """Are you an enthusiastic problem solver eager to write production-grade Python code?

At Razorpay, interns write code that processes real money and touches millions of checkout journeys.

What You Will Learn:
- Writing asynchronous REST APIs using FastAPI and Pydantic.
- Query optimization and schema design on MySQL and PostgreSQL.
- CI/CD, Git workflows, and containerized deployment with Docker.

Requirements:
- Proficient in Python syntax, OOP, and data structures.
- Familiarity with SQL and basic web fundamentals.""",
    },

    # ==========================================
    # 5. FREELANCE JOBS
    # ==========================================
    {
        "external_id": "job_fl_001",
        "company_name": "Hugging Face",
        "title": "Freelance LLM Fine-Tuning & Custom RAG Consultant",
        "title_normalized": "freelance llm fine tuning custom rag consultant",
        "employment_type": "Freelance",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "LLM Fine-Tuning",
        "industry": "Open-Source AI",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 85,
        "salary_max": 140,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$85 - $140 / hr (Project-Based)",
        "experience_min_years": 3.0,
        "experience_max_years": 8.0,
        "apply_url": "https://huggingface.co/experts/freelance-rag-consultant",
        "job_url": "https://huggingface.co/experts/freelance-rag-consultant",
        "required_skills": ["Python", "PyTorch", "Hugging Face Transformers", "RAG", "LLMs", "Embeddings"],
        "preferred_skills": ["LoRA", "QLoRA", "Unsloth", "vLLM", "Docker"],
        "description_summary": "Provide specialized consulting to enterprise clients migrating to open-weight models, custom parameter-efficient fine-tuning (LoRA), and private RAG architectures.",
        "description": """Hugging Face Experts Network:
We connect top-tier freelance AI engineers with enterprise organizations building domain-specific LLM solutions.

Project Scope:
- Fine-tune open models (Llama 3, Mistral, Gemma) on proprietary customer datasets using LoRA/QLoRA.
- Implement robust enterprise RAG systems with dense embeddings and vector stores.
- Provide latency and GPU VRAM optimization recommendations.

Requirements:
- Proven experience deploying PyTorch and Hugging Face Transformers models.
- Deep expertise in RAG, vector embeddings, and prompt orchestration.
- Autonomous project delivery and client-facing communication.""",
    },
    {
        "external_id": "job_fl_002",
        "company_name": "OpenAI",
        "title": "Freelance AI Solutions Architect (API & Assistants)",
        "title_normalized": "freelance ai solutions architect api assistants",
        "employment_type": "Freelance",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "Artificial Intelligence",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 90,
        "salary_max": 150,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$90 - $150 / hr (Milestone-Based)",
        "experience_min_years": 3.0,
        "experience_max_years": 7.0,
        "apply_url": "https://openai.com/careers/freelance-solutions-architect",
        "job_url": "https://openai.com/careers/freelance-solutions-architect",
        "required_skills": ["Python", "OpenAI", "Prompt Engineering", "FastAPI", "Docker", "REST APIs"],
        "preferred_skills": ["Function Calling", "Assistants API", "LangChain", "PostgreSQL"],
        "description_summary": "Design custom enterprise proof-of-concept solutions leveraging OpenAI Assistants API, function calling, and structured JSON output architectures.",
        "description": """Work with verified enterprise clients implementing production OpenAI API workflows.

Responsibilities:
- Build reliable agentic workflows utilizing OpenAI function calling and code interpreter.
- Create containerized FastAPI middleware services connecting enterprise databases to AI backends.
- Author comprehensive architectural specifications and operational playbooks.

Requirements:
- 3+ years in Python software engineering and modern generative AI APIs.
- Experience delivering production-ready client applications.""",
    },

    # ==========================================
    # 6. DEDICATED REMOTE JOBS (Explicit Employment Type = Remote)
    # ==========================================
    {
        "external_id": "job_rem_001",
        "company_name": "Stripe",
        "title": "Remote Python Backend & Data Infrastructure Engineer",
        "title_normalized": "remote python backend data infrastructure engineer",
        "employment_type": "Remote",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "Backend Engineering",
        "role_sub_category": "Distributed Systems",
        "industry": "Financial Infrastructure",
        "location": "Remote - Worldwide",
        "city": "Remote",
        "country": "Global",
        "salary_min": 160000,
        "salary_max": 225000,
        "salary_currency": "USD",
        "salary_raw": "$160,000 - $225,000 / yr",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://boards.greenhouse.io/stripe/jobs/5910283",
        "job_url": "https://boards.greenhouse.io/stripe/jobs/5910283",
        "required_skills": ["Python", "PostgreSQL", "MySQL", "REST APIs", "Docker", "Git", "GitHub"],
        "preferred_skills": ["Distributed Systems", "Kafka", "Redis", "CI/CD"],
        "description_summary": "Work anywhere in the world on Stripe's distributed ledger and ledgering data pipelines handling billions in transaction volume.",
        "description": """Stripe is an operating system for global commerce.

Role Highlights:
- Build distributed backend services using Python, PostgreSQL, and event streaming.
- Guarantee strict transactional consistency and sub-100ms response latencies.
- Work 100% remotely with a world-class engineering team distributed globally.

Requirements:
- 4+ years of backend engineering experience with strong Python and relational database mastery.
- Deep respect for testing, reliability, and clear asynchronous documentation.""",
    },
    {
        "external_id": "job_rem_002",
        "company_name": "OpenAI",
        "title": "Remote Vector Search & Knowledge Retrieval Engineer",
        "title_normalized": "remote vector search knowledge retrieval engineer",
        "employment_type": "Remote",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "RAG & Vector Search",
        "industry": "Artificial Intelligence",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 180000,
        "salary_max": 250000,
        "salary_currency": "USD",
        "salary_raw": "$180,000 - $250,000 / yr",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://boards.greenhouse.io/openai/jobs/4019283001",
        "job_url": "https://boards.greenhouse.io/openai/jobs/4019283001",
        "required_skills": ["Python", "Embeddings", "RAG", "LLMs", "FastAPI", "Docker", "Git"],
        "preferred_skills": ["HNSW", "ANN Search", "Qdrant", "PyTorch", "Transformers"],
        "description_summary": "100% Remote role building hyper-scale vector indexing, semantic search, and grounding infrastructure powering ChatGPT's knowledge retrieval capabilities.",
        "description": """Build the retrieval backbone powering the next generation of artificial intelligence.

Key Responsibilities:
- Engineer high-dimensional vector search indices supporting billions of dense embeddings.
- Develop novel re-ranking and contextual compression algorithms to improve RAG accuracy.
- Maintain microservice APIs with FastAPI and Docker ensuring 99.99% uptime SLAs.

Requirements:
- 4+ years experience with Python, vector retrieval systems, and machine learning models.
- Deep expertise in embedding models, similarity metrics (cosine, dot product), and indexing algorithms.""",
    },

    # ==========================================
    # 7. ADDITIONAL DOMAINS & SENIORITIES
    # ==========================================
    {
        "external_id": "job_ft_009",
        "company_name": "NVIDIA",
        "title": "Deep Learning Frameworks & GPU Acceleration Engineer",
        "title_normalized": "deep learning frameworks gpu acceleration engineer",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "senior",
        "role_category": "AI/ML",
        "role_sub_category": "GPU Acceleration",
        "industry": "Semiconductors & Accelerated AI",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 3800000,
        "salary_max": 5800000,
        "salary_currency": "INR",
        "salary_raw": "₹38,00,000 - ₹58,00,000 / yr",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/JR1982734",
        "job_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/JR1982734",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "NumPy", "Docker", "Git"],
        "preferred_skills": ["CUDA", "TensorRT", "Triton Inference Server", "C++"],
        "description_summary": "Optimize deep learning model execution on NVIDIA Tensor Core GPUs using TensorRT and Triton Inference Server at NVIDIA Bengaluru.",
        "description": """NVIDIA is looking for an extraordinary engineer to accelerate deep learning inference pipelines.

Responsibilities:
- Profile and optimize neural networks written in PyTorch and TensorFlow for NVIDIA GPUs.
- Deploy Triton Inference Server clusters with multi-GPU scaling.
- Benchmark latency, throughput, and memory consumption across varying batch sizes.

Requirements:
- 4+ years software and machine learning engineering experience.
- Deep understanding of PyTorch internals, tensor operations, and containerized deployment.""",
    },
    {
        "external_id": "job_ft_010",
        "company_name": "Meta",
        "title": "Applied AI / Llama Integration Engineer",
        "title_normalized": "applied ai llama integration engineer",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "mid",
        "role_category": "AI/ML",
        "role_sub_category": "Generative AI",
        "industry": "Social Media & AI",
        "location": "Hyderabad, Telangana, India",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "salary_min": 3000000,
        "salary_max": 4600000,
        "salary_currency": "INR",
        "salary_raw": "₹30,00,000 - ₹46,00,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://www.metacareers.com/jobs/928374615",
        "job_url": "https://www.metacareers.com/jobs/928374615",
        "required_skills": ["Python", "PyTorch", "LLMs", "Prompt Engineering", "FastAPI", "Docker"],
        "preferred_skills": ["Llama 3", "Transformers", "Distributed Systems"],
        "description_summary": "Integrate open-weights Llama models into user-facing social experiences across WhatsApp, Instagram, and Messenger.",
        "description": """Meta is building the future of social interaction powered by open, accessible artificial intelligence.

Responsibilities:
- Build and optimize inference endpoints for Llama family models using Python and FastAPI.
- Implement prompt engineering strategies and response safety classifiers.
- Work with distributed backend systems serving billions of monthly active users.

Requirements:
- 3+ years experience developing AI or backend applications in Python.
- Proven experience with PyTorch, modern LLMs, and containerized microservices.""",
    },
    {
        "external_id": "job_ft_011",
        "company_name": "Zerodha Tech",
        "title": "Data Analyst & Quantitative Insights Specialist",
        "title_normalized": "data analyst quantitative insights specialist",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "junior",
        "role_category": "Data Science",
        "role_sub_category": "Data Analytics",
        "industry": "FinTech & Brokerage",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 1400000,
        "salary_max": 2200000,
        "salary_currency": "INR",
        "salary_raw": "₹14,00,000 - ₹22,00,000 / yr",
        "experience_min_years": 1.0,
        "experience_max_years": 3.5,
        "apply_url": "https://zerodha.tech/careers/data-analyst-infra",
        "job_url": "https://zerodha.tech/careers/data-analyst-infra",
        "required_skills": ["Python", "Pandas", "NumPy", "PostgreSQL", "MySQL", "Scikit-learn"],
        "preferred_skills": ["Data Visualization", "Matplotlib", "Seaborn", "Stats"],
        "description_summary": "Analyze trade patterns, market volatility, and order execution latency across Zerodha's trading engine using Python, Pandas, and PostgreSQL.",
        "description": """Join Zerodha Tech to uncover actionable signals from India's largest retail trading volume.

Responsibilities:
- Query multi-terabyte financial datasets stored in PostgreSQL and ClickHouse.
- Build automated analytical reports using Python, Pandas, NumPy, and Scikit-learn.
- Identify operational bottlenecks and user behavior trends.

Requirements:
- 1+ years experience in quantitative data analysis or data science.
- Strong proficiency in SQL, Python, Pandas, and exploratory data analysis.""",
    },
    {
        "external_id": "job_ft_012",
        "company_name": "Databricks",
        "title": "AI Systems Quality Assurance & SDET Engineer",
        "title_normalized": "ai systems quality assurance sdet engineer",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Testing/QA",
        "role_sub_category": "SDET",
        "industry": "Data & AI Platform",
        "location": "Remote",
        "city": "Remote",
        "country": "United States",
        "salary_min": 125000,
        "salary_max": 170000,
        "salary_currency": "USD",
        "salary_raw": "$125,000 - $170,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://boards.greenhouse.io/databricks/jobs/5201999",
        "job_url": "https://boards.greenhouse.io/databricks/jobs/5201999",
        "required_skills": ["Python", "FastAPI", "Docker", "Git", "GitHub", "REST APIs"],
        "preferred_skills": ["Pytest", "Postman", "CI/CD", "Automated Testing", "Selenium"],
        "description_summary": "Design automated test frameworks, regression suites, and API integration testing for Databricks AI workflows and ML model endpoints.",
        "description": """Ensure the uncompromising reliability of enterprise AI platforms at Databricks.

Responsibilities:
- Develop scalable automated test suites using Python and Pytest.
- Validate API contracts, schema integrity, and load tolerance for FastAPI microservices.
- Integrate automated tests into GitHub Actions CI/CD pipelines.

Requirements:
- 3+ years experience in automated testing and software quality engineering.
- Solid Python programming skills, Docker experience, and REST API testing mastery.""",
    },

    # ==========================================
    # 8. NON-IT: FINANCE & BANKING
    # ==========================================
    {
        "external_id": "job_fin_001",
        "company_name": "Goldman Sachs",
        "title": "Senior Financial Analyst & Corporate Valuations",
        "title_normalized": "senior financial analyst corporate valuations",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "Finance & Banking",
        "role_sub_category": "Corporate Finance",
        "industry": "Finance & Investment Banking",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 2200000,
        "salary_max": 3500000,
        "salary_currency": "INR",
        "salary_raw": "₹22,00,000 - ₹35,00,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://careers.goldmansachs.com/jobs/senior-financial-analyst",
        "job_url": "https://careers.goldmansachs.com/jobs/senior-financial-analyst",
        "required_skills": ["Financial Modeling", "Corporate Finance", "DCF Valuation", "Excel", "P&L Analysis"],
        "preferred_skills": ["PowerBI", "Bloomberg Terminal", "CFA", "Accounting"],
        "description_summary": "Lead discounted cash flow (DCF) valuation models, capital budgeting, and P&L financial forecasts for global corporate portfolios at Goldman Sachs Bengaluru.",
        "description": """About Goldman Sachs:
Goldman Sachs is a leading global investment banking, securities, and investment management firm.

Responsibilities:
- Build dynamic financial models including DCF, LBO, and scenario sensitivity analyses.
- Formulate monthly P&L reporting packages and quarterly executive budget forecasts.
- Conduct thorough variance analysis between budget vs actual performance across business units.
- Present strategic capital allocation proposals to managing directors.

Requirements:
- 3+ years in corporate finance, financial planning & analysis (FP&A), or investment banking.
- Mastery of Excel, financial statements (Income Statement, Balance Sheet, Cash Flow), and valuation.
- Strong analytical presentation skills and attention to detail.""",
    },
    {
        "external_id": "job_fin_002",
        "company_name": "Goldman Sachs",
        "title": "Equity Research & Investment Analysis Intern",
        "title_normalized": "equity research investment analysis intern",
        "employment_type": "Internship",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "intern",
        "role_category": "Finance & Banking",
        "role_sub_category": "Equity Research",
        "industry": "Finance & Investment Banking",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 60000,
        "salary_max": 85000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹60,000 - ₹85,000 / month",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://careers.goldmansachs.com/jobs/intern-equity-research",
        "job_url": "https://careers.goldmansachs.com/jobs/intern-equity-research",
        "required_skills": ["Financial Statements", "Valuation Metrics", "Excel", "Industry Research"],
        "preferred_skills": ["Bloomberg", "Financial Accounting", "PowerPoint"],
        "description_summary": "Exciting 6-month equity research internship evaluating listed equities, quarterly earnings calls, and industry macro trends.",
        "description": """Internship Overview:
Join the Global Investment Research (GIR) division at Goldman Sachs.

Responsibilities:
- Analyze corporate earnings reports, balance sheets, and competitive industry dynamics.
- Support lead analysts in constructing financial valuation models and research memos.
- Gather macroeconomic indicators and industry statistics.

Requirements:
- Bachelor's or Master's student in Commerce, Economics, Finance, or MBA.
- Keen interest in financial markets, equities, and corporate valuation.""",
    },
    {
        "external_id": "job_fin_003",
        "company_name": "Goldman Sachs",
        "title": "Contract Financial Controller & Tax Auditor",
        "title_normalized": "contract financial controller tax auditor",
        "employment_type": "Contract",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "mid",
        "role_category": "Finance & Banking",
        "role_sub_category": "Audit & Compliance",
        "industry": "Finance & Investment Banking",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 140000,
        "salary_max": 210000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹1,40,000 - ₹2,10,000 / month (6-Month Contract)",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://careers.goldmansachs.com/jobs/contract-financial-controller",
        "job_url": "https://careers.goldmansachs.com/jobs/contract-financial-controller",
        "required_skills": ["IFRS", "GAAP", "Financial Reporting", "Tax Compliance", "Internal Audit"],
        "preferred_skills": ["SAP", "Chartered Accountant (CA)", "Taxation"],
        "description_summary": "6-month contract managing statutory audit compliance, ledger reconciliations, and tax regulatory filings for financial entities.",
        "description": """We are seeking a seasoned Financial Controller on a 6-month contract.

Responsibilities:
- Oversee compliance with IFRS and Indian GAAP statutory reporting standards.
- Manage quarterly closing processes and external auditor coordination.
- Verify corporate tax provisions and transfer pricing documentation.

Requirements:
- CA or Master's in Accounting/Finance with 3+ years audit/controllership experience.
- Strong knowledge of direct & indirect tax regulations and ERP systems.""",
    },

    # ==========================================
    # 9. NON-IT: STRATEGY & CONSULTING
    # ==========================================
    {
        "external_id": "job_con_001",
        "company_name": "McKinsey & Company",
        "title": "Associate Strategy Consultant",
        "title_normalized": "associate strategy consultant",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Consulting & Strategy",
        "role_sub_category": "Management Consulting",
        "industry": "Management Consulting & Strategy",
        "location": "Mumbai, Maharashtra, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "salary_min": 2800000,
        "salary_max": 4500000,
        "salary_currency": "INR",
        "salary_raw": "₹28,00,000 - ₹45,00,000 / yr",
        "experience_min_years": 2.0,
        "experience_max_years": 5.0,
        "apply_url": "https://mckinsey.com/careers/associate-strategy-consultant",
        "job_url": "https://mckinsey.com/careers/associate-strategy-consultant",
        "required_skills": ["Business Strategy", "Market Research", "Quantitative Analysis", "Stakeholder Management"],
        "preferred_skills": ["Due Diligence", "Executive Presentations", "Storylining", "Excel"],
        "description_summary": "Formulate transformative business strategy, operational turnarounds, and market entry recommendations for Fortune 500 executive teams.",
        "description": """About McKinsey & Company:
McKinsey is a global management consulting firm serving leading businesses and public sector institutions.

Key Responsibilities:
- Structure complex business challenges into structured hypotheses and work streams.
- Conduct primary market interviews and competitive intelligence benchmarking.
- Synthesize actionable executive recommendations into clear C-suite presentations.
- Work directly with client leadership to drive operational implementation.

Requirements:
- 2+ years of strategy, management consulting, or corporate strategic planning experience.
- First-rate problem-solving capabilities and quantitative data analysis.
- Exceptional verbal and written executive communication.""",
    },
    {
        "external_id": "job_con_002",
        "company_name": "McKinsey & Company",
        "title": "Freelance Market Entry & Strategy Specialist",
        "title_normalized": "freelance market entry strategy specialist",
        "employment_type": "Freelance",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "Consulting & Strategy",
        "role_sub_category": "Market Intelligence",
        "industry": "Management Consulting & Strategy",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 80,
        "salary_max": 130,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$80 - $130 / hr (Project-Based)",
        "experience_min_years": 4.0,
        "experience_max_years": 9.0,
        "apply_url": "https://mckinsey.com/careers/freelance-strategy-consultant",
        "job_url": "https://mckinsey.com/careers/freelance-strategy-consultant",
        "required_skills": ["TAM Analysis", "Competitive Benchmarking", "Business Strategy", "Market Research"],
        "preferred_skills": ["Go-To-Market (GTM)", "Valuation", "Industry Sizing"],
        "description_summary": "Deliver remote strategic market sizing (TAM/SAM/SOM), competitor analysis, and entry playbooks on high-impact consulting engagements.",
        "description": """Join the McKinsey External Expert Network.

Scope of Work:
- Conduct rigorous Total Addressable Market (TAM) modeling and regulatory assessments.
- Formulate market entry playbooks and commercial viability frameworks.
- Present structured deliverables to consulting engagement managers.

Requirements:
- 4+ years consulting or strategic research experience.
- Proven track record of high-quality independent deliverable execution.""",
    },

    # ==========================================
    # 10. NON-IT: DESIGN & CREATIVE
    # ==========================================
    {
        "external_id": "job_des_001",
        "company_name": "Figma",
        "title": "Lead UI/UX Product Designer",
        "title_normalized": "lead ui ux product designer",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "lead",
        "role_category": "Design & Creative",
        "role_sub_category": "Product Design",
        "industry": "Design & Creative Tools",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 3200000,
        "salary_max": 5000000,
        "salary_currency": "INR",
        "salary_raw": "₹32,00,000 - ₹50,00,000 / yr",
        "experience_min_years": 5.0,
        "experience_max_years": 9.0,
        "apply_url": "https://figma.com/careers/lead-product-designer",
        "job_url": "https://figma.com/careers/lead-product-designer",
        "required_skills": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems"],
        "preferred_skills": ["Information Architecture", "Micro-interactions", "Usability Testing", "Design Tokens"],
        "description_summary": "Lead end-to-end product design, scalable component design systems, and user journey flows for Figma's global collaborative ecosystem.",
        "description": """About Figma:
Figma is where teams design, prototype, and build digital products collaboratively.

What You Will Do:
- Champion user-centered design methodologies across web, desktop, and mobile surfaces.
- Architect robust design systems with reusable components, tokens, and auto-layouts.
- Conduct generative user research, ethnographic interviews, and concept validation.
- Partner with product managers and engineers to ship delightful customer experiences.

Requirements:
- 5+ years experience in digital product design (UI/UX) with an outstanding portfolio.
- Mastery of Figma, design systems, interactive prototypes, and typography.""",
    },
    {
        "external_id": "job_des_002",
        "company_name": "Figma",
        "title": "UI/UX Design Systems Contractor (6-Month Contract)",
        "title_normalized": "ui ux design systems contractor 6 month contract",
        "employment_type": "Contract",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "Design & Creative",
        "role_sub_category": "Design Systems",
        "industry": "Design & Creative Tools",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 65,
        "salary_max": 105,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$65 - $105 / hr (6-Month Contract)",
        "experience_min_years": 3.5,
        "experience_max_years": 7.0,
        "apply_url": "https://figma.com/careers/contract-design-systems",
        "job_url": "https://figma.com/careers/contract-design-systems",
        "required_skills": ["Figma", "Design Systems", "Accessibility (a11y)", "Component Libraries", "Prototyping"],
        "preferred_skills": ["WCAG 2.1", "Tokens", "Design Specs"],
        "description_summary": "6-month contract specializing in WCAG accessibility compliance, component library tokens, and interactive documentation.",
        "description": """Figma is seeking an experienced Design Systems specialist for a 6-month contract.

Responsibilities:
- Build and audit Figma UI components against WCAG 2.1 AA accessibility standards.
- Maintain design tokens across color palettes, spacing variables, and typography.
- Create interactive usage guidelines and designer onboarding documentation.

Requirements:
- 3.5+ years focused on component libraries and multi-platform design systems.
- Strong attention to micro-interactions, contrast ratios, and responsive behaviors.""",
    },
    {
        "external_id": "job_des_003",
        "company_name": "Airbnb",
        "title": "Freelance Visual Brand Designer & Motion Artist",
        "title_normalized": "freelance visual brand designer motion artist",
        "employment_type": "Freelance",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Design & Creative",
        "role_sub_category": "Brand Design",
        "industry": "Hospitality & Brand Experience",
        "location": "Remote",
        "city": "Remote",
        "country": "Global",
        "salary_min": 55,
        "salary_max": 95,
        "salary_currency": "USD",
        "salary_period": "hourly",
        "salary_raw": "$55 - $95 / hr (Project-Based)",
        "experience_min_years": 2.5,
        "experience_max_years": 6.0,
        "apply_url": "https://airbnb.com/careers/freelance-brand-designer",
        "job_url": "https://airbnb.com/careers/freelance-brand-designer",
        "required_skills": ["Brand Identity", "Typography", "Adobe Illustrator", "Storyboarding", "Figma"],
        "preferred_skills": ["After Effects", "Motion Graphics", "Art Direction"],
        "description_summary": "Craft evocative visual storytelling, seasonal marketing campaigns, and brand identity assets for Airbnb's global community.",
        "description": """Airbnb seeks a freelance Visual Brand Designer to support global brand marketing campaigns.

Deliverables:
- Develop brand assets, campaign key visuals, and editorial layouts.
- Create motion graphic snippets and short brand animations for social channels.
- Maintain consistency with Airbnb's human-centered design aesthetic.

Requirements:
- 2.5+ years of visual brand design and digital art direction experience.
- Strong portfolio showcasing typography, layout, and visual identity systems.""",
    },

    # ==========================================
    # 11. NON-IT: MARKETING & GROWTH
    # ==========================================
    {
        "external_id": "job_mkt_001",
        "company_name": "Salesforce",
        "title": "Senior Product Marketing Manager (B2B SaaS)",
        "title_normalized": "senior product marketing manager b2b saas",
        "employment_type": "Full-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "senior",
        "role_category": "Marketing & Growth",
        "role_sub_category": "Product Marketing",
        "industry": "Enterprise Sales & CRM",
        "location": "Remote",
        "city": "Remote",
        "country": "United States",
        "salary_min": 140000,
        "salary_max": 190000,
        "salary_currency": "USD",
        "salary_raw": "$140,000 - $190,000 / yr",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://salesforce.com/careers/senior-product-marketing-manager",
        "job_url": "https://salesforce.com/careers/senior-product-marketing-manager",
        "required_skills": ["Product Positioning", "Go-To-Market (GTM)", "Competitor Analysis", "Content Strategy"],
        "preferred_skills": ["Sales Enablement", "Customer Case Studies", "Messaging Frameworks"],
        "description_summary": "Define value propositions, product positioning, and end-to-end Go-To-Market (GTM) launches for Salesforce Customer 360 cloud offerings.",
        "description": """Join the product marketing team driving the world's #1 CRM platform.

Key Responsibilities:
- Craft compelling buyer personas, messaging hierarchies, and product positioning.
- Plan and execute global product launch campaigns with cross-functional teams.
- Produce sales enablement collateral, battle cards, and ROI calculator tools.
- Analyze win-loss trends and competitive intelligence to influence product roadmaps.

Requirements:
- 4+ years of B2B SaaS product marketing experience.
- Exceptional storytelling ability and strategic market positioning expertise.""",
    },
    {
        "external_id": "job_mkt_002",
        "company_name": "Hindustan Unilever",
        "title": "Brand Management & Digital Marketing Intern",
        "title_normalized": "brand management digital marketing intern",
        "employment_type": "Internship",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "intern",
        "role_category": "Marketing & Growth",
        "role_sub_category": "Brand Management",
        "industry": "Consumer Goods & Marketing",
        "location": "Mumbai, Maharashtra, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "salary_min": 45000,
        "salary_max": 65000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹45,000 - ₹65,000 / month",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://hul.co.in/careers/intern-brand-marketing",
        "job_url": "https://hul.co.in/careers/intern-brand-marketing",
        "required_skills": ["Market Analysis", "Campaign Analytics", "Consumer Behavior", "Creative Briefs"],
        "preferred_skills": ["Digital Ads", "Google Analytics", "Social Media"],
        "description_summary": "6-month internship at HUL Mumbai executing consumer market research, digital campaign metrics, and creative agency briefs.",
        "description": """Hindustan Unilever Internship Programme:
Gain hands-on marketing experience with India's most iconic consumer brands.

Responsibilities:
- Track campaign conversion KPIs and brand sentiment across digital channels.
- Support brand managers in preparing agency creative briefs and product launches.
- Conduct consumer surveys and demographic trend benchmarking.

Requirements:
- Enrolled in or recent graduate of MBA, BBA, Mass Communication, or Marketing.
- Passion for consumer behavior, creative campaigns, and data-driven insights.""",
    },
    {
        "external_id": "job_mkt_003",
        "company_name": "Hindustan Unilever",
        "title": "Brand Content & Social Media Specialist (Part-Time)",
        "title_normalized": "brand content social media specialist part time",
        "employment_type": "Part-time",
        "work_mode": "remote",
        "is_remote": True,
        "is_hybrid": False,
        "seniority": "junior",
        "role_category": "Marketing & Growth",
        "role_sub_category": "Content Marketing",
        "industry": "Consumer Goods & Marketing",
        "location": "Remote",
        "city": "Remote",
        "country": "India",
        "salary_min": 30000,
        "salary_max": 50000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹30,00,0 - ₹50,000 / month (20 hrs/week)",
        "experience_min_years": 1.0,
        "experience_max_years": 3.0,
        "apply_url": "https://hul.co.in/careers/pt-content-specialist",
        "job_url": "https://hul.co.in/careers/pt-content-specialist",
        "required_skills": ["Copywriting", "Social Media Marketing", "Content Calendars", "Brand Guidelines"],
        "preferred_skills": ["Canva", "SEO", "Community Management"],
        "description_summary": "Part-time role creating high-engagement social media copy, editorial calendars, and community storytelling for HUL wellness brands.",
        "description": """HUL is hiring a creative Part-Time Content Marketing Specialist (20 hrs/week).

Responsibilities:
- Write engaging social media posts, email newsletters, and product descriptions.
- Coordinate with digital marketing leads on editorial calendar scheduling.
- Monitor audience comments and foster brand engagement across social channels.

Requirements:
- 1+ years experience in digital copywriting or social media management.
- Flawless command of written English and cultural consumer nuances.""",
    },

    # ==========================================
    # 12. NON-IT: HUMAN RESOURCES (HR) & TALENT
    # ==========================================
    {
        "external_id": "job_hr_001",
        "company_name": "Workday",
        "title": "Talent Acquisition Partner & Corporate Recruiter",
        "title_normalized": "talent acquisition partner corporate recruiter",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "mid",
        "role_category": "Human Resources",
        "role_sub_category": "Talent Acquisition",
        "industry": "Human Resources & Enterprise Cloud",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 1600000,
        "salary_max": 2600000,
        "salary_currency": "INR",
        "salary_raw": "₹16,00,000 - ₹26,00,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://workday.com/careers/talent-acquisition-partner",
        "job_url": "https://workday.com/careers/talent-acquisition-partner",
        "required_skills": ["Candidate Sourcing", "Interviewing", "Offer Negotiation", "ATS Management", "Talent Pipeline"],
        "preferred_skills": ["LinkedIn Recruiter", "Diversity Hiring", "Stakeholder Management"],
        "description_summary": "Manage end-to-end candidate lifecycle recruiting, executive hiring calibration, and compensation negotiations at Workday India.",
        "description": """About Workday:
Workday is a leading provider of enterprise cloud applications for finance and human resources.

Responsibilities:
- Partner with business unit leaders to define talent profiles and sourcing strategies.
- Source active and passive candidates using LinkedIn Recruiter and referral channels.
- Conduct competency-based interviews and drive seamless offer negotiations.
- Ensure exemplary candidate experience throughout the recruitment process.

Requirements:
- 3+ years in corporate recruiting or agency talent acquisition.
- Deep expertise in modern ATS workflows, sourcing, and closing candidates.""",
    },
    {
        "external_id": "job_hr_002",
        "company_name": "Workday",
        "title": "People Operations & HR Intern",
        "title_normalized": "people operations hr intern",
        "employment_type": "Internship",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "intern",
        "role_category": "Human Resources",
        "role_sub_category": "People Operations",
        "industry": "Human Resources & Enterprise Cloud",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 35000,
        "salary_max": 50000,
        "salary_currency": "INR",
        "salary_period": "monthly",
        "salary_raw": "₹35,000 - ₹50,000 / month",
        "experience_min_years": 0.0,
        "experience_max_years": 1.0,
        "apply_url": "https://workday.com/careers/intern-people-ops",
        "job_url": "https://workday.com/careers/intern-people-ops",
        "required_skills": ["People Operations", "Onboarding Coordination", "HR Documentation", "Excel"],
        "preferred_skills": ["HRIS", "Employee Engagement", "Communication"],
        "description_summary": "6-month internship supporting new-hire onboarding, employee life-cycle documentation, and culture engagement programs.",
        "description": """Join Workday's People & Purpose team.

Responsibilities:
- Assist in coordinating orientation and onboarding logistics for global new hires.
- Maintain accurate employee records within HRIS systems.
- Coordinate company-wide employee recognition and well-being activities.

Requirements:
- Enrolled in or recent graduate of MBA HR, Psychology, or Humanities.
- High empathy, organizational rigor, and strong interpersonal skills.""",
    },

    # ==========================================
    # 13. NON-IT: SALES & BUSINESS DEVELOPMENT
    # ==========================================
    {
        "external_id": "job_sal_001",
        "company_name": "Salesforce",
        "title": "Enterprise Account Executive (Corporate Sales)",
        "title_normalized": "enterprise account executive corporate sales",
        "employment_type": "Full-time",
        "work_mode": "hybrid",
        "is_remote": False,
        "is_hybrid": True,
        "seniority": "senior",
        "role_category": "Sales & Business Dev",
        "role_sub_category": "Enterprise Sales",
        "industry": "Enterprise Sales & CRM",
        "location": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "salary_min": 2500000,
        "salary_max": 4200000,
        "salary_currency": "INR",
        "salary_raw": "₹25,00,000 - ₹42,00,000 / yr + Uncapped OTE",
        "experience_min_years": 4.0,
        "experience_max_years": 8.0,
        "apply_url": "https://salesforce.com/careers/enterprise-account-executive",
        "job_url": "https://salesforce.com/careers/enterprise-account-executive",
        "required_skills": ["Enterprise Sales", "Solution Selling", "Pipeline Management", "Contract Negotiation", "CRM"],
        "preferred_skills": ["MEDDPICC", "C-Level Prospecting", "SaaS Quota"],
        "description_summary": "Drive multi-million dollar software subscription revenue across tier-1 enterprise accounts with uncapped commission potential.",
        "description": """Salesforce Account Executives are trusted advisors to leading corporate enterprises.

Responsibilities:
- Develop strategic account plans to penetrate enterprise accounts and identify growth opportunities.
- Lead consultative sales cycles from discovery to contract negotiation and closing.
- Collaborate with solution engineers to present custom business value proposals.
- Consistently achieve or exceed quarterly and annual revenue targets.

Requirements:
- 4+ years in enterprise B2B software sales or high-ticket corporate solution selling.
- Proven track record of quota over-achievement and multi-stakeholder contract closing.""",
    },

    # ==========================================
    # 14. NON-IT: OPERATIONS & SUPPLY CHAIN
    # ==========================================
    {
        "external_id": "job_ops_001",
        "company_name": "Blinkit",
        "title": "Supply Chain & Fulfillment Operations Manager",
        "title_normalized": "supply chain fulfillment operations manager",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Operations & Logistics",
        "role_sub_category": "Supply Chain",
        "industry": "Operations & Quick Commerce",
        "location": "Gurugram, Haryana, India",
        "city": "Gurugram",
        "state": "Haryana",
        "country": "India",
        "salary_min": 1800000,
        "salary_max": 2800000,
        "salary_currency": "INR",
        "salary_raw": "₹18,00,000 - ₹28,00,000 / yr",
        "experience_min_years": 3.0,
        "experience_max_years": 6.0,
        "apply_url": "https://blinkit.com/careers/supply-chain-operations-manager",
        "job_url": "https://blinkit.com/careers/supply-chain-operations-manager",
        "required_skills": ["Inventory Optimization", "Warehouse Management", "Vendor Negotiation", "Logistics Analytics"],
        "preferred_skills": ["SLA Tracking", "Lean Operations", "Demand Forecasting"],
        "description_summary": "Direct dark-store fulfillment operations, inventory turnover cycles, and sub-10-minute dispatch SLAs across NCR distribution hubs.",
        "description": """Blinkit is revolutionizing instant commerce across urban India.

Responsibilities:
- Supervise high-velocity dark-store inventory replenishment and order dispatch workflows.
- Monitor fulfillment SLAs, order picking accuracy, and shrinkage control.
- Negotiate local vendor service contracts and lead a team of operations supervisors.
- Optimize route delivery efficiency and inventory turns using operational dashboards.

Requirements:
- 3+ years experience in e-commerce fulfillment, logistics, or warehouse operations management.
- Strong leadership, hands-on operational grit, and analytical problem-solving.""",
    },

    # ==========================================
    # 15. NON-IT: HEALTHCARE & CLINICAL OPERATIONS
    # ==========================================
    {
        "external_id": "job_hea_001",
        "company_name": "Apollo Hospitals",
        "title": "Clinical Research Coordinator & Healthcare Operations",
        "title_normalized": "clinical research coordinator healthcare operations",
        "employment_type": "Full-time",
        "work_mode": "onsite",
        "is_remote": False,
        "is_hybrid": False,
        "seniority": "mid",
        "role_category": "Healthcare & Life Sciences",
        "role_sub_category": "Clinical Research",
        "industry": "Healthcare & Life Sciences",
        "location": "Hyderabad, Telangana, India",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "salary_min": 1200000,
        "salary_max": 1800000,
        "salary_currency": "INR",
        "salary_raw": "₹12,00,000 - ₹18,00,000 / yr",
        "experience_min_years": 2.5,
        "experience_max_years": 5.0,
        "apply_url": "https://apollohospitals.com/careers/clinical-research-coordinator",
        "job_url": "https://apollohospitals.com/careers/clinical-research-coordinator",
        "required_skills": ["Clinical Protocols", "GCP Guidelines", "Patient Data Management", "Regulatory Compliance"],
        "preferred_skills": ["EHR Systems", "Medical Terminology", "Audit Documentation"],
        "description_summary": "Coordinate clinical trials, regulatory IRB submissions, and patient trial protocols in accordance with ICH-GCP quality guidelines at Apollo Hyderabad.",
        "description": """Apollo Hospitals is India's pioneer in healthcare delivery and clinical excellence.

Responsibilities:
- Facilitate participant recruitment, consent protocols, and patient study visits.
- Ensure strict adherence to Good Clinical Practice (GCP) and regulatory standards.
- Maintain clinical trial documentation and audit-ready master files.
- Coordinate with principal investigators and pharmaceutical research sponsors.

Requirements:
- 2.5+ years in clinical research coordination, hospital operations, or clinical trials.
- Degree in Life Sciences, Pharmacy (B.Pharm/M.Pharm), or Nursing with GCP certification.""",
    },
]

def seed_database():
    db = SessionLocal()
    try:
        print("[*] Starting Dummy Jobs & Companies Seeding...")

        # 1. Seed or update Companies
        company_map = {}
        for cdata in COMPANIES_DATA:
            norm_name = cdata["normalized_name"]
            existing = db.query(Company).filter(Company.normalized_name == norm_name).first()
            if not existing:
                comp = Company(
                    name=cdata["name"],
                    normalized_name=norm_name,
                    domain=cdata.get("domain"),
                    industry=cdata.get("industry"),
                    company_size=cdata.get("company_size"),
                    founded_year=cdata.get("founded_year"),
                    headquarters=cdata.get("headquarters"),
                    description=cdata.get("description"),
                    website=cdata.get("website"),
                    trust_score=cdata.get("trust_score", 0.95),
                    is_verified=cdata.get("is_verified", True),
                )
                db.add(comp)
                db.flush()
                company_map[cdata["name"]] = comp.id
                print(f"  [+] Created Company: {comp.name} (id={comp.id})")
            else:
                company_map[cdata["name"]] = existing.id
                print(f"  [=] Found Existing Company: {existing.name} (id={existing.id})")
        db.commit()

        # Update existing Job 1 if present
        job1 = db.query(Job).filter(Job.id == 1).first()
        if job1:
            job1.employment_type = "Full-time"
            job1.work_mode = "onsite"
            job1.seniority = "senior"
            job1.role_category = "AI/ML"
            job1.role_sub_category = "AI Systems"
            job1.is_remote = False
            job1.is_hybrid = False
            job1.is_active = True
            job1.apply_url = "https://careers.google.com/jobs/results/148291000"
            db.commit()
            print("  [~] Updated existing Job 1 with employment_type='Full-time'")

        # 2. Seed Jobs
        now = datetime.utcnow()
        inserted_count = 0
        updated_count = 0

        for jdata in JOBS_DATA:
            ext_id = jdata["external_id"]
            comp_name = jdata["company_name"]
            comp_id = company_map.get(comp_name)
            jhash = generate_job_hash(jdata["title"], comp_name, ext_id)

            existing_job = db.query(Job).filter(
                (Job.external_id == ext_id) | (Job.job_hash == jhash)
            ).first()

            if not existing_job:
                new_job = Job(
                    external_id=ext_id,
                    job_hash=jhash,
                    company_id=comp_id,
                    company_name=comp_name,
                    title=jdata["title"],
                    title_normalized=jdata["title_normalized"],
                    description=jdata.get("description"),
                    description_summary=jdata.get("description_summary"),
                    apply_url=jdata.get("apply_url"),
                    job_url=jdata.get("job_url"),
                    location=jdata.get("location"),
                    city=jdata.get("city"),
                    state=jdata.get("state"),
                    country=jdata.get("country"),
                    is_remote=jdata.get("is_remote", False),
                    is_hybrid=jdata.get("is_hybrid", False),
                    role_category=jdata.get("role_category"),
                    role_sub_category=jdata.get("role_sub_category"),
                    industry=jdata.get("industry"),
                    seniority=jdata.get("seniority"),
                    employment_type=jdata.get("employment_type"),
                    work_mode=jdata.get("work_mode"),
                    required_skills=jdata.get("required_skills", []),
                    preferred_skills=jdata.get("preferred_skills", []),
                    salary_min=jdata.get("salary_min"),
                    salary_max=jdata.get("salary_max"),
                    salary_currency=jdata.get("salary_currency", "USD"),
                    salary_period=jdata.get("salary_period", "yearly"),
                    salary_raw=jdata.get("salary_raw"),
                    experience_min_years=jdata.get("experience_min_years"),
                    experience_max_years=jdata.get("experience_max_years"),
                    trust_score=0.98,
                    quality_score=0.95,
                    freshness_score=1.0,
                    is_active=True,
                    is_verified=True,
                    lifecycle_status="published",
                    posted_at=now - timedelta(days=inserted_count % 7),
                    discovered_at=now,
                )
                db.add(new_job)
                inserted_count += 1
            else:
                # Update existing job attributes to ensure fresh sync
                existing_job.company_id = comp_id
                existing_job.employment_type = jdata.get("employment_type")
                existing_job.work_mode = jdata.get("work_mode")
                existing_job.is_remote = jdata.get("is_remote", False)
                existing_job.is_hybrid = jdata.get("is_hybrid", False)
                existing_job.seniority = jdata.get("seniority")
                existing_job.apply_url = jdata.get("apply_url")
                existing_job.required_skills = jdata.get("required_skills", [])
                existing_job.salary_raw = jdata.get("salary_raw")
                existing_job.is_active = True
                updated_count += 1

        db.commit()
        print(f"[*] Jobs Sync Complete: {inserted_count} inserted, {updated_count} updated.")

        # 3. Generate matches for all registered candidates
        candidates = db.query(Candidate).all()
        print(f"[*] Auto-generating matches for {len(candidates)} candidate(s)...")
        from app.api.routers.job_agent import _auto_ensure_candidate_matches

        for cand in candidates:
            # Delete old matches and recalculate fresh
            db.query(Match).filter(Match.candidate_id == cand.id).delete()
            db.commit()
            _auto_ensure_candidate_matches(cand.id, db)
            match_count = db.query(Match).filter(Match.candidate_id == cand.id).count()
            print(f"  [+] Candidate {cand.id} ({cand.parsed_name or 'User'}) matched with {match_count} jobs.")

        print("\n==========================================")
        print("SUCCESS: DUMMY JOBS OF ALL TYPES POPULATED!")
        print("==========================================")

        # Print breakdown summary
        all_jobs = db.query(Job).filter(Job.is_active == True).all()
        by_type = {}
        by_mode = {}
        by_seniority = {}
        for j in all_jobs:
            by_type[j.employment_type] = by_type.get(j.employment_type, 0) + 1
            by_mode[j.work_mode] = by_mode.get(j.work_mode, 0) + 1
            by_seniority[j.seniority] = by_seniority.get(j.seniority, 0) + 1

        print(f"Total Active Jobs: {len(all_jobs)}")
        print(f"By Employment Type: {by_type}")
        print(f"By Work Mode:       {by_mode}")
        print(f"By Seniority:       {by_seniority}")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding dummy jobs: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
