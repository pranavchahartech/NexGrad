# NexGrad: DevOps Automation & Self-Healing Infrastructure Management Platform

[![CI/CD Pipeline](https://github.com/nexgrad/nexgrad-devops/actions/workflows/backend-deploy.yml/badge.svg)](https://github.com/nexgrad/nexgrad-devops/actions)
[![Infrastructure](https://img.shields.io/badge/AWS-Terraform-orange.svg)](https://aws.amazon.com/)
[![Configuration](https://img.shields.io/badge/Configuration-Puppet%20%7C%20Ansible-red.svg)](https://www.ansible.com/)
[![Monitoring](https://img.shields.io/badge/Monitoring-Nagios%20Self--Healing-blue.svg)](https://www.nagios.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Executive Summary

**NexGrad** is an enterprise-grade Career Intelligence and Employment Ecosystem coupled with an industry-standard **DevOps Automation and Self-Healing Infrastructure Management Platform**.

Designed for high reliability, autonomous resilience, and automated continuous delivery on **Amazon Web Services (AWS)**, NexGrad integrates:
- **Terraform** for declarative Cloud Infrastructure as Code (VPC, Subnets, Security Groups, EC2, ALB, and RDS PostgreSQL).
- **Puppet** for declarative system baseline enforcement and drift management.
- **Ansible** for multi-tier rolling deployment orchestration and automated incident remediation.
- **Nagios Core** for 24/7 continuous health probing and event-handler-driven **autonomic self-healing**.
- **GitHub Actions** for multi-pipeline CI/CD automation across frontend, backend, AI service, and infrastructure tiers.
- **NOVUS AI Assistant** powered by Google Gemini 2.5 Flash for natural-language career intelligence, resume critique, and platform navigation.

---

## 2. Professional DevOps Directory Structure

```text
nexgrad-devops/
│
├── frontend/                              # Frontend presentation tier
│   ├── templates/                         # Django semantic HTML templates (base, accounts, jobs, bot)
│   ├── static/                            # Static assets (CSS stylesheets, JS logic, brand & bot icons)
│   ├── nginx.conf                         # Production Nginx reverse-proxy & caching configuration
│   ├── Dockerfile                         # Lightweight Alpine Nginx container
│   ├── package.json                       # Static asset linting & tooling scripts
│   └── README.md                          # Frontend UI documentation
│
├── backend/                               # Core Django application backend
│   ├── accounts/                          # User identity, RBAC (Student, Recruiter, Institution, Admin)
│   ├── core/                              # Global views, landing page, brand context & Developer API portal
│   ├── students/                          # Student profiles, portfolio, verified skills & resume builder
│   ├── recruiters/                        # Recruiter talent pipeline & candidate management
│   ├── institutions/                      # Placement cell dashboards & batch analytics
│   ├── jobs/                              # Job & internship management, eligibility scoring
│   ├── applications/                      # Job applications lifecycle & status tracking
│   ├── assessments/                       # Skill tests, coding challenges, evaluation engine
│   ├── career_intelligence/               # Role roadmaps & skill gap analysis
│   ├── challenges/                        # Competitive coding challenges & leaderboards
│   ├── notifications/                     # In-app alerts & notification center
│   ├── nexgrad/                           # Project settings, WSGI, ASGI, and root routing
│   ├── manage.py                          # Django administrative controller
│   ├── seed_data.py                       # Automated database seeder (mock users, jobs, questions)
│   ├── db.sqlite3                         # Development database (pre-seeded)
│   ├── media/                             # Uploaded student resumes, avatars, company logos
│   ├── requirements.txt                   # Backend Python dependencies
│   ├── Dockerfile                         # Multi-stage Python 3.12 production container
│   ├── run.bat / run.ps1                  # Local execution utilities
│   └── README.md                          # Backend service documentation
│
├── ai-service/                            # Autonomous AI Career Intelligence & Diagnostic Service
│   ├── ai_assistant/                      # Django modular AI application
│   │   ├── services/                      # Gemini client, VEX intent router, context resolver, tools, memory
│   │   ├── models.py                      # AIMessage, ConversationState, StudentAIMemory
│   │   ├── views.py                       # Chat endpoints & floating popup widget handlers
│   │   └── tests.py                       # 30 automated intent classification & context continuity tests
│   ├── main.py                            # Standalone FastAPI microservice runner
│   ├── requirements.txt                   # Dedicated AI service dependencies (google-genai, fastapi, uvicorn)
│   ├── Dockerfile                         # Production AI microservice container
│   └── README.md                          # AI microservice documentation
│
├── terraform/                             # AWS Infrastructure as Code (IaC)
│   ├── modules/                           # Reusable Terraform modules
│   │   ├── vpc/                           # Custom VPC, Internet Gateway, public/private subnets, route tables
│   │   ├── security/                      # ALB, App, and RDS PostgreSQL Security Groups
│   │   ├── ec2/                           # EC2 application instances with EBS volume encryption
│   │   ├── rds/                           # Multi-AZ managed PostgreSQL database
│   │   └── alb/                           # Application Load Balancer with HTTP/HTTPS listeners & health checks
│   ├── environments/                      # Environment-specific orchestrations
│   │   └── production/                    # Production deployment root (main.tf, variables.tf, tfvars.example)
│   ├── main.tf                            # Root module composition
│   ├── variables.tf                       # Global configuration variables
│   ├── outputs.tf                         # Infrastructure outputs (ALB DNS, VPC ID, EC2 IPs)
│   ├── providers.tf                       # HashiCorp AWS provider configuration
│   └── versions.tf                        # Terraform and provider constraint specifications
│
├── puppet/                                # Declarative Configuration Management
│   ├── manifests/                         # Node definitions and site rules
│   │   ├── site.pp                        # Primary manifest mapping roles to nodes
│   │   └── nodes.pp                       # Node classification
│   ├── modules/                           # Reusable Puppet modules
│   │   ├── nexgrad_backend/               # Installs Python, virtualenv, dependencies & systemd service
│   │   ├── nexgrad_frontend/              # Installs and configures Nginx virtual hosts
│   │   ├── nexgrad_ai/                    # Configures and manages Uvicorn AI service daemon
│   │   └── nagios_monitoring/             # Deploys NRPE agent and check plugins
│   └── hieradata/                         # Centralized configuration data
│       ├── common.yaml                    # Global platform parameters
│       └── production.yaml                # Production-specific environment overrides
│
├── ansible/                               # Push-based Orchestration & Remediation
│   ├── inventory/                         # Host inventory definitions
│   │   ├── hosts.ini                      # Server group mappings (web, app, ai, monitoring)
│   │   └── group_vars/                    # Group variables (all.yml, production.yml)
│   ├── playbooks/                         # Automation playbooks
│   │   ├── site.yml                       # Full-stack baseline infrastructure provisioning
│   │   ├── deploy.yml                     # Zero-downtime rolling application deployment
│   │   └── self_healing.yml               # Automated self-healing remediation playbook
│   ├── roles/                             # Modular task roles
│   │   ├── common/                        # System users, logging paths, base packages
│   │   ├── backend/                       # Python venv, gunicorn service setup
│   │   ├── frontend/                      # Nginx virtual host and static sync
│   │   ├── ai_service/                    # AI microservice deployment
│   │   └── self_healing/                  # Self-healing script synchronization
│   └── ansible.cfg                        # Ansible execution configuration
│
├── nagios/                                # Continuous Monitoring & Autonomic Healing
│   ├── configurations/                    # Nagios Core configuration files
│   │   ├── nagios.cfg                     # Core configuration with event handlers enabled
│   │   ├── hosts.cfg                      # Monitored host definitions (web, app, ai)
│   │   ├── services.cfg                   # Health check definitions with attached self-healing handlers
│   │   ├── commands.cfg                   # Health check and event handler command mappings
│   │   └── contacts.cfg                   # Alert escalation contacts and on-call groups
│   ├── plugins/                           # Custom monitoring plugins
│   │   ├── check_django_health.py         # HTTP endpoint and latency health probe
│   │   ├── check_ai_service.py            # AI microservice & Gemini connectivity check
│   │   ├── check_db_connectivity.py       # PostgreSQL / database query latency probe
│   │   └── check_system_metrics.sh        # CPU, RAM, and disk threshold monitor
│   ├── event-handlers/                    # Autonomic self-healing event handlers
│   │   ├── handle_backend_failure.sh      # Remediates backend crashes (soft & hard states)
│   │   ├── handle_ai_failure.sh           # Restarts and recovers hung AI microservices
│   │   └── self_healing_recovery.py       # Autonomous multi-step daemon recovery controller
│   └── scripts/                           # Administrative scripts
│       ├── install_nagios.sh              # Ubuntu/Debian Nagios installation script
│       └── verify_configs.sh              # Configuration syntax validator
│
├── .github/workflows/                     # Continuous Integration & Delivery (CI/CD)
│   ├── frontend-deploy.yml                # Validates Nginx config & syncs static assets to S3/CloudFront
│   ├── backend-deploy.yml                 # Runs Django check, 38+ unit tests, builds & pushes Docker image
│   ├── ai-deploy.yml                      # Runs 30 AI assistant tests & validates AI container
│   └── terraform.yml                      # Formats, initializes, and validates Terraform IaC
│
├── scripts/                               # Operational Tooling & Runbooks
│   ├── setup/                             # Environment bootstrapping scripts
│   │   ├── bootstrap_environment.sh       # One-click environment bootstrap
│   │   ├── install_dependencies.sh        # System package and pip installer
│   │   └── setup_database.sh              # Applies migrations and seeds database
│   ├── deployment/                        # Release automation
│   │   ├── deploy_all.sh                  # Multi-tier deployment orchestrator
│   │   ├── rolling_update.sh              # Zero-downtime rolling update executor
│   │   └── rollback.sh                    # Instant commit rollback script
│   └── monitoring/                        # Monitoring diagnostics
│       ├── health_check.sh                # Probes web and AI ports
│       ├── collect_metrics.sh             # Reports host hardware utilization
│       └── nagios_diagnostic.py           # Validates check plugins locally
│
├── docs/                                  # Comprehensive Documentation
│   ├── architecture/                      # Architecture blueprints & self-healing specifications
│   │   ├── system_architecture.md         # 3-tier distributed architecture guide
│   │   └── self_healing_design.md         # State diagram and remediation design
│   ├── deployment/                        # Operations and CI/CD guides
│   │   ├── deployment_guide.md            # AWS production deployment runbook
│   │   └── ci_cd_pipeline.md              # Pipeline architecture and secrets guide
│   └── screenshots/                       # Visual verification and UI screenshots
│       └── README.md
│
├── run.bat / run.ps1                      # Unified root management helper scripts
├── .gitignore                             # Master gitignore excluding secrets, keys, and credentials
├── README.md                              # This documentation
└── LICENSE                                # MIT Open-Source License
```

---

## 3. Self-Healing Architecture

NexGrad implements **Autonomic Self-Healing**:

1. **Active Probing**: Nagios actively pings `/healthz` on the Django backend (port 8000) and `/health` on the AI microservice (port 8001) every 60 seconds.
2. **Soft Failure Detection (Attempt 1-2)**:
   - If a probe fails, Nagios enters a `SOFT CRITICAL` state.
   - The attached event handler (`handle_backend_failure.sh` / `handle_ai_failure.sh`) triggers an immediate localized daemon restart via systemd.
3. **Hard Failure Remediation (Attempt 3)**:
   - If the service remains unresponsive across 3 consecutive checks, Nagios enters `HARD CRITICAL`.
   - The event handler triggers the Ansible `self_healing.yml` remediation playbook.
   - The playbook clears hung sockets, kills orphaned processes, restarts the daemon, runs an integrity test, and logs the incident audit trail to `/var/log/nexgrad/self-healing.log`.
4. **Escalation**: If automated remediation fails, on-call SRE alerts are dispatched directly via email to `karthiksn20112004@gmail.com`.

---

## 4. Verification and Testing

### 1. Verification of System Health
From the repository root:

```powershell
# Run Django system integrity check
.\run check
```

### 2. Verification of Automated Test Suite (All 38 Tests)
```powershell
# Executes all core platform and AI assistant unit tests
.\run test core ai_assistant
```

Expected output:
```text
Ran 38 tests in X.XXXs
OK
System check identified no issues (0 silenced).
```

### 3. Verification of Terraform IaC Syntax
```bash
cd terraform
terraform fmt -check
terraform init -backend=false
terraform validate
```

---

## 5. Security and Secret Management

All environment variables, API keys, passwords, AWS credentials, and SSH keys are strictly excluded via `.gitignore`:
- Never commit `.env` or production credentials.
- Use `terraform.tfvars.example` as a template for infrastructure variables.
- CI/CD secrets must be configured exclusively in **GitHub Repository Secrets**.

---

## 6. License

This project is licensed under the terms of the [MIT License](LICENSE).
