import os
import json
import datetime
import streamlit as st

def check_and_increment_quota(max_daily_limit=10):
    """
    Kullanıcının günlük AI üretim kotasını kontrol eder. 
    Limit aşılmadıysa sayacı artırır ve True döner; dolduysa False döner.
    """
    user_email = getattr(st.user, "email", "guest") if hasattr(st, "user") else "guest"
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    
    # İlgili kullanıcının dizini
    dir_path = os.path.join("data", safe_email)
    os.makedirs(dir_path, exist_ok=True)
    
    quota_file = os.path.join(dir_path, "quota.json")
    today_str = datetime.date.today().isoformat()
    
    data = {"date": today_str, "generation_count": 0}
    
    if os.path.exists(quota_file):
        try:
            with open(quota_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                if content.get("date") == today_str:
                    data = content
                else:
                    # Yeni bir güne geçildiyse sayacı sıfırla
                    data = {"date": today_str, "generation_count": 0}
        except Exception:
            pass
            
    # Limit kontrolü
    if data["generation_count"] >= max_daily_limit:
        return False, data["generation_count"]
        
    # Sayacı artır ve kaydet
    data["generation_count"] += 1
    try:
        with open(quota_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass
        
    return True, data["generation_count"]

def get_current_quota(max_daily_limit=10):
    """
    Sayacı artırmadan kullanıcının bugünkü mevcut kullanım miktarını okur.
    """
    user_email = getattr(st.user, "email", "guest") if hasattr(st, "user") else "guest"
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    
    dir_path = os.path.join("data", safe_email)
    quota_file = os.path.join(dir_path, "quota.json")
    today_str = datetime.date.today().isoformat()
    
    if os.path.exists(quota_file):
        try:
            with open(quota_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                if content.get("date") == today_str:
                    return content.get("generation_count", 0), max_daily_limit
        except Exception:
            pass
            
    return 0, max_daily_limit