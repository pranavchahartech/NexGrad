#!/bin/bash
# Initialize and seed database
echo "Applying Django migrations..."
cd backend
python manage.py migrate --noinput

echo "Seeding default data (academic roles, jobs, assessments)..."
python seed_data.py
echo "Database ready."

