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
},
"sn": {
"general_greeting": "Mhoro. Ndiri MamaBot. Ndinogona kukubatsira nezveruzivo rwepamuviri, zviyeuchidzo zvemisangano, kana kukubatanidza nemukoti.",
"nutrition_information": "Idyai zvokudya zvakasiyana semuriwo, michero, bhinzi, zviyo, nemapuroteni akachengeteka. Inwai mvura yakachena uye shandisai mishonga sezvamakurudzirwa nemushandi wezvehutano.",
"danger_sign_query": "Handikwanisi kuongorora chirwere. Kubuda ropa zvakanyanya, kurwadziwa kukuru mudumbu, musoro unorwadza kana kusaona zvakanaka, pfari, kufema zvakaoma, fivha, kana kubuda kwemvura zvinoda rubatsiro nekukurumidza. Endai kuchipatara chiri pedyo kana kufonera rubatsiro izvozvi.",
"appointment_reminder": "Ndinogona kukubatsira kunyora zuva remusangano. Tumirai zuva nenzira yeYYYY-MM-DD, kana bvunzai kukiriniki yenyu.",
"escalation_to_nurse": "Ndichakubatsirai kubata mukoti. Kana pane njodzi ikozvino, endai kuchipatara chiri pedyo kana kufonera rubatsiro.",
"language_switch": "Ndinogona kutaura Chirungu, Shona, kana Ndebele. Itai kuti Chirungu, Shona, kana Ndebele.",
"fallback": "Handina kunyatsonzwisisa. Ndinobatsira nezviratidzo zvine ngozi, zvokudya, zviyeuchidzo, mutauro, kukwazisana, kana kubata mukoti.",
},
"nd": {
"general_greeting": "Sawubona. NginguMamaBot. Ngingabelana ngolwazi lokukhulelwa, izikhumbuzo zemihlangano, njalo ngikuncede uxhumane lomhlengikazi.",
"nutrition_information": "Zama ukudla okwehlukeneyo okufaka imibhida, izithelo, ubhontshisi, amabele, lamaprotheni aphephileyo. Natha amanzi ahlanzekileyo njalo sebenzisa izengezo ulandela izeluleko zomsebenzi wezempilo.",
"danger_sign_query": "Angikwazi ukuhlola isifo. Ukopha kakhulu, ubuhlungu obukhulu esiswini, ikhanda elibuhlungu kumbe ukubona kufiphele, ukudlikizela, ukuphefumula nzima, umkhuhlane, kumbe ukuphuma kwamanzi kudinga usizo oluphuthumayo. Hamba esibhedlela esiseduze kumbe ubize usizo khathesi.",
"appointment_reminder": "Ngingakunceda ubhale usuku lomhlangano. Thumela usuku ngefomethi yeYYYY-MM-DD, kumbe uqinisekise lomtholampilo wakho.",
"escalation_to_nurse": "Ngizakunceda uxhumane lomhlengikazi. Nxa usengozini khathesi, hamba esibhedlela esiseduze kumbe ubize usizo.",
"language_switch": "Ngingakhuluma isiNgisi, isiShona, kumbe isiNdebele. Khetha isiNgisi, isiShona, kumbe isiNdebele.",
"fallback": "Angizwisisanga kahle. Nginganceda ngezimpawu eziyingozi, ukudla, izikhumbuzo, ulimi, ukubingelela, kumbe ukuxhumana lomhlengikazi.",
},
}

def response_for(language: str, intent: str) -> str:
    language = language if language in RESPONSES else "en"
    return RESPONSES[language].get(intent, RESPONSES[language]["fallback"])
