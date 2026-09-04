from database.queries import repository


def get_or_create_user(phone_number: str, language: str = "en"): return repository.get_or_create_user(phone_number, language)
