"""
app/models/__init__.py
Exports all database models so they can be imported as:
  from app.models import Message, User
"""

from app.models.message import Message
from app.models.user import User

__all__ = ["Message", "User"]
