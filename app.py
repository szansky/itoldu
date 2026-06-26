from __future__ import annotations

import ctypes
import io
import json
import os
import queue
import socket
import tempfile
import threading
import time
import wave
from dataclasses import asdict, dataclass
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

import keyboard
import numpy as np
import pyautogui
import pyperclip
import requests
import sounddevice as sd
import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox, ttk
from ctypes import wintypes


APP_NAME = "I Told U"
SAMPLE_RATE = 16_000
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2

LANGUAGE_OPTIONS = {
    "Auto PL/EN": "auto_pl_en",
    "Polski": "pl-PL",
    "English": "en-US",
    "Deutsch": "de-DE",
    "Espanol": "es-ES",
    "Francais": "fr-FR",
    "Italiano": "it-IT",
    "Ukrainski": "uk-UA",
}

TARGET_LANGUAGE_OPTIONS = [
    "polski",
    "angielski",
    "niemiecki",
    "hiszpanski",
    "francuski",
    "wloski",
    "ukrainski",
]

UI_LANGUAGE_OPTIONS = {
    "en": "English",
    "pl": "Polski",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "uk": "Українська",
    "pt": "Português",
    "nl": "Nederlands",
    "cs": "Čeština",
}

I18N: dict[str, dict[str, str]] = {
    "en": {
        "app_on": "Enabled",
        "api_key": "DeepSeek API",
        "api_saved": "API saved",
        "api_source": "API source",
        "api_source_env": ".env",
        "api_source_local": "local, encrypted",
        "api_source_missing": "missing",
        "api_source_plain": "local",
        "api_toast_env": "Using the key from .env when available",
        "api_toast_title": "API source updated",
        "app_language": "App language",
        "auto_paste": "Paste into active window",
        "base_url": "DeepSeek base URL",
        "capture_key": "Capture key",
        "choose_key": "Press the exact key to use as the hotkey.",
        "controls": "Controls",
        "destination": "Output",
        "done": "Done. Text handled.",
        "env_key": "Use .env",
        "hotkey": "Push-to-talk hotkey",
        "hotkey_active": "Hotkey active",
        "hotkey_cancel": "Hotkey capture cancelled.",
        "hotkey_error": "Hotkey error",
        "hotkey_physical": "Physical",
        "hotkey_ready": "Hotkey set",
        "internet_check": "Checking connection...",
        "language_api": "Language and API",
        "last_result": "Last result will appear here.",
        "listening": "Listening",
        "mic": "Microphone",
        "mic_refresh": "Refresh",
        "model": "Model",
        "network_missing": "Internet: offline",
        "network_ok": "Internet: OK",
        "overlay": "Status overlay",
        "preview": "Preview",
        "processing": "Processing...",
        "recording": "Recording...",
        "save_hotkey": "Save hotkey",
        "save_key": "Save key",
        "save_settings": "Save settings",
        "saved": "Settings saved.",
        "source_language": "Speech language",
        "speech_driver": "Speech driver",
        "start_log": "Start. Hold {hotkey}, speak, release.",
        "status_ready": "Ready. Hold the hotkey and speak.",
        "too_short": "Too short. Hold the hotkey a little longer.",
        "translate": "DeepSeek translation",
        "translating": "Translating...",
        "use_env": "Use .env",
        "write_paste": "Pasting...",
    },
    "pl": {
        "app_on": "Appka wlaczona",
        "api_key": "DeepSeek API",
        "api_saved": "API zapisane",
        "api_source": "Zrodlo API",
        "api_source_env": ".env",
        "api_source_local": "lokalny, zaszyfrowany",
        "api_source_missing": "brak",
        "api_source_plain": "lokalny",
        "api_toast_env": "Appka uzywa klucza z .env, jesli istnieje",
        "api_toast_title": "API ustawione",
        "app_language": "Jezyk aplikacji",
        "auto_paste": "Wklej do aktywnego okna",
        "base_url": "DeepSeek base URL",
        "capture_key": "Zlap klawisz",
        "choose_key": "Nacisnij dokladnie ten klawisz, ktory ma byc hotkeyem.",
        "controls": "Sterowanie",
        "destination": "Docelowo",
        "done": "Gotowe. Tekst obrobiony.",
        "env_key": "Uzyj .env",
        "hotkey": "Hotkey push-to-talk",
        "hotkey_active": "Hotkey aktywny",
        "hotkey_cancel": "Przypisywanie hotkey anulowane.",
        "hotkey_error": "Hotkey nie dziala",
        "hotkey_physical": "Fizyczny",
        "hotkey_ready": "Hotkey ustawiony",
        "internet_check": "Sprawdzam internet...",
        "language_api": "Jezyki i API",
        "last_result": "Ostatni wynik pojawi sie tutaj.",
        "listening": "Nasluch",
        "mic": "Mikrofon",
        "mic_refresh": "Odswiez",
        "model": "Model",
        "network_missing": "Internet: brak",
        "network_ok": "Internet: OK",
        "overlay": "Status overlay",
        "preview": "Podglad",
        "processing": "Przetwarzanie...",
        "recording": "Nagrywanie...",
        "save_hotkey": "Zapisz hotkey",
        "save_key": "Zapisz klucz",
        "save_settings": "Zapisz ustawienia",
        "saved": "Ustawienia zapisane.",
        "source_language": "Jezyk mowy",
        "speech_driver": "Sterownik mowy",
        "start_log": "Start. Przytrzymaj {hotkey}, mow, pusc.",
        "status_ready": "Gotowe. Przytrzymaj hotkey i mow.",
        "too_short": "Za krotko. Przytrzymaj hotkey troche dluzej.",
        "translate": "Tlumaczenie DeepSeek",
        "translating": "Tlumaczenie...",
        "use_env": "Uzyj z .env",
        "write_paste": "Wklejanie...",
    },
}

for _lang in ("de", "es", "fr", "it", "uk", "pt", "nl", "cs"):
    I18N[_lang] = I18N["en"] | {"app_language": UI_LANGUAGE_OPTIONS[_lang]}

