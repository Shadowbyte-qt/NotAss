# Notification Assistant.spec
# minimaler Build mit nur qwindows + qpng

import os
import sys
from PyInstaller.utils.hooks import collect_submodules
from PySide6.QtCore import QLibraryInfo, QLibraryInfo as QLI

block_cipher = None

app_name = "Notification Assistant"
script = "Notification Assistant.py"

# Qt-Pfade ermitteln (dynamisch, keine Hardcodes)
plugins_path = QLibraryInfo.path(QLI.PluginsPath)

datas = [
    ("icon.png", "."),  # App-Icon einbetten
]

binaries = [
    # Nur die wirklich benötigten Qt-Plugins:
    (os.path.join(plugins_path, "platforms", "qwindows.dll"), "PySide6/plugins/platforms"),
]

# Hinweis: qasync und winrt werden normal mitgezogen
hiddenimports = collect_submodules("qasync")

a = Analysis(
    [script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # explizit große, ungenutzte Qt-Module rauswerfen (Sicherheitsnetz)
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtCharts",
        "PySide6.QtPdf",
        "PySide6.QtSvg",
        "PySide6.QtNetworkAuth",
        "PySide6.QtDataVisualization",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DInput",
		"PySide6.QtQml",
        "PySide6.QtQmlModels",
        "PySide6.QtQmlMeta",
        "PySide6.QtQmlWorkerScript",
        "PySide6.QtQuick",
        "PySide6.QtOpenGL",
        "PySide6.QtCharts",
        "PySide6.QtSvg",
        "PySide6.QtPdf",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtNetworkAuth",
        "PySide6.QtDataVisualization",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DInput",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=app_name,
    icon="icon.png",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,      # unter Windows hat strip wenig Effekt
    upx=True,        # s. Abschnitt 3 für UPX
    console=False,    # Fenster-App
)

# Onefile
coll = COLLECT(exe, name=app_name)
