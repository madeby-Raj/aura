# tts_stt.py
"""
Robust speech I/O:
- speak(text): prints + speaks (safe, catches exceptions)
- listen(...): tries mic (speech_recognition + google recognizer), returns string or None
- typed_fallback(prompt): helper to ask user to type if listen() fails
- safe defaults and small timeouts to avoid blocking
"""

import traceback
import speech_recognition as sr
import pyttsx3
import threading

# Initialize TTS engine once
_engine = None
_engine_lock = threading.Lock()

def _init_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            try:
                _engine = pyttsx3.init()
                _engine.setProperty('rate', 170)
                _engine.setProperty('volume', 1.0)
            except Exception:
                _engine = None

def speak(text, block=True):
    """Speak text and also print it. Non-fatal if TTS fails."""
    print("AURA:", text)
    try:
        _init_engine()
        if _engine is None:
            return
        # run speak in same thread or background depending on block
        if block:
            _engine.say(str(text))
            _engine.runAndWait()
        else:
            def _bg():
                try:
                    _engine.say(str(text))
                    _engine.runAndWait()
                except Exception:
                    pass
            t = threading.Thread(target=_bg, daemon=True)
            t.start()
    except Exception:
        # avoid crashing the main app for any TTS errors
        # print a short traceback for debugging only
        print("TTS error (ignored):", str(traceback.format_exc())[:200])

def listen(timeout=4, phrase_time_limit=6):
    """
    Try to listen via microphone and return recognized text (Google recognizer).
    Returns None on failure (so caller can fallback to typed input).
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            text = r.recognize_google(audio)
            print("You (voice):", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print("Speech recognition request failed:", str(e))
            return None
    except Exception as e:
        # Microphone or PyAudio problems -> return None (typed fallback is used)
        print("Microphone error or not available (falling back to typed input).")
        # print minimal debug info
        # print("DEBUG:", e)
        return None

def typed_fallback(prompt="You: "):
    """Simple typed fallback for when listen() returns None."""
    try:
        return input(prompt)
    except Exception:
        return None
