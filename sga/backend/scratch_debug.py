import os
import sys

# Add backend root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
settings = get_settings()
print("DATABASE_URL env:", os.getenv("DATABASE_URL"))
print("database_url in settings:", settings.database_url)
print("resolved_database_url in settings:", settings.resolved_database_url)
