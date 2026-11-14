# NexGrad System Architecture

NexGrad is an enterprise-grade Career Intelligence and DevOps Automation Platform.

## 3-Tier Distributed Architecture

```text
       +-------------------------------------------------------+
       |             AWS Route 53 / CloudFront CDN             |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |         AWS Application Load Balancer (ALB)           |
       +-------------------------------------------------------+
                |                                   |
       (Port 80 / Static)                  (Port 8000 / API)
                v                                   v
+-------------------------------+   +-------------------------------+
|      Frontend Web Tier        |   |       Django Backend Tier     |
|   (Nginx Alpine Container)    |   |    (Gunicorn WSGI Cluster)    |
|   - Server-Rendered UI Views  |   |    - Accounts & Roles (RBAC)  |
|   - Dynamic Chat Bot Popup    |   |    - Jobs, Apps & Assessments |
|   - Developer & Partner APIs  |   |    - Student Portfolios       |
+-------------------------------+   +-------------------------------+
                                                    |
                                                    | (Inter-Service RPC)
                                                    v
                                    +-------------------------------+
                                    |       AI Microservice         |
                                    |    (FastAPI / NOVUS Engine)   |
                                    |    - Intent Routing           |
                                    |    - State & Memory Context   |
                                    |    - Google Gemini 2.5 Flash  |
                                    +-------------------------------+
                                                    |
                                                    v
                                    +-------------------------------+
                                    |   AWS RDS PostgreSQL / DB     |
                                    |     Multi-AZ Managed Cluster  |
                                    +-------------------------------+
```

## DevOps Automation Stack

1. **Infrastructure as Code**: Terraform provisioner for AWS VPC, subnets, EC2 instances, ALB, and RDS.
2. **Configuration Management**: Puppet modules enforcing system baselines, Nginx configs, and systemd units.
3. **Application Deployment**: Ansible playbooks executing rolling deployments, dependency setups, and database migrations.
4. **Monitoring & Self-Healing**: Nagios Core active health probes with automated event handlers triggering remediation upon service failure.
5. **Continuous Integration**: GitHub Actions automated workflows validating code, executing unit test suites, and pushing container artifacts.

