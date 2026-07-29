# Meteor Dodge Documentation

The project is a survival game built with **pygame** (a library for creating games in Python). The player controls a ship that must dodge and destroy meteors falling from the sky. It has 5 levels, each with different difficulty, visual background, and weapon type.

---

## 1. Imports (lines 14-19)

```python
import pygame    # Main game library (window, images, sound, events)
import random    # For generating random numbers (positions, speeds, colors)
import sys       # To exit the game with sys.exit()
import math      # For trigonometric calculations (explosion particle angles)
import os        # To build file paths that work on any operating system
import json      # To encode score data as JSON for the web server
import audio     # Audio manager: loads and plays sound effects + music
```

---

## 2. Global Constants (lines 24-57)

These are fixed values that do not change during the game. They are in uppercase by convention.

- **Window**: 800x600 pixels, 60 frames per second (FPS)
- **Colors**: RGB tuples (red, green, blue). Example: `RED = (220, 50, 50)`
- **Player**: Size 40px, speed 8px per frame, 3 initial lives
- **Meteors**: Minimum 8 at start, maximum 60 on screen
- **Score**: +1 per second alive, +5 for dodging, +15 for destroying
- **Bullets**: 4px wide, 12px tall, speed 12px per frame
- **Assets**: `assets/images/` folder where all images are stored

---

## 3. Level System (lines 67-126)

This is a **dictionary** where each key (1, 2, 3, 4, 5) is a level. Each level has:

| Field                                   | What it means                                                 |
| --------------------------------------- | ------------------------------------------------------------- |
| `name`                                  | Name displayed on screen                                      |
| `background`                            | Background image file for that level                          |
| `meteor_min_speed` / `meteor_max_speed` | Speed range for meteors                                       |
| `spawn_rate`                            | How many frames between meteor spawns (lower = more frequent) |
| `ammo_type`                             | Ammo type: normal, double, spread, rapid                      |
| `cooldown`                              | Frames of wait between each shot                              |
| `score_to_advance`                      | Score needed to advance to the next level                     |
| `has_enemy_ships`                       | Whether enemy ships appear (level 5 only)                     |
| `ship_spawn_rate`                       | How many frames between enemy ship spawns (level 5)           |

The difficulty progression:

- **Level 1 (Nebula)**: Slow meteors (3-5), single shot, score 50
- **Level 2 (Storm)**: Medium meteors (4-7), double shot, score 150
- **Level 3 (Belt)**: Fast meteors (5-9), spread shot, score 300
- **Level 4 (Supernova)**: Very fast meteors (6-11), rapid fire, score 500
- **Level 5 (Warzone)**: Enemy ships + meteors, final endless level

---

## 4. `load_image` Function (lines 134-168)

Loads an image from disk and prepares it for use in the game.

**Parameters:**

- `filename`: File name (e.g., "player.png")
- `size`: Optional tuple to resize (e.g., (40, 40))
- `has_alpha`: `True` if it has transparency (PNG), `False` if not (background JPGs)

**What it does step by step:**

1. `os.path.join` builds the full path: `"assets/images/player.png"`
2. `pygame.image.load` reads the file from disk
3. If it fails, prints a clear error message and closes the game
4. `convert_alpha()` or `convert()` optimizes the image so pygame can draw it fast
5. `transform.scale` resizes it if requested

---

## 5. `Player` Class (lines 176-249)

Represents the player's ship.

### `__init__` (line 179)

Starts at the center-bottom of the screen (x=400, y=520). Has 3 lives, not invincible at the start, and has a `trail` list for the trail effect.

### `update` (line 190)

Every frame:

1. Saves the current position to `trail` (keeps a maximum of 10 positions)
2. Reads the pressed keys and moves the ship 8px in that direction
3. Limits the position so it does not leave the screen (lines 208-209)
4. If invincible, reduces the timer. When it reaches 0, stops being invincible

### `hit` (line 217)

When a meteor hits the ship:

1. If already invincible, does nothing (returns False)
2. Otherwise, loses 1 life, becomes invincible for 90 frames (1.5 seconds)
3. Returns True so the game knows a life was lost

### `draw` (line 232)

Draws:

1. The trail: Blue rectangles that grow from small to large, following the last positions
2. The ship: Draws the image centered at (x, y). Blinks when invincible (appears and disappears alternately)

---

## 6. `Bullet` Class (lines 257-298)

Represents a bullet fired by the player.

### `__init__` (line 264)

Receives position (x, y) and optionally horizontal speed (`vx`) and vertical speed (`vy`). Defaults to `vx=0` and `vy=-12` (upward).

### `update` (line 275)

Moves the bullet by adding `vx` to x and `vy` to y. This allows bullets to move in any direction, not just upward.

### `is_off_screen` (line 280)

Returns `True` if the bullet has left the screen in any direction (top, bottom, left, right).

### `draw` (line 296)

Draws a yellow rectangle.

---

## 7. `Meteor` Class (lines 306-357)

Represents a falling meteor.

### `__init__` (line 309)

1. Random size between 15 and 35 pixels
2. Random X position (within the screen)
3. Y position = -size (appears just above the screen)
4. Random speed within the current level's range
5. Random rotation and rotation speed
6. Picks a random image from the list and scales it to its size

### `update` (line 323)

Moves the meteor downward by adding `self.speed` to Y. Updates rotation. Saves positions for the trail.

### `draw` (line 342)

Draws:

1. Trail of gray rectangles
2. The meteor image rotated with `pygame.transform.rotate`. After rotating, it is recentered because the bounding rectangle changes size

---

## 8. `EnemyShip` Class (lines 365-427)

Enemy ship that appears only in level 5.

### `__init__` (line 369)

Similar to the player but:

- Appears at the top of the screen (y = -size)
- Moves downward at speed 2-4
- Picks a random horizontal direction (-1 or +1, left or right)
- Has a `shoot_timer` random (30-90 frames) to shoot

### `update` (line 382)

Moves downward and laterally. When it hits an edge, reverses direction (bounces).

### `should_shoot` (line 397)

When the timer reaches 0, returns `True` (should shoot) and resets the timer to 60-120 frames.

### `draw` (line 414)

Draws the player's image **flipped vertically** with `pygame.transform.flip(image, False, True)` so it points downward. The trail is red (vs blue for the player) to distinguish them.

---

## 9. `EnemyBullet` Class (lines 435-464)

Projectile fired by enemy ships. Same as `Bullet` but:

- Moves **downward** (`self.speed = 6`, no negative vy)
- Is red in color (vs yellow for the player)

---

## 10. `Explosion` Class (lines 472-515)

Visual effect when something explodes.

### `__init__` (line 475)

Creates 15 particles. Each particle has:

- Initial position (x, y) of the destroyed object
- Random velocity in any angle (`vx`, `vy` calculated with `cos` and `sin`)
- Random size (2-6px)
- Random color from red, orange, yellow, and white

### `update` (line 495)

Moves each particle according to its velocity and reduces its size by 1 pixel per frame. When size reaches 0, the particle disappears.

### `is_alive` (line 513)

Returns `True` while the `lifetime` (30 frames = 0.5 seconds) has not run out.

---

## 11. `LevelNotification` Class (lines 523-562)

Shows a temporary message when advancing to a new level.

- Lasts 2 seconds (120 frames at 60fps)
- Shows "LEVEL COMPLETE" in yellow
- Below it shows "Entering: [new level name]" in white
- Semi-transparent black background

---

## 12. `Game` Class - The Main Controller (lines 570-1095)

This is the largest class. It coordinates everything.

### `__init__` (line 573) - Initialization

1. **pygame.init()**: Starts all pygame modules (window, sound, keyboard, etc.)
2. **audio.init()**: Initializes all sound effects (must be called after pygame.init so the mixer is ready)
3. **Creates the window**: 800x600 pixels
3. **Creates the clock**: Controls 60 FPS
4. **Creates 3 fonts**: For large (48), medium (28), and small (20) text
5. **Loads images**:
   - Player ship image (40x40)
   - Enemy ship image (same as player, will be flipped when drawn)
   - Meteor image
   - Backgrounds for all 5 levels (stored in `self.backgrounds` dictionary)
6. **Creates empty lists**: For meteors, bullets, enemy ships, enemy bullets, explosions
7. **Control variables**: score, high_score, game_over, frame_count, current_level, etc.
8. **Initial spawn**: Creates 8 slow meteors (speed 1-3) at start
9. **audio.play_level_music(1)**: Starts the background music for Level 1 (Nebula)

### `shoot` (line 666) - Shooting System

Reads the current level's ammo type and creates different bullets:

- **normal**: 1 bullet straight up
- **double**: 2 parallel bullets 10px apart
- **spread**: 3 bullets in a fan (one straight, one with vx=-3, one with vx=+3)
- **rapid**: 1 bullet straight up but with only 5 frames cooldown (vs 15 normal)

After shooting, activates the cooldown based on the level. It also plays the `laser.wav` sound effect (if the file is available).

### `handle_events` (line 708) - User Input

Processes pygame events:

- `QUIT`: Closes the window
- `ESCAPE`: Closes the game
- `SPACE` on game over: Restarts (plays click sound if available)
- `P`: Toggles pause with a pause sound effect (only when not game over)
- `SPACE` while playing: Shoots

### `check_level_advance` (line 728) - Level Advancement

Checks if the player meets both conditions:

1. `level_score >= score_to_advance` (enough score in this level)
2. `seconds_in_level >= 60` (survived more than 1 minute)

If both are met:

1. Increments `current_level`
2. Resets `level_score` and `level_timer` to 0
3. Clears enemy ships and enemy bullets
4. Shows the notification for the new level
5. Plays the `level_up.wav` sound effect
6. Fades out the current music and starts the new level's music track

### `update` (line 758) - Game State Update

If the game is paused (`self.paused == True`), it returns immediately without updating anything. This freezes all objects in place.

This is the heart of the game. Every frame it:

1. **Score**: If 1 second has passed (60 frames), adds 1 point to total score and level score
2. **Level advance**: Calls `check_level_advance()`
3. **Meteor spawning**: According to the level's `spawn_rate`
4. **Enemy ship spawning**: Level 5 only, every `ship_spawn_rate` frames
5. **Shoot cooldown**: Reduces the timer by 1
6. **Update player**: Reads keys and moves
7. **Update bullets**: Moves each bullet and removes those that left the screen
8. **Update enemy ships**: Moves them, and if `should_shoot()` returns True, creates an `EnemyBullet`
9. **Update meteors**: Moves and removes those that left the screen
10. **Bullet vs meteor collision**: If a bullet rectangle touches a meteor rectangle:
    - Creates explosion
    - Plays a random explosion sound variant (one of `explosion.wav`, `explosion2.wav`, `explosion3.wav`)
    - Removes both
    - Adds 15 points
11. **Bullet vs enemy ship collision**: Same but adds 30 points (x2), plays `enemy_explosion.wav`
12. **Player vs meteor collision**: If they touch, the player loses 1 life, plays `hit.wav`. If it reaches 0, game over: plays `game_over.wav`, stops music, and plays `highscore.wav` if a new record was set
13. **Player vs enemy ship collision**: Same audio behavior as with meteors
14. **Player vs enemy bullet collision**: Same audio behavior
15. **Update explosions**: Moves particles and removes dead ones
16. **Update notification**: If it exists, reduces timer and removes it when expired

### `draw_hud` (line 913) - Heads-Up Display

Draws game information on screen:

- **Score** (top-left, white)
- **High Score** (top-right, yellow)
- **Lives** (left, green)
- **Level + name** (right, blue)
- **Weapon + type** (left, purple)
- **Time** in the current level (right, gray)
- **Progress bar** (bottom-center): Shows how close the player is to advancing to the next level. Changes from yellow to green when ready
- **Pause overlay** (when paused): Darkens the screen with a semi-transparent black layer and displays "PAUSED" in yellow with "Press P to continue" hint

### `run` (line 1046) - Main Game Loop

The loop that keeps the game running:

```
while running:
    1. handle_events()    -> Process keyboard/close window
    2. update()           -> Move everything, detect collisions, update score
    3. Draw in order:
       a. Background
       b. Meteors
       c. Enemy ships
       d. Player bullets
       e. Enemy bullets
       f. Explosions
       g. Player
       h. HUD
       i. Level notification
       j. Game over (if applicable)
    4. pygame.display.flip() -> Show everything on screen
    5. clock.tick(60)     -> Wait to maintain 60 FPS
```

The **drawing order** matters: what is drawn first ends up behind. The player is drawn after meteors so it appears "on top" of them.

---

## 13. Entry Point (lines 1102-1104)

```python
if __name__ == "__main__":
    game = Game()    # Creates a game instance (starts pygame, loads images)
    game.run()       # Runs the main loop
```

`__name__ == "__main__"` checks that the file is being executed directly (not imported from another file). Only in that case does it create and run the game.

---

## 16. Online Scoreboard (Laravel)

The game can submit scores to a Laravel web server that stores them in a MySQL database.

### In the game (meteor_dodge.py)

The `send_score_to_server()` method is called automatically inside `restart()`. It gathers the final score, level reached, and time survived, then sends a POST request (JSON) to `http://localhost:8000/scores`.

