# utils.py
"""
Utility helpers:
- open_website(site): safe mapping to known sites or google-search
- get_time(): returns formatted time string
- set_reminder_in_seconds(seconds, message, speak_fn=None): background reminder thread
- open_system_tool(name): cross-platform attempts to open small tools (calc, notepad)
- system_info(): lightweight system info (no external services)
- play_youtube_search(query): open youtube search safely
"""

import webbrowser
import threading
import time
from datetime import datetime
import platform
import subprocess
import socket
import shutil

def open_website(name):
    """Open a known website safely. 'name' may be 'youtube', 'google', 'facebook' or search term."""
    name_low = name.lower().strip()
    try:
        if 'youtube' in name_low:
            webbrowser.open('https://www.youtube.com')
            return True
        if 'facebook' in name_low or 'fb' == name_low:
            webbrowser.open('https://www.facebook.com')
            return True
        if 'google' in name_low:
            webbrowser.open('https://www.google.com')
            return True
        # fallback: perform a Google search for the phrase
        query = name.replace(' ', '+')
        webbrowser.open(f'https://www.google.com/search?q={query}')
        return True
    except Exception:
        return False

def play_youtube_search(query):
    """Open YouTube search results for a query (safe URL quoting)."""
    try:
        import requests
        q = requests.utils.quote(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
        return True
    except Exception:
        # fallback simple quote
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ','+')}")
        return False

def get_time():
    now = datetime.now()
    return now.strftime("%I:%M %p")

def set_reminder_in_seconds(seconds, message, speak_fn=None):
    """Fire a reminder after seconds. Works only while program runs."""
    def _remind():
        try:
            time.sleep(seconds)
            msg = f"Reminder: {message}"
            if callable(speak_fn):
                try:
                    speak_fn(msg)
                except Exception:
                    print(msg)
            else:
                print(msg)
        except Exception:
            pass
    t = threading.Thread(target=_remind, daemon=True)
    t.start()
    return True

def open_system_tool(name):
    """Attempt to open a simple system tool: calculator or notepad.
    Returns a short message."""
    sysname = platform.system().lower()
    name_low = name.lower()
    try:
        # Windows common apps
        if 'calc' in name_low or 'calculator' in name_low:
            if sysname == 'windows':
                subprocess.Popen(['calc.exe'])
            elif sysname == 'darwin':
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:
                # linux: try gnome-calculator or just return message
                if shutil.which('gnome-calculator'):
                    subprocess.Popen(['gnome-calculator'])
                elif shutil.which('kcalc'):
                    subprocess.Popen(['kcalc'])
                else:
                    return "Calculator not found on this system."
            return "Opening calculator."
        if 'note' in name_low or 'notepad' in name_low:
            if sysname == 'windows':
                subprocess.Popen(['notepad.exe'])
            elif sysname == 'darwin':
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:
                if shutil.which('gedit'):
                    subprocess.Popen(['gedit'])
                elif shutil.which('nano'):
                    subprocess.Popen(['x-terminal-emulator', '-e', 'nano'])
                else:
                    return "No suitable text editor found."
            return "Opening notes."
    except Exception:
        return "Could not open system tool."
    return "Tool not recognized."

def system_info():
    """Return light-weight system info: OS, host, local IP (may be local network)."""
    try:
        host = socket.gethostname()
        ip = socket.gethostbyname(host)
    except Exception:
        host = "unknown"
        ip = "unknown"
    info = f"OS: {platform.system()} {platform.release()} | Host: {host} | IP: {ip}"
    return info
