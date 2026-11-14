#!/bin/bash
# Immediate rollback script to revert to previous stable git commit tag
TARGET_COMMIT=${1:-"HEAD~1"}
echo "Rolling back deployment to commit: $TARGET_COMMIT"

cd backend
git checkout "$TARGET_COMMIT"
python manage.py migrate
systemctl restart nexgrad-backend
systemctl restart nexgrad-ai

echo "Rollback completed. Current service state:"
systemctl status nexgrad-backend --no-pager

