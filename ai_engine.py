import json
import streamlit as st
from openai import OpenAI

SENTENCE_LENGTH_LIMITS = {
    "A1": (8, 12),
    "A2": (10, 14),
    "B1": (12, 17),
    "B2": (15, 22),
    "C1": (18, 28)
}

def get_cognitive_config(level: str) -> dict:
    """Kullanıcının seviyesine göre dinamik bilişsel kurallar döndürür."""
    min_len, max_len = SENTENCE_LENGTH_LIMITS.get(level.upper(), (12, 17))
    
    return {
        "max_sentence_length": max_len,
        "min_sentence_length": min_len,
        "use_active_verbs": True,
        "avoid_metadiscourse": True,
        "show_not_tell": True,
        "concrete_scene_per_paragraph": 1
    }

def build_memory_instruction(heatmap_vocab):
    """Kullanıcının geçmiş kelime hafızasına göre bilişsel devamlılık (continuity) kurallarını hazırlar."""
    if not heatmap_vocab:
        return ""
        
    known_words = [w for w, status in heatmap_vocab.items() if "I know this" in str(status)]
    seen_words = [w for w, status in heatmap_vocab.items() if "I've seen this" in str(status)]
    new_words = [w for w, status in heatmap_vocab.items() if "New to me" in str(status)]
    
    return f"""
    \nCRITICAL - COGNITIVE CONTINUITY & LEARNER PROFILE ADAPTATION:
    The user has a personalized vocabulary history tracking profile:
    - 🔴 New to me (Target / In-need of reinforcement): {new_words}
    - 🟡 I've seen this (In-progress / Developing): {seen_words}
    - 🟢 I know this (Mastered / Familiar): {known_words}
    
    CONTINUITY GENERATION RULES:
    1. SEAMLESS REUSE: Pick 1 to 2 words from '🔴 New to me' (or '🟡 I've seen this') and weave them NATURALLY into the new context/story. Do NOT force them unnaturally.
    2. STRUCTURAL SCAFFOLDING: Reuse familiar simple sentence patterns (e.g. Subject + Verb + Object) from previous contexts so the reader recognizes the structure even with new vocabulary.
    3. COGNITIVE LOAD CONTROL: Limit completely unfamiliar, advanced words to at most 2-3 words. The rest should rely on familiar scaffolding and clear representative vocabulary.
    4. Do NOT fill the text with words from '🟢 I know this' unless contextually essential.
    """

@st.cache_data(show_spinner=False, ttl=3600)
def _cached_openai_generation(api_key, target_language, seviye, ton, kelime_sayisi, konu, vocab_tuple, settings_tuple):
    """Önbelleklenen (Cached) OpenAI API çağrı katmanı - Maliyet ve Token Koruması"""
    # Hashlenebilir tuple formatından tekrar sözlüklere dönüştürüyoruz
    heatmap_vocab = dict(vocab_tuple)
    exercise_settings = dict(settings_tuple)

    final_topic = konu if konu.strip() else "General topics suitable for this level"
    cognitive_config = get_cognitive_config(seviye)

    cognitive_rules = f"""
    STRICT READING COMPREHENSION RULES (Cognitive Optimization):
    1. SYNTAX & LENGTH: Keep sentences strictly between {cognitive_config['min_sentence_length']} and {cognitive_config['max_sentence_length']} words.
    2. SHOW, DON'T TELL: Do not use abstract emotional descriptions. Include at least {cognitive_config['concrete_scene_per_paragraph']} concrete visual scene per paragraph.
    3. NO ZOMBIENESS: Use active, direct verbs only. Avoid nominalizations.
    4. NO META-DISCOURSE: Do NOT write "In this story..." or "You will read...". Start directly with the narrative scene.
    5. REPRESENTATIVE VOCABULARY: Do not overwhelm the reader with many items from the same category (e.g., do not list 5 different fruits or animals; use 1-2 representative items).
    """

    client = OpenAI(api_key=api_key)
    
    exercise_requirements = []
    json_exercise_schema = {}

    if exercise_settings.get("show_tf"):
        exercise_requirements.append("- true_false: 3 statements based on the text. Each statement MUST have 'statement' (string), 'correct_answer' (boolean), 'evidence' (exact sentence from text)")
        json_exercise_schema["true_false"] = [{"statement": "example statement", "correct_answer": True, "evidence": "exact sentence from text"}]

    if exercise_settings.get("show_mc"):
        exercise_requirements.append("- multiple_choice: 3 questions. Each question MUST have 'question' (string), 'options' (array of strings), 'correct_answer': 'Option A', 'evidence': 'exact sentence from text'")
        json_exercise_schema["multiple_choice"] = [{"question": "example question", "options": ["Option A", "Option B"], "correct_answer": "Option A", "evidence": "exact sentence from text"}]

    if exercise_settings.get("show_writing"):
        exercise_requirements.append("- open_ended: 1 writing prompt string asking the user to write a short paragraph.")
        json_exercise_schema["open_ended"] = "example writing prompt here"
        
    exercise_req_text = "\n".join(exercise_requirements)
    adaptive_instruction = build_memory_instruction(heatmap_vocab)
    cognitive_instruction = f"\n{cognitive_rules}\n"
    
    system_prompt = (
        "You are an expert " + str(target_language) + " language teacher that outputs raw JSON data.\n"
        "You must return a valid JSON object matching this strict schema exactly:\n"
        "{\n"
        "   \"reading_difficulty\": {\n"
        "      \"vocabulary\": \"★★★★☆\",\n"
        "      \"grammar\": \"★★★☆☆\",\n"
        "      \"inference\": \"★★★★★\"\n"
        "   },\n"
        "   \"estimated_reading_time\": \"4 min\",\n"
        "   \"title\": \"Title of the reading text\",\n"
        "   \"text\": \"The complete reading text\",\n"
        "   \"vocabulary\": [\n"
        "      {\n"
        "         \"word\": \"[Base lemma form of the word]\",\n"
        "         \"meaning\": \"[Turkish meaning]\",\n"
        "         \"level\": \"[CEFR level]\",\n"
        "         \"pronunciation\": \"[IPA]\",\n"
        "         \"example\": \"[Example sentence]\",\n"
        "         \"variants\": [\n"
        "             {\"form\": \"[The exact text variant used]\", \"explanation\": \"[Grammar description in Turkish]\"}\n"
        "         ]\n"
        "      }\n"
        "   ],\n"
        "   \"exercises\": " + json.dumps(json_exercise_schema) + "\n"
        "}\n\n"
        "GRAMMATICAL ACCURACY & VARIANT RULES:\n"
        "- Check parts of speech carefully. If a word is a noun and ends with a plural marker (e.g. Dutch 'fiets' -> 'fietsen', German 'Hund' -> 'Hunde'), classify it as 'Çoğul İsim' (Plural Noun), NEVER as past tense or verb conjugation.\n"
        "- Only describe verbal tense (e.g. 'Geçmiş Zaman') if the word is genuinely acting as a verb in that sentence.\n\n"
        "VOCABULARY CONSTRAINTS:\n"
        "- Generate exactly 5 vocabulary words from the generated text.\n"
        "- The vocabulary words MUST be strictly in the selected target language (" + str(target_language) + ") and match the requested CEFR level (" + str(seviye) + ").\n"
        "Include only the requested exercises in the 'exercises' object:\n" + str(exercise_req_text) + "\n"
        + str(adaptive_instruction)
        + str(cognitive_instruction)
    )
    
    user_prompt = f"Write a reading text in {target_language}. Level: {seviye}, Tone: {ton}, Length: ~{kelime_sayisi} words, Subject: {final_topic}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=1500
    )
    
    raw_json_string = response.choices[0].message.content
    return json.loads(raw_json_string)

