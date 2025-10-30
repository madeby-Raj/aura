# nlp_engine.py (cleaned & fixed)
import json
import random
import re
import os
import webbrowser
from datetime import datetime, timedelta

import requests
import wikipedia
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from memory import load_memory, save_memory
from sentiment import get_sentiment
from utils import (
    open_website,
    get_time,
    set_reminder_in_seconds,
    play_youtube_search,
    open_system_tool,
    system_info,
)
from calc_logic import calculate_expression, compare_logic
from motivation import random_quote

# load intents (must exist)
INTENTS_FILE = "intents.json"
if not os.path.exists(INTENTS_FILE):
    raise FileNotFoundError("intents.json not found. Add it before running.")

with open(INTENTS_FILE, "r", encoding="utf-8") as f:
    intents = json.load(f).get("intents", [])

# prepare TF-IDF patterns
patterns = []
pattern_to_tag = []
for intent in intents:
    for p in intent.get("patterns", []):
        patterns.append(p.lower())
        pattern_to_tag.append(intent.get("tag"))

if patterns:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2)).fit(patterns)
    tfidf_matrix = vectorizer.transform(patterns)
else:
    vectorizer = None
    tfidf_matrix = None

CONTEXT_WINDOW = 6
conversation_history = []  # list of (role, text)

memory = load_memory()

WIKI_CACHE = "wiki_cache.json"
if os.path.exists(WIKI_CACHE):
    try:
        with open(WIKI_CACHE, "r", encoding="utf-8") as f:
            wiki_cache = json.load(f)
    except Exception:
        wiki_cache = {}
else:
    wiki_cache = {}


def save_wiki_cache():
    try:
        with open(WIKI_CACHE, "w", encoding="utf-8") as f:
            json.dump(wiki_cache, f, indent=2)
    except Exception:
        pass


def append_history(role, text):
    conversation_history.append((role, text))
    if len(conversation_history) > CONTEXT_WINDOW * 2:
        conversation_history[:] = conversation_history[-CONTEXT_WINDOW * 2 :]


def sanitize_text(t):
    """Basic sanitize: strip control chars and collapse whitespace."""
    if not isinstance(t, str):
        return ""
    s = re.sub(r"[\x00-\x1f\x7f]", "", t)  # remove control chars
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def similar_intent(user_text):
    if vectorizer is None:
        return None, 0.0
    v = vectorizer.transform([user_text.lower()])
    sims = cosine_similarity(v, tfidf_matrix)[0]
    best_idx = int(sims.argmax())
    return pattern_to_tag[best_idx], float(sims[best_idx])


def extract_name(text):
    m = re.search(r"(?:my name is|call me|i am|i'm)\s+([A-Za-z ]{2,40})", text, re.IGNORECASE)
    if m:
        return " ".join(m.group(1).strip().split()[:2]).title()
    return None


def parse_reminder(text):
    # support "remind me in 10 seconds to X" and "remind me at 18:30 to X"
    m = re.search(
        r"remind me in (\d+)\s*(second|seconds|minute|minutes|min|mins|hour|hours|hr|hrs)",
        text,
        re.IGNORECASE,
    )
    if m:
        num = int(m.group(1))
        unit = m.group(2).lower()
        seconds = num
        if "min" in unit:
            seconds = num * 60
        elif "hour" in unit or "hr" in unit:
            seconds = num * 3600
        mm = re.search(r"to (.+)", text, re.IGNORECASE)
        msg = mm.group(1).strip() if mm else "your task"
        return seconds, msg

    # absolute time HH:MM (optional am/pm)
    m2 = re.search(r"at\s+(\d{1,2}:\d{2})(?:\s*(am|pm))?.*to\s+(.+)", text, re.IGNORECASE)
    if m2:
        timestr = m2.group(1)
        ampm = m2.group(2)
        try:
            hh, mm = map(int, timestr.split(":"))
            if ampm:
                ampm = ampm.lower()
                if "pm" in ampm and hh != 12:
                    hh += 12
                if "am" in ampm and hh == 12:
                    hh = 0
            now = datetime.now()
            target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            seconds = int((target - now).total_seconds())
            msg = m2.group(3).strip()
            return seconds, msg
        except Exception:
            pass
    return None, None


def wiki_lookup(query):
    key = query.lower().strip()
    if key in wiki_cache:
        return wiki_cache[key]
    try:
        summary = wikipedia.summary(query, sentences=2)
        wiki_cache[key] = summary
        save_wiki_cache()
        return summary
    except Exception:
        return None


def summarize_text(text, sentences=2):
    try:
        import nltk

        sents = nltk.sent_tokenize(text)
        if len(sents) <= sentences:
            return text
        return " ".join(sents[:sentences])
    except Exception:
        # fallback: first N lines
        parts = [p.strip() for p in text.splitlines() if p.strip()]
        return " ".join(parts[:sentences])


def get_recent_user_messages(n=3):
    return [t for r, t in conversation_history if r == "user"][-n:]


