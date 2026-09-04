"""Minimal state constants for extensible conversation flows."""
from enum import Enum


class ConversationState(str, Enum): IDLE = "idle"; AWAITING_APPOINTMENT_DATE = "awaiting_appointment_date"; ESCALATED = "escalated"
