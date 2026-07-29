#!/usr/bin/env python3
"""
Meteor Dodge - A survival game where you dodge falling meteors.

Controls:
    Arrow keys or WASD to move the player
    SPACE to shoot
    ESC to quit
    SPACE or ENTER to restart after game over

Author: Orami

Attribution / Credits:
    Sound effects by exewin (CC-BY 3.0):
    https://github.com/exewin
    https://exewin.github.io/
"""

import pygame
import random
import sys
import math
import os
import urllib.request
import urllib.parse
import json
import audio

# ============================================================
# CONSTANTS
# ============================================================

# Window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Meteor Dodge"
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
GREEN = (50, 200, 50)
BLUE = (50, 100, 220)
PURPLE = (180, 50, 220)

# Game settings
PLAYER_SIZE = 40
PLAYER_SPEED = 8
INITIAL_METEORS = 8
MAX_METEORS = 60
SCORE_PER_SECOND = 1
SCORE_PER_DODGE = 5
SCORE_PER_METEOR_DESTROYED = 15

# Bullet settings
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_SPEED = 12

# Images folders
ASSETS_FOLDER = "assets/images"
SHIP_FOLDER = os.path.join(ASSETS_FOLDER, "spaceships")
SHIP_IMAGE_FILE = "ship.png"
ENEMY_SHIP_IMAGE_FILE = "ship1.png"
METEOR_FOLDER = os.path.join(ASSETS_FOLDER, "meteors")
BACKGROUND_FOLDER = os.path.join(ASSETS_FOLDER, "backgrounds")

# Laravel API endpoint for submitting scores
LARAVEL_URL = "http://localhost:8000/scores"

# ============================================================
# LEVEL SYSTEM
# Each level defines: background, meteor speed, spawn rate,
# ammo type, and conditions to advance to the next level.
# To advance you need BOTH enough score AND more than 60
# seconds survived in the current level.
# ============================================================

LEVELS = {
    1: {
        "name": "Nebula",
        "background": "background_01.png",
        "meteor_min_speed": 3,
        "meteor_max_speed": 5,
        "spawn_rate": 30,
        "ammo_type": "normal",
        "cooldown": 15,
        "score_to_advance": 50,
        "has_enemy_ships": False,
    },
    2: {
        "name": "Storm",
        "background": "background_02.png",
        "meteor_min_speed": 4,
        "meteor_max_speed": 7,
        "spawn_rate": 25,
        "ammo_type": "double",
        "cooldown": 15,
        "score_to_advance": 150,
        "has_enemy_ships": False,
    },
    3: {
        "name": "Belt",
        "background": "background_03.png",
        "meteor_min_speed": 5,
        "meteor_max_speed": 9,
        "spawn_rate": 20,
        "ammo_type": "spread",
        "cooldown": 18,
        "score_to_advance": 300,
        "has_enemy_ships": False,
    },
    4: {
        "name": "Supernova",
        "background": "background_04.png",
        "meteor_min_speed": 6,
        "meteor_max_speed": 11,
        "spawn_rate": 15,
        "ammo_type": "rapid",
        "cooldown": 5,
        "score_to_advance": 500,
        "has_enemy_ships": False,
    },
    5: {
        "name": "Warzone",
        "background": "background_05.png",
        "meteor_min_speed": 4,
        "meteor_max_speed": 8,
        "spawn_rate": 25,
        "ammo_type": "spread",
        "cooldown": 12,
        "score_to_advance": 0,
        "has_enemy_ships": True,
        "ship_spawn_rate": 90,
    },
}

MAX_LEVEL = 5


# ============================================================
# IMAGE LOADING
# ============================================================


