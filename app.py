import os
import streamlit as st
from storage import load_heatmap, save_heatmap, load_reading_session, save_reading_session
from highlighter import highlight_text
from ai_engine import (
    generate_reading_package,
    generate_explanation,
    generate_speech,
    evaluate_content_recall,
)
from ui import render_sidebar, render_vocabulary_assistant, render_exercises
from quota_manager import check_and_increment_quota, get_current_quota

st.set_page_config(page_title="VosWeave", page_icon="🦊", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none !important;}
    .highlight-green { background-color: rgba(40, 167, 69, 0.25); border-bottom: 2px solid #28a745; padding: 0 4px; border-radius: 4px; }
    .highlight-yellow { background-color: rgba(255, 193, 7, 0.3); border-bottom: 2px solid #ffc107; padding: 0 4px; border-radius: 4px; }
    .highlight-red { background-color: rgba(220, 53, 69, 0.25); border-bottom: 2px solid #dc3545; padding: 0 4px; border-radius: 4px; }
    .main-title { text-align: center; color: #1E3A8A; font-weight: bold; margin-bottom: 5px; }
    .subtitle { text-align: center; color: #6B7280; font-weight: bold; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

# --- KULLANICI GİRİŞİ KONTROLÜ (GATEKEEPER) ---
# AttributeError önlemi: getattr ile güvenli okuma
is_logged_in = getattr(st.user, "is_logged_in", False) if hasattr(st, "user") else False

# Codespaces ortamında yerel test yaparken otomatik geçiş sağlar; canlıda (production) ise login zorunluluğunu korur
is_local_dev = os.getenv("CODESPACES") == "true"

if not is_logged_in and not is_local_dev:
    st.title("🦊 VosWeave")
    st.caption("Adaptive Cognitive Reading & Language Continuity Engine")
    st.info("Lütfen devam etmek için Google hesabınızla giriş yapın.")
    if st.button("Sign in with Google 🚀", type="primary"):
        st.login("google")
    st.stop()

if 'heatmap_vocab' not in st.session_state:
    st.session_state['heatmap_vocab'] = load_heatmap()

if 'learner_analytics' not in st.session_state:
    from storage import load_analytics
    st.session_state['learner_analytics'] = load_analytics()    

if 'saved_session' not in st.session_state:
    st.session_state['saved_session'] = load_reading_session()

saved = st.session_state['saved_session'] if st.session_state['saved_session'] is not None else {}

st.markdown("<h1 class='main-title'>🦊 VosWeave</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Adaptive Cognitive Reading & Language Continuity Engine</p>", unsafe_allow_html=True)
st.write("---")

# Secrets dosyası yoksa patlamaması için güvenli kontrol:
secret_key = ""
try:
    secret_key = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    secret_key = ""

api_key = os.getenv("OPENAI_API_KEY") or secret_key
if not api_key:
    st.warning("⚠️ Please define 'OPENAI_API_KEY' in your system environment or Streamlit Secrets.")
    api_key = st.text_input("Or enter your API Key here for testing:", type="password")

lang_options = ["Nederlands", "English", "Deutsch", "French", "Korean", "Spanish"]
default_lang_idx = lang_options.index(saved["ui_target_language"]) if "ui_target_language" in saved else 0
target_language = st.selectbox("Select the language you want to learn:", lang_options, index=default_lang_idx)
st.write("")

col1, col2, col3, col4 = st.columns(4)
level_options = ["A1", "A2", "B1", "B2", "C1"]
default_level_idx = level_options.index(saved["ui_seviye"]) if "ui_seviye" in saved else 0

tone_options = ["Casual", "Friendly", "Formal", "Academic"]
default_tone_idx = tone_options.index(saved["ui_ton"]) if "ui_ton" in saved else 0

with col1:
    seviye = st.selectbox("CEFR Level", level_options, index=default_level_idx)
with col2:
    ton = st.selectbox("Text Tone", tone_options, index=default_tone_idx)
with col3:
    kelime_sayisi = st.number_input("Word Count", min_value=30, max_value=500, value=saved.get("ui_kelime_sayisi", 100), step=10)
with col4:
    konu = st.text_input("Topic", value=saved.get("ui_konu", ""), placeholder="e.g., Daily Routine, Hobbies, Travel...")
st.write("")

st.markdown("### 🛠️ Select Exercise Types")
ex_col1, ex_col2, ex_col3 = st.columns(3)
with ex_col1:
    show_tf = st.checkbox("True / False", value=saved.get("ui_show_tf", True))
with ex_col2:
    show_mc = st.checkbox("Reading Comprehension", value=saved.get("ui_show_mc", True))
with ex_col3:
    show_writing = st.checkbox("Open-ended Writing", value=saved.get("ui_show_writing", False))
st.write("")

used_count, max_limit = get_current_quota(max_daily_limit=10)
remaining = max_limit - used_count
st.caption(f"⚡ Daily AI Quota Remaining: **{remaining} / {max_limit}**")

if st.button("Generate Text & Exercises 🚀", use_container_width=True):
    allowed, current_count = check_and_increment_quota(max_daily_limit=10)
    
    if not allowed:
        st.error(f"🚨 You have reached your daily AI text generation quota (10/10)! See you tomorrow.")
    else:
        st.info(f"📊 Today's AI usage count: {current_count}/10")
        
        if 'saved_session' in st.session_state:
            del st.session_state['saved_session']

        if not api_key:
            st.error("⚠️ Please enter a valid API Key before generating content.")
        else:
            with st.spinner(f"Generating {target_language} data structure..."):
                exercise_settings = {"show_tf": show_tf, "show_mc": show_mc, "show_writing": show_writing}
                
                success, parsed_data, error_msg = generate_reading_package(
                    api_key, target_language, seviye, ton, kelime_sayisi, konu,
                    st.session_state['heatmap_vocab'], exercise_settings
                )
            
            if success:
                # Yeni metin üretildiğinde önceki recall verilerini sıfırla
                st.session_state["recall_text_visible"] = True
                st.session_state.pop("content_recall_answer", None)
                st.session_state.pop("content_recall_feedback", None)

                session_payload = {
                    "api_data": parsed_data, "ui_target_language": target_language,
                    "ui_seviye": seviye, "ui_ton": ton, "ui_kelime_sayisi": kelime_sayisi,
                    "ui_konu": konu, "ui_show_tf": show_tf, "ui_show_mc": show_mc, "ui_show_writing": show_writing
                }
                st.session_state['saved_session'] = session_payload
                save_reading_session(session_payload)
                st.rerun()
            else:
                st.error(f"OpenAI API Error: {error_msg}")

if st.session_state['saved_session'] is not None and "api_data" in st.session_state['saved_session']:
    data = st.session_state['saved_session']["api_data"]
    st.write("---")
    
    main_col1, main_col2 = st.columns([1.1, 1.0], gap="large")
    
    # 📖 SOL KOLON: Sabit Okuma Metni, Skorlar, Seslendirme ve Recall Alanı
    with main_col1:
        st.subheader(f"📖 {data.get('title', 'Reading Text')}")
        
        # Zorluk Skorları ve Okuma Süresi Etiketleri
        diff = data.get('reading_difficulty', {})
        reading_time = data.get('estimated_reading_time', 'N/A')
        
        st.markdown(f"""
        <div style='margin-bottom: 15px; font-size: 0.95rem; color: #9CA3AF;'>
            ⏱️ <strong>Estimated Time:</strong> {reading_time} &nbsp;|&nbsp; 
            📚 <strong>Vocab:</strong> <span style='color: #1c8cf0;'>{diff.get('vocabulary', '★★★☆☆')}</span> &nbsp;|&nbsp; 
            🧩 <strong>Grammar:</strong> <span style='color: #1c8cf0;'>{diff.get('grammar', '★★★☆☆')}</span> &nbsp;|&nbsp; 
            💡 <strong>Inference:</strong> <span style='color: #1c8cf0;'>{diff.get('inference', '★★★☆☆')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # --- READING TEXT VISIBILITY ---
        if "recall_text_visible" not in st.session_state:
            st.session_state["recall_text_visible"] = True

        if st.session_state["recall_text_visible"]:
            reading_text = highlight_text(
                data.get("text", ""),
                st.session_state['heatmap_vocab']
            )
            st.markdown(
                f"<div style='line-height:1.8; font-size:1.1rem; "
                f"background-color: rgba(255,255,255,0.03); "
                f"padding: 15px; border-radius: 8px; "
                f"border: 1px solid rgba(255,255,255,0.1);'>"
                f"{reading_text}</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("🔒 The reading text is hidden. Try to recall its main ideas.")

        st.write("")

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.session_state["recall_text_visible"]:
                if st.button(
                    "🔊 Listen to Whole Text",
                    use_container_width=True,
                    key="listen_whole_text_main"
                ):
                    with st.spinner("Generating audio..."):
                        entire_audio = generate_speech(api_key, data.get("text", ""))
                        if entire_audio:
                            st.audio(entire_audio, format="audio/mp3", autoplay=True)

        with btn_c2:
            toggle_label = "🔒 Hide text to practice" if st.session_state["recall_text_visible"] else "👀 Show reading text"
            if st.button(toggle_label, use_container_width=True, key="toggle_recall_text"):
                st.session_state["recall_text_visible"] = not st.session_state["recall_text_visible"]
                st.rerun()

        # --- RECALL INTERFACE ---
        st.write("---")
        st.subheader("🧠 Content Recall")
        st.caption("Hide the text above and try to recall its main ideas in your own words.")

        recall_answer = st.text_area(
            "What do you remember from the text?",
            key="content_recall_answer",
            height=150,
            placeholder="Write the main ideas you remember...",
        )

        if st.button("Check my recall 🚀", use_container_width=True, key="check_content_recall"):
            if not recall_answer.strip():
                st.warning("Write down what you remember first.")
            else:
                with st.spinner("Reviewing your recall..."):
                    feedback = evaluate_content_recall(
                        api_key=api_key,
                        original_text=data.get("text", ""),
                        user_recall=recall_answer,
                        target_language=st.session_state["saved_session"]["ui_target_language"],
                        level=st.session_state["saved_session"]["ui_seviye"],
                    )
                    st.session_state["content_recall_feedback"] = feedback

        if st.session_state.get("content_recall_feedback"):
            st.markdown("### 💡 Feedback")
            st.markdown(st.session_state["content_recall_feedback"])
                    
    with main_col2:
        render_vocabulary_assistant(data.get('vocabulary', []), save_heatmap, api_key)
        st.write("---")
        
        render_exercises(
            data.get("exercises", {}),
            api_key,
            data.get("text", ""),
            show_tf,
            show_mc,
            show_writing
        )

render_sidebar(save_heatmap)