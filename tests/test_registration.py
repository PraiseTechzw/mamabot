"""Automated tests for the MamaBot registration flow.

Tests cover:
- Successful full registration in English, Shona, and Ndebele
- Invalid name, phone, language, due-date inputs
- Cancellation at each step
- Field correction at confirmation
- Existing user re-registration path
- Duplicate-free persistence
- /webhook/test endpoint integration
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import create_app
from database.queries import InMemoryRepository
from dialogue.manager import DialogueManager
from dialogue.registration import RegistrationHandler, _build_confirm_prompt
from dialogue.state import ConversationSession, ConversationState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FUTURE_DATE = (date.today() + timedelta(days=120)).isoformat()
FAR_FUTURE_DATE = (date.today() + timedelta(weeks=50)).isoformat()
PAST_DATE = (date.today() - timedelta(days=1)).isoformat()


def new_session() -> ConversationSession:
    return ConversationSession()


def make_handler(repo=None) -> RegistrationHandler:
    repo = repo or InMemoryRepository()
    return RegistrationHandler(repo)


def run_full_registration(
    repo: InMemoryRepository,
    phone: str = "+263771000001",
    name: str = "Chipo Moyo",
    language: str = "en",
    due_date: str | None = None,
    channel: str = "test",
) -> list[str]:
    """Drive a full registration through the RegistrationHandler and return all reply texts."""
    if due_date is None:
        due_date = FUTURE_DATE
    handler = make_handler(repo)
    session = new_session()
    replies = []

    def send(text: str) -> tuple[str, bool]:
        r, done = handler.handle(text, session, phone_number=phone, channel=channel)
        replies.append(r)
        return r, done

    # Trigger
    r, done = send("register")
    assert not done, "should not complete immediately"
    assert "name" in r.lower() or "zita" in r.lower() or "ibizo" in r.lower(), f"unexpected welcome: {r}"

    # Name
    r, done = send(name)
    assert not done

    # Language (phone is pre-filled from transport, so phone step is skipped)
    r, done = send(language)
    assert not done

    # Due date
    r, done = send(due_date)
    assert not done

    # Confirmation (channel=test means channel step is skipped)
    r, done = send("yes")
    assert done, f"expected flow to complete; last reply: {r}"
    return replies


# ---------------------------------------------------------------------------
# State machine basics
# ---------------------------------------------------------------------------

class TestConversationState:
    def test_idle_session_is_not_registering(self):
        session = new_session()
        assert not session.is_registering()

    def test_registration_name_is_registering(self):
        session = new_session()
        session.state = ConversationState.REGISTRATION_NAME
        assert session.is_registering()

    def test_reset_returns_to_idle(self):
        session = new_session()
        session.state = ConversationState.REGISTRATION_LANGUAGE
        session.draft.name = "Test"
        session.reset()
        assert session.state == ConversationState.IDLE
        assert session.draft.name is None


# ---------------------------------------------------------------------------
# Validation utilities
# ---------------------------------------------------------------------------

class TestValidators:
    def test_validate_name_accepts_real_name(self):
        from utils.validators import validate_name
        assert validate_name("Chipo")
        assert validate_name("Mary Jane")

    def test_validate_name_rejects_short_or_numeric(self):
        from utils.validators import validate_name
        assert not validate_name("x")
        assert not validate_name("123")

    def test_validate_phone_accepts_zimbabwe_formats(self):
        from utils.validators import validate_phone_number
        assert validate_phone_number("0771234567")
        assert validate_phone_number("+263771234567")
        assert validate_phone_number("0712345678")

    def test_validate_phone_rejects_invalid(self):
        from utils.validators import validate_phone_number
        assert not validate_phone_number("123")
        assert not validate_phone_number("0811234567")  # 08x is not valid ZW mobile
        assert not validate_phone_number("")

    def test_normalize_phone(self):
        from utils.validators import normalize_phone_number
        assert normalize_phone_number("0771234567") == "+263771234567"
        assert normalize_phone_number("+263771234567") == "+263771234567"

    def test_parse_language_input(self):
        from utils.validators import parse_language_input
        assert parse_language_input("english") == "en"
        assert parse_language_input("Shona") == "sn"
        assert parse_language_input("ndebele") == "nd"
        assert parse_language_input("1") is None  # numbers not aliased by default

    def test_validate_due_date_accepts_near_future(self):
        from utils.validators import validate_due_date
        ok, _, parsed = validate_due_date(FUTURE_DATE)
        assert ok
        assert parsed is not None

    def test_validate_due_date_rejects_past(self):
        from utils.validators import validate_due_date
        ok, reason, _ = validate_due_date(PAST_DATE)
        assert not ok
        assert "future" in reason.lower()

    def test_validate_due_date_rejects_too_far(self):
        from utils.validators import validate_due_date
        ok, reason, _ = validate_due_date(FAR_FUTURE_DATE)
        assert not ok
        assert "far" in reason.lower()

    def test_validate_due_date_rejects_bad_format(self):
        from utils.validators import validate_due_date
        ok, reason, _ = validate_due_date("31/12/2027")
        assert not ok
        assert "YYYY-MM-DD" in reason


# ---------------------------------------------------------------------------
# RegistrationHandler unit tests
# ---------------------------------------------------------------------------

class TestRegistrationHandler:
    def test_should_start_on_register_keyword(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        assert handler.should_start("register", session)
        assert handler.should_start("I want to register", session)
        assert handler.should_start("signup", session)

    def test_should_not_start_on_regular_greeting(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        assert not handler.should_start("hello", session)

    def test_welcome_message_shown(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        r, done = handler.handle("register", session, channel="test")
        assert not done
        assert session.state == ConversationState.REGISTRATION_NAME

    def test_invalid_name_retries(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        handler.handle("register", session, channel="test")
        r, done = handler.handle("x", session, channel="test")
        assert not done
        assert "valid" in r.lower() or "name" in r.lower()
        assert session.state == ConversationState.REGISTRATION_NAME

    def test_invalid_phone_retries(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        handler.handle("register", session, phone_number="", channel="test")
        handler.handle("Chipo Moyo", session, phone_number="", channel="test")
        r, done = handler.handle("not-a-phone", session, phone_number="", channel="test")
        assert not done
        assert session.state == ConversationState.REGISTRATION_PHONE

    def test_invalid_language_retries(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_LANGUAGE
        r, done = handler.handle("Klingon", session, channel="test")
        assert not done
        assert session.state == ConversationState.REGISTRATION_LANGUAGE

    def test_invalid_due_date_retries(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_DUE_DATE
        session.draft.language = "en"
        session.draft.channel = "test"
        r, done = handler.handle("not-a-date", session, channel="test")
        assert not done
        assert "YYYY-MM-DD" in r

    def test_past_due_date_rejected(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_DUE_DATE
        session.draft.language = "en"
        session.draft.channel = "test"
        r, done = handler.handle(PAST_DATE, session, channel="test")
        assert not done
        assert "future" in r.lower()

    def test_cancel_at_name_step(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        handler.handle("register", session, channel="test")
        r, done = handler.handle("cancel", session, channel="test")
        assert done
        assert "cancel" in r.lower() or "miswa" in r.lower() or "miselwe" in r.lower()
        assert session.state == ConversationState.IDLE

    def test_cancel_at_due_date_step(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_DUE_DATE
        session.draft.language = "en"
        r, done = handler.handle("cancel", session, channel="test")
        assert done
        assert session.state == ConversationState.IDLE

    def test_cancel_at_confirm_step(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_CONFIRM
        session.draft.name = "Chipo"
        session.draft.phone_number = "+263771000001"
        session.draft.language = "en"
        session.draft.due_date = date.today() + timedelta(days=100)
        session.draft.channel = "test"
        r, done = handler.handle("no", session, channel="test")
        assert done
        assert session.state == ConversationState.IDLE

    def test_full_registration_persists_user(self):
        repo = InMemoryRepository()
        run_full_registration(repo, phone="+263771000002", name="Tendai Ncube")
        user = repo.get_user_by_phone("+263771000002")
        assert user is not None
        assert user.name == "Tendai Ncube"
        assert user.due_date is not None

    def test_full_registration_persists_pregnancy_profile(self):
        repo = InMemoryRepository()
        run_full_registration(repo, phone="+263771000003", name="Rudo Dube")
        user = repo.get_user_by_phone("+263771000003")
        profile = repo.get_pregnancy_profile(user.id)
        assert profile is not None
        assert profile.due_date is not None

    def test_no_duplicate_users_on_re_registration(self):
        repo = InMemoryRepository()
        run_full_registration(repo, phone="+263771000004", name="Sifiso Mpofu")
        # Register again — should update, not duplicate
        run_full_registration(repo, phone="+263771000004", name="Sifiso Mpofu Updated")
        users_with_phone = [u for u in repo.users.values() if u.phone_number == "+263771000004"]
        assert len(users_with_phone) == 1
        assert users_with_phone[0].name == "Sifiso Mpofu Updated"

    def test_language_response_uses_selected_language(self):
        """After choosing Shona, prompts should include Shona text."""
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        handler.handle("register", session, phone_number="+263771000005", channel="test")
        handler.handle("Rudo Mufandichimwe", session, phone_number="+263771000005", channel="test")
        # Choose Shona
        r, done = handler.handle("shona", session, phone_number="+263771000005", channel="test")
        # The due date prompt should be in Shona
        assert not done
        assert "YYYY-MM-DD" in r  # format is universal
        assert session.draft.language == "sn"

    def test_correction_of_name_at_confirm(self):
        """User can correct their name at the confirmation step."""
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_CONFIRM
        session.draft.name = "Wrong Name"
        session.draft.phone_number = "+263771000006"
        session.draft.language = "en"
        session.draft.due_date = date.today() + timedelta(days=100)
        session.draft.channel = "test"

        # Ask to correct name
        r, done = handler.handle("name", session, channel="test")
        assert not done
        assert session.state == ConversationState.REGISTRATION_NAME

        # Provide corrected name
        r, done = handler.handle("Correct Name", session, channel="test")
        assert not done
        assert session.draft.name == "Correct Name"
        # Should return to confirm
        assert session.state == ConversationState.REGISTRATION_CONFIRM

    def test_correction_of_due_date_at_confirm(self):
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        session.state = ConversationState.REGISTRATION_CONFIRM
        session.draft.name = "Chipo"
        session.draft.phone_number = "+263771000007"
        session.draft.language = "en"
        session.draft.due_date = date.today() + timedelta(days=100)
        session.draft.channel = "test"

        r, done = handler.handle("due date", session, channel="test")
        assert not done
        assert session.state == ConversationState.REGISTRATION_DUE_DATE

    def test_shona_full_registration(self):
        """Complete flow in Shona."""
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        phone = "+263773000001"

        def send(t):
            return handler.handle(t, session, phone_number=phone, channel="test")

        send("register")
        send("Rudo Mufandichimwe")
        r, done = send("shona")
        assert not done
        send(FUTURE_DATE)
        r, done = send("hongu")   # "yes" in Shona
        assert done
        user = repo.get_user_by_phone(phone)
        assert user is not None
        assert user.language == "sn"

    def test_ndebele_full_registration(self):
        """Complete flow in Ndebele."""
        repo = InMemoryRepository()
        handler = make_handler(repo)
        session = new_session()
        phone = "+263774000001"

        def send(t):
            return handler.handle(t, session, phone_number=phone, channel="test")

        send("register")
        send("Sifiso Nkosi")
        r, done = send("ndebele")
        assert not done
        send(FUTURE_DATE)
        r, done = send("yebo")    # "yes" in Ndebele
        assert done
        user = repo.get_user_by_phone(phone)
        assert user is not None
        assert user.language == "nd"


# ---------------------------------------------------------------------------
# InMemoryRepository registration tests
# ---------------------------------------------------------------------------

class TestInMemoryRepositoryRegistration:
    def test_register_user_creates_record(self):
        repo = InMemoryRepository()
        due = date.today() + timedelta(days=120)
        user, profile = repo.register_user("+263771111111", "Nyasha Banda", "en", due, "sms")
        assert user.phone_number == "+263771111111"
        assert user.name == "Nyasha Banda"
        assert user.due_date == due
        assert profile.due_date == due
        assert profile.user_id == user.id

    def test_register_user_updates_existing(self):
        repo = InMemoryRepository()
        due1 = date.today() + timedelta(days=120)
        due2 = date.today() + timedelta(days=200)
        repo.register_user("+263771111112", "Old Name", "en", due1, "sms")
        user, _ = repo.register_user("+263771111112", "New Name", "sn", due2, "whatsapp")
        assert user.name == "New Name"
        assert user.due_date == due2
        # Only one user record
        matching = [u for u in repo.users.values() if u.phone_number == "+263771111112"]
        assert len(matching) == 1


# ---------------------------------------------------------------------------
# Webhook integration tests
# ---------------------------------------------------------------------------

class TestWebhookTestEndpoint:
    @pytest.fixture
    def client(self):
        app = create_app({"TESTING": True})
        with app.test_client() as c:
            yield c

    def test_webhook_test_exists(self, client):
        # An empty message should return 400
        resp = client.post("/webhook/test", json={"message": "  "})
        assert resp.status_code == 400

    def test_full_registration_via_webhook(self, client):
        """Drive a complete registration through the /webhook/test endpoint."""
        sender = "0771234567"

        def post(text):
            return client.post(
                "/webhook/test",
                json={"message": text, "sender": sender, "channel": "test"},
            )

        # Start registration
        r = post("register")
        assert r.status_code == 200
        data = r.get_json()
        assert "name" in data["text"].lower() or "zita" in data["text"].lower()

        # Name
        r = post("Grace Chikwanda")
        assert r.status_code == 200

        # Language
        r = post("english")
        assert r.status_code == 200

        # Due date
        r = post(FUTURE_DATE)
        assert r.status_code == 200

        # Confirm
        r = post("yes")
        assert r.status_code == 200
        data = r.get_json()
        # Completion message should reference the user's name
        assert "Grace" in data["text"] or "registered" in data["text"].lower()

    def test_webhook_test_rejects_empty_message(self, client):
        resp = client.post("/webhook/test", json={"message": ""})
        assert resp.status_code == 400

    def test_webhook_test_cancel(self, client):
        sender = "0771234568"

        def post(text):
            return client.post(
                "/webhook/test",
                json={"message": text, "sender": sender, "channel": "test"},
            )

        post("register")
        post("Test User")
        r = post("cancel")
        assert r.status_code == 200
        data = r.get_json()
        assert "cancel" in data["text"].lower()

    def test_webhook_test_invalid_input_does_not_crash(self, client):
        sender = "0771234569"

        def post(text):
            return client.post(
                "/webhook/test",
                json={"message": text, "sender": sender, "channel": "test"},
            )

        post("register")
        r = post("x")    # invalid name
        assert r.status_code == 200
        data = r.get_json()
        assert "valid" in data["text"].lower() or "name" in data["text"].lower()

    def test_non_registration_message_still_works(self, client):
        r = client.post(
            "/webhook/test",
            json={"message": "hello", "sender": "0771230000", "channel": "test"},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["intent"] == "general_greeting"
