import streamlit as st
import os
import datetime
from ai_engine import generate_explanation, generate_speech
from analytics import update_analytics
from storage import save_analytics

def render_sidebar(save_heatmap):
    st.sidebar.markdown(f"👤 **{st.user.name or st.user.email}**")
    if st.sidebar.button("Log out"):
        st.logout()
    st.sidebar.divider()

    st.sidebar.info("🦊 VosWeave is weaving your learning progress in real-time.")
    st.sidebar.markdown("## 📊 Learner Analytics")

    analytics = st.session_state.get('learner_analytics', {})
    total_texts = analytics.get("total_texts_read", 0)
    total_q = analytics.get("total_questions_answered", 0)
    correct_q = analytics.get("correct_answers", 0)
    
    accuracy = int((correct_q / total_q) * 100) if total_q > 0 else 0
    
    col_side1, col_side2 = st.sidebar.columns(2)
    with col_side1:
        st.metric("Sessions 📚", total_texts)
    with col_side2:
        st.metric("Accuracy 🎯", f"%{accuracy}")
        
    st.sidebar.write(f"❓ **Questions Answered:** {total_q}")
    st.sidebar.write(f"✅ **Correct Answers:** {correct_q}")
    
    lang_dist = analytics.get("language_distribution", {})
    if lang_dist:
        st.sidebar.markdown("##### 📚 Languages Studied")
        for lang, count in lang_dist.items():
            st.sidebar.write(f"• **{lang}:** {count} text(s)")
            
    st.sidebar.write("---")

    if st.session_state.get('heatmap_vocab'):
        st.sidebar.markdown("### 📊 AI Memory Dashboard")
        
        all_words = st.session_state['heatmap_vocab']
        
        def get_status(val):
            if isinstance(val, dict):
                return val.get("status", "")
            return str(val)

        know_count = sum(1 for val in all_words.values() if "I know this" in get_status(val))
        seen_count = sum(1 for val in all_words.values() if "I've seen this" in get_status(val))
        new_count = sum(1 for val in all_words.values() if "New to me" in get_status(val))
        
        st.sidebar.write(f"🟢 **I know this:** {know_count}")
        st.sidebar.write(f"🟡 **I've seen this:** {seen_count}")
        st.sidebar.write(f"🔴 **New to me:** {new_count}")
        st.sidebar.write("---")
        
        st.sidebar.markdown("#### 🗺️ Registered Vocabulary Heatmap")
        for word, val in all_words.items():
            status = get_status(val)
            if "I know this" in status:
                st.sidebar.write(f"🟢 **{word}**")
            elif "I've seen this" in status:
                st.sidebar.write(f"🟡 **{word}**")
            else:
                st.sidebar.write(f"🔴 **{word}**")
                
        if st.sidebar.button("🗑️ Reset All Progress"):
            st.session_state['heatmap_vocab'] = {}
            st.session_state['saved_session'] = None
            st.session_state['learner_analytics'] = {
                "total_texts_read": 0,
                "language_distribution": {},
                "correct_answers": 0,
                "total_questions_answered": 0,
                "mistake_types_distribution": {"Inference": 0, "False Assumption": 0, "Careless Reading": 0}
            }
            save_heatmap({})
            from storage import save_analytics
            save_analytics(st.session_state['learner_analytics'])
            if os.path.exists("reading_session.json"):
                os.remove("reading_session.json")
            if os.path.exists("learner_analytics.json"):
                os.remove("learner_analytics.json")
            st.rerun()

