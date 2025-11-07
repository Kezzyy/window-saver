#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Saver 5.2 by Kezzy / Shimatsu Edition
--------------------------------------------
Aplikace pro automatické ukládání a obnovu pozic oken.

📁 Struktura:
window_saver.py
translations/
 ├── cs.json
 ├── en.json

📝 Jak přidat jazyk:
1. Zkopíruj en.json do nového souboru, např. fr.json
2. Uprav hodnoty dle potřeby
3. Po spuštění se jazyk objeví automaticky v nabídce
"""

import subprocess, json, os, sys, time, webbrowser, datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QListWidget,
    QPushButton, QLabel, QTextEdit, QMessageBox, QHBoxLayout,
    QSystemTrayIcon, QMenu, QComboBox
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

# --- Cesty ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATION_DIR = os.path.join(BASE_DIR, "translations")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

# --- Výchozí pozice/velikost ---
DEFAULT_GAME_POS = [3482, 36]
DEFAULT_GAME_SIZE = [2428, 1405]


# --- Pomocné funkce ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            try:
                return json.load(f)
            except Exception:
                return default
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def list_windows():
    try:
        output = subprocess.check_output(["wmctrl", "-lG"]).decode()
    except Exception:
        return []
    windows = []
    for line in output.strip().splitlines():
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        try:
            win_id, _, x, y, w, h, _, title = parts
            windows.append({
                "id": win_id,
                "id_dec": str(int(win_id, 16)),
                "title": title.strip(),
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h)
            })
        except Exception:
            continue
    return windows


def have_cmd(cmd):
    from shutil import which
    return which(cmd) is not None


def set_window_geometry(win):
    title = win.get("title", "?")
    xid_hex = win["id"]
    xid_dec = win.get("id_dec") or str(int(xid_hex, 16))
    X, Y, W, H = win["x"], win["y"], win["w"], win["h"]

    subprocess.run(["wmctrl", "-i", "-r", xid_hex, "-b", "remove,fullscreen"], check=False)
    subprocess.run(["wmctrl", "-i", "-r", xid_hex, "-b", "remove,maximized_vert,maximized_horz"], check=False)
    time.sleep(0.2)
    ok = False

    try:
        subprocess.run(["wmctrl", "-i", "-r", xid_hex, "-a"], check=False)
        subprocess.run(["wmctrl", "-i", "-r", xid_hex, "-e", f"0,{X},{Y},{W},{H}"], check=True)
        ok = True
    except:
        pass

    if not ok and have_cmd("xdotool"):
        subprocess.run(["xdotool", "windowactivate", xid_dec], check=False)
        subprocess.run(["xdotool", "windowsize", xid_dec, str(W), str(H)], check=False)
        subprocess.run(["xdotool", "windowmove", xid_dec, str(X), str(Y)], check=False)
        ok = True

    msg = f"✅ {title} → {W}x{H} @ {X},{Y}" if ok else f"❌ {title} – změna selhala."
    print(msg)
    return msg


def load_translations():
    langs = {}
    if not os.path.exists(TRANSLATION_DIR):
        os.makedirs(TRANSLATION_DIR)
    for file in os.listdir(TRANSLATION_DIR):
        if file.endswith(".json"):
            code = file.split(".")[0]
            langs[code] = load_json(os.path.join(TRANSLATION_DIR, file), {})
    return langs


# --- Hlavní třída ---
class WindowSaver(QWidget):
    VERSION = "5.2"
    AUTHOR = "Kezzy"
    PROJECT = "Shimatsu"

    def __init__(self, tray_icon):
        super().__init__()
        self.tray_icon = tray_icon
        self.translations = load_translations()
        self.settings = load_json(SETTINGS_PATH, {"lang": "en"})
        self.lang_code = self.settings.get("lang", "en")
        self.lang = self.translations.get(self.lang_code, self.translations.get("en", {}))

        self.setWindowTitle(f"Window Saver {self.VERSION} by {self.AUTHOR}")
        self.setWindowIcon(QIcon.fromTheme("preferences-system-windows"))

        self.tabs = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.active_tab = QWidget()
        self.saved_tab = QWidget()
        self.settings_tab = QWidget()
        self.about_tab = QWidget()

        self.setup_ui()
        self.refresh_active()
        self.refresh_saved()

        self._applied = set()
        self.watcher_timer = QTimer()
        self.watcher_timer.timeout.connect(self.check_auto_apply)
        self.watcher_timer.start(3000)

    def t(self, key):
        return self.lang.get(key, f"[{key}]")

    def setup_ui(self):
        # Vyčištění duplikátů
        try:
            for btn in [getattr(self, n) for n in ("refresh_btn", "save_btn", "apply_btn", "delete_btn") if hasattr(self, n)]:
                btn.clicked.disconnect()
        except Exception:
            pass

        self.tabs.clear()

        # Aktivní okna
        a_layout = QVBoxLayout(self.active_tab)
        self.active_label = QLabel(self.t("active_windows"))
        self.active_list = QListWidget()
        self.refresh_btn = QPushButton(self.t("refresh"))
        self.save_btn = QPushButton(self.t("save_selected"))
        a_layout.addWidget(self.active_label)
        a_layout.addWidget(self.active_list)
        a_layout.addWidget(self.refresh_btn)
        a_layout.addWidget(self.save_btn)

        # Uložené
        s_layout = QVBoxLayout(self.saved_tab)
        s_layout.addWidget(QLabel(self.t("saved_configs")))
        self.saved_list = QListWidget()
        self.apply_btn = QPushButton(self.t("apply_selected"))
        self.delete_btn = QPushButton(self.t("delete_selected"))
        hl = QHBoxLayout()
        hl.addWidget(self.apply_btn)
        hl.addWidget(self.delete_btn)
        s_layout.addWidget(self.saved_list)
        s_layout.addLayout(hl)

        # Nastavení
        set_layout = QVBoxLayout(self.settings_tab)
        set_layout.addWidget(QLabel(self.t("lang_label")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(sorted(self.translations.keys()))
        self.lang_combo.setCurrentText(self.lang_code)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        set_layout.addWidget(self.lang_combo)

        # O aplikaci
        ab_layout = QVBoxLayout(self.about_tab)
        self.about_label = QLabel(
            self.t("about_html").format(version=self.VERSION, author=self.AUTHOR)
        )
        self.about_label.setWordWrap(True)
        ab_layout.addWidget(self.about_label)

        # Tlačítka odkazy
        web_row = QHBoxLayout()
        btn_web = QPushButton("🌐 shimatsu.eu")
        btn_yt = QPushButton("▶️ YouTube")
        btn_twitch = QPushButton("🎮 Twitch")
        web_row.addWidget(btn_web)
        web_row.addWidget(btn_yt)
        web_row.addWidget(btn_twitch)
        ab_layout.addLayout(web_row)

        current_year = datetime.datetime.now().year
        rights = QLabel(f"© {current_year} {self.PROJECT} | Všechna práva vyhrazena.")
        rights.setStyleSheet("font-size: 10px; color: gray; margin-top: 8px;")
        ab_layout.addWidget(rights)

        btn_web.clicked.connect(lambda: webbrowser.open("https://shimatsu.eu"))
        btn_yt.clicked.connect(lambda: webbrowser.open("https://www.youtube.com/@kezzyoff"))
        btn_twitch.clicked.connect(lambda: webbrowser.open("https://twitch.tv/kezzyofficial"))

        # Tabs
        self.tabs.addTab(self.active_tab, self.t("tab_active"))
        self.tabs.addTab(self.saved_tab, self.t("tab_saved"))
        self.tabs.addTab(self.settings_tab, self.t("tab_settings"))
        self.tabs.addTab(self.about_tab, self.t("tab_about"))

        # Log
        if not hasattr(self, "log"):
            self.log = QTextEdit()
            self.log.setReadOnly(True)
            layout = self.layout()
            layout.addWidget(QLabel("Log:"))
            layout.addWidget(self.log)

        # Signály
        self.refresh_btn.clicked.connect(self.refresh_active)
        self.save_btn.clicked.connect(self.save_selected)
        self.apply_btn.clicked.connect(self.apply_selected)
        self.delete_btn.clicked.connect(self.delete_selected)

    def change_language(self, lang_code):
        self.lang_code = lang_code
        self.lang = self.translations.get(lang_code, self.translations.get("en", {}))
        save_json(SETTINGS_PATH, {"lang": lang_code})
        self.log.append(f"{self.t('lang_switched')} {lang_code.upper()}")
        self.setup_ui()
        QMessageBox.information(
        self,
        "Language changed",
        "Restart the application to fully apply language changes."
)

    def refresh_active(self):
        self.active_list.clear()
        for w in list_windows():
            self.active_list.addItem(f"{w['title']} ({w['w']}x{w['h']} @ {w['x']},{w['y']})")

    def refresh_saved(self):
        self.saved_list.clear()
        for win in load_json(CONFIG_PATH, []):
            self.saved_list.addItem(f"{win['title']} ({win['w']}x{win['h']} @ {win['x']},{win['y']})")

    def save_selected(self):
        idx = self.active_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Error", self.t("err_no_window"))
            return
        all_windows = list_windows()
        if idx >= len(all_windows):
            return
        win = all_windows[idx]
        data = load_json(CONFIG_PATH, [])
        if not any(w["title"] == win["title"] for w in data):
            data.append(win)
            save_json(CONFIG_PATH, data)
            self.refresh_saved()
            QMessageBox.information(self, "OK", f"{self.t('saved')} {win['title']}")
        else:
            QMessageBox.information(self, "Info", self.t("already_saved"))

    def apply_selected(self):
        idx = self.saved_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Error", self.t("err_no_saved"))
            return
        data = load_json(CONFIG_PATH, [])
        if idx >= len(data):
            return
        saved = data[idx]
        open_windows = list_windows()
        target = next((w for w in open_windows if saved["title"] in w["title"]), None)
        if target:
            msg = set_window_geometry({
                **saved, "id": target["id"], "id_dec": target["id_dec"],
                "x": DEFAULT_GAME_POS[0], "y": DEFAULT_GAME_POS[1],
                "w": DEFAULT_GAME_SIZE[0], "h": DEFAULT_GAME_SIZE[1]
            })
            self.log.append(msg)
        else:
            QMessageBox.warning(self, "Error", self.t("err_not_running"))

    def delete_selected(self):
        idx = self.saved_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Error", self.t("err_no_saved"))
            return
        data = load_json(CONFIG_PATH, [])
        if idx < len(data):
            removed = data.pop(idx)
            save_json(CONFIG_PATH, data)
            self.refresh_saved()
            QMessageBox.information(self, "Deleted", f"{self.t('deleted')} {removed['title']}")

    def check_auto_apply(self):
        saved_data = load_json(CONFIG_PATH, [])
        if not saved_data:
            return
        open_list = list_windows()
        for saved in saved_data:
            match = next((w for w in open_list if saved["title"] in w["title"]), None)
            if match and saved["title"] not in self._applied:
                msg = set_window_geometry({
                    **saved, "id": match["id"], "id_dec": match["id_dec"],
                    "x": DEFAULT_GAME_POS[0], "y": DEFAULT_GAME_POS[1],
                    "w": DEFAULT_GAME_SIZE[0], "h": DEFAULT_GAME_SIZE[1]
                })
                self.log.append(f"Auto-apply → {msg}")
                self._applied.add(saved["title"])

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            self.t("tray_title"),
            self.t("tray_running"),
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


# --- Main ---
if __name__ == "__main__":
    app = QApplication([])
    tray = QSystemTrayIcon(QIcon.fromTheme("preferences-system-windows"))
    menu = QMenu()
    show_action = QAction("Open")
    quit_action = QAction("Quit")
    menu.addAction(show_action)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.setToolTip("Window Saver 5.2 by Kezzy / Shimatsu")
    tray.show()

    window = WindowSaver(tray)
    tray.activated.connect(lambda r: window.show() if not window.isVisible() else window.hide())
    show_action.triggered.connect(lambda: window.show())
    quit_action.triggered.connect(lambda: (tray.hide(), app.quit()))

    window.show()
    sys.exit(app.exec())
