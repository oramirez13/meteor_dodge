# Meteor Dodge

A survival game where you dodge and shoot falling meteors. Built with pygame.

## Requirements

- Python 3.7+
- pygame

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd meteor_dodge

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python meteor_dodge.py
```

When you are done playing, deactivate the virtual environment:

```bash
deactivate
```

## Controls

| Input         | Action                  |
| ------------- | ----------------------- |
| Arrow keys / WASD | Move the player ship |
| SPACE         | Shoot at meteors        |
| ESC           | Quit game               |
| SPACE / ENTER | Restart after game over |

## Features

- Keyboard-controlled player (arrows/WASD) with trail effect
- Shooting system with cooldown (SPACE to shoot)
- Destroy meteors for bonus points (15 pts vs 5 pts for dodging)
- Progressive difficulty (speed and spawn rate increase)
- Score tracking with high score
- Lives system (3 lives)
- Invincibility frames after being hit
- Particle explosion effects
- Animated starfield background
- Level indicator

## How It Works

1. Move your ship with arrow keys or WASD to dodge falling meteors
2. Press SPACE to shoot and destroy meteors for bonus points
3. Time-based score increases every second
4. Difficulty increases every 100 points
5. Game ends when all 3 lives are lost

## Project Structure

```
meteor_dodge/
├── meteor_dodge.py       # Main game
├── assets/images/        # Game images
│   ├── background.png
│   ├── player.png
│   └── meteor.png
├── requirements.txt      # Dependencies
├── .gitignore            # Excludes cache and venv
└── README.md             # This file
```
