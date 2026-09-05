"""Safe, conservative response catalog for supported languages."""

RESPONSES = {
    "en": {
        "general_greeting": "Hello. I am MamaBot. I can share pregnancy information, appointment reminders, and help you contact a nurse.",
        "nutrition_information": "Try a varied diet with vegetables, fruit, beans, whole grains, and safe proteins. Drink clean water and take supplements only as advised by your health worker.",
        "danger_sign_query": "I cannot diagnose a condition. Heavy bleeding, severe abdominal pain, severe headache or blurred vision, convulsions, difficulty breathing, fever, or leaking fluid need urgent care. Please go to the nearest health facility or call emergency services now.",
        "appointment_reminder": "I can help record an appointment date. Please send it in YYYY-MM-DD format, or contact your clinic if you need to confirm the date.",
        "escalation_to_nurse": "I will help you contact a nurse. If you may be in immediate danger, go to the nearest health facility or call emergency services now.",
        "language_switch": "I can communicate in English, Shona, or Ndebele. Say English, Shona, or Ndebele to choose a language.",
        "fallback": "I am not sure I understood. I can help with danger signs, nutrition, appointment reminders, language choice, greetings, or contacting a nurse.",
        # Registration flow
        "reg_welcome": (
            "Welcome to MamaBot. Let me register you so I can send you ANC reminders. "
            "You can type CANCEL at any time to stop.\n\nWhat is your name?"
        ),
        "reg_ask_name": "What is your name?",
        "reg_ask_phone": "Please share your Zimbabwe mobile number (e.g. 0771234567).",
        "reg_ask_language": (
            "What language do you prefer?\n"
            "1. English\n2. Shona\n3. Ndebele\n\n"
            "Reply with the name or number."
        ),
        "reg_ask_due_date": (
            "What is your expected delivery date? "
            "Please use YYYY-MM-DD format (e.g. {example})."
        ),
        "reg_ask_channel": (
            "How would you like to receive reminders?\n"
            "1. SMS\n2. WhatsApp\n3. Browser\n\n"
            "Reply with the name or number."
        ),
        "reg_confirm": (
            "Please confirm your details:\n"
            "  Name: {name}\n"
            "  Phone: {phone}\n"
            "  Language: {lang_display}\n"
            "  Expected delivery: {due_date}\n"
            "  Channel: {channel}\n\n"
            "Reply YES to confirm, NO to start over, or the name of a field to correct it "
            "(e.g. 'name', 'phone', 'language', 'due date', 'channel')."
        ),
        "reg_complete": (
            "You are registered, {name}! "
            "I will send you ANC reminders before your appointments. "
            "Stay well and visit your clinic regularly."
        ),
        "reg_already_registered": (
            "You are already registered, {name}. "
            "Reply YES to update your details or NO to continue."
        ),
        "reg_cancelled": "Registration cancelled. Send a message any time to start again.",
        "reg_invalid_name": "Please enter a valid name (at least two characters).",
        "reg_invalid_phone": "Please enter a valid Zimbabwe mobile number (e.g. 0771234567 or +2637xxxxxxxx).",
        "reg_invalid_language": "Please choose: 1 (English), 2 (Shona), or 3 (Ndebele).",
        "reg_invalid_due_date": "That date could not be accepted: {reason}. Please use YYYY-MM-DD format.",
        "reg_invalid_channel": "Please choose: 1 (SMS), 2 (WhatsApp), or 3 (Browser).",
        "reg_correct_prompt": "Please enter your corrected {field}:",
        "reg_error": "Something went wrong saving your registration. Please try again.",
    },
    "sn": {
        "general_greeting": "Mhoro. Ndiri MamaBot. Ndinogona kukubatsira nezveruzivo rwepamuviri, zviyeuchidzo zvemisangano, kana kukubatanidza nemukoti.",
        "nutrition_information": "Idyai zvokudya zvakasiyana semuriwo, michero, bhinzi, zviyo, nemapuroteni akachengeteka. Inwai mvura yakachena uye shandisai mishonga sezvamakurudzirwa nemushandi wezvehutano.",
        "danger_sign_query": "Handikwanisi kuongorora chirwere. Kubuda ropa zvakanyanya, kurwadziwa kukuru mudumbu, musoro unorwadza kana kusaona zvakanaka, pfari, kufema zvakaoma, fivha, kana kubuda kwemvura zvinoda rubatsiro nekukurumidza. Endai kuchipatara chiri pedyo kana kufonera rubatsiro izvozvi.",
        "appointment_reminder": "Ndinogona kukubatsira kunyora zuva remusangano. Tumirai zuva nenzira yeYYYY-MM-DD, kana bvunzai kukiriniki yenyu.",
        "escalation_to_nurse": "Ndichakubatsirai kubata mukoti. Kana pane njodzi ikozvino, endai kuchipatara chiri pedyo kana kufonera rubatsiro.",
        "language_switch": "Ndinogona kutaura Chirungu, Shona, kana Ndebele. Itai kuti Chirungu, Shona, kana Ndebele.",
        "fallback": "Handina kunyatsonzwisisa. Ndinobatsira nezviratidzo zvine ngozi, zvokudya, zviyeuchidzo, mutauro, kukwazisana, kana kubata mukoti.",
        # Registration flow
        "reg_welcome": (
            "Mauya kuMamaBot. Ngatikurejistarire kuitira kuti nditumire zviyeuchidzo zveANC. "
            "Unogona kunyora CANCEL panguva ipi neipi kusiya.\n\nZita rako nderei?"
        ),
        "reg_ask_name": "Zita rako nderei?",
        "reg_ask_phone": "Tapota ipa nhamba yako yefoni yeZimbabwe (somuenzaniso 0771234567).",
        "reg_ask_language": (
            "Unoda kutaura mutauro upi?\n"
            "1. Chirungu\n2. Shona\n3. Ndebele\n\n"
            "Pindura nezita kana nhamba."
        ),
        "reg_ask_due_date": (
            "Zuva raungangoda kusununguka riri ripi? "
            "Shandisai chimiro cheYYYY-MM-DD (somuenzaniso {example})."
        ),
        "reg_ask_channel": (
            "Unoda kugamuchira zviyeuchidzo sei?\n"
            "1. SMS\n2. WhatsApp\n3. Browser\n\n"
            "Pindura nezita kana nhamba."
        ),
        "reg_confirm": (
            "Simbisai ruzivo rwenyu:\n"
            "  Zita: {name}\n"
            "  Foni: {phone}\n"
            "  Mutauro: {lang_display}\n"
            "  Zuva rekuzvara: {due_date}\n"
            "  Nzira: {channel}\n\n"
            "Pindura HONGU kusimbisa, AIWA kutanga patsva, kana zita rechikamu kugadzirisa "
            "(somuenzaniso 'zita', 'foni', 'mutauro', 'zuva', 'nzira')."
        ),
        "reg_complete": (
            "Warejistawa, {name}! "
            "Ndichatumira zviyeuchidzo zveANC. "
            "Chengeteka uye shanyira kiriniki yako nguva dzose."
        ),
        "reg_already_registered": (
            "Warejistawa kare, {name}. "
            "Pindura HONGU kugadzirisa ruzivo rwako kana AIWA kuenderera mberi."
        ),
        "reg_cancelled": "Kurejista kwamiswa. Tumira meseji chero nguva kutanga zvakare.",
        "reg_invalid_name": "Ndokumbira upe zita rakanaka (manauro maviri kana kupfuura).",
        "reg_invalid_phone": "Ndokumbira upe nhamba yeZimbabwe yakanaka (somuenzaniso 0771234567).",
        "reg_invalid_language": "Ndokumbira sarudza: 1 (Chirungu), 2 (Shona), kana 3 (Ndebele).",
        "reg_invalid_due_date": "Zuva iro harigumirano: {reason}. Shandisai chimiro cheYYYY-MM-DD.",
        "reg_invalid_channel": "Ndokumbira sarudza: 1 (SMS), 2 (WhatsApp), kana 3 (Browser).",
        "reg_correct_prompt": "Ndokumbira ipe {field} yakagadziridzwa:",
        "reg_error": "Pane chakakanganisika pakuchengetedza rejistaresheni yako. Ndokumbira edzazve.",
    },
    "nd": {
        "general_greeting": "Sawubona. NginguMamaBot. Ngingabelana ngolwazi lokukhulelwa, izikhumbuzo zemihlangano, njalo ngikuncede uxhumane lomhlengikazi.",
        "nutrition_information": "Zama ukudla okwehlukeneyo okufaka imibhida, izithelo, ubhontshisi, amabele, lamaprotheni aphephileyo. Natha amanzi ahlanzekileyo njalo sebenzisa izengezo ulandela izeluleko zomsebenzi wezempilo.",
        "danger_sign_query": "Angikwazi ukuhlola isifo. Ukopha kakhulu, ubuhlungu obukhulu esiswini, ikhanda elibuhlungu kumbe ukubona kufiphele, ukudlikizela, ukuphefumula nzima, umkhuhlane, kumbe ukuphuma kwamanzi kudinga usizo oluphuthumayo. Hamba esibhedlela esiseduze kumbe ubize usizo khathesi.",
        "appointment_reminder": "Ngingakunceda ubhale usuku lomhlangano. Thumela usuku ngefomethi yeYYYY-MM-DD, kumbe uqinisekise lomtholampilo wakho.",
        "escalation_to_nurse": "Ngizakunceda uxhumane lomhlengikazi. Nxa usengozini khathesi, hamba esibhedlela esiseduze kumbe ubize usizo.",
        "language_switch": "Ngingakhuluma isiNgisi, isiShona, kumbe isiNdebele. Khetha isiNgisi, isiShona, kumbe isiNdebele.",
        "fallback": "Angizwisisanga kahle. Nginganceda ngezimpawu eziyingozi, ukudla, izikhumbuzo, ulimi, ukubingelela, kumbe ukuxhumana lomhlengikazi.",
        # Registration flow
        "reg_welcome": (
            "Wamkelekile kuMamaBot. Ake ngikubhalise ukuze ngikuthumele izikhumbuzo ze-ANC. "
            "Ungathayipha CANCEL nganoma nini ukuyeka.\n\nNgubani ibizo lakho?"
        ),
        "reg_ask_name": "Ngubani ibizo lakho?",
        "reg_ask_phone": "Sicela unike inombolo yakho yefoni yaseZimbabwe (isibonelo 0771234567).",
        "reg_ask_language": (
            "Ufuna ulimi luni?\n"
            "1. IsiNgisi\n2. IsiShona\n3. IsiNdebele\n\n"
            "Phendula ngebizo kumbe inombolo."
        ),
        "reg_ask_due_date": (
            "Lithini usuku olulindelekileyo lokuzala? "
            "Sebenzisa ifomethi ye-YYYY-MM-DD (isibonelo {example})."
        ),
        "reg_ask_channel": (
            "Ungathanda ukuthola izikhumbuzo kanjani?\n"
            "1. SMS\n2. WhatsApp\n3. Ibhrawuza\n\n"
            "Phendula ngebizo kumbe inombolo."
        ),
        "reg_confirm": (
            "Sicela uqinisekise imininingwane yakho:\n"
            "  Ibizo: {name}\n"
            "  Ifoni: {phone}\n"
            "  Ulimi: {lang_display}\n"
            "  Usuku lokuzala: {due_date}\n"
            "  Indlela: {channel}\n\n"
            "Phendula YEBO ukuqinisekisa, CHA ukuqala kabusha, kumbe igama lensimu ozosiguqula "
            "(isibonelo 'ibizo', 'ifoni', 'ulimi', 'usuku', 'indlela')."
        ),
        "reg_complete": (
            "Ubhalisile, {name}! "
            "Ngizakuthumela izikhumbuzo ze-ANC. "
            "Hlala uphila uye emtholampilo wakho njalonjalo."
        ),
        "reg_already_registered": (
            "Usuvele ubhalisile, {name}. "
            "Phendula YEBO ukuhlela imininingwane yakho kumbe CHA uqhubeke."
        ),
        "reg_cancelled": "Ukubhaliswa kumiselwe. Thumela umyalezo nganoma nini ukuqala kabusha.",
        "reg_invalid_name": "Sicela unike ibizo elifaneleyo (okungenani izinhlamvu ezimbili).",
        "reg_invalid_phone": "Sicela unike inombolo yaseZimbabwe efaneleyo (isibonelo 0771234567).",
        "reg_invalid_language": "Sicela ukhethe: 1 (IsiNgisi), 2 (IsiShona), kumbe 3 (IsiNdebele).",
        "reg_invalid_due_date": "Lolo suku alwamukeleki: {reason}. Sebenzisa ifomethi ye-YYYY-MM-DD.",
        "reg_invalid_channel": "Sicela ukhethe: 1 (SMS), 2 (WhatsApp), kumbe 3 (Ibhrawuza).",
        "reg_correct_prompt": "Sicela unike {field} okuguqulwayo:",
        "reg_error": "Kuye kwaba nenkinga yokulondoloza ukubhaliswa kwakho. Sicela uzame futhi.",
    },
}

# Human-readable language labels per language
LANGUAGE_LABELS: dict[str, dict[str, str]] = {
    "en": {"en": "English", "sn": "Shona", "nd": "Ndebele"},
    "sn": {"en": "Chirungu", "sn": "Shona", "nd": "Ndebele"},
    "nd": {"en": "IsiNgisi", "sn": "IsiShona", "nd": "IsiNdebele"},
}

CHANNEL_LABELS: dict[str, dict[str, str]] = {
    "en": {"sms": "SMS", "whatsapp": "WhatsApp", "browser": "Browser", "test": "Test"},
    "sn": {
        "sms": "SMS",
        "whatsapp": "WhatsApp",
        "browser": "Browser",
        "test": "Bvunzo",
    },
    "nd": {
        "sms": "SMS",
        "whatsapp": "WhatsApp",
        "browser": "Ibhrawuza",
        "test": "Uhlelo",
    },
}


def response_for(language: str, intent: str, **kwargs: object) -> str:
    lang = language if language in RESPONSES else "en"
    if intent == "nurse_escalation":
        intent = "escalation_to_nurse"
    template = RESPONSES[lang].get(intent, RESPONSES[lang]["fallback"])
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template
