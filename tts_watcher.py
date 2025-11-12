import asyncio
import time
import os
from typing import Set, Tuple, Callable, Optional
from datetime import datetime

# ---------- Optional: Rich für Konsolenlauf ----------
# (Für GUI-Betrieb wird nur das Log-Callback benutzt.)
try:
    from rich.console import Console
    from rich.theme import Theme
    THEME = Theme({
        "default": "turquoise2",
        "header": "bold dark_orange3",
        "warn": "yellow",
        "error": "bold red",
        "muted": "grey50",
    })
    _console: Optional[Console] = Console(theme=THEME)
except Exception:
    _console = None  # Falls rich fehlt, läuft alles trotzdem

# Windows-Terminal-Basisfarbe (optional; hat keinen Einfluss auf GUI)
try:
    os.system("color 0B")
except Exception:
    pass

# ---------- Externe Abhängigkeiten ----------
import pyttsx3
from winrt.windows.ui.notifications.management import (
    UserNotificationListener,
    UserNotificationListenerAccessStatus,
)
from winrt.windows.ui.notifications import NotificationKinds


# ---------- Typen & Konfiguration ----------
LogFn = Callable[[str], None]

IGNORED_APPS = {"Alexa"}
POLL_INTERVAL = 2.0  # Sekunden

MUTE_TTS = False  # globale Stummschaltung
MAX_CHARS = 800   # <<< Globale Maximal-Länge


def set_ignore_discord(enabled: bool) -> None:
    """
    Beibehalten zur Kompatibilität: erlaubt das explizite Stummschalten von 'Discord'
    als App-Quelle über die IGNORED_APPS-Liste. Hat keinen Einfluss auf Fallbacks,
    da es keine App-spezifischen Fallbacks mehr gibt.
    """
    DISCORD_APP_NAME = "Discord"
    if enabled:
        IGNORED_APPS.add(DISCORD_APP_NAME)
    else:
        IGNORED_APPS.discard(DISCORD_APP_NAME)


def set_mute(enabled: bool) -> None:
    """Aktiviert/Deaktiviert die Sprachausgabe."""
    global MUTE_TTS
    MUTE_TTS = enabled


# ---------- Logging-Helfer ----------
def _default_log(msg: str) -> None:
    """
    Standard-Logger:
    - falls Rich verfügbar ist: rich console.print
    - sonst: normales print
    """
    if _console is not None:
        _console.print(msg)
    else:
        print(msg)


