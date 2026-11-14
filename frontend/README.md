# NexGrad Frontend

The unified presentation layer, templates, and static assets of the NexGrad Career Intelligence & DevOps Platform.

## Structure

```text
frontend/
├── templates/                 # Django semantic HTML templates
│   ├── base.html              # Core layout with navigation, footer & Novus AI popup
│   ├── core/                  # Landing, About, and Partner/Developer API documentation
│   ├── accounts/              # Sign-in, student/recruiter authentication
│   ├── jobs/                  # Job and internship listings & detail views
│   ├── assessments/           # Coding tests and score displays
│   ├── challenges/            # Competitive coding leaderboard & problem sets
│   ├── students/              # Student portfolio, skill analytics & resume builder
│   ├── recruiters/            # Recruiter talent pipeline & candidate evaluation
│   ├── institutions/          # Placement cell analytics & cohort reports
│   ├── notifications/         # Notification dropdown and center
│   ├── ai_assistant/          # Full-page Novus / VEX conversational interface
│   └── errors/                # Custom 400, 403, 404, 500 error templates
├── static/
│   ├── css/                   # Responsive stylesheets (brand styles, dashboards, bot widget)
│   ├── js/                    # Client-side scripts (chat widget, dynamic modals, filters)
│   └── images/                # Brand identity logos and bot avatars
├── nginx.conf                 # Production reverse proxy and caching configuration
├── Dockerfile                 # Lightweight Alpine Nginx container
└── package.json               # Asset linting and build scripts
```

## Production Delivery

In production, frontend assets are served via high-performance Nginx with gzip compression, cache-control headers, and reverse-proxy routing to the backend and AI services.

