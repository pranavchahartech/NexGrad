import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexgrad.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from recruiters.models import Company, RecruiterProfile
from jobs.models import Skill, Internship
from django.utils.text import slugify

User = get_user_model()

print("--- Starting Nexgrad Internship & Recruiter Seeding Engine ---")

# 1. Expand Skills Taxonomy
skills_data = [
    ('Python', 'BACKEND'),
    ('Django', 'BACKEND'),
    ('React.js', 'FRONTEND'),
    ('TypeScript', 'FRONTEND'),
    ('Next.js', 'FRONTEND'),
    ('PostgreSQL', 'DATABASE'),
    ('Redis & Caching', 'DATABASE'),
    ('RESTful APIs', 'BACKEND'),
    ('Docker', 'CLOUD'),
    ('Kubernetes', 'CLOUD'),
    ('AWS Cloud', 'CLOUD'),
    ('Terraform & DevOps', 'CLOUD'),
    ('Linux Systems & Shell Scripting', 'SYSTEMS'),
    ('C++', 'SYSTEMS'),
    ('Embedded C & RTOS', 'SYSTEMS'),
    ('ROS2 & Robotics', 'SYSTEMS'),
    ('Computer Vision & OpenCV', 'AI_ML'),
    ('PyTorch & Deep Learning', 'AI_ML'),
    ('Generative AI & LLMs', 'AI_ML'),
    ('Cybersecurity & Pentesting', 'SYSTEMS'),
    ('Data Structures & Algorithms', 'BACKEND'),
    ('System Architecture', 'BACKEND'),
]

skill_map = {}
for name, category in skills_data:
    skill, created = Skill.objects.get_or_create(
        name=name,
        defaults={'category': category, 'slug': slugify(name)}
    )
    skill_map[name] = skill
    if created:
        print(f"Created skill: {name}")