def load_image(filename, size=None, has_alpha=True, folder=ASSETS_FOLDER):
    """Load a single image file from the assets folder.

    filename: name of the file inside the assets folder.
    size: optional (width, height) tuple to resize the image.
    has_alpha: True if the image has transparency (PNG with transparent background).
    folder: directory path where the image is located (default ASSETS_FOLDER).
    """
    path = os.path.join(folder, filename)
    # os.path.join builds the full path by joining the folder and filename,
    # respecting the correct separator for the operating system.
    try:
        image = pygame.image.load(path)
        # pygame.image.load reads the image file from disk.
    except (pygame.error, FileNotFoundError):
        # If the file does not exist or is corrupted, show a clear
        # error message instead of a hard-to-read traceback.
        print(f"Could not load image: {path}")
        print("Make sure the file exists inside the assets folder.")
        pygame.quit()
        sys.exit()

    if has_alpha:
        image = image.convert_alpha()
        # convert_alpha() prepares the image for fast drawing and
        # respects the transparent parts of the PNG.
    else:
        image = image.convert()
        # convert() prepares the image for fast drawing without transparency.
        # Used for the background that fills the entire screen.

    if size is not None:
        image = pygame.transform.scale(image, size)
        # pygame.transform.scale resizes the image to the given dimensions.

    return image


# ============================================================
# PLAYER CLASS
# ============================================================


class Player:
    """Player controlled by the keyboard."""

    def __init__(self, image):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT - 80
        self.size = PLAYER_SIZE
        self.image = image
        # Stores the ship image, already loaded and scaled by the game.
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.trail = []

    def update(self, keys_pressed):
        """Update player position based on keyboard input."""
        # Store trail positions
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)

        # Movement with arrow keys or WASD
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.x -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.x += PLAYER_SPEED
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.y -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.y += PLAYER_SPEED

        # Keep player within bounds
        self.x = max(self.size // 2, min(WINDOW_WIDTH - self.size // 2, self.x))
        self.y = max(self.size // 2, min(WINDOW_HEIGHT - self.size // 2, self.y))

        # Handle invincibility timer
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def hit(self):
        """Handle player being hit by a meteor or enemy."""
        if self.invincible:
            return False
        self.lives -= 1
        self.invincible = True
        self.invincible_timer = 90  # 1.5 seconds at 60fps
        return True

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            self.x - self.size // 2, self.y - self.size // 2, self.size, self.size
        )

    def draw(self, surface):
        """Draw the player with trail effect."""
        # Draw trail
        # The trail is drawn with simple rectangles to keep the
        # effect without complicating the code with semi-transparent images.
        for i, (tx, ty) in enumerate(self.trail):
            size = int(self.size * (i / len(self.trail)) * 0.5)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, BLUE, trail_rect)

        # Draw player image (blink when invincible)
        if not self.invincible or self.invincible_timer % 10 < 5:
            image_rect = self.image.get_rect(center=(self.x, self.y))
            # get_rect(center=...) places the image centered on the current
            # position of the ship, instead of using the top-left corner.
            surface.blit(self.image, image_rect)
            # blit draws the ship image onto the screen.


# ============================================================
# BULLET CLASS
# ============================================================


class Bullet:
    """Bullet fired by the player to destroy meteors or enemy ships.

    Supports shooting in different directions using vx and vy.
    By default it travels upward (negative vy = upward on screen).
    """

    def __init__(self, x, y, vx=0, vy=None):
        # vx = horizontal speed (positive = right, negative = left)
        # vy = vertical speed (negative = upward on screen)
        self.x = x
        self.y = y
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.vx = vx
        # If vy is not provided, use -BULLET_SPEED (upward)
        self.vy = vy if vy is not None else -BULLET_SPEED

    def update(self):
        """Move bullet in its direction."""
        self.x += self.vx
        self.y += self.vy

    def is_off_screen(self):
        """Check if bullet has left the screen in any direction."""
        return (self.y < -self.height or
                self.y > WINDOW_HEIGHT + self.height or
                self.x < -self.width or
                self.x > WINDOW_WIDTH + self.width)

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height
        )

    def draw(self, surface):
        """Draw the bullet."""
        pygame.draw.rect(surface, YELLOW, self.get_rect())


# ============================================================
# METEOR CLASS
# ============================================================


