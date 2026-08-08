# tests/conftest.py
"""Shared pytest fixtures."""
import sys
from pathlib import Path

# Add backend to sys.path so we can import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