# 2. Company & Recruiter Definitions
recruiter_accounts = [
    {
        'username': 'recruiter_google',
        'password': 'Google#2026!Cloud',
        'email': 'talent-in@googlecloud.com',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'phone': '+91 98765 43210',
        'designation': 'Staff University Relations & Talent Partner',
        'department': 'Cloud & AI Talent Acquisition',
        'company_name': 'Google Cloud & AI Labs',
        'company_slug': 'google-cloud-ai-labs',
        'industry': 'Cloud Computing & Artificial Intelligence',
        'headquarters': 'Bengaluru, Karnataka, India',
        'website': 'https://cloud.google.com',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
        'company_size': '10,000+ Employees',
        'description': 'Google Cloud & AI Labs engineers planet-scale distributed compute platforms, transformer architectures, and sovereign cloud infrastructure powering global technological innovation.',
        'internships': [
            {
                'title': 'Generative AI & LLM Systems Research Intern',
                'duration': '6 Months',
                'stipend': '₹1,00,000 / Month',
                'location': 'Bengaluru, India (Hybrid)',
                'eligible_branches': 'CSE, AI & DS, IT, Math & Computing',
                'deadline_days': 45,
                'skills': ['Generative AI & LLMs', 'PyTorch & Deep Learning', 'Python', 'RESTful APIs'],
                'description': """Join the Google Cloud Applied AI Research Lab as an engineering intern. You will work side-by-side with principal research engineers on fine-tuning state-of-the-art multimodal foundation models, building latency-optimized Retrieval-Augmented Generation (RAG) architectures, and deploying tensor-parallel inference runtimes.

Key Learning Outcomes:
• Design and benchmark synthetic data generation pipelines for specialized domain adaptation.
• Implement semantic chunking, vector embeddings, and re-ranking pipelines using hybrid dense-sparse retrieval.
• Quantize 70B+ parameter transformer checkpoints (FP8/INT4) for low-latency production serving.
• Collaborate on research papers and open-source contributions to our AI developer ecosystem.

Candidate Qualifications:
• Currently enrolled in B.Tech/M.Tech/MS in Computer Science, Data Science, or related engineering discipline.
• Strong proficiency in Python, PyTorch, and linear algebra fundamentals.
• Hands-on project experience with open-source LLMs (Llama, Gemma, Mistral) or vector databases."""
            },
            {
                'title': 'Cloud Infrastructure & Kubernetes Systems Intern',
                'duration': '6 Months',
                'stipend': '₹85,000 / Month',
                'location': 'Bengaluru, India (Hybrid)',
                'eligible_branches': 'CSE, IT, ECE',
                'deadline_days': 40,
                'skills': ['Kubernetes', 'Docker', 'Linux Systems & Shell Scripting', 'Python', 'Terraform & DevOps'],
                'description': """Are you passionate about large-scale distributed systems and cloud-native resilience? As a Cloud Infrastructure Intern at Google Cloud, you will contribute directly to the Kubernetes control plane and multi-region network routing backbones that run mission-critical enterprise workloads.

Key Learning Outcomes:
• Develop custom Kubernetes CRDs (Custom Resource Definitions) and Go/Python operators for autonomous pod recovery.
• Implement declarative infrastructure automation modules using Terraform and GitOps practices.
• Profile Linux kernel networking (eBPF, iptables) to optimize TCP throughput and cross-pod communication latency.
• Establish distributed telemetry dashboards utilizing Prometheus, Grafana, and OpenTelemetry.

Candidate Qualifications:
• Solid understanding of Operating Systems, Linux system calls, networking (TCP/IP, DNS, HTTP/2).
• Proficiency in Python or Go; familiarity with Docker containers and container orchestration."""
            }
        ]
    },
    {
        'username': 'recruiter_novus',
        'password': 'Novus#2026!Robotics',
        'email': 'talent@novusrobotics.ai',
        'first_name': 'Vikram',
        'last_name': 'Malhotra',
        'phone': '+91 98450 11223',
        'designation': 'VP of Engineering & Talent',
        'department': 'Autonomous Systems & Edge AI',
        'company_name': 'Novus Robotics & Embedded AI',
        'company_slug': 'novus-robotics',
        'industry': 'Autonomous Robotics & Edge Intelligence',
        'headquarters': 'Hyderabad, Telangana, India',
        'website': 'https://novusrobotics.ai',
        'logo_url': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=200&q=80',
        'company_size': '100-250 Employees',
        'description': 'Novus Robotics develops cutting-edge autonomous mobile robots (AMRs), embedded edge computing hardware, and real-time computer vision perception systems for next-generation industrial automation.',
        'internships': [
            {
                'title': 'Embedded Systems & Edge AI Firmware Intern',
                'duration': '6 Months',
                'stipend': '₹45,000 / Month',
                'location': 'Hyderabad, India (On-Site)',
                'eligible_branches': 'ECE, CSE, EEE, Robotics & Automation',
                'deadline_days': 35,
                'skills': ['Embedded C & RTOS', 'C++', 'PyTorch & Deep Learning', 'Linux Systems & Shell Scripting'],
                'description': """Become an integral member of our Firmware & Edge Hardware team. You will write bare-metal and RTOS-level C/C++ firmware controlling actuators, sensors, and hardware accelerators on high-performance robotics motherboards.

Key Learning Outcomes:
• Write low-latency device drivers for SPI, I2C, UART, and CAN-bus industrial peripherals.
• Port and optimize INT8 quantized neural network inference on ARM Cortex-M and NVIDIA Jetson edge compute modules.
• Implement real-time scheduling guarantees, watchdog mechanisms, and fail-safe safety protocols on FreeRTOS.
• Utilize digital oscilloscopes, logic analyzers, and JTAG debuggers for embedded hardware troubleshooting.

Candidate Qualifications:
• Strong command of C, modern C++, and embedded microcontroller architectures.
• Demonstrated portfolio project involving microcontrollers (ESP32, STM32, Arduino) or Linux SBCs."""
            },
            {
                'title': 'Computer Vision & Autonomous Robotics Intern',
                'duration': '6 Months',
                'stipend': '₹50,000 / Month',
                'location': 'Hyderabad, India (Hybrid)',
                'eligible_branches': 'CSE, ECE, AI & DS, Robotics',
                'deadline_days': 50,
                'skills': ['Computer Vision & OpenCV', 'ROS2 & Robotics', 'PyTorch & Deep Learning', 'Python'],
                'description': """Join the Perception and Navigation division at Novus Robotics. You will work on real-time visual simultaneous localization and mapping (vSLAM), 3D point cloud processing, and deep neural networks for semantic obstacle segmentation on industrial factory floors.

Key Learning Outcomes:
• Build modular ROS2 nodes in Python and C++ for sensor synchronization (LiDAR, stereo cameras, IMU).
• Implement Kalman filtering and graph optimization algorithms for precise robot pose estimation.
• Train and deploy lightweight object detection models (YOLOv8, MobileNet) running at 60+ FPS on edge GPUs.
• Conduct hardware-in-the-loop (HIL) robot simulation in Gazebo and real-world warehouse test tracks.

Candidate Qualifications:
• Familiarity with OpenCV, Python, and ROS/ROS2 communication patterns.
• Passion for robotics, computer vision, and spatial computing."""
            }
        ]
    },
    {
        'username': 'recruiter_msft',
        'password': 'Azure#2026!Recruit',
        'email': 'talent-apac@microsoft.com',
        'first_name': 'Ananya',
        'last_name': 'Deshmukh',
        'phone': '+91 97112 33445',
        'designation': 'University Relations & Technical Talent Director',
        'department': 'Cloud Platform & Developer Tooling',
        'company_name': 'Microsoft Technology Center',
        'company_slug': 'microsoft-technology-center',
        'industry': 'Enterprise Cloud & Developer Ecosystems',
        'headquarters': 'Hyderabad, Telangana, India',
        'website': 'https://microsoft.com',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/9/96/Microsoft_logo_%282012%29.svg',
        'company_size': '10,000+ Employees',
        'description': 'Microsoft Technology Center accelerates digital transformation for global enterprises through Azure cloud platforms, enterprise intelligence, and developer tooling.',
        'internships': [
            {
                'title': 'Full Stack Cloud Platform Engineering Intern (TypeScript & React)',
                'duration': '6 Months',
                'stipend': '₹70,000 / Month',
                'location': 'Hyderabad, India (Hybrid)',
                'eligible_branches': 'CSE, IT, Software Engineering',
                'deadline_days': 30,
                'skills': ['React.js', 'TypeScript', 'Next.js', 'Django', 'PostgreSQL'],
                'description': """Collaborate with the Azure Developer Experience engineering team building world-class developer portals and management dashboards used by millions of engineers daily.

Key Learning Outcomes:
• Engineer responsive, accessible, and high-performance user interfaces using React, TypeScript, and modern state management.
• Build scalable RESTful and GraphQL API gateways with Django and Node.js microservices.
• Write comprehensive end-to-end integration tests using Playwright and Jest with continuous testing in CI pipelines.
• Implement enterprise identity and role-based access control (RBAC) protocols adhering to Zero-Trust architecture.

Candidate Qualifications:
• Strong foundation in JavaScript/TypeScript, React fundamentals, HTML5, and CSS/Tailwind.
• Good understanding of relational databases, API contracts, and clean component architecture."""
            },
            {
                'title': 'DevOps & Site Reliability Engineering (SRE) Intern',
                'duration': '3 Months',
                'stipend': '₹65,000 / Month',
                'location': 'Hyderabad, India (Remote)',
                'eligible_branches': 'CSE, IT, ECE, EEE',
                'deadline_days': 30,
                'skills': ['Terraform & DevOps', 'Docker', 'Kubernetes', 'Linux Systems & Shell Scripting', 'Python'],
                'description': """Join the Cloud Reliability engineering practice to design resilient failover automation, automated disaster recovery plans, and continuous telemetry pipelines across enterprise production clusters.

Key Learning Outcomes:
• Author reusable Terraform modules for automated multi-tier infrastructure provisioning.
• Implement automated canary deployment pipelines and blue/green traffic shifting.
• Build alerting pipelines tracking SLIs, SLOs, and error budgets with Prometheus and Grafana.
• Write automated diagnostic Python scripts for self-healing infrastructure.

Candidate Qualifications:
• Strong shell scripting / Python abilities; familiarity with cloud fundamentals and Docker."""
            }
        ]
    },
    {
        'username': 'recruiter_nexpay',
        'password': 'FinTech#2026!Pay',
        'email': 'recruitment@nexpayfintech.com',
        'first_name': 'Rohan',
        'last_name': 'Verma',
        'phone': '+91 99887 66554',
        'designation': 'Senior Technical Recruiter & Engineering Partner',
        'department': 'High-Frequency FinTech Engineering',
        'company_name': 'NexPay Global FinTech',
        'company_slug': 'nexpay-global-fintech',
        'industry': 'Financial Technology & High-Volume Payments',
        'headquarters': 'Mumbai, Maharashtra, India',
        'website': 'https://nexpayfintech.com',
        'logo_url': 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=200&q=80',
        'company_size': '500-1,000 Employees',
        'description': 'NexPay Global FinTech processes billions in payment transactions with sub-millisecond settlement engines, intelligent fraud detection, and regulatory compliance infrastructure.',
        'internships': [
            {
                'title': 'High-Frequency Backend & Payments API Intern',
                'duration': '6 Months',
                'stipend': '₹60,000 / Month',
                'location': 'Mumbai, India (Hybrid)',
                'eligible_branches': 'CSE, IT, ECE',
                'deadline_days': 45,
                'skills': ['Django', 'Python', 'PostgreSQL', 'Redis & Caching', 'RESTful APIs'],
                'description': """Design and optimize low-latency payment processing pipelines. You will contribute to distributed payment gateway integrations, double-entry financial ledger accounting systems, and asynchronous webhook dispatchers.

Key Learning Outcomes:
• Build idempotent, fault-tolerant REST APIs with distributed locking and queue management (Celery/Redis).
• Write strictly ACID-compliant transactional SQL queries with PostgreSQL table partitioning and index optimization.
• Implement cryptographic signature verification and rate-limiting middleware to guard against payment replay attacks.
• Profile query execution plans (EXPLAIN ANALYZE) to eliminate N+1 bottlenecks and reduce p99 latency below 30ms.

Candidate Qualifications:
• Excellent problem-solving skills in Python and relational database design.
• Passion for building rock-solid, production-grade distributed backend systems."""
            },
            {
                'title': 'Application Security & Cyber Defense Intern',
                'duration': '6 Months',
                'stipend': '₹55,000 / Month',
                'location': 'Bengaluru, India (Remote)',
                'eligible_branches': 'CSE, Cybersecurity, IT',
                'deadline_days': 40,
                'skills': ['Cybersecurity & Pentesting', 'Python', 'Linux Systems & Shell Scripting', 'RESTful APIs'],
                'description': """Safeguard mission-critical financial applications against sophisticated cyber threats. You will conduct penetration testing, analyze code for OWASP Top 10 vulnerabilities, and build automated security guardrails.

Key Learning Outcomes:
• Perform automated and manual web/API application security audits and penetration tests.
• Implement OAuth2, OpenID Connect, and mutual TLS (mTLS) authentication across microservices.
• Build security static analysis (SAST) and dynamic analysis (DAST) checks into CI/CD build gates.
• Analyze security telemetry logs to detect credential stuffing and unauthorized API scraping.

Candidate Qualifications:
• Foundational knowledge of web vulnerabilities (SQLi, XSS, CSRF, SSRF, IDOR) and secure coding principles.
• Enthusiasm for ethical hacking, cryptography, and network security."""
            }
        ]
    },
    {
        'username': 'recruiter_sarah',
        'password': 'Arcturus#2026!Sarah',
        'email': 'sarah.jenkins@arcturuscloud.io',
        'first_name': 'Sarah',
        'last_name': 'Jenkins',
        'phone': '+91 91234 56789',
        'designation': 'Lead Technical Talent Partner',
        'department': 'Cloud Talent Acquisition',
        'company_name': 'Arcturus Cloud Technologies',
        'company_slug': 'arcturus-cloud-technologies',
        'industry': 'Cloud Infrastructure & Enterprise Systems',
        'headquarters': 'Bengaluru, Karnataka, India',
        'website': 'https://arcturuscloud.io',
        'logo_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=200&q=80',
        'company_size': '250-500 Employees',
        'description': 'Arcturus Cloud Technologies delivers next-generation enterprise hybrid cloud infrastructure and scalable data plane management.',
        'internships': [
            {
                'title': 'Site Reliability & Kubernetes Infrastructure Intern',
                'duration': '3 Months',
                'stipend': '₹40,000 / Month',
                'location': 'Bengaluru, India (Hybrid)',
                'eligible_branches': 'CSE, IT, ECE',
                'deadline_days': 25,
                'skills': ['Kubernetes', 'Docker', 'AWS Cloud', 'Linux Systems & Shell Scripting'],
                'description': """Assist in managing and scaling production multi-tenant Kubernetes clusters on AWS. Learn hands-on cloud orchestration, automated deployment pipelines, and observability monitoring.

Key Learning Outcomes:
• Maintain Helm charts and Kustomize templates for cloud microservices deployments.
• Configure Prometheus alerts and Grafana dashboards for proactive incident resolution.
• Automate AWS cloud resources using Terraform and shell scripts."""
            }
        ]
    }
]