I18N["de"] |= {
    "app_on": "Aktiviert", "auto_paste": "In aktives Fenster einfügen", "capture_key": "Taste erfassen",
    "controls": "Steuerung", "destination": "Ziel", "hotkey": "Push-to-talk Hotkey",
    "language_api": "Sprache und API", "mic": "Mikrofon", "mic_refresh": "Aktualisieren",
    "preview": "Vorschau", "save_hotkey": "Hotkey speichern", "save_key": "Schlüssel speichern",
    "save_settings": "Einstellungen speichern", "source_language": "Spracheingabe",
    "speech_driver": "Spracherkennung", "status_ready": "Bereit. Hotkey halten und sprechen.",
    "translate": "DeepSeek Übersetzung", "recording": "Aufnahme...", "processing": "Verarbeitung...",
    "translating": "Übersetzen...", "write_paste": "Einfügen...", "saved": "Einstellungen gespeichert.",
}
I18N["es"] |= {
    "app_on": "Activado", "auto_paste": "Pegar en ventana activa", "capture_key": "Capturar tecla",
    "controls": "Controles", "destination": "Destino", "hotkey": "Hotkey push-to-talk",
    "language_api": "Idioma y API", "mic": "Micrófono", "mic_refresh": "Actualizar",
    "preview": "Vista previa", "save_hotkey": "Guardar hotkey", "save_key": "Guardar clave",
    "save_settings": "Guardar ajustes", "source_language": "Idioma hablado",
    "speech_driver": "Reconocimiento", "status_ready": "Listo. Mantén el hotkey y habla.",
    "translate": "Traducción DeepSeek", "recording": "Grabando...", "processing": "Procesando...",
    "translating": "Traduciendo...", "write_paste": "Pegando...", "saved": "Ajustes guardados.",
}
I18N["fr"] |= {
    "app_on": "Activée", "auto_paste": "Coller dans la fenêtre active", "capture_key": "Capturer touche",
    "controls": "Contrôles", "destination": "Destination", "hotkey": "Raccourci push-to-talk",
    "language_api": "Langue et API", "mic": "Microphone", "mic_refresh": "Actualiser",
    "preview": "Aperçu", "save_hotkey": "Enregistrer raccourci", "save_key": "Enregistrer clé",
    "save_settings": "Enregistrer", "source_language": "Langue parlée",
    "speech_driver": "Reconnaissance", "status_ready": "Prêt. Maintenez le raccourci et parlez.",
    "translate": "Traduction DeepSeek", "recording": "Enregistrement...", "processing": "Traitement...",
    "translating": "Traduction...", "write_paste": "Collage...", "saved": "Paramètres enregistrés.",
}
I18N["it"] |= {
    "app_on": "Attiva", "auto_paste": "Incolla nella finestra attiva", "capture_key": "Cattura tasto",
    "controls": "Controlli", "destination": "Destinazione", "hotkey": "Hotkey push-to-talk",
    "language_api": "Lingua e API", "mic": "Microfono", "mic_refresh": "Aggiorna",
    "preview": "Anteprima", "save_hotkey": "Salva hotkey", "save_key": "Salva chiave",
    "save_settings": "Salva impostazioni", "source_language": "Lingua parlata",
    "speech_driver": "Riconoscimento", "status_ready": "Pronto. Tieni premuto l'hotkey e parla.",
    "translate": "Traduzione DeepSeek", "recording": "Registrazione...", "processing": "Elaborazione...",
    "translating": "Traduzione...", "write_paste": "Incolla...", "saved": "Impostazioni salvate.",
}
I18N["uk"] |= {
    "app_on": "Увімкнено", "auto_paste": "Вставити в активне вікно", "capture_key": "Захопити клавішу",
    "controls": "Керування", "destination": "Ціль", "hotkey": "Hotkey push-to-talk",
    "language_api": "Мова та API", "mic": "Мікрофон", "mic_refresh": "Оновити",
    "preview": "Перегляд", "save_hotkey": "Зберегти hotkey", "save_key": "Зберегти ключ",
    "save_settings": "Зберегти налаштування", "source_language": "Мова мовлення",
    "speech_driver": "Розпізнавання", "status_ready": "Готово. Утримуйте hotkey і говоріть.",
    "translate": "Переклад DeepSeek", "recording": "Запис...", "processing": "Обробка...",
    "translating": "Переклад...", "write_paste": "Вставка...", "saved": "Налаштування збережено.",
}
I18N["pt"] |= {
    "app_on": "Ativo", "auto_paste": "Colar na janela ativa", "capture_key": "Capturar tecla",
    "controls": "Controles", "destination": "Destino", "hotkey": "Hotkey push-to-talk",
    "language_api": "Idioma e API", "mic": "Microfone", "mic_refresh": "Atualizar",
    "preview": "Prévia", "save_hotkey": "Salvar hotkey", "save_key": "Salvar chave",
    "save_settings": "Salvar ajustes", "source_language": "Idioma falado",
    "speech_driver": "Reconhecimento", "status_ready": "Pronto. Segure o hotkey e fale.",
    "translate": "Tradução DeepSeek", "recording": "Gravando...", "processing": "Processando...",
    "translating": "Traduzindo...", "write_paste": "Colando...", "saved": "Ajustes salvos.",
}
I18N["nl"] |= {
    "app_on": "Ingeschakeld", "auto_paste": "Plakken in actief venster", "capture_key": "Toets vastleggen",
    "controls": "Bediening", "destination": "Doel", "hotkey": "Push-to-talk hotkey",
    "language_api": "Taal en API", "mic": "Microfoon", "mic_refresh": "Vernieuwen",
    "preview": "Voorbeeld", "save_hotkey": "Hotkey opslaan", "save_key": "Sleutel opslaan",
    "save_settings": "Instellingen opslaan", "source_language": "Spraaktaal",
    "speech_driver": "Spraakherkenning", "status_ready": "Klaar. Houd de hotkey vast en spreek.",
    "translate": "DeepSeek vertaling", "recording": "Opnemen...", "processing": "Verwerken...",
    "translating": "Vertalen...", "write_paste": "Plakken...", "saved": "Instellingen opgeslagen.",
}
I18N["cs"] |= {
    "app_on": "Zapnuto", "auto_paste": "Vložit do aktivního okna", "capture_key": "Zachytit klávesu",
    "controls": "Ovládání", "destination": "Cíl", "hotkey": "Push-to-talk hotkey",
    "language_api": "Jazyk a API", "mic": "Mikrofon", "mic_refresh": "Obnovit",
    "preview": "Náhled", "save_hotkey": "Uložit hotkey", "save_key": "Uložit klíč",
    "save_settings": "Uložit nastavení", "source_language": "Jazyk řeči",
    "speech_driver": "Rozpoznávání", "status_ready": "Připraveno. Držte hotkey a mluvte.",
    "translate": "Překlad DeepSeek", "recording": "Nahrávám...", "processing": "Zpracování...",
    "translating": "Překládám...", "write_paste": "Vkládám...", "saved": "Nastavení uloženo.",
}

ACCENT = "#0f766e"
ACCENT_DARK = "#115e59"
BG = "#f3f5f2"
PANEL = "#ffffff"
TEXT = "#17211f"
MUTED = "#5f6d68"
SUCCESS = "#16a34a"
WARN = "#f59e0b"
ERROR = "#dc2626"
API_ENV_KEYS = ("DEEPSEEK_API_KEY", "DEEP_SEEK_API", "DEEPSEEK_API", "DEEP_SEEK_API_KEY")


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _bytes_to_blob(data: bytes) -> DATA_BLOB:
    buffer = ctypes.create_string_buffer(data)
    blob = DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    blob._buffer = buffer  # type: ignore[attr-defined]
    return blob


def _blob_to_bytes(blob: DATA_BLOB) -> bytes:
    data = ctypes.string_at(blob.pbData, blob.cbData)
    ctypes.windll.kernel32.LocalFree(blob.pbData)
    return data


def protect_secret(text: str) -> str:
    if not text:
        return ""
    try:
        crypt32 = ctypes.windll.crypt32
        in_blob = _bytes_to_blob(text.encode("utf-8"))
        out_blob = DATA_BLOB()
        if not crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
            raise ctypes.WinError()
        return _blob_to_bytes(out_blob).hex()
    except Exception:
        return text.encode("utf-8").hex()


