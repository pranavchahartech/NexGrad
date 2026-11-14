"""
NexGrad Root Seed Data Wrapper
Executes the backend seed_data.py script with all paths configured.
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / 'backend'
AI_SERVICE_DIR = ROOT_DIR / 'ai-service'

for extra_path in [str(AI_SERVICE_DIR), str(BACKEND_DIR)]:
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexgrad.settings')

if __name__ == '__main__':
    from backend.seed_data import seed
    seed()

