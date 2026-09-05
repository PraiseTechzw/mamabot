from datetime import date

from database.queries import InMemoryRepository
from dialogue.registration import RegistrationHandler
from dialogue.state import ConversationSession
from nlp.entity_extractor import extract_entities
from nlp.pipeline import analyze


def test_english_name_appointment_date_and_phone_are_normalized():
    entities = extract_entities(
        "My name is Tariro, call 0771234567. My appointment is on 2027-03-15"
    )

    assert entities.person_name == "Tariro"
    assert entities.phone_number == "+263771234567"
    assert entities.date == "2027-03-15"
    assert entities.appointment_date == "2027-03-15"
    assert entities.due_date is None


def test_shona_due_date_and_name_are_extracted():
    entities = extract_entities("Zita rangu ndiRudo, zuva rekuzvara ndi 2027/04/20")

    assert entities.person_name == "Rudo"
    assert entities.due_date == "2027-04-20"
    assert entities.appointment_date is None


def test_ndebele_appointment_date_and_name_are_extracted():
    entities = extract_entities(
        "Ibizo lami nguNompilo, umhlangano ungomhla ka 12 May 2027"
    )

    assert entities.person_name == "Nompilo"
    assert entities.appointment_date == "2027-05-12"
    assert entities.language is None


def test_language_entity_is_explicit_and_validated():
    assert extract_entities("Please change my language to Shona").language == "sn"
    assert extract_entities("Sebenzisa isiNdebele").language == "nd"
    assert extract_entities("Use Klingon").language is None


def test_invalid_or_ambiguous_dates_are_not_returned():
    assert extract_entities("My appointment is on 2027-99-99").date is None
    assert extract_entities("My appointment date is unknown").appointment_date is None


def test_pipeline_exposes_entities_to_downstream_analysis():
    analysis = analyze("My appointment is on 2027-03-15")

    assert analysis.entities.appointment_date == "2027-03-15"
    assert analysis.entities.date == "2027-03-15"


def test_registration_uses_extracted_name_and_validated_due_date():
    repository = InMemoryRepository()
    handler = RegistrationHandler(repository)
    session = ConversationSession()

    handler.handle("register", session, phone_number="0771234567", channel="test")
    handler.handle(
        "My name is Tariro", session, phone_number="0771234567", channel="test"
    )
    handler.handle("Shona", session, phone_number="0771234567", channel="test")
    handler.handle("2027-04-20", session, phone_number="0771234567", channel="test")

    assert session.draft.name == "Tariro"
    assert session.draft.due_date == date(2027, 4, 20)
