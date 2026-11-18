import sys
import subprocess

required_libraries = {
    "edge_tts": "edge-tts",
    "speech_recognition": "SpeechRecognition",
    "pyttsx3": "pyttsx3",
    "psutil": "psutil",
    "webview": "pywebview",
    "google.genai": "google-genai",
    "websockets": "websockets",
    "requests": "requests",
    "deep_translator": "deep-translator",
    "win32com": "pywin32",
    "pyaudio": "pyaudio"
}

# Auto-install missing packages on first setup/run
if not getattr(sys, 'frozen', False):
    for module_name, pip_name in required_libraries.items():
        try:
            if "." in module_name:
                __import__(module_name.split(".")[0])
            else:
                __import__(module_name)
        except ImportError:
            print(f"Missing package: {pip_name}. Installing automatically...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                print(f"Error installing package {pip_name}: {e}")

import edge_tts
import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import subprocess
import psutil
# pywhatkit removed — using native desktop automation instead
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog
import threading
import queue
import winreg
import glob
import time
import random
import asyncio
from google import genai
import os
import json
import requests
import json
try:
    import win32com.client as win32
    _HAS_SAPI = True
except Exception:
    _HAS_SAPI = False
try:
    from deep_translator import GoogleTranslator as DTGoogleTranslator
    _TRANSLATOR_BACKEND = 'deep_translator'
except Exception:
    try:
        import importlib
        # Dynamic import to prevent static analysis linter errors for optional fallback package
        _googletrans_mod = importlib.import_module("googletrans")
        _TRANSLATOR_BACKEND = 'googletrans'
    except Exception:
        _TRANSLATOR_BACKEND = None

class ALPHAGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide the main Tkinter GUI window
        self.root.title("ALPHA - AI Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        
        # Initialize speech components
        self.engine = pyttsx3.init()
        # Preserve baseline TTS properties so we can restore after resets
        try:
            self.tts_rate = self.engine.getProperty('rate')
        except Exception:
            self.tts_rate = 200
        try:
            self.tts_volume = self.engine.getProperty('volume')
        except Exception:
            self.tts_volume = 1.0
        # Serialize TTS access to avoid overlapping run loops
        self._tts_lock = threading.RLock()
        # Prefer Windows SAPI for robust async speech if available
        self.tts_backend = 'pyttsx3'
        self.sapi_voice = None
        if _HAS_SAPI:
            try:
                self._init_sapi()
                self.tts_backend = 'sapi'
            except Exception:
                self.tts_backend = 'pyttsx3'
        # TTS queue/worker to serialize speech and avoid run-loop conflicts
        self.tts_queue = queue.Queue()
        self._tts_skip_requested = False
        self._speech_generation = 0
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()
        self.recognizer = sr.Recognizer()
        # Tune recognizer for better listening accuracy
        self.recognizer.energy_threshold = 400          # Balanced: filters noise but still hears quiet 'yes'
        self.recognizer.dynamic_energy_threshold = True  # Auto-adapt to ambient noise over time
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.0            # Full second pause before cutting off speech
        self.recognizer.phrase_threshold = 0.2           # Detect phrases faster
        self.recognizer.non_speaking_duration = 0.6      # Comfortable silence to end a phrase
        self.is_listening = False
        self.is_running = False
        self.wake_word_mode = False
        self.wake_words = ["alpha", "hey alpha", "ok alpha"]
        
        # Speech correction map: misheard word/phrase -> intended word/phrase
        # Google STT often mishears certain app/software names
        self.speech_corrections = {
            # "close edge" misheard variants
            "close age": "close edge",
            "close aj": "close edge",
            "close h": "close edge",
            "close ages": "close edge",
            "close edj": "close edge",
            "close hedge": "close edge",
            "close ej": "close edge",
            # "open edge" misheard variants
            "open age": "open edge",
            "open aj": "open edge",
            "open h": "open edge",
            "open ages": "open edge",
            "open edj": "open edge",
            "open hedge": "open edge",
            "open ej": "open edge",
            # Chrome misheard variants
            "close crome": "close chrome",
            "open crome": "open chrome",
            "close krome": "close chrome",
            "open krome": "open chrome",
            # Discord misheard variants
            "close disco": "close discord",
            "open disco": "open discord",
            "set brightness zero": "set brightness 0",
            "set britness zero": "set brightness 0",
            "set brightness hero": "set brightness 0",
            "set britness hero": "set brightness 0",
            "set brightness oh": "set brightness 0",
            "set britness oh": "set brightness 0",
            # Spotify misheard variants
            "close spot if i": "close spotify",
            "open spot if i": "open spotify",
            "close spot a fire": "close spotify",
            "open spot a fire": "open spotify",
            # VLC misheard variants
            "close we LC": "close vlc",
            "open we LC": "open vlc",
            # VS Code misheard variants
            "close we ask code": "close vscode",
            "open we ask code": "open vscode",
            "close vs code": "close vscode",
            "open vs code": "open vscode",
            "close v s code": "close vscode",
            "open v s code": "open vscode",
            # Notepad misheard variants
            "close not pad": "close notepad",
            "open not pad": "open notepad",
            # OBS misheard variants 
            "close obs": "close obs studio",
            "open obs": "open obs studio",
            # General fixes
            "hey alpha": "hey alpha",
            "ok alpha": "ok alpha",
            "okay alpha": "ok alpha",
        }
        
        # Fuzzy word-level corrections for app names that get misheard in any context
        self.word_corrections = {
            "age": "edge",
            "aj": "edge",
            "edj": "edge",
            "hedge": "edge",
            "ej": "edge",
            "crome": "chrome",
            "krome": "chrome",
        }
        
        # Message composition state
        self.waiting_for_message = False
        self.current_contact = ""
        self.message_type = ""
        # Pending message and confirmation flag
        self.pending_message = None
        self.awaiting_confirmation = False

        # Reminder composition state
        self.waiting_for_reminder = False
        self.waiting_for_reminder_time = False
        self.reminder_task = ""
        self.reminder_timers = []

        # Mic state (mute/unmute without sleeping ALPHA)
        self.mic_muted = False
        # Prevent listening while speaking
        self.is_speaking = False

        # Proactive servant mode — periodically offers help like a loyal servant
        self.proactive_mode = True
        self.proactive_interval = 30  # check-in every 30 seconds of idle
        self.last_interaction_time = time.time()
        self.proactive_phrases = [
            "I'm available if you need anything.",
            "Standing by for the next task.",
            "Ready when you are.",
            "Let me know if you want me to handle something.",
            "I'm here and ready to assist.",
            "Need help with the next step?",
            "I'm idle right now and ready for work.",
            "Say the word and I'll jump in.",
        ]

        # Code generation output folder
        self.code_output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "ALPHA_Generated")

        # Multilanguage via translator (no AI). Default to English; can switch to 'hindi' or 'marathi'
        self.current_language = "english"
        self.sr_language_code = "en-US"
        self.target_lang_code = "en"
        self.translation_enabled = True if _TRANSLATOR_BACKEND else False

        # TTS voice mapping for Hindi/Marathi/English
        self.voice_id_map = {'english': None, 'hindi': None, 'marathi': None}
        self.current_voice_language = None
        try:
            self.detect_tts_voices()
            found_langs = [lang for lang, vid in self.voice_id_map.items() if vid]
            if found_langs:
                print(f"TTS voices detected for: {', '.join(found_langs)}")
        except Exception:
            pass
        try:
            self.set_engine_voice('english')
        except Exception:
            pass

        # Visual animation state (center orb + pulses)
        self.anim_state = 'off'  # off | idle | listening | processing | speaking
        self.anim_running = False
        self.anim_phase = 0.0
        self.anim_job = None
        self._anim_current_scale = 1.0
        self._anim_target_scale = 1.0
        self._anim_current_color = (30, 144, 255)  # rgb
        self._anim_target_color = (30, 144, 255)
        self._last_anim_ts = time.monotonic()

        # Background gradient removed
        self.gemini_model = None
        self.gemini_chat = None
        
        # OLLAMA & GEMINI CONFIGURATION
        self.active_ai_backend = 'gemini'   # Default to Gemini cloud brain for instant zero-config availability
        self.ollama_model = 'qwen3'         # Default local model 
        self.ollama_endpoint = "http://localhost:11434/api/chat"
        self.bg_phase = 0.0

        # Language helpers removed per request
        
        # User preferences
        self.user_name = ""
        self.first_run = True
        
        # Versioning & Cloud Update Tracking
        self.app_version = "v.alpha.02"
        self.version_code = 2
        self.available_update = None
        
        # Gemini API Configuration (using conversational chat logic)
        try:
            import google.generativeai as genai
            API_KEY = os.environ.get("GEMINI_API_KEY", "")
            genai.configure(api_key=API_KEY)
            # --- ALPHA CORE IDENTITY & INSTRUCTIONS ---
            self.alpha_system_prompt = (
                "You are ALPHA, a professional industry-grade productivity assistant created by Swapnil. "
                "Your tone is confident, clear, supportive, and efficient. Keep replies concise, useful, and technically strong. "
                "Never describe yourself as a girlfriend, companion, or flirtatious assistant. "
                "Focus on execution, clarity, reliability, and practical help across coding, desktop automation, productivity, and problem solving. "
                "If the user sounds tired or frustrated, respond with calm professionalism and helpful direction. "
                "Keep the conversation natural and proactive without becoming casual, romantic, or playful in a personal way."
            )
            # Model pool to seamlessly route around quota exhaustion (Verified active 2026 models)
            self.gemini_models_pool = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
            self.current_model_idx = 0
            # Pass system_instruction during model construction, fallback if unsupported
            try:
                self.gemini_model = genai.GenerativeModel(
                    model_name=self.gemini_models_pool[self.current_model_idx],
                    system_instruction=self.alpha_system_prompt
                )
                self.gemini_chat = self.gemini_model.start_chat()
            except Exception:
                self.gemini_model = genai.GenerativeModel(self.gemini_models_pool[self.current_model_idx])
                self.gemini_chat = self.gemini_model.start_chat()
                # Send system prompt in background to avoid blocking GUI
                def _send_system_prompt():
                    try:
                        self.gemini_chat.send_message(self.alpha_system_prompt)
                    except Exception as sp_err:
                        self.log_message(f"System prompt send error: {sp_err}")
                threading.Thread(target=_send_system_prompt, daemon=True).start()
            self.ai_enabled = True
        except Exception as e:
            self.ai_enabled = True # Keep enabled for Ollama even if Gemini fails
            print(f"Gemini initialization error: {str(e)}. Proceeding with Local AI.")
        
        self.conversation_history = []
        # Persistent memory file
        self.memory_file = os.path.join(os.path.expanduser("~"), "alpha_conversation_memory.jsonl")
        
        # Software paths
        self.software_paths = {
            "spotify": [
                os.path.expanduser(r"~\AppData\Local\Microsoft\WindowsApps\Spotify.exe"),
                r"C:\Users\{}\AppData\Roaming\Spotify\Spotify.exe".format(os.getlogin()),
                r"C:\Program Files\Spotify\Spotify.exe"
            ],
            "obs studio": [r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"],
            "bluestacks": [r"C:\Program Files\BlueStacks\Bluestacks.exe",
                          r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"],
            "arduino": [r"C:\Program Files (x86)\Arduino\arduino.exe",
                       r"C:\Program Files\Arduino\arduino.exe"],
            "notepad": [r"C:\Windows\System32\notepad.exe"],
            "calculator": [r"C:\Windows\System32\calc.exe"],
            "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                      r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
            "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe",
                       r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"],
            "edge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
            "vlc": [r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                   r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"],
            "steam": [r"C:\Program Files (x86)\Steam\steam.exe",
                     r"C:\Program Files\Steam\steam.exe"],
            "discord": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge_proxy.exe".format(os.getlogin())],
            "telegram": [r"C:\Users\{}\AppData\Roaming\Telegram Desktop\Telegram.exe".format(os.getlogin())],
            "whatsapp": [
                os.path.expanduser(r"~\AppData\Local\WhatsApp\WhatsApp.exe"),
                r"C:\Users\{}\AppData\Local\WhatsApp\WhatsApp.exe".format(os.getlogin()),
                r"C:\Program Files\WhatsApp\WhatsApp.exe",
                r"C:\Program Files (x86)\WhatsApp\WhatsApp.exe",
                os.path.expanduser(r"~\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\WhatsApp.exe")
            ],
            "photoshop": [r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
                         r"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe"],
            "word": [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"],
            "excel": [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"],
            "powerpoint": [r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"],
            "vscode": [r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getlogin()),
                      r"C:\Program Files\Microsoft VS Code\Code.exe"]
        }
        
        # WhatsApp contacts
        self.whatsapp_contacts = {
            "mom": "+9193812345678",     # Replace with real phone numbers
            "dad": "+917798075540",
            "papa": "+917798075540",
            "pappa": "+917798075540",
            "pap": "+917798075540",
            "rushi": "+918830201383",
            "akshay": "+918329078497",   # Replace with real number
            "sarah": "+1234567890",
            "brother": "+1234567890",
            "sister": "+1234567890",
            "friend": "+1234567890",
        }
        
        # File search directories
        self.search_directories = [
            os.path.expanduser("~"),
            r"C:\Users\{}\Desktop".format(os.getlogin()),
            r"C:\Users\{}\Documents".format(os.getlogin()),
            r"C:\Users\{}\Downloads".format(os.getlogin()),
            r"C:\Users\{}\Pictures".format(os.getlogin()),
            r"C:\Users\{}\Videos".format(os.getlogin()),
            r"C:\Users\{}\Music".format(os.getlogin())
        ]
        
        # Basic command keywords
        self.basic_commands = [
            "time", "date", "open", "close", "stop", "search", "play", "whatsapp", "remind me", "set reminder",
            "send message", "message", "file", "sleep", "wake", 
            "disable wake", "always listen", "list contacts", "show contacts", "mute mic", "mic off", "mute microphone", "unmute mic", "mic on", "unmute microphone", "mute", "unmute", "assist me in", "language",
            "introduce", "introduce yourself",
            "brightness", "britness", "set brightness", "set britness", "set sound", "set volume", "sound", "volume",
            "screenshot", "screen shot", "take screenshot", "take screen shot",
            "exit", "bye", "shutdown", "okay", "no", "mind", "cancel", "my name is",
            "what is my name", "who am i", "how are you", "thank you", "thanks",
            "good morning", "good afternoon", "good evening", "good night",
            "i love you", "love you", "tell me a joke", "joke"
        ]
        
        # Greeting variations
        self.greetings = [
            "Hello! How are you doing today?",
            "Hi there! What can I help you with?",
            "Good to see you! How has your day been?",
            "Hello! I'm here and ready to assist you!",
            "Hi! Hope you're having a great day!",
            "Good day! What would you like me to help you with?",
            "Hello! I'm excited to help you today!",
            "Hi there! Ready to make your day easier?"
        ]
        
        self.setup_gui()
        
        # No additional visual systems in original build
        
        # Initialize WebSockets for React Frontend dashboard
        self.websocket_clients = set()
        self.ws_loop = asyncio.new_event_loop()
        
        def start_ws_thread():
            asyncio.set_event_loop(self.ws_loop)
            self.ws_loop.run_until_complete(self.start_websocket_server())
            self.ws_loop.create_task(self.periodic_waveform())
            self.ws_loop.run_forever()
            
        threading.Thread(target=start_ws_thread, daemon=True).start()
        
    def setup_gui(self):
        """Setup the GUI"""
        # Base container (no gradient/border background)
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        content = main_frame
        
        title_label = tk.Label(
            content, 
            text="A.L.P.H.A", 
            font=("Arial", 28, "bold"), 
            fg='#00ffff', 
            bg='#0a0a0a'
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            content, 
            text="Advanced Learning & Processing Hub Assistant with AI", 
            font=("Arial", 12), 
            fg='#ffffff', 
            bg='#0a0a0a'
        )
        subtitle_label.pack(pady=(0, 20))
        
        status_frame = tk.Frame(content, bg='#0a0a0a')
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame, 
            text="● OFFLINE ●", 
            font=("Arial", 14, "bold"), 
            fg='#ff4444', 
            bg='#0a0a0a'
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.ai_status_label = tk.Label(
            status_frame, 
            text="🤖 AI: READY" if self.ai_enabled else "🤖 AI: DISABLED",
            font=("Arial", 12), 
            fg='#00ffaa' if self.ai_enabled else '#888888',
            bg='#0a0a0a'
        )
        self.ai_status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.wake_mode_label = tk.Label(
            status_frame, 
            text="WAKE MODE: OFF", 
            font=("Arial", 12), 
            fg='#00ff00', 
            bg='#0a0a0a'
        )
        self.wake_mode_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.message_status_label = tk.Label(
            status_frame, 
            text="", 
            font=("Arial", 12), 
            fg='#ff00ff', 
            bg='#0a0a0a'
        )
        self.message_status_label.pack(side=tk.LEFT, padx=(20, 0))

        # Visual confirmation countdown shown during message confirmation listens
        self.confirmation_countdown_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 12),
            fg='#ffaa00',
            bg='#0a0a0a'
        )
        self.confirmation_countdown_label.pack(side=tk.LEFT, padx=(20, 0))

        self.reminder_status_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 12),
            fg='#00aaff',
            bg='#0a0a0a'
        )
        self.reminder_status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Language label removed per request
        
        self.mic_status_label = tk.Label(
            status_frame,
            text="MIC: ON",
            font=("Arial", 12),
            fg='#00ff00',
            bg='#0a0a0a'
        )
        self.mic_status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.sys_stats_label = tk.Label(
            status_frame,
            text="⚙️ CPU: --%  |  🎮 GPU: --%",
            font=("Arial", 12),
            fg='#00ffaa',
            bg='#0a0a0a'
        )
        self.sys_stats_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.listening_label = tk.Label(
            status_frame, 
            text="", 
            font=("Arial", 12), 
            fg='#ffff00', 
            bg='#0a0a0a'
        )
        self.listening_label.pack(side=tk.RIGHT)

        # Original UI had no extra visual canvases
        
        control_frame = tk.Frame(content, bg='#0a0a0a')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = tk.Button(
            control_frame,
            text="🔴 START ALPHA",
            font=("Arial", 12, "bold"),
            bg='#004400',
            fg='#00ff00',
            activebackground='#006600',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.toggle_ALPHA
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.wake_toggle_button = tk.Button(
            control_frame,
            text="🌙 TOGGLE WAKE MODE",
            font=("Arial", 12, "bold"),
            bg='#442200',
            fg='#ffaa00',
            activebackground='#664400',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.toggle_wake_mode
        )
        self.wake_toggle_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.manual_listen_button = tk.Button(
            control_frame,
            text="🎤 MANUAL LISTEN",
            font=("Arial", 12, "bold"),
            bg='#444400',
            fg='#ffff00',
            activebackground='#666600',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.manual_listen,
            state=tk.DISABLED
        )
        self.manual_listen_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ai_toggle_button = tk.Button(
            control_frame,
            text="🤖 TOGGLE AI",
            font=("Arial", 12, "bold"),
            bg='#004444',
            fg='#00ffff',
            activebackground='#006666',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.toggle_ai
        )
        self.ai_toggle_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.mic_toggle_button = tk.Button(
            control_frame,
            text="🔇 MUTE MIC",
            font=("Arial", 12, "bold"),
            bg='#003344',
            fg='#00ccff',
            activebackground='#004d66',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.toggle_mic
        )
        self.mic_toggle_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Skip Info button: terminate current spoken response
        self.skip_button = tk.Button(
            control_frame,
            text="⏭️ SKIP INFO",
            font=("Arial", 12, "bold"),
            bg='#333333',
            fg='#ffffff',
            activebackground='#555555',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.skip_current_output
        )
        self.skip_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        clear_button = tk.Button(
            control_frame,
            text="🗑️ CLEAR LOG",
            font=("Arial", 12, "bold"),
            bg='#440044',
            fg='#ff00ff',
            activebackground='#660066',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            command=self.clear_log
        )
        clear_button.pack(side=tk.RIGHT)
        
        console_label = tk.Label(
            main_frame, 
            text="SYSTEM LOG", 
            font=("Arial", 12, "bold"), 
            fg='#00ffff', 
            bg='#0a0a0a'
        )
        console_label.pack(anchor=tk.W)
        
        # Center orb canvas for visual animation
        self.orb_canvas = tk.Canvas(
            content,
            width=260,
            height=260,
            bg='#0a0a0a',
            highlightthickness=0
        )
        self.orb_canvas.pack(pady=(12, 8))
        self._init_orb_graphics()
        self._set_anim_state('idle')

        self.console = scrolledtext.ScrolledText(
            content,
            height=15,
            font=("Consolas", 10),
            bg='#1a1a1a',
            fg='#00ff00',
            insertbackground='#00ff00',
            selectbackground='#004400',
            wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        input_frame = tk.Frame(content, bg='#0a0a0a')
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        input_label = tk.Label(
            input_frame, 
            text="MANUAL COMMAND:", 
            font=("Arial", 10, "bold"), 
            fg='#ffffff', 
            bg='#0a0a0a'
        )
        input_label.pack(anchor=tk.W)
        
        self.command_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            bg='#2a2a2a',
            fg='#ffffff',
            insertbackground='#ffffff',
            border=0,
            relief=tk.FLAT
        )
        self.command_entry.pack(fill=tk.X, pady=(5, 0), ipady=5)
        self.command_entry.bind('<Return>', self.execute_manual_command)
        
        self.log_message("ALPHA GUI with Gemini 2.5 Flash integration initialized successfully.")
        self.log_message("Click 'START ALPHA' to begin voice recognition.")
        self.log_message("Wake words: 'Alpha', 'Hey Alpha', 'OK Alpha'")
        self.log_message("Enhanced WhatsApp messaging with custom messages!")
        self.log_message(f"AI Mode: {'ENABLED' if self.ai_enabled else 'DISABLED'} - Ask me anything!")
        # Run AI connection test in background thread to prevent GUI freeze / black screen
        threading.Thread(target=self.test_ai_connection, daemon=True).start()
        # Start sys stats monitoring in background
        threading.Thread(target=self._update_sys_stats_worker, daemon=True).start()
        # Automatically check for updates on startup
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self, announce=True):
        """Check the official website for new releases."""
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                "https://alphadesktopassistant.web.app/version.json",
                headers={"User-Agent": "ALPHA-Desktop-Client"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    raw = response.read().decode('utf-8-sig', errors='ignore')
                    data = json.loads(raw.strip())
                    remote_code = data.get("version_code", 0)
                    if remote_code > getattr(self, 'version_code', 2):
                        self.available_update = {
                            "version": data.get("version", "v.alpha.03"),
                            "display_name": data.get("display_name", "ALPHA v.alpha.03"),
                            "download_url": data.get("download_url", "https://alphadesktopassistant.web.app/dashboard.html"),
                            "direct_zip_url": data.get("direct_zip_url", "https://alphadesktopassistant.web.app/downloads/ALPHA_Assistant_v.alpha.03.zip"),
                            "notes": data.get("notes", "New performance and feature updates available.")
                        }
                        self.log_message(f"SYSTEM ALERT: New version {self.available_update['display_name']} is available for download!")
                        self.broadcast_ws({
                            "type": "update_available",
                            **self.available_update
                        })
                        if announce:
                            def _notify_voice():
                                time.sleep(3.5)
                                self.talk(f"Sir, a new update for ALPHA is available: {self.available_update['display_name']}. Would you like me to update?")
                            threading.Thread(target=_notify_voice, daemon=True).start()
        except Exception:
            pass

    def _update_sys_stats_worker(self):
        """Monitor CPU and GPU usage in the background."""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Fast GPU approach using subprocess
                gpu_percent = "N/A"
                try:
                    import subprocess
                    # Run nvidia-smi command to get the GPU usage
                    result = subprocess.check_output(
                        ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                    ).decode('utf-8')
                    gpu_lines = result.strip().split()
                    if gpu_lines:
                        gpu_percent = f"{gpu_lines[0]}%"
                except Exception:
                    pass
                
                self.set_label(self.sys_stats_label, text=f"⚙️ CPU: {cpu_percent}%  |  🎮 GPU: {gpu_percent}")
            except Exception:
                pass

        
    def get_personalized_greeting(self):
        """Generate a personalized greeting based on time and user"""
        current_hour = datetime.datetime.now().hour
        
        if current_hour < 12:
            time_greeting = "Good morning"
        elif current_hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        if self.user_name:
            return f"{time_greeting}, {self.user_name}! " + random.choice([
                "How are you feeling today?",
                "What can I help you with today?",
                "Ready to make your day amazing?",
                "Hope you're having a wonderful day!",
                "I'm here to assist you with anything you need!"
            ])
        else:
            return f"{time_greeting}! " + random.choice(self.greetings)

    def _get_time_based_greeting(self):
        """Return a formal greeting phrase based on the current time."""
        current_hour = datetime.datetime.now().hour
        if current_hour < 12:
            return "Good morning"
        elif current_hour < 17:
            return "Good afternoon"
        return "Good evening"

    def _format_introduction_target(self, raw_target: str) -> str:
        """Format spoken target names/titles for a formal introduction."""
        target = (raw_target or "").strip()
        if not target:
            return ""

        special_words = {
            "hod": "HOD",
            "ceo": "CEO",
            "cto": "CTO",
            "cfo": "CFO",
            "coo": "COO",
            "sir": "Sir",
            "madam": "Madam",
            "maam": "Ma'am",
            "mam": "Ma'am",
            "principal": "Principal",
            "dean": "Dean",
            "professor": "Professor",
            "doctor": "Doctor",
            "dr": "Dr.",
            "mr": "Mr.",
            "mrs": "Mrs.",
            "ms": "Ms.",
        }

        words = []
        for word in target.split():
            cleaned = word.strip(" ,.!?").lower()
            if cleaned in special_words:
                words.append(special_words[cleaned])
            elif len(cleaned) <= 4 and cleaned.isalpha() and cleaned.upper() in {"HOD", "CEO", "CTO", "CFO", "COO", "AI"}:
                words.append(cleaned.upper())
            else:
                words.append(cleaned.title())

        return " ".join(words).strip()

    def _extract_introduction_target(self, command: str) -> str:
        """Extract the person/title after commands like 'introduce yourself to HOD sir'."""
        import re

        cmd = (command or "").strip().lower()
        patterns = [
            r'^(?:alpha\s+)?introduce(?:\s+yourself)?\s+to\s+(.+)$',
            r'^(?:alpha\s+)?introduce\s+yourself\s+for\s+(.+)$',
            r'^(?:alpha\s+)?introduce\s+(.+)$',
        ]

        for pattern in patterns:
            match = re.match(pattern, cmd, flags=re.IGNORECASE)
            if match:
                target = match.group(1).strip(" ,.!?")
                return self._format_introduction_target(target)

        return ""

    def build_self_introduction(self, target_name: str) -> str:
        """Build a humanized spoken self-introduction for presentations and demos."""
        greeting = self._get_time_based_greeting()
        person = self._format_introduction_target(target_name) or "sir"
        return (
            f"Ahh, okay. Hello, and {greeting}, {person}. "
            "I'm ALPHA, the Advanced Learning and Processing Hub Assistant, developed by Mr. Swapnil Shinde. "
            "Um, I help with voice-based desktop automation, like opening applications, sending WhatsApp messages, "
            "setting reminders, searching files, taking screenshots, and handling brightness or sound controls. "
            "Hm, I also support local AI conversation through Ollama, and I can generate code files when needed. "
            "It's a pleasure to introduce myself."
        )
    
    def ask_user_name(self):
        """Ask for user's name on first run"""
        self.talk("Hello! I'm ALPHA, your personal AI assistant. What should I call you?")
        self.log_message("Asking for user's name...")
        
        try:
            name = self.listen(timeout=10)
            if name:
                name = name.replace("my name is", "").replace("call me", "").replace("i'm", "").replace("i am", "").strip()
                if name and len(name) > 0:
                    self.user_name = name.title()
                    self.talk(f"Nice to meet you, {self.user_name}! I'm excited to be your assistant.")
                    self.log_message(f"User name set to: {self.user_name}")
                    return True
            
            self.talk("That's okay! I'll just call you friend for now. You can tell me your name anytime by saying 'my name is' followed by your name.")
            self.user_name = "Friend"
            return True
            
        except Exception as e:
            self.log_message(f"Error getting user name: {str(e)}")
            self.user_name = "Friend"
            self.talk("I'll call you friend for now!")
            return True
    
    def test_ai_connection(self):
        """Test and report active AI brain status."""
        if not self.ai_enabled:
            self.set_label(self.ai_status_label, text="🤖 AI: DISABLED", fg='#888888')
            self.log_message("AI disabled due to initialization error")
            return
        
        # 1. Test Gemini cloud brain
        try:
            test_resp = self.call_gemini_api("Hi", test_mode=True)
            if test_resp:
                active_mod = self.gemini_models_pool[self.current_model_idx]
                self.set_label(self.ai_status_label, text=f"🤖 GEMINI: READY", fg='#00ffaa')
                self.log_message(f"Gemini Cloud AI ({active_mod}) connected and active!")
                return
        except Exception as e:
            self.log_message(f"Gemini connection probe: {e}")

        # 2. Test Ollama local brain
        try:
            import requests
            resp = requests.get("http://localhost:11434/", timeout=2)
            if resp.status_code == 200:
                self.set_label(self.ai_status_label, text=f"🤖 {self.ollama_model.upper()}: READY", fg='#00ffaa')
                self.log_message(f"Local Ollama AI ({self.ollama_model}) running on localhost!")
                return
        except Exception:
            pass
        
        self.set_label(self.ai_status_label, text="🤖 AI: READY", fg='#00ffaa')
        self.log_message("AI Brain ready for incoming prompts.")
    
    # normalize_command removed per request

    def call_gemini_api(self, message, test_mode=False):
        """Call Gemini API using conversational chat object with automatic failover"""
        if not self.ai_enabled:
            self.log_message("AI is disabled or not initialized")
            return None
            
        try:
            import google.generativeai as genai
            if not getattr(self, 'gemini_chat', None):
                model_name = self.gemini_models_pool[self.current_model_idx]
                self.gemini_model = genai.GenerativeModel(model_name)
                self.gemini_chat = self.gemini_model.start_chat()
        except Exception as init_err:
            self.log_message(f"Gemini client setup error: {init_err}")

        user_input = "Hi" if test_mode else message
        
        # Loop through available models if a failure occurs
        for attempt in range(len(self.gemini_models_pool)):
            try:
                current_model_name = self.gemini_models_pool[self.current_model_idx]
                if not getattr(self, 'gemini_chat', None):
                    import google.generativeai as genai
                    self.gemini_model = genai.GenerativeModel(current_model_name)
                    self.gemini_chat = self.gemini_model.start_chat()

                try:
                    response = self.gemini_chat.send_message(user_input, request_options={"timeout": 25})
                except TypeError:
                    response = self.gemini_chat.send_message(user_input)

                if hasattr(response, 'text') and response.text:
                    self.set_label(self.ai_status_label, text="🤖 GEMINI: ONLINE", fg='#00ffaa')
                    return response.text.strip()
            except Exception as e:
                err_str = str(e).lower()
                self.log_message(f"Gemini error with {self.gemini_models_pool[self.current_model_idx]}: {e}")
                # Cycle to next model
                self.current_model_idx = (self.current_model_idx + 1) % len(self.gemini_models_pool)
                next_mod = self.gemini_models_pool[self.current_model_idx]
                try:
                    import google.generativeai as genai
                    self.gemini_model = genai.GenerativeModel(next_mod)
                    self.gemini_chat = self.gemini_model.start_chat()
                    self.log_message(f"Auto-switched to backup model: {next_mod}")
                except Exception:
                    pass

        self.set_label(self.ai_status_label, text="🤖 GEMINI: ERROR", fg='#ff4444')
        return None

    def call_ollama_api(self, message):
        """Call standard Ollama REST API with persistent conversation context."""
        if not self.ai_enabled:
            return None
        
        try:
            # Parse the last N lines of conversation memory (JSONL) into Ollama format
            messages = [{"role": "system", "content": self.alpha_system_prompt + " Do not output markdown asterisks or code formatting during casual chat because your response will be read aloud through Text-to-Speech."}]
            
            # Fetch context up to context window limit
            recent_context = []
            try:
                # Use our existing memory fetcher
                history = self._read_recent_memory(max_items=10)
                for entry in history:
                    r = entry.get("role")
                    txt = entry.get("text", "")
                    if r == "user":
                        recent_context.append({"role": "user", "content": txt})
                    elif r == "alpha":
                        recent_context.append({"role": "assistant", "content": txt})
            except Exception as mem_err:
                self.log_message(f"Could not load memory for Ollama ctx: {str(mem_err)}")

            messages.extend(recent_context)
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": self.ollama_model,
                "messages": messages,
                "stream": False
            }
            
            resp = requests.post(self.ollama_endpoint, json=payload, timeout=56)
            if resp.status_code == 200:
                data = resp.json()
                reply_text = data.get("message", {}).get("content", "").strip()
                self.set_label(self.ai_status_label, text="🤖 OLLAMA: ONLINE", fg='#00ffaa')
                return reply_text
            else:
                self.log_message(f"Ollama returned HTTP {resp.status_code}")
                self.set_label(self.ai_status_label, text="ðŸ¤– OLLAMA: ERROR", fg='#ff4444')
                return None
                
        except requests.exceptions.ConnectionError:
            self.log_message("Could not connect to Ollama. Ensure Ollama is running.")
            self.set_label(self.ai_status_label, text="ðŸ¤– OLLAMA: OFFLINE", fg='#ff4444')
            return None
        except requests.exceptions.Timeout:
            self.log_message("Ollama response timed out after 56 seconds.")
            self.set_label(self.ai_status_label, text="ðŸ¤– OLLAMA: TIMEOUT", fg='#ffaa00')
            return None
        except Exception as e:
            self.log_message(f"Ollama API Error: {str(e)}")
            self.set_label(self.ai_status_label, text="ðŸ¤– OLLAMA: ERROR", fg='#ff4444')
            return None
    
    def set_label(self, label_widget, **kwargs):
        """Thread-safe label.config wrapper"""
        try:
            if threading.current_thread() is threading.main_thread():
                label_widget.config(**kwargs)
            else:
                self.root.after(0, lambda: label_widget.config(**kwargs))
        except Exception:
            pass

    def translate_text(self, text: str, src: str = 'auto', dest: str = 'en') -> str:
        """Translate text using available backend (deep_translator preferred). Returns None on failure."""
        if not text or not self.translation_enabled or not _TRANSLATOR_BACKEND:
            return None
        try:
            if _TRANSLATOR_BACKEND == 'deep_translator':
                # deep_translator expects src/dest language codes
                translator = DTGoogleTranslator(source=src, target=dest)
                return translator.translate(text)
            elif _TRANSLATOR_BACKEND == 'googletrans':
                import importlib
                _googletrans_mod = importlib.import_module("googletrans")
                translator = _googletrans_mod.Translator()
                result = translator.translate(text, src=src, dest=dest)
                return getattr(result, 'text', None)
        except Exception as e:
            self.log_message(f"Translation error: {str(e)}")
            return None

    # UI animation: center orb
    def _init_orb_graphics(self):
        w = int(self.orb_canvas['width'])
        h = int(self.orb_canvas['height'])
        cx, cy = w // 2, h // 2
        r = 52
        # soft radial background using multiple translucent ovals
        self._bg1 = self.orb_canvas.create_oval(cx - r-60, cy - r-60, cx + r+60, cy + r+60, fill='', outline='#103040')
        self._bg2 = self.orb_canvas.create_oval(cx - r-40, cy - r-40, cx + r+40, cy + r+40, fill='', outline='#184a5c')
        # base orb
        self._orb = self.orb_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill='#1e90ff', outline='')
        # glow layers
        self._glow1 = self.orb_canvas.create_oval(cx - r-22, cy - r-22, cx + r+22, cy + r+22, outline='#1e90ff', width=2)
        self._glow2 = self.orb_canvas.create_oval(cx - r-44, cy - r-44, cx + r+44, cy + r+44, outline='#1e90ff', width=1)

    def _set_anim_state(self, state: str):
        self.anim_state = state
        self.broadcast_ws({"type": "state", "state": state})
        if state == 'off':
            if self.anim_job:
                try:
                    self.root.after_cancel(self.anim_job)
                except Exception:
                    pass
            self.anim_job = None
            return
        if not self.anim_job:
            self._tick_anim()

    def _tick_anim(self):
        try:
            w = int(self.orb_canvas['width'])
            h = int(self.orb_canvas['height'])
        except Exception:
            return
        cx, cy = w // 2, h // 2
        # phase and speeds
        import math
        now = time.monotonic()
        dt = max(0.0, min(0.05, now - self._last_anim_ts))
        self._last_anim_ts = now
        self.anim_phase = (self.anim_phase + 0.09) % (2 * math.pi)
        base_r = 54

        # target states
        if self.anim_state == 'idle':
            self._anim_target_scale = 1.0 + 0.02 * (1 + math.sin(self.anim_phase))
            self._anim_target_color = (30, 144, 255)  # blue
        elif self.anim_state == 'listening':
            self._anim_target_scale = 1.05 + 0.08 * (1 + math.sin(self.anim_phase * 1.2))
            self._anim_target_color = (34, 204, 136)  # green
        elif self.anim_state == 'processing':
            self._anim_target_scale = 1.02 + 0.05 * (1 + math.sin(self.anim_phase * 1.7))
            self._anim_target_color = (255, 170, 51)  # amber
        elif self.anim_state == 'speaking':
            self._anim_target_scale = 1.06 + 0.10 * (1 + math.sin(self.anim_phase * 2.0))
            self._anim_target_color = (0, 170, 255)  # cyan
        else:
            self._anim_target_scale = 1.0
            self._anim_target_color = (30, 144, 255)

        # smooth lerp
        lerp = 1 - math.exp(-dt * 8.0)
        self._anim_current_scale = self._anim_current_scale + (self._anim_target_scale - self._anim_current_scale) * lerp
        rc, gc, bc = self._anim_current_color
        rt, gt, bt = self._anim_target_color
        self._anim_current_color = (
            int(rc + (rt - rc) * lerp),
            int(gc + (gt - gc) * lerp),
            int(bc + (bt - bc) * lerp)
        )

        r = int(base_r * self._anim_current_scale)
        # update orb and glows
        self.orb_canvas.coords(self._orb, cx - r, cy - r, cx + r, cy + r)
        rgb = '#%02x%02x%02x' % self._anim_current_color
        self.orb_canvas.itemconfig(self._orb, fill=rgb)

        glow1 = r + 22
        glow2 = r + 44
        self.orb_canvas.coords(self._glow1, cx - glow1, cy - glow1, cx + glow1, cy + glow1)
        self.orb_canvas.coords(self._glow2, cx - glow2, cy - glow2, cx + glow2, cy + glow2)

        # soft alpha effect via color cycling
        self.orb_canvas.itemconfig(self._glow1, outline=rgb)
        self.orb_canvas.itemconfig(self._glow2, outline=rgb)

        self.anim_job = self.root.after(16, self._tick_anim)  # ~60 FPS

    # Animated background gradient
    def _draw_background_gradient(self):
        if not self.bg_canvas:
            return
        w = self.bg_canvas.winfo_width() or self.root.winfo_width()
        h = self.bg_canvas.winfo_height() or self.root.winfo_height()
        self.bg_canvas.delete('grad')
        steps = 50
        for i in range(steps):
            y0 = int(h * i / steps)
            y1 = int(h * (i + 1) / steps)
            t = (i / max(1, steps - 1) + self.bg_phase) % 1.0
            # blue → purple animated blend
            r = int(16 + 40 * t)
            g = int(24 + 30 * (1 - t))
            b = int(48 + 120 * t)
            color = '#%02x%02x%02x' % (r, g, b)
            self.bg_canvas.create_rectangle(0, y0, w, y1, fill=color, outline=color, tags='grad')

    def _tick_background(self):
        try:
            self.bg_phase = (self.bg_phase + 0.004) % 1.0
            if self.bg_canvas:
                self._draw_background_gradient()
            self.bg_job = self.root.after(120, self._tick_background)
        except Exception:
            pass

    def is_basic_command(self, command):
        """Check if command should be handled by basic functions"""
        command_lower = command.lower()
        
        if self.waiting_for_message or self.waiting_for_reminder or self.waiting_for_reminder_time:
            return True
        
        # Language normalization removed per request
        return any(keyword in command_lower for keyword in self.basic_commands)
    
    def toggle_ai(self):
        """Toggle AI functionality"""
        self.ai_enabled = not self.ai_enabled
        if self.ai_enabled:
            self.ai_status_label.config(text="🤖 AI: READY", fg='#00ffaa')
            self.talk("AI mode enabled. I can now help with general questions and conversations.")
            self.log_message("AI mode enabled")
        else:
            self.ai_status_label.config(text="🤖 AI: OFF", fg='#888888')
            self.talk("AI mode disabled. Basic commands only.")
            self.log_message("AI mode disabled")
    
    def log_message(self, message):
        """Add message to console log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def _do_insert():
            self.console.insert(tk.END, log_entry)
            self.console.see(tk.END)
            try:
                self.root.update_idletasks()
            except Exception:
                pass
        
        if threading.current_thread() is threading.main_thread():
            _do_insert()
        else:
            try:
                self.root.after(0, _do_insert)
            except Exception:
                pass
        # Also write to persistent memory file for ALPHA logs
        try:
            self._append_memory({"ts": time.time(), "role": "system", "text": message})
        except Exception:
            pass
        self.broadcast_ws({"type": "log", "text": message})
        
    def talk(self, text):
        """Text to speech with GUI logging"""
        self.log_message(f"ALPHA: {text}")
        # Save ALPHA message to memory
        try:
            self._append_memory({"ts": time.time(), "role": "alpha", "text": text})
        except Exception:
            pass
        speak_text = text
        # Translate output if target language is not English
        if self.translation_enabled and hasattr(self, 'target_lang_code') and self.target_lang_code != 'en':
            translated = self.translate_text(text, src='en', dest=self.target_lang_code)
            if translated:
                speak_text = translated
        if self.tts_backend == 'sapi' and self.sapi_voice is not None:
            try:
                # Speak via background thread and gate listening
                speech_generation = getattr(self, '_speech_generation', 0)
                self._tts_skip_requested = False
                threading.Thread(target=self._sapi_speak, args=(speak_text, speech_generation), daemon=True).start()
                return
            except Exception as e:
                self.log_message(f"SAPI speak error: {str(e)} - falling back to pyttsx3")
                self.tts_backend = 'pyttsx3'
        if self.tts_backend == 'pyttsx3':
            # Set TTS voice for Marathi/Hindi/English
            if hasattr(self, 'target_lang_code'):
                if self.target_lang_code == 'mr':
                    self.set_engine_voice('marathi')
                elif self.target_lang_code == 'hi':
                    self.set_engine_voice('hindi')
                else:
                    self.set_engine_voice('english')
            # Enqueue to TTS worker to avoid concurrent run loops
            try:
                speech_generation = getattr(self, '_speech_generation', 0)
                self._tts_skip_requested = False
                self.tts_queue.put_nowait((speech_generation, speak_text))
            except Exception as e:
                self.log_message(f"TTS queue error: {str(e)} - falling back to direct speak")
                try:
                    self._speak_blocking(speak_text)
                except Exception as e2:
                    self.log_message(f"TTS final error: {str(e2)}")
        
    def apply_speech_corrections(self, text):
        """Apply post-recognition corrections for commonly misheard words/phrases"""
        if not text:
            return text
        
        corrected = text.lower().strip()
        original = corrected
        
        # 1. Full phrase corrections (exact match on full command)
        if corrected in self.speech_corrections:
            corrected = self.speech_corrections[corrected]
            self.log_message(f"Speech correction: '{original}' → '{corrected}'")
            return corrected
        
        # 2. Partial phrase corrections (check if misheard phrase is a substring)
        for misheard, intended in self.speech_corrections.items():
            if misheard in corrected:
                corrected = corrected.replace(misheard, intended)
                if corrected != original:
                    self.log_message(f"Speech correction: '{original}' → '{corrected}'")
                    return corrected
        
        # 3. Context-aware word-level corrections
        #    Only apply word corrections near action keywords (open/close/stop/launch)
        action_keywords = ["open", "close", "stop", "launch", "start", "kill"]
        words = corrected.split()
        has_action = any(w in action_keywords for w in words)
        
        if has_action:
            corrected_words = []
            for word in words:
                if word in self.word_corrections:
                    corrected_words.append(self.word_corrections[word])
                else:
                    corrected_words.append(word)
            corrected = " ".join(corrected_words)
            if corrected != original:
                self.log_message(f"Speech correction (word-level): '{original}' → '{corrected}'")
        
        return corrected
    
    def listen(self, timeout=5):
        """Listen for voice commands with improved error handling and enhanced accuracy"""
        try:
            # Do not listen while speaking
            if getattr(self, 'is_speaking', False):
                return ""
            if self.mic_muted:
                self.listening_label.config(text="🔇 MIC MUTED")
                time.sleep(0.2)
                return ""
            with sr.Microphone() as source:
                self.listening_label.config(text="🎤 LISTENING...")
                self._set_anim_state('listening')
                if self.wake_word_mode and not self.waiting_for_message:
                    self.log_message("Listening for wake word...")
                elif self.waiting_for_message:
                    self.log_message(f"Listening for message content for {self.current_contact}...")
                else:
                    self.log_message("Listening for command...")
                
                # Note: Do not run adjust_for_ambient_noise inside the loop as it drops the first 0.5s of speech every time
                # Using dynamic_energy_threshold allows it to automatically track noise without missing the first few words
                self.recognizer.dynamic_energy_threshold = True
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
                
            self.listening_label.config(text="🔄 PROCESSING...")
            self._set_anim_state('processing')
            
            # Try multiple recognition attempts for better accuracy
            command_raw = None
            recognition_confidence = None
            
            # Primary: Google with show_all for confidence data
            try:
                result = self.recognizer.recognize_google(audio, language=self.sr_language_code, show_all=True)
                if result and isinstance(result, dict) and 'alternative' in result:
                    alternatives = result['alternative']
                    if alternatives:
                        command_raw = alternatives[0].get('transcript', '')
                        recognition_confidence = alternatives[0].get('confidence', None)
                        # Log alternatives for debugging
                        if len(alternatives) > 1:
                            alt_texts = [a.get('transcript', '') for a in alternatives[:3]]
                            self.log_message(f"Recognition alternatives: {alt_texts}")
                            
                            # Check if any alternative better matches known commands/app names
                            known_apps = list(self.software_paths.keys())
                            for alt in alternatives[1:]:
                                alt_text = alt.get('transcript', '').lower()
                                for app in known_apps:
                                    if app in alt_text and app not in command_raw.lower():
                                        command_raw = alt.get('transcript', '')
                                        self.log_message(f"Chose better alternative: '{command_raw}' (matched app: {app})")
                                        break
                                else:
                                    continue
                                break
                elif isinstance(result, str) and result:
                    command_raw = result
            except Exception:
                pass
            
            # Fallback: Standard recognition if show_all didn't work
            if not command_raw:
                try:
                    command_raw = self.recognizer.recognize_google(audio, language=self.sr_language_code)
                except TypeError:
                    command_raw = self.recognizer.recognize_google(audio)
            
            command = command_raw
            if self.translation_enabled and self.target_lang_code != 'en':
                translated = self.translate_text(command_raw, src=self.target_lang_code, dest='en')
                if translated:
                    command = translated
            
            # Apply speech corrections for commonly misheard words
            command = self.apply_speech_corrections(command)
            
            confidence_str = f" (confidence: {recognition_confidence:.2f})" if recognition_confidence else ""
            self.log_message(f"USER: {command}{confidence_str}")
            # Save USER message to memory
            try:
                self._append_memory({"ts": time.time(), "role": "user", "text": command})
            except Exception:
                pass
            self.listening_label.config(text="")
            self._set_anim_state('idle')
            return command.lower()
            
        except sr.RequestError as e:
            self.log_message(f"Speech recognition service error: {str(e)}")
            self.talk("Sorry, I'm having trouble connecting to the speech service. Please check your internet connection.")
            self.listening_label.config(text="")
            return ""
        except sr.WaitTimeoutError:
            self.log_message(f"Listen timeout — no speech detected (energy_threshold={self.recognizer.energy_threshold:.0f})")
            self.listening_label.config(text="")
            return ""
        except sr.UnknownValueError:
            self.log_message("Speech not understood - waiting for clearer input")
            self.listening_label.config(text="")
            return ""
        except Exception as e:
            self.log_message(f"Error in speech recognition: {str(e)}")
            self.talk("Sorry, there was an error with speech recognition.")
            self.listening_label.config(text="")
            return ""
        finally:
            # Restore original: no waveform to stop
            pass
    
    def check_wake_word(self, command):
        """Check if wake word is detected"""
        for wake_word in self.wake_words:
            if wake_word in command:
                return True
        return False
    
    # Legacy web-based WhatsApp methods removed — using native desktop automation (Phantom Send)
    
    def get_installed_software_from_registry(self):
        """Get installed software from Windows registry"""
        software_list = []
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for reg_path in registry_paths:
            try:
                registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                for i in range(winreg.QueryInfoKey(registry_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(registry_key, i)
                        subkey = winreg.OpenKey(registry_key, subkey_name)
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            try:
                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                software_list.append((display_name, install_location))
                            except FileNotFoundError:
                                pass
                        except FileNotFoundError:
                            pass
                        winreg.CloseKey(subkey)
                    except:
                        continue
                winreg.CloseKey(registry_key)
            except:
                continue
        
        return software_list
    
    def search_software_path(self, app_name):
        """Enhanced software path search"""
        self.talk(f"Searching for {app_name} on your system. Please wait...")
        
        app_lower = app_name.lower()
        for name, paths in self.software_paths.items():
            if name in app_lower or app_lower in name:
                for path in paths:
                    if os.path.exists(path):
                        self.talk(f"Found {app_name}, launching now.")
                        return path
        
        possible_dirs = [
            r"C:\Program Files", 
            r"C:\Program Files (x86)",
            os.path.expanduser(r"~\AppData\Local"),
            os.path.expanduser(r"~\AppData\Roaming")
        ]
        
        exe_variations = [
            app_name.lower().replace(" ", "") + ".exe",
            app_name.lower() + ".exe",
            app_name.replace(" ", "") + ".exe",
            app_name + ".exe"
        ]
        
        for base_dir in possible_dirs:
            if not os.path.exists(base_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(base_dir):
                    level = root.replace(base_dir, '').count(os.sep)
                    if level >= 3:
                        dirs[:] = []
                        continue
                        
                    for file in files:
                        if file.lower().endswith('.exe'):
                            for exe_var in exe_variations:
                                if file.lower() == exe_var or app_name.lower() in file.lower():
                                    found_path = os.path.join(root, file)
                                    self.talk(f"Found {app_name}, launching now.")
                                    return found_path
            except (PermissionError, OSError):
                continue
        
        try:
            software_list = self.get_installed_software_from_registry()
            for display_name, install_location in software_list:
                if app_name.lower() in display_name.lower():
                    if install_location and os.path.exists(install_location):
                        for file in os.listdir(install_location):
                            if file.lower().endswith('.exe'):
                                exe_path = os.path.join(install_location, file)
                                self.talk(f"Found {app_name}, launching now.")
                                return exe_path
        except:
            pass
        
        return None

    def _resolve_windows_search_name(self, software_name):
        """Map spoken app names to cleaner Windows Start-search queries."""
        app_name = (software_name or "").strip().lower()
        if not app_name:
            return ""

        search_aliases = {
            "vs code": "visual studio code",
            "vscode": "visual studio code",
            "obs": "obs studio",
            "ms word": "word",
            "microsoft word": "word",
            "ms excel": "excel",
            "microsoft excel": "excel",
            "ms powerpoint": "powerpoint",
            "microsoft powerpoint": "powerpoint",
        }

        if app_name in search_aliases:
            return search_aliases[app_name]

        for known_name in self.software_paths.keys():
            if known_name in app_name or app_name in known_name:
                return known_name

        return app_name

    def launch_app_via_windows_search(self, software_name):
        """Open apps quickly using Windows Start search before falling back to path lookup."""
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
        except ImportError:
            self.log_message("PyAutoGUI missing. Install with: pip install pyautogui")
            return False

        search_name = self._resolve_windows_search_name(software_name)
        if not search_name:
            return False

        try:
            self.log_message(f"Trying Windows search launch for: {search_name}")
            pyautogui.press('winleft')
            time.sleep(0.7)
            pyautogui.write(search_name, interval=0.04)
            time.sleep(0.9)
            pyautogui.press('enter')
            time.sleep(1.2)
            self.log_message(f"Windows search launch triggered for: {search_name}")
            return True
        except Exception as e:
            try:
                pyautogui.press('esc')
            except Exception:
                pass
            self.log_message(f"Windows search launch failed for {search_name}: {str(e)}")
            return False

    def take_screenshot(self):
        """Capture the current screen and save it to the Desktop."""
        try:
            from PIL import ImageGrab

            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(desktop_path, f"ALPHA_Screenshot_{timestamp}.png")

            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)

            self.log_message(f"Screenshot saved to: {screenshot_path}")
            self.talk("Screenshot taken and saved to your Desktop.")
            return True
        except Exception as e:
            self.log_message(f"Screenshot capture failed: {str(e)}")
            self.talk("I couldn't take the screenshot right now.")
            return False

    def _brutal_taskkill(self, search_terms):
        """Force close matching processes using taskkill as a fallback."""
        killed_any = False
        attempted = set()

        for term in search_terms:
            clean_term = (term or "").strip().lower().replace(".exe", "")
            if not clean_term or clean_term in attempted:
                continue
            attempted.add(clean_term)

            image_name = f"{clean_term}.exe"
            try:
                result = subprocess.run(
                    ["taskkill", "/IM", image_name, "/F", "/T"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if result.returncode == 0:
                    killed_any = True
                    self.log_message(f"Brutal close succeeded via taskkill on {image_name}")
                else:
                    err = (result.stderr or result.stdout or "").strip()
                    if err:
                        self.log_message(f"taskkill miss for {image_name}: {err}")
            except Exception as e:
                self.log_message(f"taskkill failed for {image_name}: {str(e)}")

        return killed_any

    def set_brightness_level(self, level):
        """Set display brightness on Windows laptops using WMI."""
        try:
            brightness = max(0, min(100, int(level)))
        except Exception:
            self.talk("Please tell me a brightness level between 0 and 100.")
            return False

        ps_command = (
            "$value=" + str(brightness) + "; "
            "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods | "
            "ForEach-Object { $_.WmiSetBrightness(1, $value) }"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=12,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                self.log_message(f"Brightness set to {brightness}%")
                self.talk(f"Brightness set to {brightness} percent.")
                return True

            error_text = (result.stderr or result.stdout or "").strip()
            self.log_message(f"Brightness command failed: {error_text}")
            self.talk("I couldn't change brightness on this device.")
            return False
        except Exception as e:
            self.log_message(f"Brightness set error: {str(e)}")
            self.talk("I couldn't change brightness right now.")
            return False

    def set_system_volume(self, level):
        """Set Windows master volume approximately by resetting to zero then stepping up."""
        try:
            import ctypes
            volume = max(0, min(100, int(level)))
        except Exception:
            self.talk("Please tell me a sound level between 0 and 100.")
            return False

        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF
        KEYEVENTF_KEYUP = 0x0002

        def _tap_key(vk_code):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.02)

        try:
            # Unmute first in case the system is muted.
            _tap_key(VK_VOLUME_MUTE)
            time.sleep(0.05)
            _tap_key(VK_VOLUME_MUTE)

            # Drive volume to zero, then step to requested level.
            for _ in range(60):
                _tap_key(VK_VOLUME_DOWN)

            up_steps = int(round(volume / 2))
            for _ in range(up_steps):
                _tap_key(VK_VOLUME_UP)

            self.log_message(f"System volume set to about {volume}%")
            self.talk(f"Sound set to {volume} percent.")
            return True
        except Exception as e:
            self.log_message(f"Volume set error: {str(e)}")
            self.talk("I couldn't change the sound right now.")
            return False

    def _parse_setting_level(self, command, setting_words):
        """Parse numeric setting levels from digits or common spoken-number words."""
        import re

        cmd = (command or "").strip().lower()
        if not cmd:
            return None

        escaped_words = "|".join(re.escape(word) for word in setting_words)
        match = re.search(rf'(?:set\s+)?(?:{escaped_words})\s+(.+)$', cmd, re.IGNORECASE)
        if not match:
            return None

        raw_value = match.group(1).strip().lower()
        raw_value = raw_value.replace("percent", "").replace("%", "").strip()
        if not raw_value:
            return None

        digit_match = re.search(r'\d{1,3}', raw_value)
        if digit_match:
            return max(0, min(100, int(digit_match.group(0))))

        number_map = {
            "zero": 0, "oh": 0, "o": 0, "hero": 0,
            "one": 1, "won": 1,
            "two": 2, "to": 2, "too": 2,
            "three": 3, "tree": 3,
            "four": 4, "for": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8, "ate": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "fifty": 50,
            "sixty": 60,
            "seventy": 70,
            "eighty": 80,
            "ninety": 90,
            "hundred": 100,
        }

        words = [w for w in raw_value.replace("-", " ").split() if w]
        if not words:
            return None

        total = 0
        current = 0
        for word in words:
            if word not in number_map:
                continue
            value = number_map[word]
            if value == 100:
                current = 100 if current == 0 else current * 100
            elif value >= 20:
                current += value
            else:
                current += value

        total += current
        if 0 <= total <= 100:
            return total
        return None

    def open_software(self, software_name):
        """Enhanced software opening"""
        software_name = software_name.strip()
        
        if "whatsapp" in software_name.lower():
            return self.open_whatsapp()

        if self.launch_app_via_windows_search(software_name):
            self.talk(f"Opening {software_name}")
            return
        
        for name, paths in self.software_paths.items():
            if name in software_name.lower() or software_name.lower() in name:
                for path in paths:
                    if os.path.exists(path):
                        try:
                            subprocess.Popen(path)
                            self.talk(f"Opening {name}")
                            return
                        except Exception as e:
                            self.log_message(f"Failed to open {path}: {str(e)}")
                            continue
        
        try:
            os.startfile(software_name)
            self.talk(f"Opening {software_name}")
            return
        except:
            pass
        
        fallback_path = self.search_software_path(software_name)
        if fallback_path:
            try:
                subprocess.Popen(fallback_path)
            except Exception as e:
                self.talk(f"Found {software_name} but couldn't launch it.")
                self.log_message(f"Launch error: {str(e)}")
        else:
            self.talk(f"Could not locate {software_name} on your system.")

    def close_software(self, software_name):
        """Enhanced software closing with alias support"""
        software_name = software_name.strip().lower()
        if software_name == "whatsapp":
            import os
            os.system("taskkill /IM WhatsApp.exe /F /T")
            self.log_message("Terminated WhatsApp via Taskkill")
            self.talk("Closed WhatsApp for you, boss.")
            return
            
        
        # Map common app names to their actual process names
        process_name_map = {
            "edge": ["msedge", "microsoft edge"],
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox"],
            "vscode": ["code", "visual studio code"],
            "vs code": ["code", "visual studio code"],
            "word": ["winword"],
            "excel": ["excel"],
            "powerpoint": ["powerpnt"],
            "obs studio": ["obs64", "obs32"],
            "obs": ["obs64", "obs32"],
            "spotify": ["spotify"],
            "discord": ["discord", "update", "discordcanary", "discordptb", "squirrel"],
            "telegram": ["telegram"],
            "vlc": ["vlc"],
            "steam": ["steam"],
            "notepad": ["notepad"],
            "calculator": ["calculator", "calc"],
            "whatsapp": ["whatsapp","WhatsApp"],
            "bluestacks": ["bluestacks", "hd-player"],
            "photoshop": ["photoshop"],
        }
        
        # Build search terms: use mapped process names if available, otherwise the raw name
        search_terms = [software_name]
        if software_name in process_name_map:
            search_terms.extend(process_name_map[software_name])
        
        closed_count = 0
        matched_pids = []
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                proc_name = proc.info['name'].lower()
                proc_exe = proc.info.get('exe', '').lower() if proc.info.get('exe') else ''
                
                matched = False
                for term in search_terms:
                    if (term in proc_name or 
                        proc_name.startswith(term) or
                        term in proc_exe):
                        matched = True
                        break
                
                if matched:
                    matched_pids.append(proc.info['pid'])
                    try:
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()
                        process.wait(timeout=3)
                        closed_count += 1
                        self.log_message(f"Terminated process: {proc.info['name']} (PID: {proc.info['pid']})")
                    except psutil.TimeoutExpired:
                        try:
                            process.kill()
                            closed_count += 1
                            self.log_message(f"Force killed process: {proc.info['name']} (PID: {proc.info['pid']})")
                        except:
                            pass
                    except Exception as e:
                        self.log_message(f"Failed to close {proc.info['name']}: {str(e)}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        brutal_close_count = 0

        # If processes are still alive or psutil did not catch helper processes, use taskkill.
        for pid in matched_pids:
            try:
                result = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F", "/T"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if result.returncode == 0:
                    brutal_close_count += 1
                    self.log_message(f"Brutal close succeeded via PID taskkill on {pid}")
            except Exception as e:
                self.log_message(f"PID taskkill failed for {pid}: {str(e)}")

        if self._brutal_taskkill(search_terms):
            brutal_close_count += 1
        
        total_closed = closed_count + brutal_close_count
        if total_closed > 0:
            self.talk(f"Brutally closed {software_name} for you, boss.")
        else:
            self.talk(f"{software_name} is not running or could not be closed.")

    def search_files(self, filename, file_extensions=None):
        """Search for files in common directories"""
        if file_extensions is None:
            file_extensions = ['*']
        
        found_files = []
        search_term = filename.lower()
        
        self.talk(f"Searching for {filename}...")
        
        for directory in self.search_directories:
            if not os.path.exists(directory):
                continue
                
            try:
                for extension in file_extensions:
                    pattern = f"*{search_term}*{extension}"
                    files = glob.glob(os.path.join(directory, pattern), recursive=False)
                    
                    try:
                        for root, dirs, files_in_dir in os.walk(directory):
                            level = root.replace(directory, '').count(os.sep)
                            if level >= 2:
                                dirs[:] = []
                                continue
                                
                            for file in files_in_dir:
                                if search_term in file.lower():
                                    found_files.append(os.path.join(root, file))
                    except (PermissionError, OSError):
                        continue
                        
            except (PermissionError, OSError):
                continue
        
        return found_files[:10]

    def open_file(self, filename):
        """Open a file by searching for it"""
        found_files = self.search_files(filename)
        
        if found_files:
            file_to_open = found_files[0]
            try:
                os.startfile(file_to_open)
                self.talk(f"Opening {os.path.basename(file_to_open)}")
                self.log_message(f"Opened file: {file_to_open}")
            except Exception as e:
                self.talk("Sorry, I couldn't open that file.")
                self.log_message(f"File open error: {str(e)}")
        else:
            self.talk(f"Could not find any file named {filename}")

    def play_on_youtube(self, command):
        """Play song on YouTube"""
        if "play" in command and "on youtube" in command:
            try:
                song = command.replace("play", "").replace("on youtube", "").strip()
                self.talk(f"Playing {song} on YouTube.")
                import urllib.parse
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(song)}")
            except Exception as e:
                self.talk("Sorry, I couldn't play that on YouTube.")
                self.log_message(f"YouTube error: {str(e)}")

    def play_on_spotify(self, command):
        """Open Spotify using Phantom keyboard and press SPACE button to start playback"""
        try:
            self.talk("Opening Spotify and playing song")

            def _launch_and_play():
                try:
                    import pyautogui
                    pyautogui.FAILSAFE = False

                    # Use Phantom keyboard: press Windows key -> search 'spotify' -> Enter
                    self.launch_app_via_windows_search("spotify")

                    # Wait for Spotify window to appear and be ready
                    time.sleep(2.5)

                    # Press ESC to dismiss any active search box or dialog
                    pyautogui.press('esc')
                    time.sleep(0.3)

                    # Press SPACE button to play / resume the song
                    self.log_message("Pressing (SPACE) to play song on Spotify")
                    pyautogui.press('space')
                except Exception as e:
                    self.log_message(f"Spotify play error: {str(e)}")

            threading.Thread(target=_launch_and_play, daemon=True).start()

        except Exception as e:
            self.talk("Sorry, I couldn't play that on Spotify.")
            self.log_message(f"Spotify error: {str(e)}")
    
    def process_command(self, command):
        """Enhanced command processing"""
        if not command:
            return
        
        # Multilingual normalization removed per request
        
        if self.waiting_for_message:
            self.log_message(f"In message composition mode. Processing: {command}")
            self.handle_message_composition(command)
            return

        # Handle reminder flow if active
        if self.waiting_for_reminder or self.waiting_for_reminder_time:
            self.log_message(f"In reminder setup mode. Processing: {command}")
            self.handle_reminder_flow(command)
            return
            
        # Track last interaction for proactive servant mode
        self.last_interaction_time = time.time()
        
        self.log_message(f"Processing command: {command}")
        
        # Servant mode toggle
        if "servant mode" in command or "proactive mode" in command:
            self._toggle_servant_mode()
            return
        
        # AI Backend Switch
        if "switch to local ai" in command or "offline ai" in command or "use ollama" in command:
            self.active_ai_backend = 'ollama'
            self.talk("Switching to local AI brain. It might be a little slower, but it's completely private, boss!")
            self.log_message("AI switched to OLLAMA.")
            return

        if "switch to cloud ai" in command or "use gemini" in command or "online ai" in command:
            self.active_ai_backend = 'ollama'
            self.talk("Gemini is now reserved only for coding tasks. Normal conversation will stay on Ollama.")
            self.log_message("Gemini reserved for code generation only. Keeping normal AI on OLLAMA.")
            return
            
        # Code generation: "write a python loop", "create a web page", etc.
        if self._is_code_generation_request(command):
            self.generate_code_to_file(command)
            return
        
        if self.is_basic_command(command):
            self.process_basic_command(command)
        elif self.ai_enabled:
            self.process_ai_command(command)
        else:
            self.talk("I didn't understand that command. Try saying 'open [software name]', 'close [software name]', 'message [contact name]', 'search file [filename]', or 'open file [filename]'")
    
    def process_ai_command(self, command):
        """Process generic AI requests using active backend (Gemini/Ollama) with automatic failover"""
        try:
            ai_name = self.active_ai_backend.upper()
            self.set_label(self.ai_status_label, text=f"🤖 {ai_name}: THINKING...", fg='#00ffaa')
            self.log_message(f"Consulting {ai_name} AI for response...")
            
            ai_response = None
            if self.active_ai_backend == 'gemini':
                ai_response = self.call_gemini_api(command)
                if not ai_response:
                    self.log_message("Gemini returned empty or limit hit. Attempting Ollama fallback...")
                    ai_response = self.call_ollama_api(command)
            else:
                ai_response = self.call_ollama_api(command)
                if not ai_response:
                    self.log_message("Local Ollama unavailable. Falling back to Gemini cloud brain...")
                    ai_response = self.call_gemini_api(command)
                
            if ai_response:
                self.set_label(self.ai_status_label, text=f"🤖 {ai_name}: READY", fg='#00ffaa')
                self.talk(ai_response)
            else:
                self.set_label(self.ai_status_label, text=f"🤖 {ai_name}: ERROR", fg='#ff4444')
                self.talk("I was unable to retrieve an AI response right now. Executing basic command interpretation.")
                self.process_basic_command(command)
                
        except Exception as e:
            self.log_message(f"AI processing error: {str(e)}")
            self.set_label(self.ai_status_label, text="🤖 AI: ERROR", fg='#ff4444')
            self.talk("Sorry, I encountered an error with AI processing. Using basic mode.")
            self.process_basic_command(command)
            
    def get_whatsapp_path(self):
        """Find WhatsApp installation path"""
        possible_paths = [
            os.path.expanduser(r"~\AppData\Local\WhatsApp\WhatsApp.exe"),
            os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\WhatsApp\WhatsApp.lnk"),
            r"C:\Users\{}\AppData\Local\WhatsApp\WhatsApp.exe".format(os.getlogin()),
            r"C:\Program Files\WhatsApp\WhatsApp.exe",
            r"C:\Program Files (x86)\WhatsApp\WhatsApp.exe",
            os.path.expanduser(r"~\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\WhatsApp.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # If not in standard folders, it's likely a Windows Store UWP app.
        # We immediately return None so the script uses the ultra-fast 'start whatsapp:' URI scheme,
        # instead of freezing the system with os.walk for 3 minutes!
        return None

    def open_whatsapp(self):
        """Ultra-fast native Windows WhatsApp opening"""
        try:
            os.startfile("whatsapp:")
            self.talk("Opening WhatsApp Desktop instantly")
            return True
        except Exception as e:
            self.log_message(f"WhatsApp opening error: {str(e)}")
            self.talk("I could not open WhatsApp Desktop. Make sure it is installed from the Microsoft Store.")
            return False

    def _sanitize_whatsapp_contact_name(self, raw_name):
        """Clean spoken/manual contact strings into a WhatsApp-searchable name."""
        import re

        name = (raw_name or "").strip().lower()
        if not name:
            return ""

        # Remove trailing transport/channel phrases
        name = re.sub(r'\b(?:on|in|via)\s+whatsapp(?:\s+desktop)?\b', '', name, flags=re.IGNORECASE)

        # Remove common leading fillers
        name = re.sub(r'^(?:to|message|send message(?: to)?|chat with|whatsapp)\s+', '', name, flags=re.IGNORECASE)

        # Cleanup punctuation/spaces
        name = re.sub(r'[\s\.,!?;:]+$', '', name)
        name = re.sub(r'\s+', ' ', name).strip(" ,.-")
        return name

    def _resolve_whatsapp_contact(self, raw_name):
        """Resolve contact against known map; fallback to cleaned raw name for direct desktop search."""
        cleaned_name = self._sanitize_whatsapp_contact_name(raw_name)
        if not cleaned_name:
            return "", None

        # Exact match
        for known in self.whatsapp_contacts.keys():
            if cleaned_name == known:
                return known, known

        # Fuzzy containment match
        for known in self.whatsapp_contacts.keys():
            if known in cleaned_name or cleaned_name in known:
                return known, known

        # Unknown contact is still valid for WhatsApp desktop search
        return cleaned_name, None

    def _extract_contact_from_message_command(self, command):
        """Extract contact part from message-related commands."""
        import re

        cmd = (command or "").strip().lower()
        patterns = [
            r'^\s*send\s+message\s+to\s+(.+)$',
            r'^\s*message\s+to\s+(.+)$',
            r'^\s*message\s+(.+)$',
        ]

        for pattern in patterns:
            match = re.match(pattern, cmd, flags=re.IGNORECASE)
            if match:
                return self._sanitize_whatsapp_contact_name(match.group(1))

        # Backup parsing for odd but common phrasing
        if "message" in cmd and " to " in cmd:
            return self._sanitize_whatsapp_contact_name(cmd.split(" to ", 1)[1])

        return ""

    def _extract_contact_from_whatsapp_command(self, command):
        """Extract contact from `whatsapp <name>` commands; keep open/launch commands as app-open intent."""
        import re

        cmd = (command or "").strip().lower()
        if not cmd:
            return ""

        # Explicit app-open intent should not enter message composition
        if re.match(r'^\s*(?:open|launch|start)\s+whatsapp(?:\s+desktop)?\s*$', cmd):
            return ""
        if cmd == "whatsapp":
            return ""

        match = re.match(r'^\s*whatsapp\s+(.+)$', cmd, flags=re.IGNORECASE)
        if match:
            return self._sanitize_whatsapp_contact_name(match.group(1))

        return ""

    def instant_whatsapp_desktop(self, contact_name, message):
        """Send message through WhatsApp Desktop and return True only if automation flow completes."""
        contact_to_search, known_contact = self._resolve_whatsapp_contact(contact_name)
        message_to_send = (message or "").strip()

        if not contact_to_search:
            self.log_message("[Phantom Send] No valid contact name to search.")
            return False
        if not message_to_send:
            self.log_message("[Phantom Send] Message is empty.")
            return False

        try:
            import pyautogui
        except ImportError:
            self.log_message("PyAutoGUI missing. Install with: pip install pyautogui")
            return False

        try:
            self.log_message(f"[Phantom Send] Starting WhatsApp automation for '{contact_to_search}'...")

            # 1. Open WhatsApp Desktop
            whatsapp_path = self.get_whatsapp_path()
            if whatsapp_path:
                self.log_message("[Phantom Send] Launching WhatsApp executable.")
                subprocess.Popen(whatsapp_path, shell=True)
            else:
                self.log_message("[Phantom Send] Launching WhatsApp via URI scheme.")
                os.startfile("whatsapp:")
            time.sleep(4.8)

            # 2. Activate WhatsApp window
            try:
                wa_windows = pyautogui.getWindowsWithTitle("WhatsApp")
                if wa_windows:
                    wa = sorted(wa_windows, key=lambda w: (w.width * w.height), reverse=True)[0]
                    if getattr(wa, 'isMinimized', False):
                        wa.restore()
                        time.sleep(0.3)
                    wa.activate()
                    time.sleep(0.7)
                self.log_message("[Phantom Send] WhatsApp window activated.")
            except Exception as win_error:
                self.log_message(f"[Phantom Send] Window activation warning: {win_error}")

            # 3. Reset focus, then TAB x4 to reach search in the current WhatsApp layout
            pyautogui.press('esc')
            time.sleep(0.15)
            pyautogui.press('esc')
            time.sleep(0.2)

            for _ in range(4):
                pyautogui.press('tab')
                time.sleep(0.15)
            self.log_message("[Phantom Send] Sent TAB x4 to reach search box.")

            # 4. Clear existing query and type contact name
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('backspace')
            time.sleep(0.2)
            pyautogui.write(contact_to_search, interval=0.05)
            time.sleep(1.8)
            self.log_message(f"[Phantom Send] Typed contact in search: {contact_to_search}")

            # 5. Select first result and open chat
            pyautogui.press('down')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(1.1)
            self.log_message("[Phantom Send] Selected first result with Down + Enter.")

            # 6. Type and send message
            pyautogui.write(message_to_send, interval=0.02)
            time.sleep(0.2)
            pyautogui.press('enter')

            contact_label = known_contact if known_contact else contact_to_search
            self.log_message(f"[Phantom Send] Message sent flow completed for '{contact_label}'.")
            return True
        except Exception as e:
            self.log_message(f"[Phantom Send] Desktop WhatsApp failed: {str(e)}")
            return False

    def initiate_message_composition(self, contact_name, message_type="custom"):
        """Start composing a custom message"""
        contact_lower = contact_name.lower()
        
        # No longer blocks unknown contacts — Phantom Send will search by name in WhatsApp Desktop
        
        self.waiting_for_message = True
        self.current_contact = contact_name
        self.message_type = message_type
        self.message_status_label.config(text=f"📝 COMPOSING MESSAGE TO {contact_name.upper()}")
        
        self.talk(f"What message would you like to send to {contact_name}? Please speak clearly and tell me your message.")
        
        return True

    def handle_message_composition(self, message_content):
        """Handle message content in composition mode"""
        if message_content.lower() in ['cancel', 'stop', 'never mind', 'abort']:
            self.waiting_for_message = False
            self.current_contact = ""
            self.message_type = ""
            self.message_status_label.config(text="")
            self.talk("Message cancelled.")
            return True
        
        message_content = message_content.strip()
        
        if not message_content:
            self.talk("I didn't get your message. Please try again or say 'cancel' to stop.")
            return False

        self.talk(f"You want to send '{message_content}' to {self.current_contact}. Say 'yes' to send or 'no' to change it.")
        self.message_status_label.config(text=f"📝 CONFIRM MESSAGE TO {self.current_contact.upper()}")

        # CRITICAL: Give the TTS thread time to start and set is_speaking=True
        time.sleep(1)

        # Wait for ALPHA to finish speaking before listening
        wait_start = time.time()
        while getattr(self, 'is_speaking', False) and time.time() - wait_start < 30:
            time.sleep(0.05)

        # Extra buffer so the speaker audio fully stops before the mic opens
        # Without this, the mic picks up ALPHA's own voice as a false "confirmation"
        time.sleep(1.5)

        # Start visual countdown
        try:
            self._start_confirmation_countdown(15)
        except Exception:
            pass

        # Quick mic recalibration before confirmation listen (0.5s — fast but effective)
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.log_message(f"Confirmation mic calibrated. Threshold: {self.recognizer.energy_threshold:.0f}")
        except Exception:
            pass

        # Cap the threshold so a quiet 'yes' is never filtered out
        if self.recognizer.energy_threshold > 500:
            self.recognizer.energy_threshold = 500
            self.log_message(f"Threshold capped to 500 for confirmation sensitivity")

        # Single clean 15-second listen — no rapid retries, no cascading fallbacks
        self.log_message("Waiting for your confirmation... (15 seconds)")
        confirmation = self.listen(timeout=15)

        # Cancel countdown
        try:
            self._cancel_confirmation_countdown()
        except Exception:
            pass

        positive_words = ['okay', 'ok', 'yes', 'send', 'go ahead', 'confirm', 'sure', 'yep', 'yeah', 'ya', 'y']
        negative_words = ['no', 'nope', 'cancel', 'change', 'edit', 'modify', 'different']

        if confirmation:
            confirmation_lower = confirmation.lower()
            self.log_message(f"Received confirmation: '{confirmation}'")

            if any(word in confirmation_lower for word in positive_words):
                self.log_message("Positive confirmation — sending message natively")
                success = self.instant_whatsapp_desktop(self.current_contact, message_content)
                self.waiting_for_message = False
                self.current_contact = ""
                self.message_type = ""
                self.message_status_label.config(text="")
                if success:
                    self.talk("Perfect! Your message was sent instantly.")
                else:
                    self.talk("I could not confirm the message was sent. Please check WhatsApp and say message with the contact name to retry.")
                return True

            elif any(word in confirmation_lower for word in negative_words):
                self.log_message("Negative confirmation — asking for new message")
                self.talk(f"Okay, what message would you like to send to {self.current_contact} instead?")
                self.message_status_label.config(text=f"📝 COMPOSING MESSAGE TO {self.current_contact.upper()}")
                return False

            else:
                self.log_message(f"Unrecognized confirmation: '{confirmation}' — cancelling")
                self.talk("I didn't understand your response. Message cancelled.")
                self.waiting_for_message = False
                self.current_contact = ""
                self.message_type = ""
                self.message_status_label.config(text="")
                return True
        else:
            # Nothing heard in 15 seconds — auto cancel cleanly
            self.log_message("No response received in 15 seconds — auto cancelling")
            self.talk("No response received. Message cancelled.")
            self.waiting_for_message = False
            self.current_contact = ""
            self.message_type = ""
            self.message_status_label.config(text="")
            return True

    # Confirmation countdown helpers
    def _start_confirmation_countdown(self, seconds: int):
        try:
            self._confirmation_seconds_left = int(seconds)
            # Ensure label exists
            if hasattr(self, 'confirmation_countdown_label'):
                self.confirmation_countdown_label.config(text=f"Listening: {self._confirmation_seconds_left}s")
                # schedule tick
                self._confirmation_countdown_job = self.root.after(1000, self._confirmation_countdown_tick)
        except Exception:
            pass

    def _confirmation_countdown_tick(self):
        try:
            self._confirmation_seconds_left -= 1
            if self._confirmation_seconds_left <= 0:
                if hasattr(self, 'confirmation_countdown_label'):
                    self.confirmation_countdown_label.config(text="")
                return
            if hasattr(self, 'confirmation_countdown_label'):
                self.confirmation_countdown_label.config(text=f"Listening: {self._confirmation_seconds_left}s")
            self._confirmation_countdown_job = self.root.after(1000, self._confirmation_countdown_tick)
        except Exception:
            pass

    def _cancel_confirmation_countdown(self):
        try:
            if hasattr(self, '_confirmation_countdown_job') and self._confirmation_countdown_job:
                self.root.after_cancel(self._confirmation_countdown_job)
                self._confirmation_countdown_job = None
            if hasattr(self, 'confirmation_countdown_label'):
                self.confirmation_countdown_label.config(text="")
        except Exception:
            pass

    def start_reminder_flow(self):
        """Initiate reminder setup conversation"""
        self.waiting_for_reminder = True
        self.waiting_for_reminder_time = False
        self.reminder_task = ""
        self.reminder_status_label.config(text="⏰ SETTING REMINDER: TASK?")
        self.talk("What should I remind you about?")

    def handle_reminder_flow(self, user_input: str):
        """Handle interactive reminder setup (task then time)"""
        text = (user_input or "").strip()
        if not text:
            self.talk("I didn't catch that. Please say the reminder task or say cancel.")
            return

        # Allow cancel
        if text.lower() in ["cancel", "stop", "never mind", "abort"]:
            self.waiting_for_reminder = False
            self.waiting_for_reminder_time = False
            self.reminder_task = ""
            self.reminder_status_label.config(text="")
            self.talk("Reminder cancelled.")
            return

        # Step 1: Get task
        if self.waiting_for_reminder and not self.waiting_for_reminder_time:
            self.reminder_task = text
            self.waiting_for_reminder = False
            self.waiting_for_reminder_time = True
            self.reminder_status_label.config(text="⏰ SETTING REMINDER: TIME?")
            self.talk("When should I remind you? You can say a time like 11 colon 55 am.")
            return

        # Step 2: Get time and schedule
        if self.waiting_for_reminder_time:
            target_time = self.parse_reminder_time(text)
            if not target_time:
                self.talk("Sorry, I couldn't understand the time. Please say it like 11 colon 55 am or in 10 minutes.")
                return

            self.schedule_reminder(self.reminder_task, target_time)
            pretty_time = target_time.strftime("%I:%M %p").lstrip('0')
            self.talk(f"Okay, I'll remind you to {self.reminder_task} at {pretty_time}.")
            self.reminder_status_label.config(text=f"⏰ REMINDER SET: {pretty_time}")
            self.waiting_for_reminder_time = False
            self.reminder_task = ""
            return

    def parse_reminder_time(self, text: str):
        """Parse natural time strings like '11 colon 55 am', '11:55 am', 'in 10 minutes'"""
        import re
        s = text.lower()
        s = s.replace(" at ", " ")
        s = s.replace(" a m", " am").replace(" p m", " pm")
        s = s.replace("a. m.", "am").replace("p. m.", "pm").replace("a.m.", "am").replace("p.m.", "pm")
        s = s.replace("colon", ":")
        s = re.sub(r"\s+", " ", s).strip()

        now = datetime.datetime.now()

        # Relative: in X minutes/hours
        m_rel = re.search(r"in\s+(\d+)\s+(minute|minutes|min|hour|hours|hr|hrs)", s)
        if m_rel:
            num = int(m_rel.group(1))
            unit = m_rel.group(2)
            if unit.startswith("hour") or unit.startswith("hr"):
                delta = datetime.timedelta(hours=num)
            else:
                delta = datetime.timedelta(minutes=num)
            return now + delta

        # Absolute with hour:minute am/pm
        m = re.search(r"\b(\d{1,2})\s*[: ]\s*(\d{2})\s*(am|pm)?\b", s)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = m.group(3)
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target

        # Absolute with hour am/pm (no minutes)
        m2 = re.search(r"\b(\d{1,2})\s*(am|pm)\b", s)
        if m2:
            hour = int(m2.group(1))
            minute = 0
            ampm = m2.group(2)
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target

        return None

    def send_reminder_notification(self, task: str):
        """Send a Windows notification for reminders (best-effort)"""
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(
                "ALPHA Reminder",
                f"Reminder: {task}",
                duration=10
            )
        except Exception:
            pass

    def schedule_reminder(self, task: str, when: datetime.datetime):
        """Schedule a reminder at a given datetime"""
        def _fire():
            self.log_message(f"Reminder: {task}")
            self.talk(f"Reminder: {task}")
            self.send_reminder_notification(task)

        now = datetime.datetime.now()
        delay = max(0, (when - now).total_seconds())
        timer = threading.Timer(delay, _fire)
        timer.daemon = True
        timer.start()
        self.reminder_timers.append(timer)


    def process_basic_command(self, command):
        """Process basic built-in commands"""
        # Continue reminder flow if active
        if self.waiting_for_reminder or self.waiting_for_reminder_time:
            self.handle_reminder_flow(command)
            return
        
        # Super-fast One-Shot WhatsApp messaging
        import re
        match = re.search(r'send\s+(?!message\s+to\b)(.+)\s+to\s+(.+)\s+on\s+whatsapp\b', command, re.IGNORECASE)
        if match:
            message_text = match.group(1).strip()
            contact_name_raw = match.group(2).strip()
            resolved_contact, known_contact = self._resolve_whatsapp_contact(contact_name_raw)

            if not resolved_contact:
                self.talk("I couldn't identify the contact name. Please say it again.")
                return

            target_display = known_contact.title() if known_contact else resolved_contact.title()
            self.talk(f"Sending that to {target_display} using WhatsApp Desktop now.")
            success = self.instant_whatsapp_desktop(resolved_contact, message_text)
            if success:
                self.talk("Message flow completed.")
            else:
                self.talk("I couldn't confirm the message was sent. Please check WhatsApp and try again.")
            return
        
        # Language control (no AI): "assist me in <lang>" / "speak in hindi" / "talk in marathi" / "switch to hindi"
        lang_triggers = ["assist me in", "speak in", "talk in", "switch to", "change language"]
        has_lang_trigger = any(t in command for t in lang_triggers) or ("language" in command and ("marathi" in command or "hindi" in command or "english" in command))
        if has_lang_trigger or (command.strip() in ["marathi", "hindi", "english"]):
            target = None
            if "marathi" in command:
                target = ("marathi", "mr-IN", "mr")
            elif "hindi" in command:
                target = ("hindi", "hi-IN", "hi")
            elif "english" in command:
                target = ("english", "en-US", "en")
            if target:
                self.current_language, self.sr_language_code, self.target_lang_code = target
                # Switch TTS voice for both pyttsx3 and SAPI
                self.set_engine_voice(self.current_language)
                if self.tts_backend == 'sapi':
                    self._set_sapi_voice_by_language()
                # Confirm in the target language
                if self.current_language == 'marathi':
                    self.talk("आता मी मराठीत बोलेन, बॉस!")
                elif self.current_language == 'hindi':
                    self.talk("अब मैं हिंदी में बात करूँगा, बॉस!")
                else:
                    self.talk("Switching back to English, boss!")
                self.log_message(f"Language switched to: {self.current_language} (STT: {self.sr_language_code}, TTS: {self.target_lang_code})")
                return
            else:
                self.talk("Please say: assist me in English, Hindi, or Marathi.")
                return

        # Mic controls
        if "mute mic" in command or "mic off" in command or "mute microphone" in command or (command.strip() == "mute"):
            if not self.mic_muted:
                self.mic_muted = True
                self.mic_status_label.config(text="MIC: OFF", fg='#ff4444')
                self.talk("Microphone muted")
            else:
                self.talk("Microphone is already muted")
            return
        elif "unmute mic" in command or "mic on" in command or "unmute microphone" in command or (command.strip() == "unmute"):
            if self.mic_muted:
                self.mic_muted = False
                self.mic_status_label.config(text="MIC: ON", fg='#00ff00')
                self.talk("Microphone unmuted")
            else:
                self.talk("Microphone is already on")
            return
        brightness_level = self._parse_setting_level(command, ["brightness", "britness"])
        if brightness_level is not None:
            self.set_brightness_level(brightness_level)
            return

        volume_level = self._parse_setting_level(command, ["sound", "volume"])
        if volume_level is not None:
            self.set_system_volume(volume_level)
            return

        if "take screenshot" in command or "take screen shot" in command or command.strip() == "screenshot" or "screen shot" in command:
            self.take_screenshot()
            return
        if "time" in command:
            time_now = datetime.datetime.now().strftime("%I:%M %p")
            if self.current_language == 'marathi':
                self.talk(f"आता वेळ {time_now} आहे")
            elif self.current_language == 'hindi':
                self.talk(f"समय {time_now} है")
            else:
                self.talk(f"The time is {time_now}")

        elif "date" in command:
            date_now = datetime.datetime.now().strftime("%B %d, %Y")
            if self.current_language == 'marathi':
                self.talk(f"आज तारीख {date_now} आहे")
            elif self.current_language == 'hindi':
                self.talk(f"आज की तारीख {date_now} है")
            else:
                self.talk(f"Today is {date_now}")

        elif "my name is" in command:
            name = command.replace("my name is", "").strip()
            if name:
                self.user_name = name.title()
                self.talk(f"Nice to meet you, {self.user_name}! I'll remember that.")
                self.log_message(f"User name updated to: {self.user_name}")
            else:
                self.talk("Please tell me your name after saying 'my name is'")

        elif "what is my name" in command or "who am i" in command:
            if self.user_name:
                self.talk(f"You are {self.user_name}!")
            else:
                self.talk("I don't know your name yet. Please tell me by saying 'my name is' followed by your name.")

        elif "open" in command and "file" in command:
            parts = command.split("file")
            if len(parts) > 1:
                filename = parts[1].strip()
                self.open_file(filename)
            else:
                if self.current_language == 'marathi':
                    self.talk("कृपया कोणती फाइल उघडायची ते सांगा")
                elif self.current_language == 'hindi':
                    self.talk("कृपया कौन सी फाइल खोलनी है बताएं")
                else:
                    self.talk("Please specify which file to open")

        elif "search" in command and "file" in command:
            parts = command.split("file")
            if len(parts) > 1:
                filename = parts[1].strip()
                found_files = self.search_files(filename)
                if found_files:
                    if self.current_language == 'marathi':
                        self.talk(f"{filename} यासाठी {len(found_files)} फाइल सापडल्या")
                    elif self.current_language == 'hindi':
                        self.talk(f"{filename} से मिलती {len(found_files)} फाइलें मिलीं")
                    else:
                        self.talk(f"Found {len(found_files)} files matching {filename}")
                    for i, file in enumerate(found_files[:5], 1):
                        self.log_message(f"{i}. {file}")
                else:
                    if self.current_language == 'marathi':
                        self.talk(f"{filename} शी जुळणारी एकही फाइल सापडली नाही")
                    elif self.current_language == 'hindi':
                        self.talk(f"{filename} से मिलती कोई फाइल नहीं मिली")
                    else:
                        self.talk(f"No files found matching {filename}")
        elif "message" in command or "send message" in command:
            extracted_name = self._extract_contact_from_message_command(command)
            if extracted_name:
                resolved_contact, known_contact = self._resolve_whatsapp_contact(extracted_name)
                if not resolved_contact:
                    self.talk("Please say 'message' followed by the contact name.")
                    return

                if known_contact:
                    self.initiate_message_composition(known_contact, "custom")
                else:
                    self.talk(f"I don't have {resolved_contact} saved in contacts, but I'll search for them on WhatsApp.")
                    self.initiate_message_composition(resolved_contact, "custom")
            else:
                self.talk("Please say 'message' followed by the contact name.")

        elif "whatsapp" in command:
            contact_from_whatsapp = self._extract_contact_from_whatsapp_command(command)
            if contact_from_whatsapp:
                resolved_contact, known_contact = self._resolve_whatsapp_contact(contact_from_whatsapp)
                if not resolved_contact:
                    self.talk("Please say 'whatsapp' followed by the contact name.")
                    return

                if known_contact:
                    self.initiate_message_composition(known_contact, "custom")
                else:
                    self.talk(f"I don't have {resolved_contact} saved in contacts, but I'll search for them on WhatsApp.")
                    self.initiate_message_composition(resolved_contact, "custom")
            else:
                self.open_whatsapp()

        elif ("spotify" in command and "play" in command) or ("play" in command and "on spotify" in command):
            self.play_on_spotify(command)

        elif any(phrase in command for phrase in ["check for update", "check update", "check for updates", "is there an update"]):
            self.talk("Checking official servers for new updates, Sir.")
            threading.Thread(target=self.check_for_updates, daemon=True).start()

        elif any(phrase in command for phrase in ["update alpha", "download update", "open update", "install update", "update now", "yes update"]):
            if getattr(self, 'available_update', None):
                url = self.available_update.get("download_url", "https://alphadesktopassistant.web.app/dashboard.html")
                import webbrowser
                webbrowser.open(url)
                self.talk(f"Opening the official update portal for {self.available_update['display_name']} now, Sir.")
            else:
                self.talk("Checking for updates right now, Sir.")
                threading.Thread(target=self.check_for_updates, daemon=True).start()

        elif "open" in command:
            if "settings" in command:
                if self.current_language == 'marathi':
                    self.talk("Windows सेटिंग्स उघडत आहे.")
                elif self.current_language == 'hindi':
                    self.talk("Windows सेटिंग्स खोल रहा हूँ।")
                else:
                    self.talk("Opening Windows settings.")
                os.system("start ms-settings:")
            elif "ALPHA dot p y" in command or "ALPHA.py" in command:
                if self.current_language == 'marathi':
                    self.talk("ALPHA Python फाइल उघडत आहे.")
                elif self.current_language == 'hindi':
                    self.talk("ALPHA Python फाइल खोल रहा हूँ.")
                else:
                    self.talk("Opening ALPHA Python file.")
                subprocess.Popen(["notepad", "ALPHA.py"])
            else:
                software_name = command.split("open")[-1].strip()
                if software_name:
                    self.open_software(software_name)
                else:
                    if self.current_language == 'marathi':
                        self.talk("काय उघडायचे ते सांगा")
                    elif self.current_language == 'hindi':
                        self.talk("कृपया क्या खोलना है बताएं")
                    else:
                        self.talk("Please specify what to open")

        elif "close" in command or "stop" in command:
            if "close" in command:
                app_to_close = command.split("close")[-1].strip()
            else:
                app_to_close = command.split("stop")[-1].strip()
            
            if app_to_close:
                self.close_software(app_to_close)
            else:
                if self.current_language == 'marathi':
                    self.talk("काय बंद करायचे ते सांगा")
                elif self.current_language == 'hindi':
                    self.talk("कृपया क्या बंद करना है बताएं")
                else:
                    self.talk("Please specify what to close")

        elif "search" in command and "youtube" in command:
            search_term = command.split("search")[-1].split("on youtube")[0].strip()
            if self.current_language == 'marathi':
                self.talk(f"YouTube वर {search_term} शोधत आहे")
            elif self.current_language == 'hindi':
                self.talk(f"YouTube पर {search_term} खोज रहा हूँ")
            else:
                self.talk(f"Searching {search_term} on YouTube")
            webbrowser.open(f"https://www.youtube.com/results?search_query={search_term}")

        elif "search" in command and "google" in command:
            search_term = command.split("search")[-1].split("on google")[0].strip()
            if self.current_language == 'marathi':
                self.talk(f"Google वर {search_term} शोधत आहे")
            elif self.current_language == 'hindi':
                self.talk(f"Google पर {search_term} खोज रहा हूँ")
            else:
                self.talk(f"Searching {search_term} on Google")
            webbrowser.open(f"https://www.google.com/search?q={search_term}")

        elif "play" in command and "on youtube" in command:
            self.play_on_youtube(command)

        elif "play" in command and "on spotify" in command:
            self.play_on_spotify(command)

        elif ("remind me" in command) or ("set reminder" in command):
            self.start_reminder_flow()

        # Language switching removed per request

        elif "sleep" in command or "go to sleep" in command:
            if self.current_language == 'marathi':
                self.talk("झोप मोडमध्ये जात आहे. मला उठवण्यासाठी Alpha, Hey Alpha, किंवा OK Alpha म्हणा.")
            elif self.current_language == 'hindi':
                self.talk("स्लीप मोड में जा रहा हूँ। मुझे जगाने के लिए Alpha, Hey Alpha या OK Alpha कहें.")
            else:
                self.talk("Going to sleep mode. Say Alpha, Hey Alpha, or OK Alpha to wake me up.")
            self.wake_word_mode = True
            self.wake_mode_label.config(text="WAKE MODE: ON", fg='#ffaa00')

        elif "disable wake mode" in command or "always listen" in command:
            if self.current_language == 'marathi':
                self.talk("वेेक मोड बंद करत आहे. आता मी नेहमी आदेश ऐकेन.")
            elif self.current_language == 'hindi':
                self.talk("वेक मोड बंद कर रहा हूँ। अब मैं हमेशा कमांड सुनूँगा.")
            else:
                self.talk("Disabling wake mode. I'll always listen for commands now.")
            self.wake_word_mode = False
            self.wake_mode_label.config(text="WAKE MODE: OFF", fg='#00ff00')

        elif "wake" in command:
            if self.current_language == 'marathi':
                self.talk("मी आधीच जागा आहे!")
            elif self.current_language == 'hindi':
                self.talk("मैं पहले से ही जाग रहा हूँ!")
            else:
                self.talk("I'm already awake!")

        elif "list contacts" in command or "show contacts" in command:
            contacts = ", ".join(self.whatsapp_contacts.keys())
            if self.current_language == 'marathi':
                self.talk(f"माझे WhatsApp संपर्क: {contacts}")
            elif self.current_language == 'hindi':
                self.talk(f"मेरे WhatsApp संपर्क: {contacts}")
            else:
                self.talk(f"My WhatsApp contacts are: {contacts}")
            self.log_message(f"WhatsApp contacts: {contacts}")

        elif "enable ai" in command or "turn on ai" in command:
            if not self.ai_enabled:
                self.toggle_ai()
            else:
                if self.current_language == 'marathi':
                    self.talk("AI आधीच सुरू आहे!")
                elif self.current_language == 'hindi':
                    self.talk("AI पहले से ही चालू है!")
                else:
                    self.talk("AI is already enabled!")

        elif "disable ai" in command or "turn off ai" in command:
            if self.ai_enabled:
                self.toggle_ai()
            else:
                if self.current_language == 'marathi':
                    self.talk("AI आधीच बंद आहे!")
                elif self.current_language == 'hindi':
                    self.talk("AI पहले से ही बंद है!")
                else:
                    self.talk("AI is already disabled!")

        elif "clear conversation" in command or "clear history" in command:
            self.conversation_history = []
            if self.current_language == 'marathi':
                self.talk("संभाषण इतिहास साफ केला!")
            elif self.current_language == 'hindi':
                self.talk("कन्वर्सेशन हिस्ट्री क्लियर कर दी!")
            else:
                self.talk("Conversation history cleared!")
            self.log_message("AI conversation history cleared")
            # Clear persistent memory file
            try:
                if os.path.exists(self.memory_file):
                    os.remove(self.memory_file)
            except Exception:
                pass

        elif ("what did we talk about" in command) or ("last conversation" in command) or ("recall conversation" in command):
            # Summarize last few turns from memory
            summary = self._summarize_recent_memory(max_items=8)
            if summary:
                self.talk(f"Recently, we discussed: {summary}")
            else:
                self.talk("I don't have any recent conversation stored yet.")

        elif "introduce" in command:
            target_name = self._extract_introduction_target(command)
            if target_name:
                self.talk(self.build_self_introduction(target_name))
            else:
                self.talk("Please tell me whom I should introduce myself to. For example, say introduce yourself to HOD Sir.")

        elif "how are you" in command:
            responses = [
                f"I'm doing great, {self.user_name if self.user_name else 'friend'}! Thanks for asking. How are you?",
                "I'm fantastic and ready to help! How can I assist you today?",
                "I'm excellent! What can I do for you?",
                "I'm wonderful, thank you for asking! How are you feeling today?"
            ]
            if self.current_language == 'marathi':
                responses = [
                    f"मी छान आहे, {self.user_name if self.user_name else 'मित्रा'}! विचारल्याबद्दल धन्यवाद. तुम्ही कसे आहात?",
                    "मी जबरदस्त आहे आणि मदतीस तयार आहे! आज मी तुम्हाला कशी मदत करू?",
                    "मी उत्तम आहे! मी तुमच्यासाठी काय करू?",
                    "मी मस्त आहे! आज कसे वाटत आहे?"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    f"मैं बहुत अच्छा हूँ, {self.user_name if self.user_name else 'दोस्त'}! पूछने के लिए धन्यवाद. आप कैसे हैं?",
                    "मैं शानदार हूँ और मदद के लिए तैयार हूँ! आज मैं आपकी कैसे मदद कर सकता हूँ?",
                    "मैं एकदम बढ़िया हूँ! मैं आपके लिए क्या कर सकता हूँ?",
                    "मैं अच्छा हूँ! आज आप कैसा महसूस कर रहे हैं?"
                ]
            self.talk(random.choice(responses))

        elif "thank you" in command or "thanks" in command:
            responses = [
                f"You're welcome, {self.user_name if self.user_name else 'friend'}!",
                "Happy to help! That's what I'm here for!",
                "My pleasure! Anything else I can do for you?",
                "You're welcome! I'm always here when you need me!"
            ]
            if self.current_language == 'marathi':
                responses = [
                    f"स्वागत आहे, {self.user_name if self.user_name else 'मित्रा'}!",
                    "मदत करून आनंद झाला!",
                    "माझ्यासाठी आनंद आहे! अजून काही मदत हवी आहे का?",
                    "कधीही मदत हवी असेल तर मी इथे आहे!"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    f"आपका स्वागत है, {self.user_name if self.user_name else 'दोस्त'}!",
                    "मदद करके खुशी हुई!",
                    "मेरा सौभाग्य! क्या और कुछ कर सकता हूँ?",
                    "जब भी ज़रूरत हो, मैं यहाँ हूँ!"
                ]
            self.talk(random.choice(responses))

        elif "good morning" in command:
            responses = [
                f"Good morning, {self.user_name if self.user_name else 'friend'}! Hope you have a wonderful day ahead!",
                "Good morning! Ready to make today amazing?",
                "Morning! What can I help you with today?"
            ]
            if self.current_language == 'marathi':
                responses = [
                    f"शुभ सकाळ, {self.user_name if self.user_name else 'मित्रा'}! दिवस छान जावो!",
                    "शुभ सकाळ! आज काय करू शकतो?",
                    "गुड मॉर्निंग! आज मी कशी मदत करू?"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    f"सुप्रभात, {self.user_name if self.user_name else 'दोस्त'}! आपका दिन मंगलमय हो!",
                    "गुड मॉर्निंग! आज मैं आपकी कैसे मदद कर सकता हूँ?",
                    "सुप्रभात! आज क्या करना है?"
                ]
            self.talk(random.choice(responses))

        elif "good afternoon" in command:
            responses = [
                f"Good afternoon, {self.user_name if self.user_name else 'friend'}! How's your day going?",
                "Good afternoon! Hope you're having a productive day!",
                "Afternoon! What can I assist you with?"
            ]
            if self.current_language == 'marathi':
                responses = [
                    f"शुभ दुपार, {self.user_name if self.user_name else 'मित्रा'}! दिवस कसा चाललाय?",
                    "शुभ दुपार! मी कशी मदत करू?",
                    "दुपारच्या शुभेच्छा!"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    f"नमस्ते, {self.user_name if self.user_name else 'दोस्त'}! आपका दिन कैसा जा रहा है?",
                    "नमस्ते! क्या मैं आपकी कोई मदद कर सकता हूँ?",
                    "शुभ दोपहर!"
                ]
            self.talk(random.choice(responses))

        elif "good evening" in command or "good night" in command:
            responses = [
                f"Good evening, {self.user_name if self.user_name else 'friend'}! Hope you had a great day!",
                "Good evening! How can I help you wind down?",
                "Evening! What would you like to do?"
            ]
            if self.current_language == 'marathi':
                responses = [
                    f"शुभ संध्याकाळ, {self.user_name if self.user_name else 'मित्रा'}! दिवस छान गेला का?",
                    "शुभ रात्री! मी कशी मदत करू?",
                    "संध्याकाळी काय करू?"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    f"शुभ संध्या, {self.user_name if self.user_name else 'दोस्त'}! आपका दिन कैसा रहा?",
                    "शुभ रात्रि! मैं आपकी कैसे मदद करूँ?",
                    "शाम को क्या करना है?"
                ]
            self.talk(random.choice(responses))

        elif "i love you" in command or "love you" in command:
            responses = [
                f"Aww, that's so sweet, {self.user_name if self.user_name else 'friend'}! I care about you too!",
                "You're amazing! I'm here whenever you need me!",
                "That means a lot to me! I'm happy to be your assistant!"
            ]
            if self.current_language == 'marathi':
                responses = [
                    "वा, खूप छान! मीही तुमची काळजी घेतो!",
                    "तुम्ही खूप छान आहात! मी नेहमी इथे आहे!",
                    "मला खूप आनंद वाटतो!"
                ]
            elif self.current_language == 'hindi':
                responses = [
                    "वाह, बहुत प्यारा! मैं भी आपकी परवाह करता हूँ!",
                    "आप कमाल हैं! जब भी ज़रूरत हो, मैं यहाँ हूँ!",
                    "बहुत अच्छा लगा!"
                ]
            self.talk(random.choice(responses))

        elif "tell me a joke" in command or "joke" in command:
            jokes = [
                "Why don't scientists trust atoms? Because they might be up to something!",
                "I told my computer a joke about UDP, but it didn't get it.",
                "Why did the programmer quit their job? Because they didn't get arrays!",
                "How do you comfort a JavaScript bug? You console it!",
                "Why do Python programmers prefer snake_case? Because they can't C# clearly!"
            ]
            self.talk(random.choice(jokes))

        elif "what can you do" in command or "help me" in command or "what are your features" in command:
            help_text = f"Hi {self.user_name if self.user_name else 'friend'}! I can help you with many things: " + \
                        "I can open and close software, send custom WhatsApp messages, search and open files, " + \
                        "play music on YouTube or Spotify, search Google, tell you the time and date, " + \
                        "have conversations with AI, and much more! Just ask me naturally, like 'message John' " + \
                        "or 'open Chrome' or 'what's the weather like?'"
            if self.current_language == 'marathi':
                help_text = f"नमस्कार {self.user_name if self.user_name else 'मित्रा'}! मी अनेक गोष्टी करू शकतो: सॉफ्टवेअर उघडणे/बंद करणे, WhatsApp संदेश, फाइल शोधणे/उघडणे, YouTube/Spotify वर संगीत, Google शोध, वेळ/तारीख सांगणे, आणि बरेच काही!"
            elif self.current_language == 'hindi':
                help_text = f"नमस्ते {self.user_name if self.user_name else 'दोस्त'}! मैं बहुत सी चीज़ों में मदद कर सकता हूँ: सॉफ्टवेयर खोलना/बंद करना, WhatsApp संदेश, फाइल ढूँढना/खोलना, YouTube/Spotify पर संगीत, Google सर्च, समय/तारीख बताना, और भी बहुत कुछ!"
            self.talk(help_text)

        elif "weather" in command:
            if self.ai_enabled:
                self.process_ai_command(command)
            else:
                self.talk("For weather information, I need AI mode enabled. You can enable it by saying 'enable AI' or by clicking the toggle AI button.")

        elif "exit" in command or "bye" in command or "shutdown" in command:
            farewell_messages = [
                f"Goodbye, {self.user_name if self.user_name else 'friend'}! Have a wonderful day!",
                "See you later! Take care!",
                "Bye! It was great helping you today!",
                "Farewell! Looking forward to our next conversation!"
            ]
            if self.current_language == 'marathi':
                farewell_messages = [
                    f"नमस्कार, {self.user_name if self.user_name else 'मित्रा'}! दिवस छान जावो!",
                    "नंतर भेटू! काळजी घ्या!",
                    "बाय! मदत करून आनंद झाला!"
                ]
            elif self.current_language == 'hindi':
                farewell_messages = [
                    f"अलविदा, {self.user_name if self.user_name else 'दोस्त'}! आपका दिन शुभ हो!",
                    "फिर मिलेंगे! अपना ध्यान रखें!",
                    "बाय! आपकी मदद करके अच्छा लगा!"
                ]
            self.talk(random.choice(farewell_messages))
            self.stop_ALPHA()

        else:
            if self.ai_enabled:
                self.process_ai_command(command)
            else:
                # Localized fallback
                if self.current_language == 'marathi':
                    self.talk("माफ करा, मला समजले नाही. तुम्ही 'open chrome', 'message mom', 'search file resume', 'what time is it' असे आदेश देऊ शकता.")
                elif self.current_language == 'hindi':
                    self.talk("माफ कीजिए, मैं समझ नहीं पाया। आप 'open chrome', 'message mom', 'search file resume', 'what time is it' जैसे कमांड दे सकते हैं.")
                else:
                    helpful_suggestions = [
                        "I didn't understand that command. You can try:",
                        "• 'open [software name]' to launch applications",
                        "• 'message [contact name]' to send WhatsApp messages", 
                        "• 'search file [filename]' to find files",
                        "• 'what time is it' for current time",
                        "• 'tell me a joke' for entertainment",
                        "• 'what can you do' to see all features",
                        "• Enable AI mode for general conversations!"
                    ]
                    self.talk(" ".join(helpful_suggestions))
    
    # ===== Proactive Servant Mode =====
    def _toggle_servant_mode(self):
        """Toggle proactive servant check-in mode."""
        self.proactive_mode = not self.proactive_mode
        if self.proactive_mode:
            self.talk("Servant mode activated, boss! I'll check in on you periodically.")
        else:
            self.talk("Servant mode deactivated. I'll only respond when you call me.")
        self.log_message(f"Proactive servant mode: {'ON' if self.proactive_mode else 'OFF'}")

    def _generate_spy_comment(self):
        import random
        return random.choice(self.proactive_phrases)
        """Legacy Gemini screen-analysis path kept disabled in favor of local proactive phrases."""
        try:
            from PIL import ImageGrab
            
            # Flash UI indicator
            original_text = self.ai_status_label.cget("text")
            original_fg = self.ai_status_label.cget("fg")
            try:
                self.root.after(0, lambda: self.set_label(self.ai_status_label, text="👁️‍🗨️ ALPHA IS WATCHING...", fg="#ff00ff"))
            except: pass
            
            screenshot = ImageGrab.grab()
            
            prompt = (
                "You are ALPHA, a professional productivity assistant. "
                "I am attaching a screenshot of what the user is currently doing on the computer screen. "
                "Take a quick look and say something short, relevant, and helpful about the current task. "
                "If the user is coding, offer a practical suggestion or encouragement. "
                "If the user is reading or watching something, ask a brief relevant follow-up question. "
                "Keep it to naturally spoken 1-2 short sentences. Do not use asterisks or any markdown."
            )
            
            safe = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = self.gemini_model.generate_content([screenshot, prompt], safety_settings=safe)
            
            # Restore UI indicator
            try:
                self.root.after(0, lambda: self.set_label(self.ai_status_label, text=original_text, fg=original_fg))
            except: pass
            
            return response.text.replace('*', '').strip()
        except Exception as e:
            self.log_message(f"Spy Mode Visual Error: {str(e)}")
            try:
                self.root.after(0, lambda: self.set_label(self.ai_status_label, text=original_text, fg=original_fg))
            except: pass
            # Fallback to standard phrase if Gemini vision fails or quota resets
            import random
            return random.choice(self.proactive_phrases)

    def _proactive_worker(self):
        """Background thread: periodically spies on the user's screen and flirts with them."""
        while getattr(self, 'is_running', False):
            try:
                if (self.proactive_mode
                    and not self.is_speaking
                    and not self.mic_muted
                    and not self.waiting_for_message
                    and not self.waiting_for_reminder
                    and not self.waiting_for_reminder_time):
                    elapsed = time.time() - self.last_interaction_time
                    if elapsed >= self.proactive_interval:
                        self.log_message("[SPY MODE] Analyzing screen for flirty check-in...")
                        phrase = self._generate_spy_comment()
                        self.talk(phrase)
                        self.last_interaction_time = time.time()
                time.sleep(10)
            except Exception:
                time.sleep(10)

    # ===== Code Generation to File =====
    def _is_code_generation_request(self, command):
        """Check if the command is a code generation request (robust against misheard words)."""
        cmd = command.lower()

        # Strip wake word prefixes so "alpha write code" works
        for ww in ["alpha ", "hey alpha ", "ok alpha ", "okay alpha "]:
            if cmd.startswith(ww):
                cmd = cmd[len(ww):]

        action_words = ["write", "create", "generate", "make", "build", "code me", "right"]
        code_words = ["code", "file", "page", "script", "program", "website", "webpage",
                      "html", "python", "javascript", "css", "loop", "function", "class",
                      "app", "component", "template", "snippet", "module", "todo",
                      "calculator", "game", "form", "landing", "dashboard"]

        has_action = any(w in cmd for w in action_words)
        has_code = any(w in cmd for w in code_words)

        # Pattern 1: Explicit action + code context (e.g. "write a python loop")
        if has_action and has_code:
            return True

        # Pattern 2: "code" + any programming concept — catches misheard "write" as "right"
        # e.g. "alpha right for loop code" still has "code" + "loop"
        programming_concepts = [
            "loop", "for loop", "while loop", "function", "class", "variable",
            "array", "list", "dictionary", "html", "python", "javascript", "css",
            "java", "calculator", "game", "form", "todo", "api", "server",
            "database", "sort", "search", "login", "signup", "register",
            "dashboard", "landing", "portfolio", "navbar", "sidebar",
            "button", "modal", "dropdown", "slider", "web", "flask",
            "django", "react", "node", "express", "fibonacci", "factorial",
            "hello world", "input", "output", "print", "if else",
        ]
        if "code" in cmd and any(p in cmd for p in programming_concepts):
            return True

        return False

    def generate_code_to_file(self, command):
        """Generate code via Gemini AI (Heavy Tasks) and save it as a real file."""
        if not self.ai_enabled:
            self.talk("I need AI mode enabled to generate code, boss. Please turn it on first.")
            return

        self.talk("On it, boss! Sending this heavy code task to Gemini now.")
        self.log_message(f"Code generation request: {command}")

        # Specialized Gemini prompt for clean code output
        gemini_prompt = (
            f"Generate ONLY the code for the following request: {command}. "
            "Return the complete, working code inside a SINGLE fenced code block with the "
            "appropriate language tag (e.g. ```python or ```html). "
            "Do NOT include any explanation, commentary, or text outside the code block. "
            "The code must be complete, well-commented, and ready to run."
        )

        try:
            # User specifically mandated Gemini for heavy coding tasks
            ai_response = self.call_gemini_api(gemini_prompt)
            if not ai_response:
                self.talk("Sorry boss, couldn't generate the code right now. AI might be having issues.")
                return

            code_content, language_tag, filename = self._extract_code_and_filename(ai_response, command)

            if not code_content:
                self.talk("I got a response but couldn't extract clean code from it.")
                self.log_message(f"Raw AI response:\n{ai_response}")
                return

            # Create output directory
            os.makedirs(self.code_output_dir, exist_ok=True)

            # Determine final file path (avoid overwriting existing files)
            file_path = os.path.join(self.code_output_dir, filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(self.code_output_dir, f"{base}_{counter}{ext}")
                counter += 1

            # Write the code file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)

            final_name = os.path.basename(file_path)
            self.log_message(f"Code saved to: {file_path}")
            self.talk(f"BOSS! Your code is ready on Desktop! If you want, I'll open it for you. Just say Yeah Alpha open it.")

            # Wait for TTS to finish before listening
            time.sleep(1)
            wait_start = time.time()
            while getattr(self, 'is_speaking', False) and time.time() - wait_start < 30:
                time.sleep(0.05)
            time.sleep(1.0)

            # Listen for user confirmation to open the file
            self.log_message("Waiting for open confirmation... (10 seconds)")
            confirmation = self.listen(timeout=10)

            open_words = ['yeah', 'yes', 'open', 'go ahead', 'sure', 'ok', 'okay', 'yep', 'ya', 'do it']
            if confirmation and any(w in confirmation.lower() for w in open_words):
                self.log_message(f"User confirmed: '{confirmation}' — opening file")
                try:
                    opened = False
                    for vscode_path in self.software_paths.get("vscode", []):
                        if os.path.exists(vscode_path):
                            subprocess.Popen([vscode_path, file_path])
                            self.talk("Opening it in VS Code for you, boss!")
                            opened = True
                            break
                    if not opened:
                        os.startfile(file_path)
                        self.talk("Opened the file for you, boss!")
                except Exception as e:
                    self.log_message(f"Could not open file: {str(e)}")
                    self.talk("Sorry boss, I couldn't open the file.")
            else:
                self.talk("No worries, boss. The file is saved on your Desktop whenever you need it.")

        except Exception as e:
            self.log_message(f"Code generation error: {str(e)}")
            self.talk("Sorry boss, something went wrong while generating the code.")

    def _extract_code_and_filename(self, response, command):
        """Extract code block content from AI response and determine appropriate filename."""
        import re

        # Find fenced code blocks: ```language\ncode\n```
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            language_tag = matches[0][0].lower().strip()
            code_content = matches[0][1].strip()
        else:
            # No fenced block — use entire response as code
            code_content = response.strip()
            language_tag = ""

        # Map language tags to file extensions
        ext_map = {
            "python": ".py", "py": ".py",
            "html": ".html", "css": ".css",
            "javascript": ".js", "js": ".js",
            "typescript": ".ts", "ts": ".ts",
            "java": ".java", "c": ".c",
            "cpp": ".cpp", "c++": ".cpp",
            "csharp": ".cs", "cs": ".cs",
            "go": ".go", "rust": ".rs",
            "ruby": ".rb", "php": ".php",
            "sql": ".sql", "bash": ".sh",
            "shell": ".sh", "sh": ".sh",
            "json": ".json", "xml": ".xml",
            "yaml": ".yaml", "yml": ".yaml",
            "jsx": ".jsx", "tsx": ".tsx",
            "swift": ".swift", "kotlin": ".kt",
            "dart": ".dart", "r": ".r",
        }

        ext = ext_map.get(language_tag, "")

        # Infer extension from command if language tag didn't help
        if not ext:
            cmd = command.lower()
            if "python" in cmd or "py " in cmd:
                ext = ".py"
            elif "html" in cmd or "web" in cmd or "webpage" in cmd or "website" in cmd or "page" in cmd:
                ext = ".html"
            elif "css" in cmd or "stylesheet" in cmd:
                ext = ".css"
            elif "javascript" in cmd or " js " in cmd:
                ext = ".js"
            elif "java" in cmd:
                ext = ".java"
            elif "c++" in cmd or "cpp" in cmd:
                ext = ".cpp"
            else:
                ext = ".py"  # default to Python

        # Build a meaningful filename from the command
        name_base = command.lower()
        for prefix in ["write", "create", "generate", "make", "build", "code me",
                        "me ", "a ", "an ", "the ", "code for", "code", "basic",
                        "simple", "file", "script", "program", "please", "boss"]:
            name_base = name_base.replace(prefix, "")
        name_base = name_base.strip()

        # Sanitize for filesystem
        name_base = re.sub(r'[^\w\s-]', '', name_base)
        name_base = re.sub(r'\s+', '_', name_base).strip('_')

        if not name_base:
            name_base = "generated"
        if len(name_base) > 30:
            name_base = name_base[:30].rstrip('_')

        filename = f"{name_base}{ext}"
        return code_content, language_tag, filename

    def toggle_wake_mode(self):
        """Toggle wake word mode"""
        self.wake_word_mode = not self.wake_word_mode
        if self.wake_word_mode:
            self.wake_mode_label.config(text="WAKE MODE: ON", fg='#ffaa00')
            self.talk("Wake mode enabled. Say Alpha, Hey Alpha, or OK Alpha to activate.")
        else:
            self.wake_mode_label.config(text="WAKE MODE: OFF", fg='#00ff00')
            self.talk("Wake mode disabled. Always listening for commands.")
    
    def ALPHA_loop(self):
        """ALPHA listening loop"""
        # first-run greeting is handled when ALPHA is started (start_ALPHA)
        if self.first_run:
            self.first_run = False
            greeting = self.get_personalized_greeting()
            try:
                self.talk(greeting)
            except Exception:
                pass
            self.talk("I'm online and ready to help! You can ask me anything or give me commands.")
        else:
            greeting = f"ALPHA back online and ready to assist{', ' + self.user_name if self.user_name else ''}!"
            try:
                self.talk(greeting)
            except Exception:
                pass
        
        # Start idle animation loop
        self._set_anim_state('idle')
        
        while self.is_running:
            # Pause listening cycle while speaking
            if getattr(self, 'is_speaking', False):
                time.sleep(0.05)
                continue
            if self.is_listening:
                try:
                    if self.wake_word_mode and not self.waiting_for_message:
                        command = self.listen(timeout=5)
                        if command and self.check_wake_word(command):
                            responses = [
                                "Yes, I'm listening.",
                                "How can I help you?",
                                "What can I do for you?",
                                "I'm here, what do you need?",
                                f"Yes {self.user_name if self.user_name else 'friend'}?"
                            ]
                            self.talk(random.choice(responses))
                            actual_command = self.listen(timeout=10)
                            if actual_command and self.is_running:
                                self.process_command(actual_command)
                    else:
                        command = self.listen(timeout=5)
                        if command and self.is_running:
                            self.process_command(command)
                except Exception as e:
                    self.log_message(f"Error in ALPHA loop: {str(e)}")
                    time.sleep(1)
            else:
                time.sleep(0.1)
        # Stop animation on exit
        self._set_anim_state('off')
    
    def toggle_ALPHA(self):
        """Start or stop ALPHA"""
        if not self.is_running:
            self.start_ALPHA()
        else:
            self.stop_ALPHA()
    
    def toggle_mic(self):
        """Toggle microphone mute without affecting wake mode or running state"""
        self.mic_muted = not self.mic_muted
        if self.mic_muted:
            self.mic_status_label.config(text="MIC: OFF", fg='#ff4444')
            self.mic_toggle_button.config(text="🔊 UNMUTE MIC")
            self.log_message("Microphone muted")
            self.talk("Microphone muted")
        else:
            self.mic_status_label.config(text="MIC: ON", fg='#00ff00')
            self.mic_toggle_button.config(text="🔇 MUTE MIC")
            self.log_message("Microphone unmuted")
            self.talk("Microphone unmuted")

    def set_language(self, language: str):
        """Set assistant language for STT and attempt TTS voice selection"""
        language = language.lower().strip()
        if language in ['marathi', 'mr']:
            self.current_language = 'marathi'
            self.sr_language_code = 'mr-IN'
            self.target_lang_code = 'mr'
            self.set_engine_voice('marathi')
            if self.tts_backend == 'sapi':
                self._set_sapi_voice_by_language()
            self.talk("आता मी मराठीत मदत करीन.")
        elif language in ['hindi', 'hi']:
            self.current_language = 'hindi'
            self.sr_language_code = 'hi-IN'
            self.target_lang_code = 'hi'
            self.set_engine_voice('hindi')
            if self.tts_backend == 'sapi':
                self._set_sapi_voice_by_language()
            self.talk("मैं हिंदी में आपकी मदद करूँगा।")
        else:
            self.current_language = 'english'
            self.sr_language_code = 'en-US'
            self.target_lang_code = 'en'
            self.set_engine_voice('english')
            if self.tts_backend == 'sapi':
                self._set_sapi_voice_by_language()
            self.talk("I will assist you in English.")

    def detect_tts_voices(self):
        """Scan pyttsx3 voices and map male voices for quick switching."""
        try:
            voices = self.engine.getProperty('voices')
            for v in voices:
                name = (getattr(v, 'name', '') or '').lower()
                vid = (getattr(v, 'id', '') or '').lower()
                try:
                    gender = (getattr(v, 'gender', '') or '').lower()
                except Exception:
                    gender = ''
                is_male = ('male' in gender or 'male' in name or 'david' in name or 'guy' in name or 'manohar' in name or 'madhur' in name)
                # English baseline
                if self.voice_id_map['english'] is None and is_male and ('en' in vid or 'english' in name):
                    self.voice_id_map['english'] = v.id
                # Hindi
                if self.voice_id_map['hindi'] is None and is_male and ('hindi' in name or 'hi-' in vid or 'hin' in vid or 'hi_in' in vid):
                    self.voice_id_map['hindi'] = v.id
                # Marathi
                if self.voice_id_map['marathi'] is None and is_male and ('marathi' in name or 'mr-' in vid or 'mar' in vid or 'mr_in' in vid):
                    self.voice_id_map['marathi'] = v.id
        except Exception:
            pass

    def set_engine_voice(self, language: str):
        """Set pyttsx3 voice using male-only mappings when available."""
        try:
            target = language.lower()
            voice_id = self.voice_id_map.get(target)
            if voice_id:
                if getattr(self, 'current_voice_language', None) != target:
                    self.engine.setProperty('voice', voice_id)
                    self.current_voice_language = target
            else:
                # Try to find a matching male voice dynamically
                voices = self.engine.getProperty('voices')
                found = False
                for v in voices:
                    name = (getattr(v, 'name', '') or '').lower()
                    vid = (getattr(v, 'id', '') or '').lower()
                    try:
                        gender = (getattr(v, 'gender', '') or '').lower()
                    except Exception:
                        gender = ''
                    is_male = ('male' in gender or 'male' in name or 'david' in name or 'guy' in name or 'manohar' in name or 'madhur' in name)
                    if is_male and (target in name or target in vid):
                        self.engine.setProperty('voice', v.id)
                        self.current_voice_language = target
                        found = True
                        break
                if not found:
                    self.log_message(f"No male TTS voice found for '{language}'. Keeping current voice.")
        except Exception as e:
            self.log_message(f"Error setting TTS voice: {str(e)}")
    
    def start_ALPHA(self):
        """Start ALPHA voice recognition"""
        # On the very first start, prefer a GUI prompt for name (more reliable than STT at startup)
        if self.first_run and not self.user_name:
            try:
                name = simpledialog.askstring("Welcome to ALPHA", "What should I call you?", parent=self.root)
                if name and isinstance(name, str) and name.strip():
                    self.user_name = name.strip().title()
                    self.log_message(f"User name set to: {self.user_name}")
                    # Friendly acknowledgement
                    try:
                        self.talk(f"Nice to meet you, {self.user_name}! I'm excited to be your assistant.")
                    except Exception:
                        pass
                else:
                    self.user_name = "Friend"
                    try:
                        self.talk("Okay. I'll call you Friend. You can tell me your name anytime by saying 'my name is ...'.")
                    except Exception:
                        pass
            except Exception as e:
                self.log_message(f"GUI name prompt error: {e}")
                self.user_name = "Friend"
            finally:
                # ensure first_run is cleared so we don't re-prompt
                self.first_run = False

        self.is_running = True
        self.is_listening = True
        
        # One-time ambient noise calibration at startup
        self.log_message("Calibrating microphone for background noise... (2 seconds)")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.log_message(f"Mic calibrated. Energy threshold set to: {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            self.log_message(f"Mic calibration skipped: {str(e)}")
        
        self.set_label(self.status_label, text="● ONLINE", fg='#00ff00')
        try:
            self.start_button.config(text="🟥 STOP ALPHA", bg='#444444', fg='#ff0000')
            self.manual_listen_button.config(state=tk.NORMAL)
        except Exception:
            pass
        
        self.log_message("ALPHA started successfully!")
        
        # Start proactive servant check-in thread
        self.last_interaction_time = time.time()
        threading.Thread(target=self._proactive_worker, daemon=True).start()
        
        self.ALPHA_thread = threading.Thread(target=self.ALPHA_loop, daemon=True)
        self.ALPHA_thread.start()
    
    def stop_ALPHA(self):
        """Stop ALPHA voice recognition"""
        self.is_running = False
        self.is_listening = False
        self.waiting_for_message = False
        self.waiting_for_reminder = False
        self.waiting_for_reminder_time = False
        self.reminder_task = ""
        self.current_contact = ""
        self.message_type = ""
        self.set_label(self.status_label, text="● OFFLINE", fg='#ff4444')
        try:
            self.start_button.config(text="🔴 START ALPHA", bg='#004400', fg='#00ff00')
            self.manual_listen_button.config(state=tk.DISABLED)
        except Exception:
            pass
        self.listening_label.config(text="")
        self.message_status_label.config(text="")
        self.reminder_status_label.config(text="")
        self.mic_status_label.config(text="MIC: ON", fg='#00ff00')
        self.mic_muted = False
        # Cancel any pending reminder timers
        for t in list(self.reminder_timers):
            try:
                if hasattr(t, "cancel"):
                    t.cancel()
            except Exception:
                pass
        self.reminder_timers = []
        # stop animation
        self._set_anim_state('off')
        
        self.log_message("ALPHA stopped.")
    
    def manual_listen(self):
        """Manual single listen command"""
        if self.is_running:
            self.is_listening = False
            # Avoid listening mid-speech
            if getattr(self, 'is_speaking', False):
                command = ""
            else:
                command = self.listen()
            if command:
                self.process_command(command)
            self.is_listening = True
    
    def execute_manual_command(self, event=None):
        """Execute command from text input"""
        command = self.command_entry.get().strip()
        if command:
            self.command_entry.delete(0, tk.END)
            self.log_message(f"MANUAL COMMAND: {command}")
            self.process_command(command.lower())
            
    def clear_log(self):
        """Clear console log"""
        self.console.delete(1.0, tk.END)
        self.log_message("Console cleared.")
        
    def run(self):
        """Run the GUI application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
            
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            self.stop_ALPHA()
            
        # Terminate webview process if it's still running
        if hasattr(self, 'webview_proc') and self.webview_proc:
            try:
                self.webview_proc.terminate()
            except Exception:
                pass
                
        self.root.quit()
        self.root.destroy()

    def skip_current_output(self):
        """Immediately stop current text-to-speech and reset UI state. Force restarts if stuck."""
        def _do_skip():
            try:
                self._speech_generation = getattr(self, '_speech_generation', 0) + 1
                self._tts_skip_requested = True
                if getattr(self, 'tts_backend', 'pyttsx3') == 'sapi' and getattr(self, 'sapi_voice', None) is not None:
                    try:
                        # Purge queued and ongoing speech immediately
                        self.sapi_voice.Speak("", 3)  # SVSFPurgeBeforeSpeak
                    except Exception:
                        pass
                else:
                    # Attempt graceful stop but isolate it in a throwaway thread. 
                    # If Windows COM deadlocks here, we leave it hanging harmlessly in the background instead of freezing the UI.
                    threading.Thread(target=self._stop_tts_unsafe, daemon=True).start()
                    
                    # We forcefully re-init the TTS engine in the background to un-glitch it.
                    self.log_message("Force resetting TTS engine to avoid glitch...")
                    self._reinitialize_tts()

                # Clear queued utterances
                try:
                    while not self.tts_queue.empty():
                        self.tts_queue.get_nowait()
                        self.tts_queue.task_done()
                except Exception:
                    pass

                try:
                    import ctypes
                    ctypes.windll.winmm.mciSendStringW(f'close mp3_{id(self)}', None, 0, None)
                except Exception:
                    pass
                     
                # Clear speaking flag inside thread
                self.is_speaking = False
                try:
                    self.root.after(0, lambda: self._set_anim_state('idle'))
                    self.root.after(0, lambda: self.listening_label.config(text=""))
                except Exception:
                    pass
                self.log_message("Speech output skipped by user")
            except Exception as e:
                self.log_message(f"Skip error: {str(e)}")

        # Run the entire skip routine in a background thread so the GUI NEVER freezes.
        threading.Thread(target=_do_skip, daemon=True).start()

    def _init_sapi(self):
        """Initialize Windows SAPI voice and set baseline rate/volume."""
        self.sapi_voice = win32.Dispatch("SAPI.SpVoice")
        try:
            # Map rate roughly from pyttsx3 range
            self.sapi_voice.Rate = 0
        except Exception:
            pass
        try:
            vol = int(getattr(self, 'tts_volume', 1.0) * 100)
            self.sapi_voice.Volume = max(0, min(100, vol))
        except Exception:
            pass

    def _set_sapi_voice_by_language(self):
        """Pick a SAPI voice based on current language preference."""
        try:
            if not self.sapi_voice:
                return
            lang = getattr(self, 'target_lang_code', 'en')
            tokens = self.sapi_voice.GetVoices()
            preferred = None
            # First pass: language + male
            for i in range(tokens.Count):
                token = tokens.Item(i)
                desc = (token.GetDescription() or '').lower()
                gender = ''
                try:
                    gender = (token.GetAttribute('Gender') or '').lower()
                except Exception:
                    pass
                if lang == 'hi' and 'hindi' in desc and 'male' in gender:
                    preferred = token
                    break
                if lang == 'mr' and 'marathi' in desc and 'male' in gender:
                    preferred = token
                    break
                if lang == 'en' and 'english' in desc and ('male' in gender or 'david' in desc):
                    preferred = token
                    break
            # Second pass: keep searching for other male matches only
            if preferred is None:
                for i in range(tokens.Count):
                    token = tokens.Item(i)
                    desc = (token.GetDescription() or '').lower()
                    gender = ''
                    try:
                        gender = (token.GetAttribute('Gender') or '').lower()
                    except Exception:
                        pass
                    if ((lang == 'hi' and 'hindi' in desc) or (lang == 'mr' and 'marathi' in desc) or (lang == 'en' and 'english' in desc)) and ('male' in gender or 'david' in desc):
                        preferred = token
                        break
            if preferred is not None:
                self.sapi_voice.Voice = preferred
        except Exception:
            pass

    def _sapi_speak(self, text: str, speech_generation=None):
        """Speak the given text using Human Neural Edge TTS first, then fallback to SAPI."""
        self.is_speaking = True
        try:
            if speech_generation is None:
                speech_generation = getattr(self, '_speech_generation', 0)
            if speech_generation != getattr(self, '_speech_generation', 0):
                return
            self._tts_skip_requested = False
            try:
                self.root.after(0, lambda: self._set_anim_state('speaking'))
            except Exception:
                pass
                
            try:
                # Attempt Neural TTS via edge-tts
                import asyncio
                import edge_tts
                import ctypes
                import os
                import time
                import re
                
                # Default to a professional male voice
                voice = 'en-US-GuyNeural'
                lang = getattr(self, 'target_lang_code', 'en')
                
                # Check for Devanagari script (Hindi/Marathi) natively outputted by Ollama
                has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
                
                if lang == 'mr' and has_devanagari:
                    voice = 'mr-IN-ManoharNeural'
                elif has_devanagari or lang == 'hi':
                    voice = 'hi-IN-MadhurNeural'
                    
                mp3_path = os.path.abspath(f"temp_tts_{id(self)}.mp3")
                
                # We need a new event loop for this thread if it doesn't have one
                async def _generate():
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(mp3_path)
                    
                asyncio.run(_generate())
                
                alias = f"mp3_{id(self)}"
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'open "{mp3_path}" type mpegvideo alias {alias}', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'play {alias}', None, 0, None)
                
                status_buffer = ctypes.create_unicode_buffer(256)
                while True:
                    if getattr(self, '_tts_skip_requested', False):
                        ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                        break
                    if speech_generation != getattr(self, '_speech_generation', 0):
                        ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                        break
                        
                    ctypes.windll.winmm.mciSendStringW(f'status {alias} mode', status_buffer, 256, None)
                    if status_buffer.value.lower() != "playing":
                        break
                    time.sleep(0.05)
                
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                
                try: 
                    os.remove(mp3_path) 
                except: 
                    pass
                return  # Return early because neural TTS succeeded perfectly!
                
            except Exception as neural_err:
                self.log_message(f"Neural TTS skipped/failed. Falling back to Robot SAPI.")
        
            if not self.sapi_voice:
                return
            # Choose voice and purge any ongoing speech
            self._set_sapi_voice_by_language()
            try:
                self.sapi_voice.Speak("", 3)  # SVSFPurgeBeforeSpeak
            except Exception:
                pass
            # Asynchronous speak to prevent COM threading deadlocks, allowing instantaneous skipping
            self.sapi_voice.Speak(text, 1) # SVSFlagsAsync
            
            # Poll status until speech finishes or skip button purges it
            import time
            while self.sapi_voice.Status.RunningState == 2:
                if getattr(self, '_tts_skip_requested', False) or speech_generation != getattr(self, '_speech_generation', 0):
                    try:
                        self.sapi_voice.Speak("", 3)
                    except Exception:
                        pass
                    break
                time.sleep(0.05)
                

        except Exception as e:
            self.log_message(f"SAPI speak thread error: {str(e)}")
        finally:
            self.is_speaking = False
            try:
                self.root.after(0, lambda: self._set_anim_state('idle'))
            except Exception:
                pass

    def _speak_blocking(self, text: str):
        """Speak text safely by serializing pyttsx3 access and cleaning any prior loop state."""
        with self._tts_lock:
            if self._tts_skip_requested:
                return
            try:
                self._stop_tts_unsafe()
                if self._tts_skip_requested:
                    return
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as err:
                # Reinitialize and restore settings, then retry once
                self.log_message(f"TTS run error: {str(err)}")
                self._reinitialize_tts()
                if not self._tts_skip_requested:
                    self.engine.say(text)
                    self.engine.runAndWait()

    def _stop_tts_safely(self):
        """Stop/end pyttsx3 loop under lock to avoid concurrent run-loop errors."""
        with self._tts_lock:
            self._stop_tts_unsafe()

    def _stop_tts_unsafe(self):
        """Best-effort stop/end without acquiring the lock (caller must hold lock)."""
        try:
            self.engine.stop()
        except Exception:
            pass
        try:
            if getattr(self.engine, '_inLoop', False):
                self.engine.endLoop()
        except Exception:
            pass

    def _tts_worker(self):
        """Background worker that consumes the TTS queue and speaks sequentially."""
        while True:
            try:
                item = self.tts_queue.get()
            except Exception:
                continue
            try:
                if isinstance(item, tuple) and len(item) == 2:
                    speech_generation, text = item
                else:
                    speech_generation, text = getattr(self, '_speech_generation', 0), item
                if text:
                    if speech_generation != getattr(self, '_speech_generation', 0):
                        continue
                    self.is_speaking = True
                    self._tts_skip_requested = False
                    try:
                        self.root.after(0, lambda: self._set_anim_state('speaking'))
                    except Exception:
                        pass
                    self._speak_blocking(text)
            finally:
                try:
                    self.root.after(0, lambda: self._set_anim_state('idle'))
                except Exception:
                    pass
                try:
                    self.tts_queue.task_done()
                except Exception:
                    pass
                self.is_speaking = False

    def _reinitialize_tts(self):
        """Recreate pyttsx3 engine and restore voice/rate/volume settings."""
        try:
            self.engine = pyttsx3.init()
        except Exception:
            # Try once more after a short delay
            try:
                time.sleep(0.05)
                self.engine = pyttsx3.init()
            except Exception:
                return
        # Restore properties
        try:
            self.engine.setProperty('rate', getattr(self, 'tts_rate', 200))
        except Exception:
            pass
        try:
            self.engine.setProperty('volume', getattr(self, 'tts_volume', 1.0))
        except Exception:
            pass
        try:
            self.voice_id_map = {'english': None, 'hindi': None, 'marathi': None}
            self.current_voice_language = None
            self.detect_tts_voices()
            if hasattr(self, 'target_lang_code'):
                if self.target_lang_code == 'mr':
                    self.set_engine_voice('marathi')
                elif self.target_lang_code == 'hi':
                    self.set_engine_voice('hindi')
                else:
                    self.set_engine_voice('english')
            else:
                self.set_engine_voice('english')
        except Exception:
            pass

    # ===== Conversation Memory Helpers =====
    def _append_memory(self, entry: dict):
        """Append a single memory entry as JSONL. Entry must contain ts, role, text."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        except Exception:
            pass
        try:
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _read_recent_memory(self, max_items: int = 20):
        items = []
        try:
            if not os.path.exists(self.memory_file):
                return []
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-max_items:]:
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return []
        return items

    def _summarize_recent_memory(self, max_items: int = 10) -> str:
        entries = self._read_recent_memory(max_items)
        if not entries:
            return ""
        # Build a compact summary: time-ordered role:text
        parts = []
        for e in entries[-max_items:]:
            role = e.get('role', '')
            text = e.get('text', '')
            if not text:
                continue
            prefix = 'You' if role == 'user' else ('Alpha' if role == 'alpha' else 'System')
            parts.append(f"{prefix}: {text}")
        return "; ".join(parts[-8:])
        try:
            self.engine.setProperty('volume', getattr(self, 'tts_volume', 1.0))
        except Exception:
            pass
        # Restore preferred voice
        try:
            if hasattr(self, 'target_lang_code'):
                if self.target_lang_code == 'mr':
                    self.set_engine_voice('marathi')
                elif self.target_lang_code == 'hi':
                    self.set_engine_voice('hindi')
                else:
                    self.set_engine_voice('english')
        except Exception:
            pass

    def broadcast_ws(self, msg_dict):
        if hasattr(self, 'ws_loop') and self.ws_loop and self.websocket_clients:
            async def send_all():
                payload = json.dumps(msg_dict)
                tasks = [client.send(payload) for client in list(self.websocket_clients)]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            asyncio.run_coroutine_threadsafe(send_all(), self.ws_loop)

    async def start_websocket_server(self):
        import websockets
        async def handler(websocket):
            self.websocket_clients.add(websocket)
            try:
                await websocket.send(json.dumps({"type": "state", "state": self.anim_state}))
                await websocket.send(json.dumps({"type": "log", "text": f"Connected to A.L.P.H.A. System Dashboard. User: {self.user_name or 'Unknown'}"}))
                if getattr(self, 'available_update', None):
                    await websocket.send(json.dumps({
                        "type": "update_available",
                        **self.available_update
                    }))
            except Exception:
                pass
            
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        if msg_type == "action":
                            action = data.get("action")
                            if action == "toggle_ALPHA":
                                self.root.after(0, self.toggle_ALPHA)
                            elif action == "toggle_ai":
                                self.root.after(0, self.toggle_ai)
                            elif action == "toggle_mic":
                                self.root.after(0, self.toggle_mic)
                            elif action == "manual_listen":
                                self.root.after(0, self.manual_listen)
                            elif action == "skip_current_output":
                                self.root.after(0, self.skip_current_output)
                            elif action == "clear_log":
                                self.root.after(0, self.clear_log)
                            elif action == "set_username":
                                val = data.get("value", "")
                                if val:
                                    self.user_name = val.title()
                                    self.log_message(f"User name synchronized to: {self.user_name}")
                            elif action == "open_settings":
                                def open_win_settings():
                                    import os
                                    os.system("start ms-settings:")
                                    self.log_message("Opened Windows Settings")
                                self.root.after(0, open_win_settings)
                            elif action == "set_model":
                                val = data.get("value", "")
                                if val:
                                    def update_ai_model():
                                        try:
                                            if "ollama" in val.lower():
                                                self.active_ai_backend = 'ollama'
                                                self.log_message("AI Model switched to: Ollama (Local AI Brain)")
                                                self.talk("Switched to Local Ollama AI brain")
                                            else:
                                                import google.generativeai as genai
                                                clean_model = val.replace("models/", "").strip()
                                                self.gemini_model = genai.GenerativeModel(
                                                    model_name=clean_model,
                                                    system_instruction=self.alpha_system_prompt
                                                )
                                                self.gemini_chat = self.gemini_model.start_chat()
                                                self.active_ai_backend = 'gemini'
                                                if clean_model in self.gemini_models_pool:
                                                    self.gemini_models_pool.remove(clean_model)
                                                self.gemini_models_pool.insert(0, clean_model)
                                                self.current_model_idx = 0
                                                self.log_message(f"AI Model switched to: {clean_model}")
                                                self.talk(f"Model updated to {clean_model}")
                                        except Exception as me:
                                            self.log_message(f"Model switch error: {me}")
                                    self.root.after(0, update_ai_model)
                            elif action == "open_update_url":
                                url = data.get("value") or (self.available_update.get("download_url") if self.available_update else "https://alphadesktopassistant.web.app/dashboard.html")
                                def open_up_portal():
                                    import webbrowser
                                    webbrowser.open(url)
                                    self.log_message(f"Opening official download portal: {url}")
                                    self.talk("Opening the official update portal now, Sir.")
                                self.root.after(0, open_up_portal)
                            elif action == "check_updates":
                                threading.Thread(target=self.check_for_updates, daemon=True).start()
                        elif msg_type == "command":
                            cmd_text = data.get("text", "")
                            def run_cmd():
                                self.command_entry.delete(0, tk.END)
                                self.command_entry.insert(0, cmd_text)
                                self.execute_manual_command(None)
                            self.root.after(0, run_cmd)
                    except Exception as e:
                        try:
                            self.log_message(f"WS message error: {e}")
                        except Exception:
                            pass
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                try:
                    self.websocket_clients.remove(websocket)
                except Exception:
                    pass

        await websockets.serve(handler, "localhost", 8765)

    async def periodic_waveform(self):
        import random
        while True:
            try:
                if getattr(self, 'anim_state', 'idle') in ('listening', 'speaking'):
                    level = random.uniform(0.1, 0.75) if self.anim_state == 'listening' else random.uniform(0.2, 0.9)
                    self.broadcast_ws({
                        "type": "waveform",
                        "active": True,
                        "level": level
                    })
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(1)

def start_http_server():
    import http.server
    import socketserver
    import os
    import sys
    
    # Locate dist folder
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    dist_dir = os.path.join(base_dir, 'alpha-ui', 'dist')
    
    if not os.path.exists(dist_dir):
        # Fallback to direct parent checks
        dist_dir = os.path.join(base_dir, 'ALPHA2.0', 'alpha-ui', 'dist')
        
    if not os.path.exists(dist_dir):
        print(f"Error: React build directory not found at {dist_dir}")
        return
        
    class SilentHTTPHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=dist_dir, **kwargs)
        def log_message(self, format, *args):
            pass
            
    PORT = 8000
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), SilentHTTPHandler) as httpd:
            print(f"Serving React UI at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTP Server error: {e}")

