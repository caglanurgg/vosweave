import os
import json
import datetime
import streamlit as st


def _get_quota_file():
    """Return the quota file path for the current user."""
    user_email = (
        getattr(st.user, "email", None) or "guest"
        if hasattr(st, "user")
        else "guest"
    )

    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    dir_path = os.path.join("data", safe_email)
    os.makedirs(dir_path, exist_ok=True)

    return os.path.join(dir_path, "quota.json")


def _load_quota_data(quota_file):
    """Load today's quota data while preserving legacy quota files."""
    today_str = datetime.date.today().isoformat()

    data = {
        "date": today_str,
        "total_count": 0,
        "generation_count": 0,
        "recall_count": 0,
    }

    if not os.path.exists(quota_file):
        return data

    try:
        with open(quota_file, "r", encoding="utf-8") as f:
            content = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError("Could not read daily quota data.") from e

    if not isinstance(content, dict):
        raise RuntimeError("Daily quota data has an invalid format.")

    if content.get("date") != today_str:
        return data

    generation_count = int(content.get("generation_count", 0))
    recall_count = int(content.get("recall_count", 0))

    total_count = int(
        content.get("total_count", generation_count + recall_count)
    )

    if min(generation_count, recall_count, total_count) < 0:
        raise RuntimeError("Daily quota data contains invalid counts.")

    return {
        "date": today_str,
        "total_count": total_count,
        "generation_count": generation_count,
        "recall_count": recall_count,
    }


def _save_quota_data(quota_file, data):
    """Persist quota data. Surface write failures instead of ignoring them."""
    try:
        with open(quota_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except OSError as e:
        raise RuntimeError("Could not save daily quota data.") from e


def check_and_increment_quota(max_daily_limit=10, action="generation"):
    """
    Check the shared daily quota and count an allowed AI operation.

    Supported actions:
    - generation: generating a reading package
    - recall: evaluating content recall

    Returns (allowed, total_count).
    """
    if action not in ("generation", "recall"):
        raise ValueError(
            "Unsupported quota action. Use 'generation' or 'recall'."
        )

    quota_file = _get_quota_file()
    data = _load_quota_data(quota_file)

    if data["total_count"] >= max_daily_limit:
        return False, data["total_count"]

    data["total_count"] += 1
    data[f"{action}_count"] += 1

    _save_quota_data(quota_file, data)

    return True, data["total_count"]


def get_current_quota(max_daily_limit=10):
    """Return today's total usage and the daily limit without incrementing."""
    quota_file = _get_quota_file()
    data = _load_quota_data(quota_file)

    return data["total_count"], max_daily_limit