class Meteor:
    """Falling meteor that the player must dodge or shoot."""

    def __init__(self, meteor_images, speed_range):
        self.size = random.randint(15, 35)
        self.x = random.randint(self.size, WINDOW_WIDTH - self.size)
        self.y = -self.size
        # speed_range is a (min, max) tuple with the current level's speed
        self.speed = random.uniform(speed_range[0], speed_range[1])
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)
        self.trail = []

        # random.choice(meteor_images) picks a random element from the list.
        # This lets each meteor use a different image without needing
        # a separate class for each graphic variant.
        chosen_image = random.choice(meteor_images)
        self.image = pygame.transform.scale(chosen_image, (self.size, self.size))

    def update(self):
        """Move meteor downward."""
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

        self.y += self.speed
        self.rotation += self.rotation_speed

    def is_off_screen(self):
        """Check if meteor has passed the bottom."""
        return self.y > WINDOW_HEIGHT + self.size

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            self.x - self.size // 2, self.y - self.size // 2, self.size, self.size
        )

    def draw(self, surface):
        """Draw the meteor with trail."""
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            size = int(self.size * (i / len(self.trail)) * 0.6)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, GRAY, trail_rect)

        # Draw meteor image, rotated according to its current rotation
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        # pygame.transform.rotate rotates the image by the given number of degrees.
        image_rect = rotated_image.get_rect(center=(self.x, self.y))
        # It is recentered after rotating, because when the image is rotated
        # its bounding rectangle changes size.
        surface.blit(rotated_image, image_rect)


# ============================================================
# ENEMY SHIP CLASS (Level 5)
# ============================================================


class EnemyShip:
    """Enemy ship that appears in level 5. Moves toward the player
    and shoots projectiles downward.

    fast: if True, the ship moves faster and shoots more often.
    """

    def __init__(self, image, fast=False):
        self.size = PLAYER_SIZE
        self.x = random.randint(self.size, WINDOW_WIDTH - self.size)
        self.y = -self.size
        self.fast = fast
        if fast:
            # Fast enemy: higher speed and more agressive shooting
            self.speed = random.uniform(4, 6)
            self.shoot_timer = random.randint(20, 50)
        else:
            self.speed = random.uniform(2, 4)
            self.shoot_timer = random.randint(30, 90)
        # Horizontal direction: moves to one side
        self.direction = random.choice([-1, 1])
        self.image = image
        # Every few frames, the enemy ship fires a projectile.
        self.trail = []
        self.alive = True

    def update(self):
        """Move enemy ship downward and slightly sideways."""
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

        self.y += self.speed
        # Moves laterally, bouncing off the edges
        self.x += self.direction * 1.5
        if self.x < self.size or self.x > WINDOW_WIDTH - self.size:
            self.direction *= -1

        # Counts down to shoot
        self.shoot_timer -= 1

    def should_shoot(self):
        """Returns True if the enemy should fire a projectile."""
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(60, 120)
            return True
        return False

    def is_off_screen(self):
        """Check if enemy has passed the bottom."""
        return self.y > WINDOW_HEIGHT + self.size

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            self.x - self.size // 2, self.y - self.size // 2, self.size, self.size
        )

    def draw(self, surface):
        """Draw the enemy ship with trail effect."""
        # Fast enemies use orange trail, normal ones use red
        trail_color = ORANGE if self.fast else RED
        for i, (tx, ty) in enumerate(self.trail):
            size = int(self.size * (i / len(self.trail)) * 0.5)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, trail_color, trail_rect)

        # Draw the enemy ship image (flipped vertically
        # so it points downward toward the player)
        flipped_image = pygame.transform.flip(self.image, False, True)
        image_rect = flipped_image.get_rect(center=(self.x, self.y))
        surface.blit(flipped_image, image_rect)


# ============================================================
# ENEMY BULLET CLASS
# ============================================================


