#!/usr/bin/env python
"""
NexGrad DevOps Root Management Utility
Allows executing Django administrative commands from the repository root
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
AI_SERVICE_DIR = ROOT_DIR / 'ai-service'
FRONTEND_DIR = ROOT_DIR / 'frontend'

for extra_path in [str(AI_SERVICE_DIR), str(BACKEND_DIR)]:
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexgrad.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

