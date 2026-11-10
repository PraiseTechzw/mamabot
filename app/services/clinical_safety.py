SAFETY_NOTICE = (
    "Automated information - not a diagnosis or a substitute for a qualified "
    "health worker. For a possible emergency, contact a clinic or emergency "
    "service now. This bot cannot alert a nurse."
)


def with_safety_notice(response: str) -> str:
    if response.endswith(SAFETY_NOTICE):
        return response
    return f"{response.rstrip()}\n\n{SAFETY_NOTICE}"