class EnemyBullet:
    """Projectile fired by enemy ships. Moves downward toward the player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.speed = 6

    def update(self):
        """Move bullet downward."""
        self.y += self.speed

    def is_off_screen(self):
        """Check if bullet has left the bottom of the screen."""
        return self.y > WINDOW_HEIGHT + self.height

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height
        )

    def draw(self, surface):
        """Draw the enemy bullet in red."""
        pygame.draw.rect(surface, RED, self.get_rect())


# ============================================================
# EXPLOSION CLASS
# ============================================================


class Explosion:
    """Visual effect when a meteor is destroyed or hits the player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = []
        self.lifetime = 30

        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "size": random.randint(2, 6),
                    "color": random.choice([RED, ORANGE, YELLOW, WHITE]),
                }
            )

    def update(self):
        """Update particle positions."""
        self.lifetime -= 1
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["size"] = max(0, p["size"] - 1)

    def draw(self, surface):
        """Draw particles."""
        for p in self.particles:
            if p["size"] > 0:
                pygame.draw.rect(
                    surface,
                    p["color"],
                    (int(p["x"]), int(p["y"]), p["size"], p["size"]),
                )

    def is_alive(self):
        """Check if explosion is still visible."""
        return self.lifetime > 0


# ============================================================
# LEVEL NOTIFICATION CLASS
# ============================================================


class LevelNotification:
    """Shows a temporary message when advancing to a new level."""

    def __init__(self, level_name):
        self.timer = 120  # 2 seconds at 60fps
        self.level_name = level_name

    def update(self):
        self.timer -= 1

    def is_alive(self):
        return self.timer > 0

    def draw(self, surface, font_large, font_small):
        """Draw the level notification centered on screen."""
        if self.timer <= 0:
            return

        # Semi-transparent background for the notification
        overlay = pygame.Surface((WINDOW_WIDTH, 120))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        overlay_rect = overlay.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(overlay, overlay_rect)

        # Level text
        level_text = font_large.render("LEVEL COMPLETE", True, YELLOW)
        level_rect = level_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)
        )
        surface.blit(level_text, level_rect)

        # New level name
        name_text = font_small.render(
            f"Entering: {self.level_name}", True, WHITE
        )
        name_rect = name_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 25)
        )
        surface.blit(name_text, name_rect)


# ============================================================
# GAME CLASS
# ============================================================