def generate_reading_package(api_key, target_language, seviye, ton, kelime_sayisi, konu, heatmap_vocab, exercise_settings):
    """
    Sözlükleri hashlenebilir tuple formatına çevirerek önbellekli fonksiyonu tetikler.
    """
    try:
        # Dict yapılarını önbellek (cache) ile uyumlu hale getiriyoruz
        vocab_tuple = tuple(sorted((k, str(v)) for k, v in heatmap_vocab.items())) if heatmap_vocab else tuple()
        settings_tuple = tuple(sorted(exercise_settings.items())) if exercise_settings else tuple()
        
        parsed_data = _cached_openai_generation(
            api_key, target_language, seviye, ton, kelime_sayisi, konu, vocab_tuple, settings_tuple
        )
        return True, parsed_data, None
    except Exception as e:
        return False, None, str(e)

def generate_explanation(api_key, target_language, reading_text, question, user_answer, correct_evidence):
    try:
        client = OpenAI(api_key=api_key)
        system_prompt = (
            "You are an expert supportive language teacher evaluating a student's wrong answer. "
            "Analyze the root cause of the student's mistake and classify it into exactly one of these 5 types:\n"
            "- 📖 Vocabulary\n"
            "- 🧩 Grammar\n"
            "- 💡 Inference\n"
            "- 👀 Careless Reading\n"
            "- 🤔 False Assumption\n\n"
            "CRITICAL FORMATTING RULE: You must output exactly 5 lines, using literal '\\n' line breaks between each line:\n"
            "Line 1: '🔍 Mistake Type: [Insert exactly one of the 5 categories above]'\n"
            "Line 2: '💡 Why?: [1 short sentence explaining the error in simple clear B1 English]'\n"
            "Line 3: '[Exact Turkish translation of Line 2]'\n"
            "Line 4: '🎯 Learning Tip: [Explain the specific grammar/morphology transformation or provide a high-value tip based on the sentence.]'\n"
            "Line 5: '[Exact Turkish translation of Line 4]'\n\n"
            "Do not output anything else. Keep lines completely separate."
        )
        user_prompt = f"""
        Reading Text Context: {reading_text}
        Question Asked: {question}
        User's Incorrect Answer: {user_answer}
        Correct Evidence Sentence from Text: {correct_evidence}
        Provide the explanation with a line break now:
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_completion_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Açıklama üretilemedi: {str(e)}"
    
def generate_speech(api_key, text_to_speak):
    try:
        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  
            input=text_to_speak
        )
        return response.read()
    except Exception as e:
        return None