def _log_header(log: LogFn, app_name: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    # Ohne Rich-Tags, damit GUI-Frontends reinen Text bekommen.
    log(f"→ {ts} [{app_name}]:")  # Header-Zeile


def _log_info(log: LogFn, msg: str) -> None:
    log(msg)


def _log_warn(log: LogFn, msg: str) -> None:
    # Emojis statt Rich-Styles, damit es in GUI/Terminal gleichermaßen klappt
    log(f"⚠️  {msg}")


def _log_error(log: LogFn, msg: str) -> None:
    log(f"❌ {msg}")


# --- NEU/ERSATZ: Globale Regeln in zwei Varianten ---------------------------

MAX_CHARS = 800   # bleibt global gültig

def _apply_log_rules(text: Optional[str]) -> str:
    """
    Für LOG-Ausgabe:
    - None/leer -> 'ohne Text'
    - Steuerzeichen \r\n\t -> Leerzeichen (einzeiliges Log)
    - auf MAX_CHARS kürzen
    - Emojis BLEIBEN ERHALTEN
    """
    if not text:
        text = "ohne Text"
    # \r, \n, \t auf Leerzeichen normalisieren
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # Mehrfache Spaces optional zusammenfassen:
    # text = re.sub(r"\s{2,}", " ", text)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + " …"
    return text


def _apply_tts_rules(text: Optional[str]) -> str:
    """
    Für TTS:
    - None/leer -> 'ohne Text'
    - entfernt Nicht-BMP (z.B. viele Emojis) + \r \n \t
    - auf MAX_CHARS kürzen
    """
    if not text:
        text = "ohne Text"
    filtered = "".join(
        ch for ch in text
        if ord(ch) <= 0xFFFF and ch not in "\r\n\t"
    )
    if len(filtered) > MAX_CHARS:
        filtered = filtered[:MAX_CHARS] + " …"
    return filtered



# ---------- TTS-Helfer ----------
def speak(app_name: str, message: Optional[str], log: LogFn = _default_log, *, notify_style: bool = True) -> None:
    if app_name in IGNORED_APPS:
        return

    # >>> WICHTIG: Log-Text behält Emojis, TTS-Text wird sanitisiert
    log_message = _apply_log_rules(message)

    if MUTE_TTS:
        if notify_style:
            _log_header(log, app_name)
            _log_info(log, log_message)   # Emojis sichtbar im Log
        else:
            _log_info(log, log_message)
        return

    # Logging
    if notify_style:
        _log_header(log, app_name)
        _log_info(log, log_message)       # Emojis sichtbar im Log
        tts_text = _apply_tts_rules(f"{app_name}: {log_message}")
    else:
        _log_info(log, log_message)
        tts_text = _apply_tts_rules(log_message)

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 190)
        engine.setProperty("volume", 1.0)
        engine.say(tts_text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        _log_warn(log, f"Fehler im TTS für {app_name}: {e}")
        # Keine App-spezifischen Fallbacks mehr.


# ---------- Notification-Logik ----------
def extract_text_from_notification(notification) -> Tuple[str, Optional[str]]:
    """
    Versucht Titel/Körper zu extrahieren. Keine App-spezifischen Fallbacks.
    Gibt (app_name, message|None) zurück. Die globale Regel ersetzt None später durch 'ohne Text'.
    """
    app_name = "Unbekannt"
    try:
        app_name = notification.app_info.display_info.display_name
        visual = notification.notification.visual
        bindings = visual.bindings
        if not bindings:
            return app_name, None

        binding = bindings[0]
        try:
            text_elements = binding.get_text_elements()
        except Exception:
            return app_name, None

        texts = [t.text for t in text_elements if getattr(t, "text", None)]
        if not texts:
            return app_name, None

        title = texts[0]
        body = " ".join(texts[1:]) if len(texts) > 1 else ""
        message = f"{title} – {body}" if body else title
        return app_name, message

    except Exception:
        return app_name, None


async def init_listener(log: LogFn = _default_log):
    """Initialisiert einmalig den UserNotificationListener und prüft die Berechtigung."""
    try:
        listener = UserNotificationListener.current
        access_status = await listener.request_access_async()
    except Exception as e:
        _log_error(log, f"request_access_async() fehlgeschlagen: {e}")
        return None

    _log_info(log, f"👌 Zugriff auf Benachritigungen")

    if access_status != UserNotificationListenerAccessStatus.ALLOWED:
        _log_warn(
            log,
            "Kein Zugriff auf Benachrichtigungen. Starte ggf. als Administrator und prüfe die Windows-Einstellungen."
        )
        return None

    return listener


async def watch_notifications(
    poll_interval: float = POLL_INTERVAL,
    log: LogFn = _default_log
) -> None:
    """Watcher-Hauptschleife mit automatischem Reconnect bei Fehlern. Alle Logs via Callback."""
    seen_ids: Set[int] = set()

    listener = await init_listener(log=log)
    while listener is None:
        _log_warn(log, "Erneuter Zugriff in 10s…")
        await asyncio.sleep(10)
        listener = await init_listener(log=log)

    # Start-Ansage einmalig – nur als Info/TTS-Test, nicht wie Benachrichtigung loggen
    try:
        speak("Status", "👍 Benachrichtigungs-Assistent gestartet!", log=log, notify_style=False)
        speak("Info", "👋 Willkommen", log=log, notify_style=False)
        speak("Placeholder", " ", log=log, notify_style=False)
    except Exception as e:
        _log_warn(log, f"Fehler bei Start-Sprachausgabe: {e}")

    while True:
        try:
            notifs = await listener.get_notifications_async(NotificationKinds.TOAST)
            current_ids: Set[int] = set()

            for n in notifs:
                nid = n.id
                current_ids.add(nid)

                if nid not in seen_ids:
                    app_name, message = extract_text_from_notification(n)
                    # Immer sprechen/loggen – globale Regeln ersetzen None/leer durch 'ohne Text'
                    try:
                        speak(app_name, message, log=log, notify_style=True)
                    except Exception as e:
                        _log_warn(log, f"Fehler beim Vorlesen von {app_name}: {e}")

            seen_ids = current_ids

        except OSError as e:
            winerr = getattr(e, "winerror", None)
            if winerr == -2147024809:  # „Falscher Parameter“ – sporadisch
                _log_warn(log, "WinRT: Falscher Parameter – wird ignoriert.")
            else:
                _log_warn(log, f"OSError beim Abrufen der Benachrichtigungen: {e}")

        except Exception as e:
            _log_warn(log, f"Fehler beim Abrufen der Benachrichtigungen: {e}")
            _log_info(log, "Versuche Re-Initialisierung in 5s…")
            await asyncio.sleep(5)
            listener = await init_listener(log=log)
            while listener is None:
                _log_warn(log, "Erneuter Zugriff in 10s…")
                await asyncio.sleep(10)
                listener = await init_listener(log=log)

        await asyncio.sleep(poll_interval)


def main() -> None:
    # Konsolenmodus (ohne GUI) weiter möglich
    while True:
        try:
            asyncio.run(watch_notifications())
            _default_log("Watcher beendet sich regulär.")
            break
        except KeyboardInterrupt:
            _default_log("Beendet durch Benutzer (Strg+C).")
            break
        except Exception as e:
            _default_log(f"Unerwarteter Fehler im Watcher: {e}")
            _default_log("Neustart in 5 Sekunden…")
            time.sleep(5)

    _default_log("\n--- Skript wurde beendet ---")
    try:
        input("Drücke Enter, um die Konsole zu schließen...")
    except Exception:
        pass


if __name__ == "__main__":
    main()
