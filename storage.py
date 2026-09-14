import json
import os
import streamlit as st

def get_user_data_dir():
    """Giriş yapan kullanıcının e-postasına ve seçtiği dile göre dinamik klasör yolu üretir."""
    user_email = getattr(st.user, "email", "guest") if hasattr(st, "user") else "guest"
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    
    # Seçilen dili session_state'den alıyoruz (varsayılan: english)
    selected_lang = st.session_state.get("selected_language", "English").lower()
    
    dir_path = os.path.join("data", safe_email, selected_lang)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def load_heatmap():
    """Uygulama başlarken izole dizinden kelime geçmişini yükler."""
    dir_path = get_user_data_dir()
    file_path = os.path.join(dir_path, "heatmap.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_heatmap(data):
    """Kelime geçmişini izole dizindeki JSON dosyasına kaydeder."""
    try:
        dir_path = get_user_data_dir()
        file_path = os.path.join(dir_path, "heatmap.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error saving heatmap to storage: {e}")

def load_reading_session():
    """Uygulama başlarken izole dizinden son okuma oturumunu yükler."""
    dir_path = get_user_data_dir()
    file_path = os.path.join(dir_path, "reading_session.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "api_data" in content:
                    return content
                return None
        except Exception:
            return None
    return None

def save_reading_session(data):
    """Yeni bir metin üretildiğinde oturum verilerini izole dizine kaydeder."""
    try:
        dir_path = get_user_data_dir()
        file_path = os.path.join(dir_path, "reading_session.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error saving reading session to storage: {e}")

def load_analytics():
    """Kullanıcının izole dizindeki öğrenme analitiğini yükler, yoksa boş şablon döner."""
    dir_path = get_user_data_dir()
    file_path = os.path.join(dir_path, "learner_analytics.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
            
    return {
        "total_texts_read": 0,
        "language_distribution": {},
        "correct_answers": 0,
        "total_questions_answered": 0,
        "mistake_types_distribution": {
            "Inference": 0,
            "False Assumption": 0,
            "Careless Reading": 0
        }
    }

def save_analytics(analytics_data):
    """Kullanıcının öğrenme analitiğini izole diske kaydeder."""
    try:
        dir_path = get_user_data_dir()
        file_path = os.path.join(dir_path, "learner_analytics.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(analytics_data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False