def get_weather_safe(place):
    """Lightweight weather lookup using open-meteo (no API key)."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(place)}&count=1"
        r = requests.get(url, timeout=6)
        data = r.json()
        results = data.get("results")
        if not results:
            return None
        first = results[0]
        lat = first.get("latitude")
        lon = first.get("longitude")
        nice = first.get("name")
        wurl = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        r2 = requests.get(wurl, timeout=6)
        dd = r2.json()
        cw = dd.get("current_weather")
        if cw:
            temp = cw.get("temperature")
            wind = cw.get("windspeed")
            return f"Current weather in {nice}: {temp}°C, wind {wind} km/h."
    except Exception:
        return None
    return None


def get_response(raw_text, speak_fn=None):
    user_text = sanitize_text(raw_text)
    if user_text == "":
        return "I didn't hear anything. Please say or type again."

    append_history("user", user_text)

    # 1) name setting
    name = extract_name(user_text)
    if name:
        memory["name"] = name
        try:
            save_memory(memory)
        except Exception:
            pass
        resp = f"Nice to meet you, {name}. I'll remember that."
        append_history("aura", resp)
        return resp

    # 2) safe math/logic
    calc = calculate_expression(user_text)
    if calc:
        append_history("aura", calc)
        return calc
    comp = compare_logic(user_text)
    if comp:
        append_history("aura", comp)
        return comp

    # 3) intent matching
    tag, score = (None, 0.0)
    if vectorizer is not None:
        tag, score = similar_intent(user_text)

    THRESH = 0.5
    mood = get_sentiment(user_text)

    if tag and score >= THRESH:
        intent = next((it for it in intents if it.get("tag") == tag), None)
        if intent:
            # handle site opens
            if tag.startswith("open_"):
                site = tag.replace("open_", "")
                open_website(site)
                resp = random.choice(intent.get("responses", ["Done."]))
                append_history("aura", resp)
                return resp

            if tag == "time":
                t = get_time()
                resp = random.choice(intent.get("responses", ["It's {time}."])).replace("{time}", t)
                append_history("aura", resp)
                return resp

            if tag == "joke":
                resp = random.choice(intent.get("responses", ["I don't have a joke now."]))
                append_history("aura", resp)
                return resp

            if tag == "name_query":
                n = memory.get("name")
                if n:
                    resp = random.choice(intent.get("responses", ["I remember you, {name}."])).replace("{name}", n)
                    append_history("aura", resp)
                    return resp
                else:
                    resp = "I don't know your name yet. You can say 'My name is Raj' and I'll remember it."
                    append_history("aura", resp)
                    return resp

            if tag == "reminder_set":
                seconds, message = parse_reminder(user_text)
                if seconds:
                    try:
                        from reminder_api import schedule_reminder_and_store

                        rid, due_ts = schedule_reminder_and_store(seconds, message, speak_fn)
                        resp = f"Okay — reminder scheduled (id={rid}) at unix {due_ts}."
                    except Exception:
                        # fallback to in-memory only
                        set_reminder_in_seconds(seconds, message, speak_fn)
                        resp = f"Okay — I'll remind you in {seconds} seconds about: {message}"
                    append_history("aura", resp)
                    return resp
                else:
                    resp = (
                        "Try: 'Remind me in 10 minutes to revise' or "
                        "'Remind me at 18:30 to call mom'."
                    )
                    append_history("aura", resp)
                    return resp

            # default for matched intent
            resp = random.choice(intent.get("responses", ["Alright."]))
            append_history("aura", resp)
            return resp

    # 4) special-purpose commands that might not be in intents
    low = user_text.lower()

    # play music/search song -> open YouTube search
    m = re.search(r"play (?:song )?(.*)", low)
    if m and m.group(1).strip():
        query = m.group(1).strip()
        play_youtube_search(query)
        resp = f"Playing results for {query} on YouTube."
        append_history("aura", resp)
        return resp

    # weather requests: "weather in <city>"
    if "weather" in low:
        m = re.search(r"weather(?: in)? (.+)", low)
        place = m.group(1).strip() if m else None
        if place:
            w = get_weather_safe(place)
            if w:
                append_history("aura", w)
                return w
            else:
                resp = "I couldn't fetch weather right now. Please try again later."
                append_history("aura", resp)
                return resp

    # summarize mode: "summarize this: <text>" or "summarize: <text>"
    if low.startswith("summarize") or "summarize this" in low:
        m = re.search(r"summarize(?: this)?:\s*(.+)", raw_text, re.IGNORECASE | re.DOTALL)
        if m:
            text_to_sum = m.group(1).strip()
            if text_to_sum:
                summary = summarize_text(text_to_sum, sentences=3)
                append_history("aura", summary)
                return summary
        return "Please paste the text after 'Summarize:' and I'll summarize it."

    # open system tool
    if "open calculator" in low or "open calc" in low:
        resp = open_system_tool("calc")
        append_history("aura", resp)
        return resp
    if "open notepad" in low or "open notes" in low:
        resp = open_system_tool("notepad")
        append_history("aura", resp)
        return resp

    if "system info" in low or "ip address" in low:
        info = system_info()
        append_history("aura", info)
        return info

    # wiki fallback
    if any(q in low for q in ["who is", "what is", "tell me about", "define", "what are"]):
        summary = wiki_lookup(user_text)
        if summary:
            append_history("aura", summary)
            return summary

    # context-aware followups (simple heuristics)
    recent_user = get_recent_user_messages(3)
    if recent_user and len(recent_user) >= 2:
        prev = recent_user[-2]
        if any(q in prev.lower() for q in ["who is", "what is", "tell me about"]) and len(user_text.split()) <= 4:
            query = prev + " " + user_text
            summary = wiki_lookup(query)
            if summary:
                append_history("aura", summary)
                return summary

    # sentiment-based empathetic fallback
    mood2 = get_sentiment(user_text)
    if mood2 == "negative":
        quote = random_quote()
        resp = f"I sense you may be feeling down. Here's something: {quote}"
        append_history("aura", resp)
        return resp
    if mood2 == "positive":
        resp = "Great to hear! How can I help further?"
        append_history("aura", resp)
        return resp

    # final fallback
    resp = "Sorry, I didn't understand that. Try 'help' or ask differently."
    append_history("aura", resp)
    return resp
