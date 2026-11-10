"""
app/nlp/engine.py
MamaBot NLP Engine — multilingual, context-aware, follow-up capable.
"""

import json, os, pickle, re, logging
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents", "intents.json")
MODEL_PATH   = os.path.join(BASE_DIR, "instance", "nlp_model.pkl")

# ── Supported languages ───────────────────────────────────────────────────────
SUPPORTED_LANGS = {"english", "shona", "ndebele"}

# ── Instant keyword routes ────────────────────────────────────────────────────
QUICK_ROUTES = {
    "hi":"greeting","hello":"greeting","hey":"greeting","hie":"greeting",
    "helo":"greeting","hallo":"greeting","hy":"greeting","hai":"greeting",
    "ok":"greeting","okay":"greeting","yes":"greeting","no":"greeting",
    "menu":"greeting","start":"greeting","help":"greeting",
    "0":"greeting","00":"greeting","back":"greeting",
    "1":"pregnancy_stages","2":"danger_signs","3":"nutrition",
    "4":"clinic_visits","5":"labour_delivery","6":"newborn_care","7":"hiv_pmtct",
    "english":"language_english","eng":"language_english","en":"language_english",
    "shona":"language_shona","chishona":"language_shona",
    "ndebele":"language_ndebele","isindebele":"language_ndebele",
    "thank you":"thanks","thanks":"thanks","thank u":"thanks",
    "thx":"thanks","ty":"thanks","maita basa":"thanks",
    "maita zvako":"thanks","tatenda":"thanks",
    "ngiyabonga":"thanks","siyabonga":"thanks",
    "emergency":"emergency","ambulance":"emergency",
    # Shona greetings
    "mhoro":"greeting","makadii":"greeting","mangwanani":"greeting",
    "masikati":"greeting","manheru":"greeting",
    # Ndebele greetings
    "sawubona":"greeting","sanibona":"greeting","lotjhani":"greeting","yebo":"greeting",
}

SAFETY_INTENTS    = {"danger_signs", "emergency"}
SAFETY_THRESHOLD  = 0.30
DEFAULT_THRESHOLD = 0.38
SHORT_THRESHOLD   = 0.22

# ── Follow-up phrases that continue a previous topic ─────────────────────────
FOLLOWUP_PHRASES = {
    "tell me more", "more information", "explain more", "and then",
    "what else", "go on", "continue", "more", "next", "what about",
    "how about", "can you explain", "i dont understand", "clarify",
    "yes please", "please tell me", "what does that mean",
    "what should i do", "how do i", "when should i", "how often",
    "is it safe", "is it normal", "what if", "why",
    # Shona
    "ndikudzidze", "ndiudze zvimwe", "urambe", "chii chinoitika",
    "sei", "rinhi", "kangani",
    # Ndebele
    "ngitshele okunengi", "qhubeka", "kuthiwani", "ngesikhathi sini",
}

# ── Quick-reply menus per language ────────────────────────────────────────────
QUICK_REPLIES = {
    "english": [
        {"label": "Pregnancy stages",  "value": "1"},
        {"label": "Danger signs",      "value": "2"},
        {"label": "Nutrition",         "value": "3"},
        {"label": "Clinic visits",     "value": "4"},
        {"label": "Labour & delivery", "value": "5"},
        {"label": "Newborn care",      "value": "6"},
        {"label": "HIV & PMTCT",       "value": "7"},
    ],
    "shona": [
        {"label": "Matanho emimba",         "value": "1"},
        {"label": "Zviratidzo zvengozi",    "value": "2"},
        {"label": "Chikafu chakanaka",      "value": "3"},
        {"label": "Kuenda kuchipatara",     "value": "4"},
        {"label": "Kubereka",               "value": "5"},
        {"label": "Kuchengeta mwana mutsva","value": "6"},
        {"label": "HIV nePMTCT",            "value": "7"},
    ],
    "ndebele": [
        {"label": "Izigaba zokukhulelwa",      "value": "1"},
        {"label": "Izibonakaliso zengozi",     "value": "2"},
        {"label": "Ukudla okuhle",             "value": "3"},
        {"label": "Ukuyabona udokotela",       "value": "4"},
        {"label": "Ukuzala",                   "value": "5"},
        {"label": "Ukunakekela ingane entsha", "value": "6"},
        {"label": "I-HIV le-PMTCT",            "value": "7"},
    ],
}


