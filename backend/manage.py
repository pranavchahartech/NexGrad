#!/usr/bin/env python
"""Django's command-line utility for administrative tasks for Nexgrad."""
import os
import sys

def main():
    """Run administrative tasks."""
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parent
    ai_service_dir = repo_root / 'ai-service'
    for extra_path in [str(ai_service_dir), str(current_dir)]:
        if extra_path not in sys.path:
            sys.path.insert(0, extra_path)

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

