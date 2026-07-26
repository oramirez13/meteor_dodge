# Meteor Dodge

A survival game where you dodge and shoot falling meteors across 5 unique levels. Built with pygame.

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

| Input              | Action                  |
| ------------------ | ----------------------- |
| Arrow keys / WASD  | Move the player ship    |
| SPACE              | Shoot at meteors        |
| ESC                | Quit game               |
| SPACE / ENTER      | Restart after game over |

## Level System

The game has **5 levels**. To advance to the next level you must meet **two conditions**:

1. Reach the required score for the current level
2. Survive for at least 60 seconds in the current level

| Level | Name     | Meteor Speed | Ammo Type      | Score to Advance |
| ----- | -------- | ------------ | -------------- | ---------------- |
| 1     | Nebula   | 3 - 5        | Normal (1 bullet) | 50            |
| 2     | Storm    | 4 - 7        | Double (2 bullets) | 150           |
| 3     | Belt     | 5 - 9        | Spread (3 bullets) | 300           |
| 4     | Supernova| 6 - 11       | Rapid (fast cooldown) | 500        |
| 5     | Warzone  | 4 - 8        | Spread (3 bullets) | Endless      |

Each level has its own background image. Level 5 introduces **enemy ships** that move, dodge, and shoot back at you.

## Features

- 5 unique levels with different backgrounds
- 4 ammo types that change per level:
  - **Normal**: single bullet straight up
  - **Double**: two parallel bullets
  - **Spread**: three bullets in a fan pattern
  - **Rapid**: single bullet with very fast fire rate
- Enemy ships in level 5 that shoot projectiles at the player
- Progress bar showing advancement toward the next level
- Level notification when advancing
- Keyboard-controlled player (arrows/WASD) with trail effect
- Destroy meteors for bonus points (15 pts vs 5 pts for dodging)
- Score tracking with high score
- Lives system (3 lives)
- Invincibility frames after being hit
- Particle explosion effects

## How It Works

1. Move your ship with arrow keys or WASD to dodge falling meteors
2. Press SPACE to shoot and destroy meteors for bonus points
3. Fill the progress bar by earning score AND surviving 60 seconds per level
4. When both conditions are met, advance to the next level with a new background and weapon
5. Survive the Warzone (level 5) against enemy ships
6. Game ends when all 3 lives are lost

## Project Structure

```
meteor_dodge/
├── meteor_dodge.py          # Main game
├── assets/images/           # Game images
│   ├── background_01.png    # Level 1 background
│   ├── background_02.png    # Level 2 background
│   ├── background_03.png    # Level 3 background
│   ├── background_04.png    # Level 4 background
│   ├── background_05.png    # Level 5 background
│   ├── player.png           # Player ship
│   └── meteor.png           # Meteor sprite
├── screenshots/             # Example screenshots
│   ├── meteor_dodge_01.png
│   └── meteor_dodge_02.png
├── requirements.txt         # Dependencies
├── .gitignore               # Excludes cache and venv
└── README.md                # This file
```
