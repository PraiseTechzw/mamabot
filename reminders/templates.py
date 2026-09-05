from datetime import date

_TEMPLATES = {
    "en": "MamaBot reminder: your antenatal care appointment is on {date}. Please attend your clinic or contact them if you need help.",
    "sn": "Chiyeuchidzo cheMamaBot: musangano wenyu weANC uri musi wa {date}. Ndokumbirai muende kukiriniki kana kuvabata kana muchida rubatsiro.",
    "nd": "Isikhumbuzo seMamaBot: umhlangano wenu weANC ungomhlaka {date}. Sicela liye emtholampilo kumbe lixhumane lawo nxa lidinga uncedo.",
}


def appointment_reminder(language: str, appointment_date: date) -> str:
    template = _TEMPLATES.get(language, _TEMPLATES["en"])
    return template.format(date=appointment_date.isoformat())
