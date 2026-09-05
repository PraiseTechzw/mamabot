"""Non-diagnostic pregnancy profile service boundary."""

from database.models import PregnancyProfile
from database.queries import repository


def disclaimer() -> str:
    return "MamaBot provides general information and does not diagnose or replace a qualified health worker."


def save_profile(profile: PregnancyProfile):
    return repository.save_pregnancy_profile(profile)


def get_profile(user_id: int):
    return repository.get_pregnancy_profile(user_id)
