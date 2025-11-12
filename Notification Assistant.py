import sys
import re
import html
import asyncio
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
)
from PySide6.QtGui import QIcon, QAction, QTextCursor
from PySide6.QtCore import Qt, Slot, QTimer
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.png")

from qasync import QEventLoop, asyncSlot
import tts_watcher


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notification Assistant")
        self.resize(720, 480)

        # ----- Widgets
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-size: 11pt; font-family: Calibri, monospace;")

        self.chk_discord = QCheckBox("Discord")
        self.chk_discord.setChecked(True)  # standardmäßig AN


        self.chk_mute = QCheckBox("Lautlos")   # << NEU
        self.chk_mute.setChecked(False)

        self.btn_start = QPushButton("✍️ Assistent starten")
        self.btn_stop = QPushButton("✋ Assistent stoppen")
        self.btn_stop.setEnabled(False)
        self.btn_quit = QPushButton("👏 Beenden")
        self.btn_minimize = QPushButton("👇 In Tray")

        # Layouts
        central = QWidget()
        vlay = QVBoxLayout(central)
        vlay.addWidget(self.text)

        # Checkbox-Zeile
        lay_opts = QHBoxLayout()
        lay_opts.addWidget(self.chk_discord)
        lay_opts.addWidget(self.chk_mute)
        lay_opts.addStretch(1)
        vlay.addLayout(lay_opts)

        # Button-Zeile
        hlay = QHBoxLayout()
        hlay.addWidget(self.btn_start)
        hlay.addWidget(self.btn_stop)
        hlay.addWidget(self.btn_minimize)
        hlay.addWidget(self.btn_quit)
        vlay.addLayout(hlay)

        self.setCentralWidget(central)

        # ----- Signals
        self.btn_start.clicked.connect(self.start_watcher)
        self.btn_stop.clicked.connect(self.stop_watcher)
        self.chk_discord.toggled.connect(self.on_toggle_discord)
        self.chk_mute.toggled.connect(self.on_toggle_mute)
        self.btn_quit.clicked.connect(QApplication.instance().quit)
        self.btn_minimize.clicked.connect(self.hide_to_tray)

        # ----- System-Tray
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(ICON_PATH))
        menu = QMenu()
        act_show = QAction("Öffnen", self, triggered=self.show_window)
        act_quit = QAction("Beenden", self, triggered=QApplication.instance().quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.setWindowIcon(QIcon(ICON_PATH))

        self._watch_task = None

        # Initialzustände an Backend übergeben
        tts_watcher.set_ignore_discord(self.chk_discord.isChecked())
        tts_watcher.set_mute(self.chk_mute.isChecked())

        # Auto-Start nach 2 Sekunden
        self.log("👉 Starte…")
        QTimer.singleShot(2000, self.start_watcher)

    # -------------------------------------------------
    @Slot()
    def show_window(self):
        self.showNormal()
        self.activateWindow()

    @Slot()
    def hide_to_tray(self):
        self.hide()
        self.tray.showMessage(
            "TTS",
            "Läuft im Hintergrund…",
            QSystemTrayIcon.Information,
            2000,
        )

    # -------------------------------------------------
    def _append_html(self, html_text: str):
        self.text.append(html_text)
        self.text.moveCursor(QTextCursor.End)
        self.text.ensureCursorVisible()

    def log(self, msg: str):
        safe = html.escape(msg)
        m = re.match(r"^→\s*(\d{2}:\d{2}:\d{2})\s*\[([^\]]+)\]:\s*$", msg)
        if m:
            ts = html.escape(m.group(1))
            app = html.escape(m.group(2))
            line = (
                f'<span style="color:gold; font-size:11pt;">→</span> '
                f'<span style="color:lightgreen;">{ts}</span> '
                f'<span style="color:turquoise;">[{app}]</span>'
            )
            self._append_html(line)
            return

        if msg.startswith("⚠️"):
            self._append_html(f'<span style="color:khaki; font-size:12pt;">{safe}</span>')
            return
        if msg.startswith("❌"):
            self._append_html(
                f'<span style="color:salmon; font-size:12pt; font-weight:600;">{safe}</span>'
            )
            return

        self._append_html(f'<span style="color:white; font-size:14pt;">{safe}</span>')

    # -------------------------------------------------
    @Slot(bool)
    def on_toggle_discord(self, checked: bool):
        # Invertierte Logik: checked=True → NICHT ignorieren
        tts_watcher.set_ignore_discord(not checked)
        if checked:
            self.log("🔊 Discord wird vorgelesen.")
        else:
            self.log("🔇 Discord bleibt stumm")


    @Slot(bool)
    def on_toggle_mute(self, checked: bool):
        tts_watcher.set_mute(checked)
        if checked:
            self.log("🔇 Lautlos - nur Nachrichten")
        else:
            self.log("🔊 Ton aktiviert")

    # -------------------------------------------------
    @asyncSlot()
    async def start_watcher(self):
        if self._watch_task and not self._watch_task.done():
            return
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        # aktuellen Status sicherheitshalber setzen
        tts_watcher.set_ignore_discord(self.chk_discord.isChecked())
        tts_watcher.set_mute(self.chk_mute.isChecked())

        async def run():
            try:
                await tts_watcher.watch_notifications(poll_interval=2.0, log=self.log)
            except asyncio.CancelledError:
                self.log("Assistent gestoppt.")
            except Exception as e:
                self.log(f"❌ Assistent-Fehler: {e}")

        self._watch_task = asyncio.create_task(run())

    @asyncSlot()
    async def stop_watcher(self):
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        self._watch_task = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    # -------------------------------------------------
    def closeEvent(self, event):
        event.ignore()
        self.hide_to_tray()


# -------------------------------------------------
def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    win = MainWindow()
    win.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
