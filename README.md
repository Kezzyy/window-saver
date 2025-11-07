# 🪟 Window Saver 5.3 — Shimatsu Edition

**Window Saver** is a lightweight PyQt6 utility that automatically restores window position and size on Linux desktops (X11 / Wayland-compatible).

Created by **Kezzy** as part of the **Shimatsu** ecosystem.

---

## ✨ Features

- Automatically repositions windows based on a defined layout  
- Auto-apply when a saved window is detected  
- System tray integration  
- Multilingual interface (English / Czech)  
- Persistent JSON configuration  
- Clean, minimal PyQt6 interface  

---

## 🧰 Requirements

- Linux system (KDE, GNOME, etc.)
- `wmctrl` installed (`sudo pacman -S wmctrl` or `sudo apt install wmctrl`)
- Python 3.10+
- PyQt6 (`pip install PyQt6`)

---

## ⚙️ Installation

```bash
git clone https://github.com/Kezzyy/window-saver.git
cd window-saver
pip install -r requirements.txt
python3 window_saver.py

🗣️ Languages

    🇬🇧 English (default)

    🇨🇿 Czech

    To change language, go to Settings → Language and restart the app to apply changes.

🧠 Customization

Default window position and size can be edited directly in the script:

DEFAULT_GAME_POS = [3482, 36]
DEFAULT_GAME_SIZE = [2428, 1405]

These define the default area used for converting 21:9 gameplay into a 16:9 stream view.
🌐 Links

    🌐 Shimatsu.eu

🎥 YouTube – KezzyOff

🎮 Twitch – KezzyOfficial
🪪 License

© 2025 Shimatsu — All rights reserved.
Part of the Shimatsu Projects suite.
Unauthorized redistribution or resale is prohibited.
⚙️ Developer Notes

Window Saver was designed for streamers, creators, and advanced Linux users who want consistent window positioning — ideal for ultra-wide setups or multi-monitor workflows.

Future roadmap ideas:

    Multiple layout profiles (Stream / Work / Gaming)

    Auto-detection of fullscreen apps

    Config export / import

    Native Wayland control (via KWin DBus)

🧾 Credits

Developed by Kezzy
Maintained under the Shimatsu ecosystem


---

## 📦 **requirements.txt**

PyQt6


---

## 🚫 **.gitignore**
