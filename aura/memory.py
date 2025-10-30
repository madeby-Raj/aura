# memory.py
import json
import os

MEM_FILE = 'memory.json'

def load_memory():
    if not os.path.exists(MEM_FILE):
        return {}
    try:
        with open(MEM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(mem):
    with open(MEM_FILE, 'w', encoding='utf-8') as f:
        json.dump(mem, f, indent=2)

# after existing functions
try:
    from db import save_memory_key, init_db
    init_db()  # ensure DB exists
    def save_memory_to_db(mem):
        # write each key to db
        for k,v in mem.items():
            save_memory_key(k, v)
except Exception:
    def save_memory_to_db(mem):
        pass