created_accounts_summary = []

for entry in recruiter_accounts:
    # 2.1 Get or Create Company
    company, c_created = Company.objects.get_or_create(
        slug=entry['company_slug'],
        defaults={
            'name': entry['company_name'],
            'industry': entry['industry'],
            'headquarters': entry['headquarters'],
            'website': entry['website'],
            'logo_url': entry['logo_url'],
            'company_size': entry['company_size'],
            'description': entry['description'],
            'is_verified': True,
        }
    )
    if not c_created:
        company.name = entry['company_name']
        company.industry = entry['industry']
        company.headquarters = entry['headquarters']
        company.website = entry['website']
        company.logo_url = entry['logo_url']
        company.company_size = entry['company_size']
        company.description = entry['description']
        company.is_verified = True
        company.save()
    print(f"Company: {company.name} ({'Created' if c_created else 'Updated'})")

    # 2.2 Get or Create Recruiter User
    user, u_created = User.objects.get_or_create(
        username=entry['username'],
        defaults={
            'email': entry['email'],
            'first_name': entry['first_name'],
            'last_name': entry['last_name'],
            'phone': entry['phone'],
            'role': User.Role.RECRUITER,
            'is_verified': True,
        }
    )
    user.set_password(entry['password'])
    user.email = entry['email']
    user.first_name = entry['first_name']
    user.last_name = entry['last_name']
    user.phone = entry['phone']
    user.role = User.Role.RECRUITER
    user.is_verified = True
    user.save()
    print(f"User: {user.username} - Password set successfully")

    # 2.3 Get or Create RecruiterProfile
    recruiter_profile, r_created = RecruiterProfile.objects.get_or_create(
        user=user,
        defaults={
            'company': company,
            'designation': entry['designation'],
            'department': entry['department'],
            'is_verified': True,
            'verification_status': RecruiterProfile.VerificationStatus.VERIFIED,
        }
    )
    recruiter_profile.company = company
    recruiter_profile.designation = entry['designation']
    recruiter_profile.department = entry['department']
    recruiter_profile.is_verified = True
    recruiter_profile.verification_status = RecruiterProfile.VerificationStatus.VERIFIED
    recruiter_profile.save()

    created_accounts_summary.append({
        'company': company.name,
        'username': user.username,
        'password': entry['password'],
        'recruiter_name': f"{user.first_name} {user.last_name}",
        'designation': entry['designation'],
        'internships_count': len(entry['internships'])
    })

    # 2.4 Create / Update Internships
    for intern_data in entry['internships']:
        intern_slug = slugify(f"{company.slug}-{intern_data['title']}")
        deadline = timezone.now().date() + timedelta(days=intern_data['deadline_days'])

        internship, i_created = Internship.objects.get_or_create(
            slug=intern_slug,
            defaults={
                'company': company,
                'recruiter': recruiter_profile,
                'title': intern_data['title'],
                'duration': intern_data['duration'],
                'stipend': intern_data['stipend'],
                'location': intern_data['location'],
                'eligible_branches': intern_data['eligible_branches'],
                'description': intern_data['description'],
                'deadline': deadline,
                'is_active': True,
            }
        )
        if not i_created:
            internship.company = company
            internship.recruiter = recruiter_profile
            internship.title = intern_data['title']
            internship.duration = intern_data['duration']
            internship.stipend = intern_data['stipend']
            internship.location = intern_data['location']
            internship.eligible_branches = intern_data['eligible_branches']
            internship.description = intern_data['description']
            internship.deadline = deadline
            internship.is_active = True
            internship.save()

        # Link skills
        skills_to_link = [skill_map[s] for s in intern_data['skills'] if s in skill_map]
        internship.required_skills.set(skills_to_link)
        print(f"  -> Internship: '{internship.title}' ({internship.duration}, {internship.stipend})")

print("\n--- Summary of Created Recruiter Accounts ---")
for acc in created_accounts_summary:
    print(f"Company: {acc['company']}")
    print(f"  Recruiter: {acc['recruiter_name']} ({acc['designation']})")
    print(f"  Username:  {acc['username']}")
    print(f"  Password:  {acc['password']}")
    print(f"  Internships Posted: {acc['internships_count']}")
    print("-" * 50)
print("Seeding completed successfully in MySQL!")