def unprotect_secret(text: str) -> str:
    if not text:
        return ""
    try:
        raw = bytes.fromhex(text)
    except ValueError:
        return text
    try:
        crypt32 = ctypes.windll.crypt32
        in_blob = _bytes_to_blob(raw)
        out_blob = DATA_BLOB()
        if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
            raise ctypes.WinError()
        return _blob_to_bytes(out_blob).decode("utf-8")
    except Exception:
        try:
            return raw.decode("utf-8")
        except Exception:
            return ""


def app_config_path() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME / "config.json"
    return Path.home() / ".itoldu" / "config.json"


def load_dotenv_file() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
    except Exception:
        pass


def get_deepseek_env_key() -> str:
    for key in API_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


@dataclass
class Settings:
    enabled: bool = True
    translate_enabled: bool = False
    hotkey: str = "-"
    hotkey_label: str = "-"
    hotkey_scan_code: int | None = None
    stt_driver: str = "google"
    source_language_label: str = "Auto PL/EN"
    target_language: str = "polski"
    app_language: str = "en"
    status_display_mode: str = "icons"
    deepseek_api_key_source: str = "env"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    mic_device: str = ""
    auto_paste: bool = True


class ConfigStore:
    def __init__(self) -> None:
        self.path = app_config_path()

    def load(self) -> Settings:
        load_dotenv_file()
        settings = Settings()
        file_data: dict[str, Any] = {}
        if self.path.exists():
            try:
                file_data = json.loads(self.path.read_text(encoding="utf-8"))
                for key, value in file_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
            except Exception:
                pass

        stored_secret = str(file_data.get("deepseek_api_key_ciphertext", "") or "").strip()
        legacy_secret = str(file_data.get("deepseek_api_key", "") or "").strip()
        env_key = get_deepseek_env_key()

        if stored_secret:
            settings.deepseek_api_key = unprotect_secret(stored_secret)
            settings.deepseek_api_key_source = "local"
        elif legacy_secret:
            settings.deepseek_api_key = legacy_secret
            settings.deepseek_api_key_source = "local"
        elif env_key:
            settings.deepseek_api_key = env_key
            settings.deepseek_api_key_source = "env"
        else:
            settings.deepseek_api_key = ""
            settings.deepseek_api_key_source = "none"
        return settings

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(settings)
        payload["deepseek_api_key_ciphertext"] = (
            protect_secret(settings.deepseek_api_key.strip())
            if settings.deepseek_api_key_source == "local" and settings.deepseek_api_key.strip()
            else ""
        )
        payload.pop("deepseek_api_key", None)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