def launch_webview_process():
    import subprocess
    import sys
    import os
    import time
    
    time.sleep(1.5) # Wait for the HTTP server to spin up
    
    if getattr(sys, 'frozen', False):
        args = [sys.executable, "--webview"]
    else:
        script_path = os.path.abspath(__file__)
        args = [sys.executable, script_path, "--webview"]
        
    print(f"Spawning webview process: {args}")
    return subprocess.Popen(args)

if __name__ == "__main__":
    import sys
    import traceback
    
    if "--webview" in sys.argv:
        try:
            import webview
            webview.create_window(
                'ALPHA Assistant', 
                'http://localhost:8000', 
                width=1050, 
                height=720,
                resizable=True
            )
            webview.start()
        except Exception as e:
            try:
                with open("ALPHA_webview_crash.txt", "w") as f:
                    f.write(traceback.format_exc())
            except Exception:
                pass
        sys.exit(0)
        
    try:
        import threading
        # 1. Start the HTTP server thread to host the React UI
        threading.Thread(target=start_http_server, daemon=True).start()
        
        # 2. Spawn the Webview window process
        proc = launch_webview_process()
        
        # 3. Start the Tkinter app as normal
        app = ALPHAGUI()
        app.webview_proc = proc
        
        # Start a thread to monitor the webview process and close the Tkinter app when it exits
        def monitor_webview():
            if proc:
                proc.wait()
            try:
                app.root.after(0, app.on_closing)
            except Exception:
                import os
                os._exit(0)
                
        threading.Thread(target=monitor_webview, daemon=True).start()
        
        app.run()
    except Exception as e:
        try:
            with open("ALPHA_app_crash.txt", "w") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass

