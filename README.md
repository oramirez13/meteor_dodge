# Meteor Dodge

A survival game where you dodge falling meteors using the mouse. Built with pygame.

## Requirements

- Python 3.7+
- pygame

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd meteor_dodge

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python meteor_dodge.py
```

## Controls

| Input | Action |
|-------|--------|
| Mouse | Move the player ship |
| ESC | Quit game |
| SPACE / ENTER | Restart after game over |

## Features

- Mouse-controlled player with trail effect
- Progressive difficulty (speed and spawn rate increase)
- Score tracking with high score
- Lives system (3 lives)
- Invincibility frames after being hit
- Particle explosion effects
- Animated starfield background
- Level indicator

## How It Works

1. Move your mouse to dodge the falling meteors
2. Each meteor dodged gives bonus points
3. Time-based score increases every second
4. Difficulty increases every 100 points
5. Game ends when all 3 lives are lost

## Project Structure

```
meteor_dodge/
├── meteor_dodge.py    # Main game
├── requirements.txt   # Dependencies
├── .gitignore         # Excludes cache and venv
└── README.md          # This file
```