The HTTP request uses `urllib.request` from Python's standard library. If the server is offline, the exception is silently ignored so the game continues to work without internet.

### In the server (meteor_dodge_site)

The Laravel app exposes:

- `GET /` - Home page with top scores
- `POST /scores` - Accepts and validates a score JSON payload
- `GET /leaderboard` - Shows the full leaderboard

The `ScoreController::store()` method validates input (player_name: alphanumeric + spaces/hyphens/underscores, score: 0-999999) and returns `{"message":"Score saved successfully","id":<id>}` with HTTP 201 on success.

## Complete Game Flow

1. You run `python meteor_dodge.py`
2. An 800x600 window is created
3. All images and sound effects are loaded; Level 1 music starts playing
4. Starts at **Level 1 (Nebula)** with a dark blue background and slow meteors
5. Every second you earn 1 point. Shooting plays a laser sound. Destroying meteors plays an explosion sound
6. When you reach 50 points AND have been alive for 60+ seconds, you advance to **Level 2 (Storm)** with a level-up sound and new music
7. The background changes, meteors move faster, and you now have **double shot**
8. Progressively until **Level 5 (Warzone)** where enemy ships appear with their own laser sounds
9. Taking damage plays a hit sound. If you lose all 3 lives, the game over sound plays, music fades out, and if you set a new record, the highscore sound plays
10. Press SPACE to restart from Level 1 with the Nebula music again

---

## 14. Pause System

Added to allow players to temporarily stop the game without losing progress.

### Implementation (4 modifications to the Game class)

**1. `__init__` - New variable:**

```python
self.paused = False
```

A boolean flag that tracks whether the game is paused. Starts as `False` (not paused).

**2. `handle_events` - New key press:**

```python
if event.key == pygame.K_p:
    if not self.game_over:
        self.paused = not self.paused
    return
```

When the player presses P and the game is not over, it flips the `paused` flag. The `return` prevents any other action from triggering on the same key press.

**3. `update` - Early return when paused:**

```python
if self.paused:
    return
```

If paused, the entire game logic (movement, collisions, spawning, scoring) is skipped. Objects freeze in place.

**4. `draw_hud` - Visual overlay:**

- Creates a semi-transparent black surface covering the whole screen
- Draws "PAUSED" in yellow centered on screen
- Draws "Press P to continue" in white below it
- The overlay is drawn AFTER all game objects but BEFORE game over screen (so the game behind is visible but dimmed)

---

## 15. Packaging with PyInstaller

PyInstaller bundles the Python interpreter, pygame, and all game assets into a single executable file. This lets users run the game without installing any dependencies.

### Build command

**Linux / macOS:**

```bash
pyinstaller --onefile --windowed --name "MeteorDodge" --add-data "assets:assets" meteor_dodge.py
```

**Windows (PowerShell or CMD):**

```cmd
pyinstaller --onefile --windowed --name "MeteorDodge" --add-data "assets;assets" meteor_dodge.py
```

### Flag explanation

| Flag                         | Purpose                                                                                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--onefile`                  | Creates a single executable file (vs a folder with many files)                                                                                              |
| `--windowed`                 | Prevents a terminal/console window from opening when the game launches                                                                                      |
| `--name "MeteorDodge"`       | Name of the output executable                                                                                                                               |
| `--add-data "assets:assets"` | Bundles the assets/images folder inside the executable so images are available at runtime (Linux/macOS). On Windows use `;` as separator: `"assets;assets"` |

### How it works

1. PyInstaller analyzes `meteor_dodge.py` to find all imported modules (pygame, audio, random, sys, math, os)
2. Copies those modules and the Python interpreter into a package
3. Compresses everything and appends it to a bootloader executable
4. When run, the bootloader extracts the modules to a temporary directory and launches the game

### Output

```
dist/
  MeteorDodge          # ~73 MB standalone executable (Linux)
  MeteorDodge.exe      # ~73 MB standalone executable (Windows)
build/                 # Temporary build files (safe to delete)
MeteorDodge.spec       # Build configuration (can be reused with: pyinstaller MeteorDodge.spec)
```

**Note:** The executable is platform-specific. You must build it on the same OS where it will run. A Linux build will not run on Windows and vice versa.

**Note:** The `--add-data "assets:assets"` flag bundles the entire `assets/` folder, which now includes both `images/` and `sounds/`. No additional flags are needed for audio support.

---

## 17. Audio System (`audio.py`)

The audio system is implemented in a separate file `audio.py` and provides sound effects and background music for the game.

### Architecture

```
audio.py
  ├── _load_sound()       -> Loads a single WAV/MP3 as a Sound object
  ├── init()              -> Loads ALL sound effects (call after pygame.init())
  ├── play_explosion()    -> Plays a random explosion variant
  ├── play_music()        -> Loads and plays an OGG music track
  ├── play_level_music()  -> Plays the track for a given level (1-5)
  ├── stop_music()        -> Fades out current music
  └── stop_music_immediate() -> Stops music instantly
```

### Why a separate file

- Keeps the main game file (`meteor_dodge.py`) focused on game logic
- All audio code is centralized, making it easy to add or modify sounds
- The module can be imported with a simple `import audio`

### Initialization order

```python
import audio              # 1. Import module (variables are None)
pygame.init()             # 2. Start pygame (includes mixer)
audio.init()              # 3. Load all sounds (mixer is now ready)
```

This order is important. Calling `pygame.mixer.Sound()` before `pygame.init()` would crash because the mixer is not running.

### Error handling

Each sound is loaded inside a `try/except` block. If a file is missing or corrupted, a warning is printed and the variable is set to `None`. The game checks `if audio.laser:` before playing, so missing files do not cause crashes.

```python
if audio.laser:
    audio.laser.play()
```

### Volume levels

Each sound has a predefined volume to create a balanced mix:

| Sound              | Volume |
| ------------------ | ------ |
| laser              | 0.15   |
| explosion variants | 0.40   |
| hit                | 0.50   |
| game_over          | 0.60   |
| level_up           | 0.50   |
| enemy_laser        | 0.20   |
| enemy_explosion    | 0.40   |
| highscore          | 0.50   |
| Background music   | 0.30   |

### Explosion variants

Three explosion sound files (`explosion.wav`, `explosion2.wav`, `explosion3.wav`) are loaded. Each time an explosion occurs, `random.choice()` picks one at random. This prevents the player from hearing the exact same sound every time, making the game feel more natural.

```python
explosion_variants = [s for s in [explosion, explosion2, explosion3] if s is not None]

def play_explosion():
    if explosion_variants:
        random.choice(explosion_variants).play()
```

### Music by level

Each level has a dedicated music track that matches its theme:

| Level | Name      | Music File    | Source                  |
| ----- | --------- | ------------- | ----------------------- |
| 1     | Nebula    | `level1.ogg`  | Juhani Junkala (CC0)    |
| 2     | Storm     | `level2.ogg`  | Juhani Junkala (CC0)    |
| 3     | Belt      | `level3.ogg`  | accion.ogg              |
| 4     | Supernova | `level4.ogg`  | Juhani Junkala (CC0)    |
| 5     | Warzone   | `level5.ogg`  | boss theme.ogg          |

When the player advances to a new level, the current music fades out over 500ms and the new level's track starts. On game over, the music fades out. On restart, it returns to Level 1 music.

### Sound events summary

| Event                    | Sound              | Priority |
| ------------------------ | ------------------ | -------- |
| Player shoots            | `laser.wav`        | High     |
| Meteor destroyed         | Random explosion   | High     |
| Enemy ship destroyed     | `enemy_explosion`  | High     |
| Player takes damage      | `hit.wav`          | High     |
| Game over                | `game_over.wav`    | High     |
| Level up                 | `level_up.wav`     | High     |
| Enemy shoots             | `enemy_laser.wav`  | Medium   |
| New high score           | `highscore.mp3`    | Medium   |
| Pause / Unpause          | `pause.wav`        | Medium   |
| UI / Button click        | `click.wav`        | Low      |

Sounds marked with a priority of "Low" or "Medium" may not be available if the corresponding audio file was not found; the game handles this gracefully by checking if the sound exists before playing it.

### Audio assets location

```
assets/sounds/
  sfx/
    laser.wav            # Player shooting
    enemy_laser.wav      # Enemy ship shooting
    explosion.wav        # Meteor explosion (variant 1)
    explosion2.wav       # Meteor explosion (variant 2)
    explosion3.wav       # Meteor explosion (variant 3)
    hit.wav              # Player takes damage
    game_over.wav        # Player dies
    level_up.wav         # Level advancement
    highscore.mp3        # New high score
  music/
    level1.ogg           # Nebula theme
    level2.ogg           # Storm theme
    level3.ogg           # Belt theme
    level4.ogg           # Supernova theme
    level5.ogg           # Warzone theme
```
