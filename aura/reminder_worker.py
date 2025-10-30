# reminder_worker.py
import threading
import time
from datetime import datetime
from db import get_due_reminders, mark_reminder_notified
# We'll import speak function dynamically from main that passes it here.

_worker_thread = None
_stop_event = threading.Event()

def start_reminder_worker(speak_fn=None, interval=3):
    """Start background thread (daemon). speak_fn(message) will be called for each due reminder."""
    global _worker_thread, _stop_event
    if _worker_thread and _worker_thread.is_alive():
        return
    _stop_event.clear()
    def _loop():
        while not _stop_event.is_set():
            try:
                now_ts = int(datetime.now().timestamp())
                due = get_due_reminders(now_ts)
                for r in due:
                    rid = r['id']
                    msg = r['message']
                    try:
                        if callable(speak_fn):
                            speak_fn(f"Reminder: {msg}")
                        else:
                            print("Reminder:", msg)
                    except Exception:
                        print("Reminder (fail speak):", msg)
                    mark_reminder_notified(rid)
            except Exception:
                pass
            time.sleep(interval)
    _worker_thread = threading.Thread(target=_loop, daemon=True)
    _worker_thread.start()

def stop_reminder_worker():
    global _stop_event
    _stop_event.set()
