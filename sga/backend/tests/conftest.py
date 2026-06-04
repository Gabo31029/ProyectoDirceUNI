"""
conftest.py – pytest configuration and shared fixtures.
"""
import sys, os

# Add the backend root to the Python path so that 'app' package is importable.
# This allows running: pytest tests/ from the 'backend' directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