class ToastOverlay:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window: tk.Toplevel | None = None
        self.hide_after_id: str | None = None
        self.message_var = tk.StringVar(value="")
        self.detail_var = tk.StringVar(value="")
        self.state_var = tk.StringVar(value="")

    def show(self, message: str, detail: str = "", state: str = "info", duration_ms: int = 1800) -> None:
        self._ensure_window()
        self.message_var.set(message)
        self.detail_var.set(detail)
        self.state_var.set(state.upper())

        color = {
            "info": ACCENT,
            "ok": SUCCESS,
            "warn": WARN,
            "error": ERROR,
        }.get(state, ACCENT)

        if self.window is not None:
            self.window.configure(bg=color)
            self.window.deiconify()
            self.window.lift()
            self._place()
            if self.hide_after_id is not None:
                try:
                    self.window.after_cancel(self.hide_after_id)
                except Exception:
                    pass
            self.hide_after_id = self.window.after(duration_ms, self.hide)

    def hide(self) -> None:
        if self.window is not None:
            try:
                self.window.withdraw()
            except Exception:
                pass

    def _ensure_window(self) -> None:
        if self.window is not None:
            return
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        try:
            self.window.attributes("-alpha", 0.96)
        except Exception:
            pass
        self.window.configure(bg=ACCENT)

        frame = tk.Frame(self.window, bg=PANEL, padx=14, pady=10)
        frame.pack(fill="both", expand=True, padx=3, pady=3)
        top = tk.Frame(frame, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, textvariable=self.state_var, bg=PANEL, fg=ACCENT_DARK, font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(top, text="I Told U", bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side="right")
        tk.Label(frame, textvariable=self.message_var, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold"), anchor="w", justify="left").pack(fill="x", pady=(4, 0))
        tk.Label(frame, textvariable=self.detail_var, bg=PANEL, fg=MUTED, font=("Segoe UI", 8), anchor="w", justify="left", wraplength=280).pack(fill="x", pady=(2, 0))
        self._place()

    def _place(self) -> None:
        if self.window is None:
            return
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        w = 320
        h = 92
        x = sw - w - 20
        y = sh - h - 60
        self.window.geometry(f"{w}x{h}+{x}+{y}")


class StatusOverlay:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        try:
            self.window.attributes("-toolwindow", True)
            self.window.attributes("-alpha", 0.88)
        except Exception:
            pass
        self.window.configure(bg="#cbd5e1")

        self.mode = "icons"
        self.phase = "nasluch"
        self.last_hotkey = "-"
        self.internet_ok = True

        self.shell = tk.Frame(self.window, bg="#cbd5e1", padx=2, pady=2)
        self.shell.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.shell, bg="#f8fafc", padx=8, pady=6)
        self.inner.pack(fill="both", expand=True)

        self.badge_row = tk.Frame(self.inner, bg="#f8fafc")
        self.badge_row.pack(fill="x")
        self.caption_var = tk.StringVar(value="")
        self.caption = tk.Label(
            self.inner,
            textvariable=self.caption_var,
            bg="#f8fafc",
            fg=MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        )

        self.badges: dict[str, tk.Frame] = {}
        self.badge_labels: dict[str, tk.Label] = {}
        badge_specs = [
            ("mic", "\u25c9"),
            ("work", "\u21bb"),
            ("net", "\u25cc"),
            ("key", "\u2328"),
        ]
        for idx, (name, glyph) in enumerate(badge_specs):
            badge = tk.Frame(self.badge_row, bg="#e2e8f0", padx=5, pady=3)
            badge.pack(side="left", padx=(0, 5 if idx < len(badge_specs) - 1 else 0))
            label = tk.Label(
                badge,
                text=glyph,
                bg="#e2e8f0",
                fg="#94a3b8",
                font=("Segoe UI Symbol", 10, "bold"),
            )
            label.pack()
            self.badges[name] = badge
            self.badge_labels[name] = label

        self.set_mode("icons")
        self.show()

    def show(self) -> None:
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.attributes("-topmost", True)
        except Exception:
            pass

    def hide(self) -> None:
        try:
            self.window.withdraw()
        except Exception:
            pass

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in {"icons", "text"} else "icons"
        self._render()

    def update_state(self, state: str, hotkey: str | None = None, internet: str | None = None) -> None:
        self.phase = self._display_state(state)
        if hotkey is not None:
            self.last_hotkey = hotkey
        if internet is not None:
            self.internet_ok = "ok" in internet.lower()
        self._render()

    def _set_alpha(self, value: float) -> None:
        try:
            self.window.attributes("-alpha", value)
        except Exception:
            pass

    def _place(self) -> None:
        self.window.update_idletasks()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        compact = self.mode == "icons"
        busy = self.phase not in {"nasluch", "gotowe", "wylaczone"}
        w = 146 if compact else 232
        h = 34 if compact and not busy else 44 if compact else 86
        x = sw - w - 18
        y = sh - h - 54
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def _render(self) -> None:
        compact = self.mode == "icons"
        busy = self.phase not in {"nasluch", "gotowe", "wylaczone"}
        if compact:
            self.caption.pack_forget()
            self.inner.configure(padx=8, pady=6)
            self._set_alpha(0.74 if not busy else 0.94)
        else:
            if not self.caption.winfo_ismapped():
                self.caption.pack(fill="x", pady=(4, 0))
            self.inner.configure(padx=10, pady=7)
            self._set_alpha(0.95)

        icon_map = {
            "mic": ("\u25c9", self.phase == "nagrywam", "#ef4444"),
            "work": (self._work_glyph(), self.phase in {"przetwarzam", "tlumacze", "wklejam"}, self._state_color(self.phase)),
            "net": ("\u25cc", self.internet_ok, "#16a34a" if self.internet_ok else "#94a3b8"),
            "key": ("\u2328", True, ACCENT_DARK),
        }
        for name, (glyph, active, accent) in icon_map.items():
            badge = self.badges[name]
            label = self.badge_labels[name]
            if active:
                badge.configure(bg=accent)
                label.configure(text=glyph, bg=accent, fg="white")
            else:
                badge.configure(bg="#e2e8f0")
                label.configure(text=glyph, bg="#e2e8f0", fg="#94a3b8")

        if compact:
            self.caption_var.set("")
        else:
            self.caption_var.set(self._caption_for_phase())

        self.window.configure(bg="#cbd5e1")
        self.shell.configure(bg="#cbd5e1")
        self.inner.configure(bg="#f8fafc")
        self.badge_row.configure(bg="#f8fafc")
        self.caption.configure(bg="#f8fafc")
        self._place()
        self.show()

    def _caption_for_phase(self) -> str:
        captions = {
            "nagrywam": "nagrywam",
            "przetwarzam": "przetwarzam",
            "tlumacze": "tlumacze",
            "wklejam": "wklejam",
            "blad": "blad",
            "wylaczone": "wylaczone",
            "gotowe": "nasluch",
            "nasluch": "nasluch",
        }
        return captions.get(self.phase, "nasluch")

    @staticmethod
    def _work_glyph() -> str:
        return "\u21bb"

    @staticmethod
    def _display_state(state: str) -> str:
        lowered = state.lower()
        if any(word in lowered for word in ("nagry", "record", "aufnahme", "grabando", "enregistrement", "registrazione", "запис", "gravando", "opnemen", "nahr")):
            return "nagrywam"
        if any(word in lowered for word in ("przetwarz", "process", "verarbeitung", "proces", "traitement", "elaborazione", "оброб", "verwerk", "zprac")):
            return "przetwarzam"
        if any(word in lowered for word in ("tlumacz", "translat", "übersetz", "traduc", "traduction", "traduzione", "переклад", "vertal", "překl")):
            return "tlumacze"
        if any(word in lowered for word in ("wklej", "past", "einfüg", "peg", "coll", "incoll", "встав", "plak", "vklád")):
            return "wklejam"
        if "blad" in lowered or "error" in lowered:
            return "blad"
        if "wylacz" in lowered or "disabled" in lowered:
            return "wylaczone"
        if "gotowe" in lowered or "done" in lowered:
            return "gotowe"
        return "nasluch"

    @staticmethod
    def _state_color(state: str) -> str:
        if state == "nagrywam":
            return "#ef4444"
        if state in {"przetwarzam", "tlumacze", "wklejam"}:
            return "#f59e0b"
        if state == "blad":
            return ERROR
        if state == "wylaczone":
            return MUTED
        return SUCCESS

    @staticmethod
    def _soft_color(state: str) -> str:
        if state == "nagrywam":
            return "#fff1f2"
        if state in {"przetwarzam", "tlumacze", "wklejam"}:
            return "#fffbeb"
        if state == "blad":
            return "#fef2f2"
        if state == "wylaczone":
            return "#f8fafc"
        return "#f0fdf4"

def probe_host(host: str, port: int = 443, timeout: float = 0.9) -> bool:
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class AudioRecorder:
    def __init__(self) -> None:
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self.started_at = 0.0

    def start(self, device: int | None) -> None:
        with self._lock:
            if self._stream is not None:
                return
            self._frames = []
            self.started_at = time.time()

            def callback(indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
                if status:
                    pass
                self._frames.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                device=device,
                callback=callback,
            )
            self._stream.start()

    def stop(self) -> bytes:
        with self._lock:
            if self._stream is None:
                return b""
            self._stream.stop()
            self._stream.close()
            self._stream = None
            if not self._frames:
                return b""
            audio = np.concatenate(self._frames, axis=0)
            return audio.tobytes()


class SpeechToText:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self._whisper_model: Any | None = None

    def transcribe(self, pcm: bytes, settings: Settings) -> str:
        if settings.stt_driver == "whisper_local":
            return self._transcribe_whisper_local(pcm, settings)
        return self._transcribe_google(pcm, settings)

    def _transcribe_google(self, pcm: bytes, settings: Settings) -> str:
        audio = sr.AudioData(pcm, SAMPLE_RATE, SAMPLE_WIDTH_BYTES)
        code = LANGUAGE_OPTIONS.get(settings.source_language_label, "auto_pl_en")
        if code == "auto_pl_en":
            errors: list[str] = []
            for lang in ("pl-PL", "en-US"):
                try:
                    text = self.recognizer.recognize_google(audio, language=lang)
                    if text.strip():
                        return text.strip()
                except Exception as exc:
                    errors.append(str(exc))
            raise RuntimeError("Nie udalo sie rozpoznac mowy w trybie Auto PL/EN.")
        return self.recognizer.recognize_google(audio, language=code).strip()

    def _transcribe_whisper_local(self, pcm: bytes, settings: Settings) -> str:
        try:
            from faster_whisper import WhisperModel
        except Exception as exc:
            raise RuntimeError(
                "Sterownik Whisper local wymaga: pip install faster-whisper"
            ) from exc

        wav_path = self._write_temp_wav(pcm)
        try:
            if self._whisper_model is None:
                self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            source_code = LANGUAGE_OPTIONS.get(settings.source_language_label, "auto_pl_en")
            whisper_language = None if source_code == "auto_pl_en" else source_code.split("-")[0]
            segments, _info = self._whisper_model.transcribe(
                wav_path,
                language=whisper_language,
                vad_filter=True,
                beam_size=1,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    @staticmethod
    def _write_temp_wav(pcm: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            with wave.open(tmp, "wb") as wav:
                wav.setnchannels(CHANNELS)
                wav.setsampwidth(SAMPLE_WIDTH_BYTES)
                wav.setframerate(SAMPLE_RATE)
                wav.writeframes(pcm)
            return tmp.name


class DeepSeekTranslator:
    def translate(self, text: str, settings: Settings) -> str:
        api_key = settings.deepseek_api_key.strip()
        if not api_key:
            raise RuntimeError("Brakuje DEEPSEEK_API_KEY albo klucza w ustawieniach appki.")

        base_url = settings.deepseek_base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            url = base_url
        else:
            url = f"{base_url}/chat/completions"

        payload = {
            "model": settings.deepseek_model.strip() or "deepseek-v4-flash",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise live dictation translator. "
                        "Translate the user's dictated text to the target language. "
                        "Return only the final translated text, with no explanations. "
                        "Preserve meaning, tone, punctuation, names, code snippets, and line breaks. "
                        "If the text is already in the target language, return a cleaned version of it."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Target language: {settings.target_language}\n\nText:\n{text}",
                },
            ],
            "temperature": 0.1,
            "max_tokens": max(128, min(4096, len(text) * 3)),
            "stream": False,
            "thinking": {"type": "disabled"},
        }

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"DeepSeek API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class ActiveWindowPaster:
    def __init__(self) -> None:
        self.user32 = getattr(getattr(ctypes, "windll", None), "user32", None)

    def current_window(self) -> int:
        if self.user32 is None:
            return 0
        return int(self.user32.GetForegroundWindow())

    def paste_text(self, hwnd: int, text: str) -> None:
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(0.08)
        if hwnd and self.user32 is not None:
            self.user32.SetForegroundWindow(hwnd)
            time.sleep(0.08)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)

        if old_clipboard:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass


