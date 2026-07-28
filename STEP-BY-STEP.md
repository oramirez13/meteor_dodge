# Step by Step Guide - How to Play Meteor Dodge

## Prerequisites

- **Python 3.7+** installed on your system
- **Git** installed (or download the ZIP from GitHub)

Not sure if you have Python? Run `python --version` (or `python3 --version` on Linux/macOS).

---

## Linux / macOS

```bash
# 1. Clone the repository
git clone https://github.com/oramirez13/meteor_dodge.git
cd meteor_dodge

# 2. (Optional but recommended) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install the game dependencies
pip install -r requirements.txt

# 4. Run the game
python meteor_dodge.py

# 5. When done, deactivate the virtual environment
deactivate
```

---

## Windows 10 / 11

```cmd
REM 1. Install Python from https://www.python.org/downloads/
REM    IMPORTANT: check "Add Python to PATH" during installation

REM 2. Open Command Prompt or PowerShell and run:
git clone https://github.com/oramirez13/meteor_dodge.git
cd meteor_dodge

REM 3. (Optional) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

REM 4. Install dependencies
pip install -r requirements.txt

REM 5. Run the game
python meteor_dodge.py

REM 6. When done, deactivate
deactivate
```

---

## Controls

| Key              | Action                  |
| ---------------- | ----------------------- |
| Arrow keys / WASD| Move the player ship    |
| SPACE            | Shoot at meteors        |
| P                | Pause / Resume game     |
| ESC              | Quit game               |
| SPACE / ENTER    | Restart after game over |

---

## Alternative: Standalone Executable (No Python Required)

If you do not want to install Python, you can compile the game into a single executable file.

### On your own machine

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "MeteorDodge" --add-data "assets:assets" meteor_dodge.py
```

The executable will be in the `dist/` folder:
- **Linux/macOS**: `dist/MeteorDodge`
- **Windows**: `dist\MeteorDodge.exe`

### Sharing with friends

1. Zip the executable from `dist/`
2. Send it to them
3. They unzip and double-click to play (no Python or pygame needed)

**Note:** The executable is platform-specific. You must build it on the same OS where it will run.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip: command not found` | Install pip: `python -m ensurepip --upgrade` |
| `pygame not found` | Run `pip install -r requirements.txt` |
| `No module named pygame-ce` | Same as above |
| Images not loading | Make sure you are in the `meteor_dodge/` folder when running the game |
| Game runs too fast/slow | The game is locked at 60 FPS. Check your monitor refresh rate |
| Game window is black | Try updating your graphics drivers |