class Game:
    """Main game controller."""

    def __init__(self):
        pygame.init()
        audio.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts (using Font instead of SysFont for Python 3.14 compatibility)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        # Load player ship image
        self.ship_image = load_image(
            SHIP_IMAGE_FILE, (PLAYER_SIZE, PLAYER_SIZE),
            folder=SHIP_FOLDER, has_alpha=True
        )

        # Load enemy ship image (will be flipped when drawn to point downward)
        self.enemy_ship_image = load_image(
            ENEMY_SHIP_IMAGE_FILE, (PLAYER_SIZE, PLAYER_SIZE),
            folder=SHIP_FOLDER, has_alpha=True
        )

        # Load meteor images (4 visual variants)
        # The Meteor class picks a random image from this list each time
        # a new meteor spawns, giving visual variety to falling meteors.
        meteor_filenames = ["meteor1.png", "meteor2.png", "meteor3.png", "meteor4.png"]
        self.meteor_images = [
            load_image(f, folder=METEOR_FOLDER, has_alpha=True)
            for f in meteor_filenames
        ]

        # Load backgrounds for all levels and store them in a dictionary
        # so they can be swapped when the player advances levels.
        self.backgrounds = {}
        for level_num, level_data in LEVELS.items():
            bg_file = level_data["background"]
            bg_image = load_image(
                bg_file, (WINDOW_WIDTH, WINDOW_HEIGHT),
                folder=BACKGROUND_FOLDER, has_alpha=False
            )
            self.backgrounds[level_num] = bg_image

        self.player = Player(self.ship_image)
        self.meteors = []
        self.bullets = []
        self.enemy_ships = []
        self.enemy_bullets = []
        self.explosions = []
        self.level_notification = None

        # Score and game control
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.running = True
        self.frame_count = 0

        # Level system
        self.current_level = 1
        self.level_score = 0
        # level_score is the score accumulated SINCE THE CURRENT LEVEL STARTED.
        # It is used to determine if the player meets the advance threshold.
        self.level_timer = 0
        # level_timer counts the frames spent in the current level.
        # It is used to verify the player survives more than 60 seconds.
        self.shoot_cooldown_timer = 0

        # Pause control
        self.paused = False

        # Spawn initial meteors
        level_data = LEVELS[self.current_level]
        speed_range = (level_data["meteor_min_speed"], level_data["meteor_max_speed"])
        for _ in range(INITIAL_METEORS):
            self.spawn_meteor(speed=random.uniform(1, 3), speed_range=speed_range)

        # Start background music for level 1
        audio.play_level_music(1)

    def get_level_data(self):
        """Get the configuration dictionary for the current level."""
        return LEVELS[self.current_level]

    def spawn_meteor(self, speed=None, speed_range=None):
        """Spawn a new meteor at the top."""
        if len(self.meteors) < MAX_METEORS:
            if speed is not None:
                # If an exact speed is passed, use that
                meteor = Meteor(self.meteor_images, (speed, speed))
            elif speed_range is not None:
                # If a range is passed, use the current level's range
                meteor = Meteor(self.meteor_images, speed_range)
            else:
                # If nothing is passed, use the level's default range
                data = self.get_level_data()
                meteor = Meteor(
                    self.meteor_images,
                    (data["meteor_min_speed"], data["meteor_max_speed"])
                )
            self.meteors.append(meteor)

    def spawn_enemy_ship(self):
        """Spawn an enemy ship at the top of the screen (level 5 only).
        25% chance of spawning a fast enemy with higher speed and
        more aggressive shooting."""
        if len(self.enemy_ships) < 5:
            is_fast = random.random() < 0.25
            self.enemy_ships.append(
                EnemyShip(self.enemy_ship_image, fast=is_fast)
            )

    def shoot(self):
        """Create bullets at the player's position based on the current ammo type.

        Each ammo type creates bullets differently:
        - normal: one bullet straight up
        - double: two parallel bullets
        - spread: three bullets in a fan (center, left, right)
        - rapid: one bullet straight up but with very low cooldown
        """
        level_data = self.get_level_data()

        if self.shoot_cooldown_timer > 0:
            return

        if audio.laser:
            audio.laser.play()

        bullet_x = self.player.x
        bullet_y = self.player.y - self.player.size // 2
        ammo_type = level_data["ammo_type"]

        if ammo_type == "normal":
            # Single shot: one bullet straight up
            self.bullets.append(Bullet(bullet_x, bullet_y))

        elif ammo_type == "double":
            # Double shot: two parallel bullets 10 pixels apart
            self.bullets.append(Bullet(bullet_x - 10, bullet_y))
            self.bullets.append(Bullet(bullet_x + 10, bullet_y))

        elif ammo_type == "spread":
            # Spread shot: three bullets at different angles
            # vx = horizontal speed, vy = vertical speed (negative = up)
            self.bullets.append(Bullet(bullet_x, bullet_y, vx=0))
            # Side bullets move upward and to the side
            self.bullets.append(Bullet(bullet_x, bullet_y, vx=-3, vy=-BULLET_SPEED))
            self.bullets.append(Bullet(bullet_x, bullet_y, vx=3, vy=-BULLET_SPEED))

        elif ammo_type == "rapid":
            # Rapid fire: same as normal but with very short cooldown
            self.bullets.append(Bullet(bullet_x, bullet_y))

        # Set the cooldown based on the level
        self.shoot_cooldown_timer = level_data["cooldown"]

    def handle_events(self):
        """Process all input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

                if self.game_over:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if audio.click:
                            audio.click.play()
                        self.restart()
                    return

                if event.key == pygame.K_p:
                    if not self.game_over:
                        self.paused = not self.paused
                        if audio.pause_sound:
                            audio.pause_sound.play()
                    return

                if event.key == pygame.K_SPACE:
                    self.shoot()

    def check_level_advance(self):
        """Check if the player has met the conditions to advance to the next level.

        TWO conditions are needed to advance:
        1. Having enough accumulated score in this level.
        2. Having survived more than 60 seconds in this level.
        Level 5 is the final level, there is no advancement.
        """
        if self.current_level >= MAX_LEVEL:
            return

        level_data = self.get_level_data()
        seconds_in_level = self.level_timer // FPS
        score_enough = self.level_score >= level_data["score_to_advance"]
        time_enough = seconds_in_level >= 60

        if score_enough and time_enough:
            self.current_level += 1
            self.level_score = 0
            self.level_timer = 0
            self.shoot_cooldown_timer = 0

            # Clear enemies and projectiles when changing level
            self.enemy_ships.clear()
            self.enemy_bullets.clear()

            # Show the notification for the new level
            new_level_data = LEVELS[self.current_level]
            self.level_notification = LevelNotification(new_level_data["name"])

            # Play level up sound and switch to the new level's music
            if audio.level_up:
                audio.level_up.play()
            audio.stop_music(500)
            audio.play_level_music(self.current_level)

    def _on_player_destroyed(self):
        """Handle player death: update high score, play sounds, stop music."""
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score
            if audio.highscore:
                audio.highscore.play()
        if audio.game_over:
            audio.game_over.play()
        audio.stop_music(500)

    def update(self):
        """Update game state."""
        if self.game_over:
            # Update explosions even during game over for visual effect
            for exp in self.explosions:
                exp.update()
            self.explosions = [e for e in self.explosions if e.is_alive()]
            return

        if self.paused:
            return

        self.frame_count += 1
        self.level_timer += 1

        level_data = self.get_level_data()
        speed_range = (level_data["meteor_min_speed"], level_data["meteor_max_speed"])

        # Update score (one point per second)
        if self.frame_count % FPS == 0:
            self.score += SCORE_PER_SECOND
            self.level_score += SCORE_PER_SECOND

        # Check if player can advance to the next level
        self.check_level_advance()

        # Spawn new meteors using the current level's spawn rate
        if self.frame_count % level_data["spawn_rate"] == 0:
            self.spawn_meteor(speed_range=speed_range)

        # Spawn enemy ships in level 5
        if level_data["has_enemy_ships"]:
            ship_rate = level_data.get("ship_spawn_rate", 90)
            if self.frame_count % ship_rate == 0:
                self.spawn_enemy_ship()

        # Update shoot cooldown
        if self.shoot_cooldown_timer > 0:
            self.shoot_cooldown_timer -= 1

        # Update player
        keys_pressed = pygame.key.get_pressed()
        self.player.update(keys_pressed)

        # Update bullets
        for bullet in self.bullets:
            bullet.update()
        # The list comprehension [b for b in self.bullets if not b.is_off_screen()]
        # creates a NEW list with only the bullets still on screen.
        # It is equivalent to a for loop with append, but in a single line.
        self.bullets = [b for b in self.bullets if not b.is_off_screen()]

        # Update enemy ships
        for ship in self.enemy_ships:
            ship.update()
            # Enemy ships fire projectiles every so often
            if ship.should_shoot():
                self.enemy_bullets.append(
                    EnemyBullet(ship.x, ship.y + ship.size // 2)
                )
                if audio.enemy_laser:
                    audio.enemy_laser.play()
        self.enemy_ships = [s for s in self.enemy_ships if not s.is_off_screen()]

        # Update enemy bullets
        for ebullet in self.enemy_bullets:
            ebullet.update()
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.is_off_screen()]

        # Update meteors
        for meteor in self.meteors:
            meteor.update()

        # Remove off-screen meteors
        # Same list comprehension technique: filters out meteors that
        # left the screen and keeps only the visible ones.
        self.meteors = [m for m in self.meteors if not m.is_off_screen()]

        # Check bullet vs meteor collisions
        # self.bullets[:] (a shallow copy via slicing) is used instead of
        # self.bullets directly because we are removing elements with
        # .remove() inside the loop. Iterating over the original list while
        # removing items shifts the indices and skips the next element,
        # causing bugs. The [:] copy prevents this.
        for bullet in self.bullets[:]:
            bullet_rect = bullet.get_rect()
            for meteor in self.meteors[:]:
                if bullet_rect.colliderect(meteor.get_rect()):
                    self.explosions.append(Explosion(meteor.x, meteor.y))
                    audio.play_explosion()
                    self.meteors.remove(meteor)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.score += SCORE_PER_METEOR_DESTROYED
                    self.level_score += SCORE_PER_METEOR_DESTROYED
                    break

        # Check bullet vs enemy ship collisions (level 5)
        for bullet in self.bullets[:]:
            bullet_rect = bullet.get_rect()
            for ship in self.enemy_ships[:]:
                if bullet_rect.colliderect(ship.get_rect()):
                    self.explosions.append(Explosion(ship.x, ship.y))
                    audio.play_explosion()
                    self.enemy_ships.remove(ship)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.score += SCORE_PER_METEOR_DESTROYED * 2
                    self.level_score += SCORE_PER_METEOR_DESTROYED * 2
                    break

        # Check player vs meteor collisions
        player_rect = self.player.get_rect()
        for meteor in self.meteors[:]:
            if player_rect.colliderect(meteor.get_rect()):
                if self.player.hit():
                    self.explosions.append(Explosion(meteor.x, meteor.y))
                    self.meteors.remove(meteor)
                    self.score += SCORE_PER_DODGE
                    self.level_score += SCORE_PER_DODGE
                    if audio.hit:
                        audio.hit.play()

                    if self.player.lives <= 0:
                        self._on_player_destroyed()
                break

        # Check player vs enemy ship collisions (level 5)
        for ship in self.enemy_ships[:]:
            if player_rect.colliderect(ship.get_rect()):
                if self.player.hit():
                    self.explosions.append(Explosion(ship.x, ship.y))
                    self.enemy_ships.remove(ship)
                    self.score += SCORE_PER_DODGE
                    self.level_score += SCORE_PER_DODGE
                    if audio.hit:
                        audio.hit.play()

                    if self.player.lives <= 0:
                        self._on_player_destroyed()
                break

        # Check player vs enemy bullet collisions (level 5)
        for ebullet in self.enemy_bullets[:]:
            if player_rect.colliderect(ebullet.get_rect()):
                if self.player.hit():
                    self.enemy_bullets.remove(ebullet)
                    self.score += SCORE_PER_DODGE
                    self.level_score += SCORE_PER_DODGE
                    if audio.hit:
                        audio.hit.play()

                    if self.player.lives <= 0:
                        self._on_player_destroyed()
                break

        # Update explosions
        for exp in self.explosions:
            exp.update()
        self.explosions = [e for e in self.explosions if e.is_alive()]

        # Update level notification
        if self.level_notification is not None:
            self.level_notification.update()
            if not self.level_notification.is_alive():
                self.level_notification = None

    def draw_background(self):
        """Draw the background image for the current level."""
        self.screen.blit(self.backgrounds[self.current_level], (0, 0))
        # Draws the full background image starting at the top-left corner (0, 0).

    def draw_hud(self):
        """Draw heads-up display (score, lives, level, ammo type)."""
        level_data = self.get_level_data()

        # Score
        score_text = self.font_small.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # High Score
        high_text = self.font_small.render(
            f"High Score: {self.high_score}", True, YELLOW
        )
        self.screen.blit(high_text, (WINDOW_WIDTH - high_text.get_width() - 10, 10))

        # Lives
        lives_text = self.font_small.render(f"Lives: {self.player.lives}", True, GREEN)
        self.screen.blit(lives_text, (10, 35))

        # Level number and name
        level_text = self.font_small.render(
            f"Level {self.current_level}: {level_data['name']}", True, BLUE
        )
        self.screen.blit(level_text, (WINDOW_WIDTH - level_text.get_width() - 10, 35))

        # Ammo type indicator
        ammo_names = {
            "normal": "Normal",
            "double": "Double",
            "spread": "Spread",
            "rapid": "Rapid",
        }
        ammo_label = ammo_names.get(level_data["ammo_type"], level_data["ammo_type"])
        ammo_text = self.font_small.render(f"Weapon: {ammo_label}", True, PURPLE)
        self.screen.blit(ammo_text, (10, 60))

        # Time survived in current level
        seconds_in_level = self.level_timer // FPS
        time_text = self.font_small.render(
            f"Time: {seconds_in_level}s", True, GRAY
        )
        self.screen.blit(time_text, (WINDOW_WIDTH - time_text.get_width() - 10, 60))

        # Progress bar for level advancement (only for levels 1-4)
        if self.current_level < MAX_LEVEL:
            bar_y = WINDOW_HEIGHT - 20
            bar_width = 200
            bar_height = 12
            bar_x = (WINDOW_WIDTH - bar_width) // 2

            # Draw the progress bar background
            pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height))

            # Calculate progress based on score and time
            score_progress = min(
                1.0, self.level_score / max(1, level_data["score_to_advance"])
            )
            time_progress = min(1.0, seconds_in_level / 60.0)
            progress = min(score_progress, time_progress)

            # Draw the bar fill (green when ready to advance)
            fill_width = int(bar_width * progress)
            bar_color = GREEN if progress >= 1.0 else YELLOW
            pygame.draw.rect(
                self.screen, bar_color, (bar_x, bar_y, fill_width, bar_height)
            )

            # Bar border
            pygame.draw.rect(
                self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1
            )

        # Pause overlay indicator
        if self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(120)
            self.screen.blit(overlay, (0, 0))
            pause_text = self.font_large.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(pause_text, pause_rect)
            tip_text = self.font_small.render("Press P to continue", True, WHITE)
            tip_rect = tip_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
            self.screen.blit(tip_text, tip_rect)

    def draw_game_over(self):
        """Draw game over screen overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        go_text = self.font_large.render("GAME OVER", True, RED)
        go_rect = go_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.screen.blit(go_text, go_rect)

        # Final score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        # Level reached
        level_data = self.get_level_data()
        level_text = self.font_small.render(
            f"Level {self.current_level}: {level_data['name']}", True, BLUE
        )
        level_rect = level_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40)
        )
        self.screen.blit(level_text, level_rect)

        # Restart instruction
        restart_text = self.font_small.render(
            "Press SPACE or ENTER to restart", True, GRAY
        )
        restart_rect = restart_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80)
        )
        self.screen.blit(restart_text, restart_rect)

    def send_score_to_server(self):
        """Send the final score to the Laravel server via POST."""
        if self.score <= 0:
            return
        data = {
            "player_name": "Player",
            "score": self.score,
            "level_reached": self.current_level,
            "time_survived": self.level_timer // 60,
        }
        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            LARAVEL_URL,
            data=json_data,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

    def restart(self):
        """Restart the game from level 1."""
        self.send_score_to_server()
        self.player = Player(self.ship_image)
        self.meteors = []
        self.bullets = []
        self.enemy_ships = []
        self.enemy_bullets = []
        self.shoot_cooldown_timer = 0
        self.explosions = []
        self.level_notification = None
        self.score = 0
        self.frame_count = 0
        self.game_over = False

        # Reset the level system
        self.current_level = 1
        self.level_score = 0
        self.level_timer = 0

        # Spawn initial meteors for level 1
        level_data = LEVELS[self.current_level]
        speed_range = (level_data["meteor_min_speed"], level_data["meteor_max_speed"])
        for _ in range(INITIAL_METEORS):
            self.spawn_meteor(speed=random.uniform(1, 3), speed_range=speed_range)

        # Stop any lingering sounds from the previous game and restart music
        audio.stop_all_sfx()
        audio.stop_music_immediate()
        audio.play_level_music(1)

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()

            # Draw everything
            self.draw_background()

            # Draw meteors
            for meteor in self.meteors:
                meteor.draw(self.screen)

            # Draw enemy ships (level 5)
            for ship in self.enemy_ships:
                ship.draw(self.screen)

            # Draw bullets
            for bullet in self.bullets:
                bullet.draw(self.screen)

            # Draw enemy bullets (level 5)
            for ebullet in self.enemy_bullets:
                ebullet.draw(self.screen)

            # Draw explosions
            for exp in self.explosions:
                exp.draw(self.screen)

            # Draw player
            self.player.draw(self.screen)

            # Draw HUD
            self.draw_hud()

            # Draw level notification (appears briefly when advancing)
            if self.level_notification is not None:
                self.level_notification.draw(
                    self.screen, self.font_large, self.font_small
                )

            # Draw game over
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    game = Game()
    game.run()