def render_vocabulary_assistant(vocabulary, save_heatmap, api_key):
    """Metnin altındaki interaktif kelime kartlarını ve oylama butonlarını çizer."""
    st.subheader("✨ Smart Reading Assistant & Heatmap Tool")
    st.markdown("*Click a word below to explore it and log your familiarity level:*")
    
    for idx, item in enumerate(vocabulary):
        word_key = item.get('word')
        status_emoji = ""
        
        if word_key in st.session_state['heatmap_vocab']:
            current_status = st.session_state['heatmap_vocab'][word_key]
            if "I know this" in current_status:
                status_emoji = "🟢 "
            elif "I've seen this" in current_status:
                status_emoji = "🟡 "
            elif "New to me" in current_status:
                status_emoji = "🔴 "
                
        with st.expander(f"{status_emoji}🔽 {word_key} ({item.get('level', 'N/A')})"):
            st.write(f"**🇹🇷 Meaning:** {item.get('meaning')}")
            
            pronunciation_text = item.get('pronunciation', 'N/A')
            col_audio1, col_audio2 = st.columns([2, 1])
            with col_audio1:
                st.write(f"**🔊 Pronunciation:** *{pronunciation_text}*")
            with col_audio2:
                if st.button("🎵 Listen", key=f"listen_{idx}"):
                    with st.spinner("🔊..."):
                        audio_bytes = generate_speech(api_key, word_key)
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

            if "variants" in item and item["variants"]:
                st.markdown("<div style='margin-top: 8px; margin-bottom: 8px;'><strong>🔗 Detected Variants in Text:</strong></div>", unsafe_allow_html=True)
                for var in item["variants"]:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• <code style='color: #1c8cf0;'>{var.get('form')}</code> — <small style='color: #9CA3AF;'>{var.get('explanation')}</small>", unsafe_allow_html=True)
                st.write("")

            st.write(f"**📝 Example:** {item.get('example', 'No example provided.')}")

            st.markdown("**How familiar is this word to you?**")
            v_col1, v_col2, v_col3 = st.columns(3)
            
            current_item_state = st.session_state['heatmap_vocab'].get(word_key, {})
            if not isinstance(current_item_state, dict):
                current_item_state = {"status": current_item_state, "times_seen": 1}

            now_str = datetime.datetime.now().isoformat()

            with v_col1:
                if st.button("🟢 I know this", key=f"know_{idx}"):
                    current_item_state["status"] = "🟢 I know this"
                    current_item_state["last_seen"] = now_str
                    current_item_state["times_seen"] = current_item_state.get("times_seen", 0) + 1
                    if "first_seen" not in current_item_state:
                        current_item_state["first_seen"] = now_str
                        
                    st.session_state['heatmap_vocab'][word_key] = current_item_state
                    save_heatmap(st.session_state['heatmap_vocab'])
                    st.rerun()
            with v_col2:
                if st.button("🟡 I've seen this", key=f"seen_{idx}"):
                    current_item_state["status"] = "🟡 I've seen this"
                    current_item_state["last_seen"] = now_str
                    current_item_state["times_seen"] = current_item_state.get("times_seen", 0) + 1
                    if "first_seen" not in current_item_state:
                        current_item_state["first_seen"] = now_str
                        
                    st.session_state['heatmap_vocab'][word_key] = current_item_state
                    save_heatmap(st.session_state['heatmap_vocab'])
                    st.rerun()
            with v_col3:
                if st.button("🔴 New to me", key=f"new_{idx}"):
                    current_item_state["status"] = "🔴 New to me"
                    current_item_state["last_seen"] = now_str
                    current_item_state["times_seen"] = current_item_state.get("times_seen", 0) + 1
                    if "first_seen" not in current_item_state:
                        current_item_state["first_seen"] = now_str
                        
                    st.session_state['heatmap_vocab'][word_key] = current_item_state
                    save_heatmap(st.session_state['heatmap_vocab'])
                    st.rerun()

