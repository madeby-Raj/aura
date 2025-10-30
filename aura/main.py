# main.py
from reminder_worker import start_reminder_worker
from tts_stt import listen, speak
from nlp_engine import get_response
from memory import load_memory

memory = load_memory()
start_reminder_worker(speak_fn=speak, interval=2)
def run():
    print("AURA starting. Say 'quit' or type 'quit' to exit.")
    while True:
        text = listen()
        if text is None:
            text = input("You: ")
        if not text:
            continue
        if text.lower() in ['quit', 'exit', 'bye']:
            speak("Goodbye! See you.")
            break
        # pass speak function so reminders can call speak
        response = get_response(text, speak_fn=speak)
        speak(response)

if __name__ == "__main__":
    run()
