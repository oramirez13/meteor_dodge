"""
Audio manager for Meteor Dodge.

Handles loading and playback of sound effects and background music.
All sounds are loaded with error handling so the game continues
even if some audio files are missing.

Usage:
    import audio
    # Call init() once after pygame.init()
    audio.init()
    # Then use any sound or music function
    audio.laser.play()
    audio.play_explosion()
    audio.play_level_music(1)
"""

import pygame
import os
import random

# Folder paths for sound effects and music
# os.path.join builds the path using the correct separator for each OS.
SFX_FOLDER = os.path.join("assets", "sounds", "sfx")
MUSIC_FOLDER = os.path.join("assets", "sounds", "music")

# ============================================================
# Module-level variables that will be populated by init()
# Each sound is None until init() loads it.
# This allows importing the module BEFORE pygame.init()
# without causing errors.
# ============================================================

laser = None
explosion = None
explosion2 = None
explosion3 = None
hit = None
game_over = None
level_up = None
click = None
pause_sound = None
enemy_laser = None
enemy_explosion = None
highscore = None

# List of available explosion variants for random selection
explosion_variants = []


def _load_sound(filename, volume=1.0):
    """Load a single sound effect from the sfx folder.

    filename: name of the file inside the sfx folder
    volume:   playback volume (0.0 to 1.0)

    Returns a pygame.mixer.Sound object, or None if the file
    is missing or corrupted.
    """
    path = os.path.join(SFX_FOLDER, filename)
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        return sound
    except (pygame.error, FileNotFoundError):
        # Print a clear warning instead of crashing.
        # The game will work without this sound.
        print(f"  [audio] Could not load sound: {path}")
        return None


_initialized = False


def init():
    """Initialize all sound effects.

    Must be called AFTER pygame.init() because pygame.mixer
    needs to be running before we can load sounds.
    Should be called once when the game starts.
    Safe to call multiple times (only loads once).
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    # The 'global' keyword tells Python to modify the module-level
    # variables instead of creating new local ones.
    global laser, explosion, explosion2, explosion3, hit
    global game_over, level_up, click, pause_sound
    global enemy_laser, enemy_explosion, highscore
    global explosion_variants

    # Each sound is loaded with its own volume level.
    # Volume values range from 0.0 (silent) to 1.0 (full).
    # SFX volumes are deliberately lower than music to create
    # a balanced mix.
    laser = _load_sound("laser.wav", 0.15)
    explosion = _load_sound("explosion.wav", 0.40)
    explosion2 = _load_sound("explosion2.wav", 0.40)
    explosion3 = _load_sound("explosion3.wav", 0.40)
    hit = _load_sound("hit.wav", 0.50)
    game_over = _load_sound("game_over.wav", 0.60)
    level_up = _load_sound("level_up.wav", 0.50)
    click = _load_sound("click.wav", 0.30)
    pause_sound = _load_sound("pause.wav", 0.40)
    enemy_laser = _load_sound("enemy_laser.wav", 0.20)
    enemy_explosion = _load_sound("enemy_explosion.wav", 0.40)
    highscore = _load_sound("highscore.mp3", 0.50)

    # Build a list of only the explosion variants that loaded
    # successfully. If a file is missing, it is excluded.
    explosion_variants = [
        s for s in [explosion, explosion2, explosion3] if s is not None
    ]


def play_explosion():
    """Play a random explosion variant.

    Using random.choice prevents the player from hearing the
    exact same sound every time an explosion occurs.
    """
    if explosion_variants:
        # random.choice picks one element at random from the list.
        random.choice(explosion_variants).play()


# ============================================================
# Music system
# Each level has its own music track that matches its theme.
# ============================================================

LEVEL_MUSIC = {
    1: "level1.ogg",
    2: "level2.ogg",
    3: "level3.ogg",
    4: "level4.ogg",
    5: "level5.ogg",
}


def play_music(filename, volume=0.30, loop=-1):
    """Load and play a background music track.

    filename: name of the file inside the music folder
    volume:   playback volume (0.0 to 1.0)
    loop:     -1 for infinite looping, 0 for once, N for N times
    """
    path = os.path.join(MUSIC_FOLDER, filename)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
    except (pygame.error, FileNotFoundError):
        print(f"  [audio] Could not load music: {path}")


def play_level_music(level, volume=0.30):
    """Play the music track corresponding to a level (1-5).

    Uses the LEVEL_MUSIC dictionary to map level numbers
    to filenames.
    """
    filename = LEVEL_MUSIC.get(level)
    if filename:
        play_music(filename, volume)


def stop_music(fadeout_ms=1000):
    """Gradually fade out the current music.

    fadeout_ms: duration of the fade in milliseconds
    """
    pygame.mixer.music.fadeout(fadeout_ms)


def stop_music_immediate():
    """Stop the current music instantly (no fade)."""
    pygame.mixer.music.stop()
