"""
Intent Router Package

Fast CPU-based intent classification service for OpenWebUI Suite.
Provides real-time classification of user inputs into appropriate processing lanes.
"""

__version__ = "1.0.0"
__author__ = "OpenWebUI Suite"
__description__ = "Lightweight intent classification service"

from .app import app
from .classifier import IntentClassifier  
from .rules import RuleEngine

__all__ = ["app", "IntentClassifier", "RuleEngine"]