class NLPEngine:
    def __init__(self):
        self.pipeline      = None
        self.label_encoder = None
        self.intents_data  = None
        self._load_intents()
        self._load_or_train()

    def _load_intents(self):
        with open(INTENTS_PATH, "r", encoding="utf-8") as f:
            self.intents_data = json.load(f)

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    saved = pickle.load(f)
                self.pipeline      = saved["pipeline"]
                self.label_encoder = saved["label_encoder"]
                logger.info("NLP model loaded from cache")
                return
            except Exception as e:
                logger.warning(f"Cache invalid, retraining: {e}")
                try: os.remove(MODEL_PATH)
                except: pass
        self._train()

    def _train(self):
        texts, labels = [], []
        for intent in self.intents_data["intents"]:
            for pattern in intent["patterns"]:
                texts.append(self._preprocess(pattern))
                labels.append(intent["tag"])

        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=1,
                                      max_features=5000, sublinear_tf=True)),
            ("clf", MultinomialNB(alpha=0.3)),
        ])
        self.pipeline.fit(texts, y)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"pipeline": self.pipeline, "label_encoder": self.label_encoder}, f)
        logger.info(f"Model trained on {len(texts)} samples, {len(set(labels))} intents")

    def retrain(self):
        """Reload the intent file and rebuild the cached classifier."""
        self._load_intents()
        self._train()

    def _preprocess(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s']", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def is_followup(self, text: str) -> bool:
        """Return True if the message looks like a follow-up question."""
        clean = text.lower().strip()
        if clean in FOLLOWUP_PHRASES:
            return True
        # Short messages (1–3 words) that start with question words
        words = clean.split()
        if len(words) <= 4 and words[0] in {
            "what", "how", "when", "why", "where", "which", "can",
            "is", "are", "do", "does", "will", "should", "would",
            "sei", "rinhi", "chii", "kuthiwani",
        }:
            return True
        return False

    def predict_intent(self, text: str, last_intent: str = None) -> tuple:
        """
        Returns (intent_tag, confidence).
        Uses last_intent for context-aware follow-up resolution.
        """
        clean = self._preprocess(text)
        words = len(clean.split())

        # Quick route — instant exact match
        key = QUICK_ROUTES.get(clean) or QUICK_ROUTES.get(text.strip().lower())
        if key:
            return key, 1.0

        # Follow-up — continue previous topic
        if last_intent and last_intent not in ("fallback", "greeting", "thanks") \
                and self.is_followup(text):
            return last_intent, 0.75

        # NLP classification
        probs   = self.pipeline.predict_proba([clean])[0]
        top_idx = probs.argmax()
        conf    = probs[top_idx]
        intent  = self.label_encoder.inverse_transform([top_idx])[0]

        # Threshold selection
        if words <= 2:
            threshold = SHORT_THRESHOLD
        elif intent in SAFETY_INTENTS:
            threshold = SAFETY_THRESHOLD
        else:
            threshold = DEFAULT_THRESHOLD

        if conf < threshold:
            # Safety net — always catch danger/emergency even at low conf
            for idx in probs.argsort()[::-1][:3]:
                candidate = self.label_encoder.inverse_transform([idx])[0]
                if candidate in SAFETY_INTENTS and probs[idx] > SAFETY_THRESHOLD:
                    return candidate, probs[idx]
            # Context carry-forward for short ambiguous messages
            if last_intent and last_intent not in ("fallback", "greeting") \
                    and words <= 3:
                return last_intent, 0.5
            return "fallback", conf

        return intent, conf

    def get_response(self, intent_tag: str, language: str = "english") -> str:
        """Return the response in the correct language."""
        lang = language if language in SUPPORTED_LANGS else "english"
        for intent in self.intents_data["intents"]:
            if intent["tag"] == intent_tag:
                responses = intent.get("responses", {})
                if isinstance(responses, dict):
                    return responses.get(lang) or responses.get("english", "")
                # Legacy string format
                return responses
        return self._fallback_response(lang)

    def get_quick_replies(self, language: str = "english") -> list:
        """Return quick reply buttons in the correct language."""
        return QUICK_REPLIES.get(language, QUICK_REPLIES["english"])

    def _fallback_response(self, language: str = "english") -> str:
        fallbacks = {
            "english": (
                "I did not quite understand that.\n\n"
                "Please reply with a number:\n"
                "1 — Pregnancy stages\n"
                "2 — Danger signs\n"
                "3 — Nutrition\n"
                "4 — Clinic visits\n"
                "5 — Labour & delivery\n"
                "6 — Newborn care\n"
                "7 — HIV & PMTCT\n\n"
                "Or ask me anything about your pregnancy."
            ),
            "shona": (
                "Handina kunzwisisa chaizvo.\n\n"
                "Ndapota pindura nenambari:\n"
                "1 — Matanho emimba\n"
                "2 — Zviratidzo zvengozi\n"
                "3 — Chikafu chakanaka\n"
                "4 — Kuenda kuchipatara\n"
                "5 — Kubereka\n"
                "6 — Kuchengeta mwana mutsva\n"
                "7 — HIV nePMTCT\n\n"
                "Kana ubvunze chero chinhu pamusoro pemimba yako."
            ),
            "ndebele": (
                "Angizwisisanga kahle.\n\n"
                "Sicela uphendule ngenombolo:\n"
                "1 — Izigaba zokukhulelwa\n"
                "2 — Izibonakaliso zengozi\n"
                "3 — Ukudla okuhle\n"
                "4 — Ukuyabona udokotela\n"
                "5 — Ukuzala\n"
                "6 — Ukunakekela ingane entsha\n"
                "7 — I-HIV le-PMTCT\n\n"
                "Noma ubuze noma yini ngokukhuluma kwakho."
            ),
        }
        return fallbacks.get(language, fallbacks["english"])


# ── Singleton ──────────────────────────────────────────────────────────────────
_instance = None

def get_engine() -> NLPEngine:
    global _instance
    if _instance is None:
        _instance = NLPEngine()
    return _instance

get_nlp = get_engine  # backwards compatibility