class IToldUApp:
    def __init__(self) -> None:
        self.config = ConfigStore()
        self.settings = self.config.load()
        self.recorder = AudioRecorder()
        self.stt = SpeechToText()
        self.translator = DeepSeekTranslator()
        self.paster = ActiveWindowPaster()
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.hotkey_handles: list[Any] = []
        self.hotkey_capture_handle: Any | None = None
        self.hotkey_capture_active = False
        self.recording = False
        self.processing = False
        self.target_hwnd = 0
        self.mic_devices: list[tuple[str, int | None]] = []
        self.main_container: ttk.Frame | None = None

        self.root = tk.Tk()
        self.toast = ToastOverlay(self.root)
        self.status_overlay = StatusOverlay(self.root)
        self.root.title(APP_NAME)
        self._apply_window_icon()
        self.root.geometry("840x680")
        self.root.minsize(760, 600)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Unmap>", self.on_root_visibility_change)
        self.root.bind("<Map>", self.on_root_visibility_change)

        self.style = ttk.Style()
        self.configure_styles()

        self._build_ui()
        self.refresh_devices(select_saved=True)
        self.sync_status_overlay_mode()
        self.register_hotkey()
        self.root.after(100, self.drain_events)
        self.root.after(2500, self.refresh_network_state)
        self._set_runtime_state(self.t("listening"))
        self._set_connection_state(self.t("internet_check"))

    def configure_styles(self) -> None:
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        elif "vista" in self.style.theme_names():
            self.style.theme_use("vista")
        self.style.configure(".", font=("Segoe UI", 9), background=BG, foreground=TEXT)
        self.style.configure("Root.TFrame", background=BG)
        self.style.configure("Panel.TFrame", background=PANEL)
        self.style.configure("Card.TLabelframe", background=PANEL, foreground=TEXT, bordercolor="#d8ded9", lightcolor="#d8ded9", darkcolor="#d8ded9")
        self.style.configure("Card.TLabelframe.Label", background=PANEL, foreground=TEXT, font=("Segoe UI", 10, "bold"))
        self.style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background=BG, foreground=TEXT)
        self.style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), background=BG, foreground=MUTED)
        self.style.configure("Subtle.TLabel", font=("Segoe UI", 9), background=PANEL, foreground=MUTED)
        self.style.configure("TLabel", background=PANEL, foreground=TEXT)
        self.style.configure("TCheckbutton", background=PANEL, foreground=TEXT)
        self.style.configure("TEntry", fieldbackground="#fbfcfb", bordercolor="#cfd8d2", lightcolor="#cfd8d2", darkcolor="#cfd8d2")
        self.style.configure("TCombobox", fieldbackground="#fbfcfb", bordercolor="#cfd8d2", arrowcolor=ACCENT_DARK)
        self.style.configure("TButton", padding=(10, 5), background="#eef3ef", foreground=TEXT, bordercolor="#cfd8d2")
        self.style.map("TButton", background=[("active", "#e1ebe5")])
        self.style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), background=ACCENT, foreground="white", bordercolor=ACCENT)
        self.style.map("Accent.TButton", background=[("active", ACCENT_DARK)], foreground=[("active", "white")])

    def _apply_window_icon(self) -> None:
        icon = tk.PhotoImage(width=32, height=32)
        icon.put("#0f766e", to=(4, 4, 28, 28))
        icon.put("#ffffff", to=(10, 9, 22, 12))
        icon.put("#ffffff", to=(10, 15, 24, 18))
        icon.put("#f59e0b", to=(20, 20, 25, 25))
        self._app_icon = icon
        try:
            self.root.iconphoto(True, icon)
        except Exception:
            pass

    def t(self, key: str, **kwargs: Any) -> str:
        lang = self.settings.app_language if self.settings.app_language in I18N else "en"
        text = I18N.get(lang, I18N["en"]).get(key, I18N["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def _build_ui(self) -> None:
        if self.main_container is not None:
            self.main_container.destroy()
        container = ttk.Frame(self.root, padding=16, style="Root.TFrame")
        self.main_container = container
        container.pack(fill="both", expand=True)

        header = tk.Frame(container, bg=ACCENT, padx=16, pady=14)
        header.pack(fill="x")
        title_row = tk.Frame(header, bg=ACCENT)
        title_row.pack(fill="x")
        tk.Label(title_row, text="I Told U", bg=ACCENT, fg="white", font=("Segoe UI", 20, "bold")).pack(side="left")
        self.runtime_state_var = tk.StringVar(value=self.t("listening"))
        self.internet_status_var = tk.StringVar(value=self.t("internet_check"))
        self.hotkey_status_var = tk.StringVar(value="Hotkey: ...")
        status_row = tk.Frame(header, bg=ACCENT)
        status_row.pack(fill="x", pady=(10, 0))
        self._pill(status_row, self.runtime_state_var, "#dbeafe", ACCENT_DARK).pack(side="left", padx=(0, 8))
        self._pill(status_row, self.internet_status_var, "#dcfce7", "#166534").pack(side="left", padx=(0, 8))
        self._pill(status_row, self.hotkey_status_var, "#fef3c7", "#92400e").pack(side="left")

        self.status_var = tk.StringVar(value=self.t("status_ready"))
        tk.Label(header, textvariable=self.status_var, bg=ACCENT, fg="#e0f2fe", font=("Segoe UI", 9), anchor="e", justify="right").pack(fill="x", pady=(10, 0))

        controls = ttk.LabelFrame(container, text=self.t("controls"), padding=14, style="Card.TLabelframe")
        controls.pack(fill="x", pady=(14, 10))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        self.enabled_var = tk.BooleanVar(value=self.settings.enabled)
        self.translate_var = tk.BooleanVar(value=self.settings.translate_enabled)
        self.auto_paste_var = tk.BooleanVar(value=self.settings.auto_paste)
        ttk.Checkbutton(controls, text=self.t("app_on"), variable=self.enabled_var, command=self.save_from_ui).grid(row=0, column=0, sticky="w", padx=(0, 16))
        ttk.Checkbutton(controls, text=self.t("translate"), variable=self.translate_var, command=self.save_from_ui).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(controls, text=self.t("auto_paste"), variable=self.auto_paste_var, command=self.save_from_ui).grid(row=0, column=2, sticky="w", padx=(16, 0))

        ttk.Label(controls, text=self.t("hotkey")).grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.hotkey_var = tk.StringVar(value=self.settings.hotkey)
        self.hotkey_entry = ttk.Entry(controls, textvariable=self.hotkey_var)
        self.hotkey_entry.grid(row=1, column=1, sticky="ew", pady=(12, 0), padx=(8, 16))
        ttk.Button(controls, text=self.t("save_hotkey"), command=self.on_save_hotkey, style="Accent.TButton").grid(row=1, column=2, sticky="w", pady=(12, 0))
        ttk.Button(controls, text=self.t("capture_key"), command=self.capture_hotkey_from_keyboard).grid(row=1, column=3, sticky="w", pady=(12, 0))
        self.hotkey_entry.bind("<Return>", lambda _event: self.on_save_hotkey())
        self.hotkey_entry.bind("<FocusOut>", lambda _event: self.on_save_hotkey())
        self.hotkey_hint_var = tk.StringVar(value=f"{self.t('hotkey_physical')}: {self.settings.hotkey_label}")
        tk.Label(controls, textvariable=self.hotkey_hint_var, bg="#ffffff", fg=MUTED, font=("Segoe UI", 8)).grid(row=2, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=(6, 0))

        ttk.Label(controls, text=self.t("mic")).grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(controls, textvariable=self.mic_var, state="readonly")
        self.mic_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(12, 0), padx=(8, 16))
        ttk.Button(controls, text=self.t("mic_refresh"), command=lambda: self.refresh_devices(select_saved=False)).grid(row=3, column=3, sticky="w", pady=(12, 0))

        options = ttk.LabelFrame(container, text=self.t("language_api"), padding=14, style="Card.TLabelframe")
        options.pack(fill="x", pady=(0, 10))
        options.columnconfigure(1, weight=1)
        options.columnconfigure(3, weight=1)

        ttk.Label(options, text=self.t("speech_driver")).grid(row=0, column=0, sticky="w")
        self.stt_driver_var = tk.StringVar(value=self.settings.stt_driver)
        ttk.Combobox(
            options,
            textvariable=self.stt_driver_var,
            state="readonly",
            values=["google", "whisper_local"],
        ).grid(row=0, column=1, sticky="ew", padx=(8, 16))

        ttk.Label(options, text=self.t("source_language")).grid(row=0, column=2, sticky="w")
        self.source_lang_var = tk.StringVar(value=self.settings.source_language_label)
        ttk.Combobox(
            options,
            textvariable=self.source_lang_var,
            state="readonly",
            values=list(LANGUAGE_OPTIONS.keys()),
        ).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        ttk.Label(options, text=self.t("destination")).grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.target_lang_var = tk.StringVar(value=self.settings.target_language)
        ttk.Combobox(
            options,
            textvariable=self.target_lang_var,
            values=TARGET_LANGUAGE_OPTIONS,
        ).grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=(12, 0))

        ttk.Label(options, text=self.t("model")).grid(row=1, column=2, sticky="w", pady=(12, 0))
        self.model_var = tk.StringVar(value=self.settings.deepseek_model)
        ttk.Entry(options, textvariable=self.model_var).grid(row=1, column=3, sticky="ew", padx=(8, 0), pady=(12, 0))

        ttk.Label(options, text=self.t("overlay")).grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.status_mode_var = tk.StringVar(value=self.settings.status_display_mode)
        ttk.Combobox(
            options,
            textvariable=self.status_mode_var,
            state="readonly",
            values=["icons", "text"],
        ).grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(12, 0))

        ttk.Label(options, text=self.t("base_url")).grid(row=2, column=2, sticky="w", pady=(12, 0))
        self.base_url_var = tk.StringVar(value=self.settings.deepseek_base_url)
        ttk.Entry(options, textvariable=self.base_url_var).grid(row=2, column=3, sticky="ew", padx=(8, 0), pady=(12, 0))

        ttk.Label(options, text=self.t("api_key")).grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.api_key_var = tk.StringVar(value="")
        ttk.Entry(options, textvariable=self.api_key_var, show="*").grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 16), pady=(12, 0))
        ttk.Button(options, text=self.t("save_key"), command=self.save_api_key_from_ui).grid(row=3, column=3, sticky="e", pady=(12, 0))

        ttk.Label(options, text=self.t("api_source")).grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.api_source_var = tk.StringVar(value=self.deepseek_api_source_text())
        tk.Label(options, textvariable=self.api_source_var, bg="#ffffff", fg=MUTED, font=("Segoe UI", 8)).grid(row=4, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(12, 0))
        ttk.Button(options, text=self.t("use_env"), command=self.use_env_api_key).grid(row=4, column=3, sticky="e", pady=(12, 0))

        ttk.Label(options, text=self.t("app_language")).grid(row=5, column=0, sticky="w", pady=(12, 0))
        self.app_language_var = tk.StringVar(value=UI_LANGUAGE_OPTIONS.get(self.settings.app_language, "English"))
        ttk.Combobox(
            options,
            textvariable=self.app_language_var,
            state="readonly",
            values=list(UI_LANGUAGE_OPTIONS.values()),
        ).grid(row=5, column=1, sticky="ew", padx=(8, 16), pady=(12, 0))
        ttk.Button(options, text=self.t("save_settings"), command=self.save_from_ui).grid(row=5, column=3, sticky="e", pady=(12, 0))

        output = ttk.LabelFrame(container, text=self.t("preview"), padding=14, style="Card.TLabelframe")
        output.pack(fill="both", expand=True)
        output.rowconfigure(1, weight=1)
        output.columnconfigure(0, weight=1)

        self.last_text_var = tk.StringVar(value=self.t("last_result"))
        ttk.Label(output, textvariable=self.last_text_var, wraplength=700).grid(row=0, column=0, sticky="ew")

        self.log = tk.Text(output, height=12, wrap="word", font=("Segoe UI", 10), bg="#f8fafc", fg=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0)
        self.log.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.log.insert("end", self.t("start_log", hotkey=self.hotkey_display_text()) + "\n")
        self.log.configure(state="disabled")

        self.root.bind("<Control-s>", lambda _event: self.save_from_ui())

    def _pill(self, parent: tk.Widget, text_var: tk.StringVar, bg: str, fg: str) -> tk.Frame:
        pill = tk.Frame(parent, bg=bg, padx=10, pady=4)
        label = tk.Label(pill, textvariable=text_var, bg=bg, fg=fg, font=("Segoe UI", 8, "bold"))
        label.pack()
        return pill

    def refresh_devices(self, select_saved: bool) -> None:
        self.mic_devices = [("Domyslny mikrofon systemowy", None)]
        try:
            devices = sd.query_devices()
            for index, device in enumerate(devices):
                if int(device.get("max_input_channels", 0)) > 0:
                    name = str(device.get("name", f"Device {index}"))
                    self.mic_devices.append((f"{index}: {name}", index))
        except Exception as exc:
            self.set_status(f"{self.t('mic')}: {exc}")

        values = [label for label, _device in self.mic_devices]
        self.mic_combo["values"] = values
        selected = self.settings.mic_device if select_saved else self.mic_var.get()
        if selected in values:
            self.mic_var.set(selected)
        else:
            self.mic_var.set(values[0] if values else "")

    def selected_device_index(self) -> int | None:
        label = self.mic_var.get()
        for device_label, index in self.mic_devices:
            if device_label == label:
                return index
        return None

    def sync_status_overlay_mode(self) -> None:
        self.status_overlay.set_mode(self.settings.status_display_mode)

    def deepseek_api_source_text(self) -> str:
        if self.settings.deepseek_api_key_source == "local" and self.settings.deepseek_api_key.strip():
            return self.t("api_source_local")
        if self.settings.deepseek_api_key_source == "env" and get_deepseek_env_key():
            return self.t("api_source_env")
        if self.settings.deepseek_api_key.strip():
            return self.t("api_source_plain")
        return self.t("api_source_missing")

    def selected_app_language_code(self) -> str:
        value = self.app_language_var.get().strip() if hasattr(self, "app_language_var") else self.settings.app_language
        for code, label in UI_LANGUAGE_OPTIONS.items():
            if value == label or value == code:
                return code
        return "en"

    def hotkey_display_text(self) -> str:
        if self.settings.hotkey_scan_code is not None:
            return self.settings.hotkey_label or f"scan {self.settings.hotkey_scan_code}"
        return self.settings.hotkey_label or self.settings.hotkey or "-"

    def register_hotkey(self) -> None:
        for handle in self.hotkey_handles:
            self._remove_hotkey_handle(handle)
        self.hotkey_handles = []
        hotkey = self.settings.hotkey.strip() or "-"
        try:
            if self.settings.hotkey_scan_code is not None:
                handle = keyboard.hook_key(int(self.settings.hotkey_scan_code), self._handle_single_key_hotkey, suppress=True)
                self.hotkey_handles = [handle]
            elif self._is_single_key_hotkey(hotkey):
                key_name = self._single_key_name(hotkey)
                handle = keyboard.hook_key(key_name, self._handle_single_key_hotkey, suppress=True)
                self.hotkey_handles = [handle]
            else:
                down = keyboard.add_hotkey(hotkey, self.on_hotkey_down, suppress=True)
                up = keyboard.add_hotkey(hotkey, self.on_hotkey_up, suppress=True, trigger_on_release=True)
                self.hotkey_handles = [down, up]
            display = self.hotkey_display_text()
            self.set_status(f"{self.t('hotkey_active')}: {display}")
            self._set_runtime_state(f"{self.t('listening')}: {display}")
            self.hotkey_status_var.set(f"Hotkey: {display}")
            self.hotkey_hint_var.set(f"{self.t('hotkey_physical')}: {display}")
        except Exception as exc:
            self.set_status(f"{self.t('hotkey_error')}: {exc}")
            self._set_runtime_state(self.t("hotkey_error"))
            self.hotkey_status_var.set("Hotkey: blad")

    def on_save_hotkey(self) -> None:
        self.save_from_ui()
        self.register_hotkey()

    def save_api_key_from_ui(self) -> None:
        self.save_from_ui()

    def use_env_api_key(self) -> None:
        self.settings.deepseek_api_key = ""
        self.settings.deepseek_api_key_source = "env" if get_deepseek_env_key() else "none"
        self.api_key_var.set("")
        self.config.save(self.settings)
        self.api_source_var.set(self.deepseek_api_source_text())
        self.toast.show(self.t("api_toast_title"), self.t("api_toast_env"), state="ok")

    def capture_hotkey_from_keyboard(self) -> None:
        if self.hotkey_capture_active:
            return
        self.hotkey_capture_active = True
        self.set_status(self.t("choose_key"))
        self.hotkey_status_var.set("Hotkey: czekam...")
        self.hotkey_hint_var.set(f"{self.t('hotkey_physical')}: ...")
        self.toast.show(self.t("capture_key"), self.t("choose_key"), state="info", duration_ms=2200)

        def callback(event: keyboard.KeyboardEvent) -> None:
            if event.event_type != keyboard.KEY_DOWN:
                return
            if self.hotkey_capture_handle is not None:
                try:
                    keyboard.unhook(self.hotkey_capture_handle)
                except Exception:
                    pass
                self.hotkey_capture_handle = None
            if event.name == "esc":
                self.root.after(0, self._cancel_hotkey_capture)
                return
            scan_code = int(event.scan_code or 0)
            name = event.name or f"scan {scan_code}"
            self.root.after(0, lambda: self._finish_hotkey_capture(scan_code, name))

        self.hotkey_capture_handle = keyboard.hook(callback, suppress=True)

    def _cancel_hotkey_capture(self) -> None:
        self.hotkey_capture_active = False
        self.hotkey_capture_handle = None
        self.set_status(self.t("hotkey_cancel"))
        self.hotkey_hint_var.set(f"{self.t('hotkey_physical')}: {self.hotkey_display_text()}")
        self.hotkey_status_var.set(f"Hotkey: {self.hotkey_display_text()}")

    def _finish_hotkey_capture(self, scan_code: int, name: str) -> None:
        self.hotkey_capture_active = False
        self.hotkey_capture_handle = None
        self.settings.hotkey_scan_code = scan_code
        self.settings.hotkey = name
        self.settings.hotkey_label = name
        self.hotkey_var.set(name)
        self.config.save(self.settings)
        self.register_hotkey()
        self.set_status(f"{self.t('hotkey_ready')}: {name}")
        self.toast.show(self.t("hotkey_ready"), f"{name} | scan {scan_code}", state="ok")

    def save_from_ui(self) -> None:
        old_language = self.settings.app_language
        manual_hotkey = self.hotkey_var.get().strip() or "-"
        if self.hotkey_capture_active:
            manual_hotkey = self.settings.hotkey
        elif manual_hotkey != (self.settings.hotkey_label or self.settings.hotkey or "-"):
            self.settings.hotkey_scan_code = None
            self.settings.hotkey_label = manual_hotkey

        self.settings.enabled = bool(self.enabled_var.get())
        self.settings.translate_enabled = bool(self.translate_var.get())
        self.settings.auto_paste = bool(self.auto_paste_var.get())
        self.settings.hotkey = manual_hotkey
        self.settings.stt_driver = self.stt_driver_var.get().strip() or "google"
        self.settings.source_language_label = self.source_lang_var.get().strip() or "Auto PL/EN"
        self.settings.target_language = self.target_lang_var.get().strip() or "polski"
        self.settings.app_language = self.selected_app_language_code()
        self.settings.status_display_mode = self.status_mode_var.get().strip() or "icons"
        typed_key = self.api_key_var.get().strip()
        if typed_key:
            self.settings.deepseek_api_key = typed_key
            self.settings.deepseek_api_key_source = "local"
        self.settings.deepseek_base_url = self.base_url_var.get().strip() or "https://api.deepseek.com"
        self.settings.deepseek_model = self.model_var.get().strip() or "deepseek-v4-flash"
        self.settings.mic_device = self.mic_var.get()
        self.config.save(self.settings)
        self.set_status(self.t("saved"))
        if self.settings.enabled:
            self._set_runtime_state(f"{self.t('listening')}: {self.hotkey_display_text()}")
        else:
            self._set_runtime_state("disabled")
        self.hotkey_status_var.set(f"Hotkey: {self.hotkey_display_text()}")
        self.hotkey_hint_var.set(f"{self.t('hotkey_physical')}: {self.hotkey_display_text()}")
        self.api_source_var.set(self.deepseek_api_source_text())
        if typed_key:
            self.api_key_var.set("")
        self.sync_status_overlay_mode()
        if old_language != self.settings.app_language:
            self._build_ui()
            self.refresh_devices(select_saved=True)
        self.toast.show(self.t("saved"), f"Hotkey: {self.hotkey_display_text()}", state="ok")

    def on_hotkey_down(self) -> None:
        if not self.enabled_var.get() or self.recording or self.processing:
            return
        self.save_from_ui()
        self.target_hwnd = self.paster.current_window()
        try:
            self.recorder.start(self.selected_device_index())
        except Exception as exc:
            self.events.put(("error", f"{self.t('mic')}: {exc}"))
            return
        self.recording = True
        self.events.put(("status", self.t("recording")))
        self.events.put(("runtime", self.t("recording")))
        self.events.put(("toast", (self.t("recording"), self.t("status_ready"), "info")))

    def on_hotkey_up(self) -> None:
        if not self.recording:
            return
        self.recording = False
        try:
            pcm = self.recorder.stop()
        except Exception as exc:
            self.events.put(("error", f"{self.t('mic')}: {exc}"))
            return

        if len(pcm) < SAMPLE_RATE * SAMPLE_WIDTH_BYTES * 0.25:
            self.events.put(("status", self.t("too_short")))
            self.events.put(("runtime", f"{self.t('listening')}: {self.hotkey_display_text()}"))
            return

        self.processing = True
        self.events.put(("status", self.t("processing")))
        self.events.put(("runtime", self.t("processing")))
        self.events.put(("toast", (self.t("processing"), "", "info")))
        worker = threading.Thread(target=self.process_audio, args=(pcm, self.target_hwnd), daemon=True)
        worker.start()

    def process_audio(self, pcm: bytes, hwnd: int) -> None:
        try:
            text = self.stt.transcribe(pcm, self.settings)
            if not text:
                raise RuntimeError("Pusty wynik rozpoznawania.")
            self.events.put(("transcript", text))
            final_text = text
            if self.settings.translate_enabled:
                self.events.put(("status", self.t("translating")))
                self.events.put(("runtime", self.t("translating")))
                final_text = self.translator.translate(text, self.settings)
                self.events.put(("translation", final_text))

            if self.settings.auto_paste:
                self.events.put(("status", self.t("write_paste")))
                self.events.put(("runtime", self.t("write_paste")))
                self.paster.paste_text(hwnd, final_text)
            self.events.put(("done", final_text))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        finally:
            self.processing = False

    def drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    self.set_status(str(payload))
                elif kind == "runtime":
                    self._set_runtime_state(str(payload))
                elif kind == "toast":
                    message, detail, state = payload
                    self.toast.show(str(message), str(detail), str(state))
                elif kind == "transcript":
                    self.append_log(f"\nMowa:\n{payload}\n")
                    self.last_text_var.set(str(payload))
                elif kind == "translation":
                    self.append_log(f"Tlumaczenie:\n{payload}\n")
                    self.last_text_var.set(str(payload))
                elif kind == "done":
                    self.set_status(self.t("done"))
                    self._set_runtime_state(f"{self.t('listening')}: {self.hotkey_display_text()}")
                    self.toast.show(self.t("done"), "", state="ok")
                    self.last_text_var.set(str(payload))
                elif kind == "error":
                    self.set_status(f"Error: {payload}")
                    self._set_runtime_state("error")
                    self.append_log(f"\nBLAD: {payload}\n")
                    self.toast.show("Error", str(payload), state="error", duration_ms=2800)
        except queue.Empty:
            pass
        self.root.after(100, self.drain_events)

    def append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _set_runtime_state(self, text: str) -> None:
        self.runtime_state_var.set(text)
        hotkey = self.hotkey_display_text() if hasattr(self, "settings") else "-"
        self.status_overlay.update_state(text, hotkey=hotkey)

    def _set_connection_state(self, text: str, ok: bool | None = None) -> None:
        self.internet_status_var.set(text)
        self.status_overlay.update_state(self.runtime_state_var.get(), internet=text)

    @staticmethod
    def _is_single_key_hotkey(hotkey: str) -> bool:
        normalized = hotkey.strip().lower()
        return "+" not in normalized and normalized != ""

    @staticmethod
    def _single_key_name(hotkey: str) -> str:
        normalized = hotkey.strip()
        if normalized == "-":
            return "-"
        return normalized

    def refresh_network_state(self) -> None:
        host = urlparse(self.settings.deepseek_base_url.strip() or "https://api.deepseek.com").hostname or "api.deepseek.com"
        ok = probe_host(host)
        self._set_connection_state("Internet: OK" if ok else "Internet: brak", ok)
        self.root.after(12000, self.refresh_network_state)

    def _handle_single_key_hotkey(self, event: keyboard.KeyboardEvent) -> bool:
        if event.event_type == keyboard.KEY_DOWN:
            self.on_hotkey_down()
        elif event.event_type == keyboard.KEY_UP:
            self.on_hotkey_up()
        return False

    def on_root_visibility_change(self, _event: tk.Event) -> None:
        self.root.after(80, self.status_overlay.show)

    def on_close(self) -> None:
        try:
            self.save_from_ui()
        except Exception:
            pass
        try:
            self.recorder.stop()
        except Exception:
            pass
        for handle in self.hotkey_handles:
            self._remove_hotkey_handle(handle)
        try:
            self.toast.hide()
        except Exception:
            pass
        try:
            self.status_overlay.hide()
        except Exception:
            pass
        self.root.destroy()

    @staticmethod
    def _remove_hotkey_handle(handle: Any) -> None:
        try:
            keyboard.unhook(handle)
            return
        except Exception:
            pass
        try:
            keyboard.remove_hotkey(handle)
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    try:
        IToldUApp().run()
    except Exception as exc:
        messagebox.showerror(APP_NAME, str(exc))
