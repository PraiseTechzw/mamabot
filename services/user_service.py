from database.queries import repository


def get_or_create_user(phone_number: str, language: str = "en"):
    return repository.get_or_create_user(phone_number, language)


def get_user(user_id: int):
    return repository.get_user_by_id(user_id)


def update_user(user_id: int, name: str | None = None, due_date=None):
    return repository.update_user(user_id, name, due_date)