def render_exercises(exercises, api_key, reading_text, show_tf=True, show_mc=True, show_writing=False):
    """🌟 Checkbox durumlarını alan ve Open-ended alanını dinamik basan güncel render motoru"""
    st.subheader("✍️ Interactive Exercises")
    
    with st.form("exercise_form"):
        user_tf_answers = {}
        user_mc_answers = {}
        user_writing_answer = ""
        
        # 1. True / False Bölümü
        if show_tf and "true_false" in exercises and exercises["true_false"]:
            st.markdown("### 📄 True / False Statements")
            for i, tf in enumerate(exercises["true_false"]):
                st.write(f"**{i+1}.** {tf.get('statement')}")
                ans = st.radio("Your Answer:", ["Not Answered", "True", "False"], key=f"tf_radio_{i}", horizontal=True)
                user_tf_answers[i] = ans
            st.write("---")
            
        # 2. Reading Comprehension Bölümü
        if show_mc and "multiple_choice" in exercises and exercises["multiple_choice"]:
            st.markdown("### ❓ Reading Comprehension")
            for i, mc in enumerate(exercises["multiple_choice"]):
                st.write(f"**Q{i+1}:** {mc.get('question')}")
                options_list = mc.get('options', [])
                ans = st.radio("Choose the correct option:", ["Not Answered"] + options_list, key=f"mc_radio_{i}")
                user_mc_answers[i] = ans
            st.write("---")
            
        # 3. Open-ended Writing Bölümü (Güvenli Şema Kontrolü)
        if show_writing and "open_ended" in exercises and exercises["open_ended"]:
            st.markdown("### ✍️ Open-ended Writing Prompt")
            
            open_ended_data = exercises["open_ended"]
            if isinstance(open_ended_data, list) and len(open_ended_data) > 0:
                open_ended_data = open_ended_data[0]
                
            if isinstance(open_ended_data, dict):
                prompt_text = open_ended_data.get('prompt', 'Write a brief response based on the text.')
            else:
                prompt_text = str(open_ended_data)
                
            st.write(f"**Prompt:** {prompt_text}")
            user_writing_answer = st.text_area("Type your essay/response here:", key="open_ended_user_input", height=150)
            st.write("---")
            
        submit_answers = st.form_submit_button("Check Answers 🎯", use_container_width=True)
        
    if submit_answers:
        st.markdown("### 📊 Evaluation Results")
        
        if show_tf and "true_false" in exercises and exercises["true_false"]:
            for i, tf in enumerate(exercises["true_false"]):
                correct = tf.get('correct_answer')
                ans = user_tf_answers[i]
                if ans != "Not Answered":
                    user_bool = True if ans == "True" else False
                    if user_bool == correct:
                        st.write(f"Statement {i+1}: ✅ Correct!")
                    else:
                        st.write(f"Statement {i+1}: ❌ Incorrect")
                        if "evidence" in tf:
                            st.markdown(f"📊 **Evidence from the text:** *\"{tf.get('evidence')}\"*")
                            with st.spinner("Öğretmen notu hazırlanıyor..."):
                                explanation = generate_explanation(api_key, "Turkish", reading_text, tf.get('statement'), str(ans), tf.get('evidence'))
                                st.markdown(f"""<div style="background-color: rgba(28, 140, 240, 0.08); border-left: 6px solid #1c8cf0; padding: 18px; border-radius: 8px; margin-top: 12px; margin-bottom: 12px;">
    <strong style="color: #1c8cf0; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">💡 Teacher's Note & Language Insight</strong>
    <div style="font-size: 1.15rem; line-height: 1.7; white-space: pre-wrap; margin-top: 8px; color: #E5E7EB;">{explanation}</div></div>""", unsafe_allow_html=True)
                    
        if show_mc and "multiple_choice" in exercises and exercises["multiple_choice"]:
            for i, mc in enumerate(exercises["multiple_choice"]):
                correct_opt = mc.get('correct_answer')
                ans = user_mc_answers[i]
                if ans != "Not Answered":
                    if ans.startswith(correct_opt) or correct_opt in ans:
                        st.write(f"Question {i+1}: ✅ Correct!")
                    else:
                        st.write(f"Question {i+1}: ❌ Incorrect")
                        if "evidence" in mc:
                            st.markdown(f"📊 **Evidence from the text:** *\"{mc.get('evidence')}\"*")
                            with st.spinner("Öğretmen notu hazırlanıyor..."):
                                explanation = generate_explanation(api_key, "Turkish", reading_text, mc.get('question'), ans, mc.get('evidence'))
                                st.markdown(f"""<div style="background-color: rgba(28, 140, 240, 0.08); border-left: 6px solid #1c8cf0; padding: 18px; border-radius: 8px; margin-top: 12px; margin-bottom: 12px;">
    <strong style="color: #1c8cf0; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">💡 Teacher's Note & Language Insight</strong>
    <div style="font-size: 1.15rem; line-height: 1.7; white-space: pre-wrap; margin-top: 8px; color: #E5E7EB;">{explanation}</div></div>""", unsafe_allow_html=True)

        total_correct = 0
        total_q = 0
        
        if show_tf and "true_false" in exercises:
            for i, tf in enumerate(exercises["true_false"]):
                if user_tf_answers.get(i) != "Not Answered":
                    total_q += 1
                    user_bool = True if user_tf_answers[i] == "True" else False
                    if user_bool == tf.get('correct_answer'):
                        total_correct += 1
                        
        if show_mc and "multiple_choice" in exercises:
            for i, mc in enumerate(exercises["multiple_choice"]):
                if user_mc_answers.get(i) != "Not Answered":
                    total_q += 1
                    correct_opt = mc.get('correct_answer')
                    if user_mc_answers[i].startswith(correct_opt) or correct_opt in user_mc_answers[i]:
                        total_correct += 1

        mistake_counter = {"Inference": 0, "False Assumption": 0, "Careless Reading": 0}
        
        if show_tf and "true_false" in exercises:
            for i, tf in enumerate(exercises["true_false"]):
                if user_tf_answers.get(i) != "Not Answered":
                    user_bool = True if user_tf_answers[i] == "True" else False
                    if user_bool != tf.get('correct_answer'):
                        m_type = tf.get('mistake_type', 'Careless Reading')
                        if m_type in mistake_counter:
                            mistake_counter[m_type] += 1
                            
        if show_mc and "multiple_choice" in exercises:
            for i, mc in enumerate(exercises["multiple_choice"]):
                if user_mc_answers.get(i) != "Not Answered":
                    correct_opt = mc.get('correct_answer')
                    if not (user_mc_answers[i].startswith(correct_opt) or correct_opt in user_mc_answers[i]):
                        m_type = mc.get('mistake_type', 'Inference')
                        if m_type in mistake_counter:
                            mistake_counter[m_type] += 1

        if total_q > 0:
            current_lang = st.session_state.get('saved_session', {}).get('ui_target_language', 'Unknown')
            
            updated_data, session_summary = update_analytics(
                st.session_state['learner_analytics'],
                total_correct,
                total_q,
                current_lang,
                mistake_counter 
            )
            
            st.session_state['learner_analytics'] = updated_data
            save_analytics(updated_data)
            
            st.toast(f"📊 Session Saved! Accuracy: %{session_summary['accuracy']}", icon="📈")

            st.markdown("---")
            st.markdown("### 📈 Overall Learner Analytics Progress")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f"""<div style="background-color: rgba(59, 130, 246, 0.1); border: 1px solid #3b82f6; padding: 15px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 0.9rem; color: #9ca3af; display: block;">Total Sessions 📚</span>
                    <strong style="font-size: 1.8rem; color: #3b82f6;">{updated_data.get('total_texts_read', 0)}</strong>
                </div>""", unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""<div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 15px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 0.9rem; color: #9ca3af; display: block;">Overall Accuracy 🎯</span>
                    <strong style="font-size: 1.8rem; color: #10b981;">%{session_summary['accuracy']}</strong>
                </div>""", unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"""<div style="background-color: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 0.9rem; color: #9ca3af; display: block;">Total Questions ❓</span>
                    <strong style="font-size: 1.8rem; color: #f59e0b;">{updated_data.get('total_questions_answered', 0)}</strong>
                </div>""", unsafe_allow_html=True)

        if show_writing and user_writing_answer.strip():
            st.markdown("### 📝 Writing Feedback")
            with st.spinner("Yazınız analiz ediliyor..."):
                open_ended_data = exercises.get("open_ended", {})
                if isinstance(open_ended_data, list) and len(open_ended_data) > 0:
                    open_ended_data = open_ended_data[0]
                
                writing_prompt = open_ended_data.get('prompt', '') if isinstance(open_ended_data, dict) else str(open_ended_data)
                
                explanation = generate_explanation(api_key, "Turkish", reading_text, writing_prompt, user_writing_answer, "Open-ended Essay Response")
                st.markdown(f"""<div style="background-color: rgba(16, 185, 129, 0.08); border-left: 6px solid #10b981; padding: 18px; border-radius: 8px; margin-top: 12px; margin-bottom: 12px;">
    <strong style="color: #10b981; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">✍️ Writing Coach Evaluation</strong>
    <div style="font-size: 1.15rem; line-height: 1.7; white-space: pre-wrap; margin-top: 8px; color: #E5E7EB;">{explanation}</div></div>""", unsafe_allow_html=True)