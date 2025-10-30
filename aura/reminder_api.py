# reminder_api.py
from datetime import datetime
import time
from db import add_reminder
from reminder_worker import start_reminder_worker

def schedule_reminder_and_store(seconds, message, speak_fn=None):
    # compute epoch seconds
    due_ts = int(datetime.now().timestamp()) + int(seconds)
    rid = add_reminder(message, due_ts)
    # ensure worker is started so reminder will be triggered
    start_reminder_worker(speak_fn=speak_fn, interval=2)
    return rid, due_ts
