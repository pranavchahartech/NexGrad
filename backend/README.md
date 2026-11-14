# NexGrad Backend

Core Django Application and Business Logic for NexGrad: The Unified Career Intelligence and Employment Ecosystem.

## Domain Apps

- `accounts/`: Multi-role user authentication, role-based authorization (Student, Recruiter, Institution, Admin).
- `core/`: Global views, landing page, brand context processors, partner & developer API documentation portal.
- `students/`: Engineering student profiles, skills verification, resume management, and portfolio showcase.
- `recruiters/`: Employer dashboard, job creation, applicant evaluation, company profiles.
- `institutions/`: College placement cell dashboards, student batch performance analytics.
- `jobs/`: Job & internship management, eligibility scoring, filtering.
- `applications/`: Job application workflow, status tracking, interview scheduling.
- `assessments/`: Automated skill tests, evaluation matrices.
- `career_intelligence/`: Career path roadmaps, skill gap insights.
- `challenges/`: Weekly competitive programming challenges and leaderboards.
- `notifications/`: Real-time system notifications and alerts.

## Configuration & Environment

Settings are located in `nexgrad/settings.py`. Key environment variables:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django cryptographic secret key | Built-in development key |
| `DEBUG` | Debug mode | `True` (dev) / `False` (prod) |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite fallback (`db.sqlite3`) |
| `GEMINI_API_KEY` | Google Gemini API key for NOVUS | Environment / Config |

## Running Tests

From project root or `backend/`:

```bash
.\run test core ai_assistant
```

