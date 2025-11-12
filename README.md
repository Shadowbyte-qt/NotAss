# NotAss (Notification Assistant)

Ein kleiner Windows-Assistent, der System-Benachrichtigungen einsammelt und sie per TTS (Text-to-Speech) vorliest. Ideal für Fokus-Phasen, Barrierefreiheit oder Streaming/Multitasking.

✨ Features
- Windows-Toast-Benachrichtigungen sammeln (WinRT API)
- Polling alle 2 s, Duplikat-Erkennung pro Notification-ID
- Robustes Reconnect bei Fehlern, inklusive Workaround für sporadisches WinRT-„Falscher Parameter“
- TTS-Vorlesen mit pyttsx3 (offline, SAPI5)
- Global stumm schaltbar (🔇 Lautlos)
- Sanitizing nur für TTS (z. B. Entfernen nicht unterstützter Emojis), Emojis bleiben im Log sichtbar
- Längenlimit (Standard: MAX_CHARS = 800) mit sauberem Truncation-Suffix
- Schlankes GUI (PySide6)
- Live-Log mit Zeitstempel, App-Name, Warn-/Fehler-Stilen
- Buttons: Assistent starten/stoppen, In Tray, Beenden
- System-Tray-Integration (Öffnen/Beenden, Hintergrundbetrieb)
- Option: Discord ansagen/ignorieren (per Checkbox)
- Auch ohne GUI nutzbar (Konsolenmodus)
- Nicht-blockierend / Async
- asyncio + qasync für nahtlose Qt-Eventloop-Integration

🖼️ So sieht’s aus:

<img width="714" height="509" alt="image" src="https://github.com/user-attachments/assets/1d02cb27-7d37-4681-9b67-7cb9ec2c49ab" />

🔧 Technischer Überblick
- Backend: winrt (Windows Notifications), pyttsx3 (TTS), asyncio
- Frontend: PySide6, qasync
- Optionale Konsole: rich (falls installiert)
- Plattform: Windows 10/11 (erfordert Benachrichtigungs-Zugriff)

⚙️ Einstellungen (aktuell)
- Lautlos: Nur Loggen, kein TTS
- Discord: Ein/Aus (per Checkbox, intern über IGNORED_APPS)
- MAX_CHARS: Globale maximale Textlänge (Standard 800)
- POLL_INTERVAL: Abfrageintervall (Standard 2 s)

🔐 Datenschutz
- Keine Cloud: TTS läuft lokal (SAPI5/pyttsx3).
- Keine Telemetrie: Benachrichtigungen werden nur lokal verarbeitet, nicht gespeichert oder hochgeladen.

🧭 Roadmap / Offene Baustellen

Per-App-Regeln im UI
- Aktuell: feste Ignore-Liste (IGNORED_APPS), UI-Toggle nur für „Discord“.
- Geplant: Liste verwalten (hinzufügen/entfernen, persistente Speicherung).


Persistente Einstellungen
- MAX_CHARS, Lautlos-Status, Ignorier-Liste etc. in config.json oder Registry speichern.
- TTS-Optionen für Nutzer
- Stimme/Rate/Volume wählbar, Test-Button, Mehrsprachigkeit.


Benachrichtigungs-Filter
- Keywords/Regex, Nur Titel/Körper, App-Whitelist/Blacklist.
- Verlauf / Export
- Letzte N Benachrichtigungen, CSV/JSON-Export, Kopieren aus dem Log.


Hotkeys
- Globaler Shortcut für Stumm/Weiterlesen/Pause.


Robustheit / Kompatibilität
- Tests auf verschiedenen Windows-Builds/Sprachen; Edge-Cases bei besonderen Toast-Layouts.
- Besseres Handling von HTML/RTF-Content in Toasts (falls vorkommend).


Packaging
- Portable .exe mit PyInstaller, optional Code-Signing (Standard/EV).
- Autoupdate (später).


Barrierefreiheit im UI
- Kontraste, Schriftgrößen, Tastatur-Nutzung verbessern.
- Icon/Branding

🐞 Bekannte Einschränkungen
- Windows-only (nutzt WinRT-APIs).
- App-spezifische Parsing-Fallbacks: bewusst entfernt → generischer Extractor (Titel + Body). Manche Apps liefern minimalistische Toasts → es kann „ohne Text“ erscheinen.
- Keine Persistenz von Log/Settings zwischen Sessions (noch).
- Python 3.13.1

  
