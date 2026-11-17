import re

def word_count(text):
    return len(re.findall(r"\b[\w’'-]+\b", text or ""))

def validate_script(script, min_words, max_words):
    issues = []
    count = word_count(script)
    if count < min_words:
        issues.append(f"Too short: {count} words (minimum {min_words}).")
    if count > max_words:
        issues.append(f"Too long: {count} words (maximum {max_words}).")
    if not script or len(script.strip()) < 20:
        issues.append("Script is empty or too short.")
    if re.search(r"\b(in today's digital age|in this day and age|let's dive in)\b", script, re.I):
        issues.append("Contains a generic AI-style opening phrase.")
    return count, issues

def acceptable_candidate(story, max_age_hours, now):
    from datetime import datetime
    try:
        published = datetime.fromisoformat(story["published"])
        if published.tzinfo is None:
            from datetime import timezone
            published = published.replace(tzinfo=timezone.utc)
        age = (now - published).total_seconds() / 3600
        return 0 <= age <= max_age_hours
    except Exception:
        return True
