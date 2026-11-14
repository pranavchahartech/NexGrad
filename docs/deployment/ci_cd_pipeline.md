# GitHub Actions CI/CD Pipeline Architecture

## Workflow Triggers & Stages

| Workflow | Path Trigger | Jobs & Actions |
|---|---|---|
| `frontend-deploy.yml` | `frontend/**` | Nginx config syntax test, template validation, static asset sync to S3/CloudFront |
| `backend-deploy.yml` | `backend/**` | Python setup, dependency install, `manage.py check`, 38+ unit tests, Docker container build & ECR push |
| `ai-deploy.yml` | `ai-service/**` | Python setup, AI assistant 30 unit tests, container build |
| `terraform.yml` | `terraform/**` | `terraform fmt`, `terraform init`, `terraform validate` |

## Required GitHub Repository Secrets

- `AWS_ACCESS_KEY_ID`: AWS IAM deployer access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS IAM deployer secret access key
- `GEMINI_API_KEY`: Google Gemini API key for NOVUS conversational assistant
- `AWS_S3_FRONTEND_BUCKET`: Production S3 bucket name for static web assets

