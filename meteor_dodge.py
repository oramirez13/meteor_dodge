#!/usr/bin/env python3
"""
Meteor Dodge - A survival game where you dodge falling meteors.

Controls:
    Arrow keys or WASD to move the player
    SPACE to shoot
    ESC to quit
    P to pause/resume
    In menu: ARROWS to navigate, ENTER to start
    SPACE or ENTER after game over to return to menu

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

# Colores del titulo grande de la pantalla de inicio
# (se definen aparte para cambiar el estilo del titulo sin tocar
# la funcion draw_big_title)
TITLE_MAIN_COLOR = ORANGE      # Color principal del texto
TITLE_OUTLINE_COLOR = BLACK    # Color del contorno (borde)
TITLE_SHADOW_COLOR = (80, 40, 0)  # Marron oscuro para la sombra

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
ENEMY_SHIP_IMAGE_FILE = "ship1.png"
METEOR_FOLDER = os.path.join(ASSETS_FOLDER, "meteors")
BACKGROUND_FOLDER = os.path.join(ASSETS_FOLDER, "backgrounds")
CHARACTER_FOLDER = os.path.join(ASSETS_FOLDER, "characters")

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

    def __init__(self, image, character_image=None, character_name=""):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT - 80
        self.size = PLAYER_SIZE
        self.image = image
        # Stores the ship image, already loaded and scaled by the game.
        # character_image es el retrato del personaje seleccionado.
        # Se muestra en el HUD como indicador visual de la eleccion.
        self.character_image = character_image
        self.character_name = character_name
        # character_name guarda el nombre del personaje (ej. "Alice")
        # para poder reproducir sonidos especiales segun el personaje.
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.trail = []

        # Calcular el tamano del trail azul segun el contenido visible
        # de la nave. get_bounding_rect() mide solo los pixeles no
        # transparentes de la imagen, ignorando el fondo. Asi las naves
        # pequenas dejan un trail pequeno y no un cuadro azul enorme.
        content_rect = self.image.get_bounding_rect()
        # Se usa el promedio del ancho y del alto de la nave, reducido
        # a la mitad, para que el trail no sea mas grande que la nave.
        self.trail_max_size = int(
            (content_rect.width + content_rect.height) / 2 * 0.5
        )

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
            # El tamano de cada cuadrado va encogiendo (i / len de la
            # lista) hasta llegar a trail_max_size, que depende de la
            # nave. Asi el trail nunca forma un cuadro mas grande
            # que la propia nave.
            size = int(self.trail_max_size * (i / len(self.trail)))
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
# FUNCION PARA DIBUJAR EL TITULO GRANDE DEL MENU
# ============================================================


def draw_big_title(surface, text, center_x, center_y, font_size=90):
    """Dibuja un titulo grande con sombra y contorno personalizado.

    surface: la superficie donde se va a dibujar (por ejemplo self.screen).
    text: el texto del titulo, por ejemplo "METEOR DODGE".
    center_x: posicion horizontal del centro del titulo, en pixeles.
    center_y: posicion vertical del centro del titulo, en pixeles.
    font_size: tamano de la fuente. Un numero grande como 90 hace que
    el titulo ocupe bastante espacio en la pantalla.
    """

    # pygame.font.Font(None, font_size) crea una fuente usando la fuente
    # por defecto de pygame, igual que las fuentes del juego. Asi no hace
    # falta instalar ni cargar ninguna fuente externa.
    title_font = pygame.font.Font(None, font_size)

    # ------------------------------------------------------------
    # PASO 1: Dibujar la sombra
    # ------------------------------------------------------------
    # Se dibuja el mismo texto un poco mas abajo y a la derecha, en un
    # color oscuro. Esto da la sensacion de que el titulo tiene volumen,
    # como si estuviera "levantado" sobre el fondo.
    shadow_surface = title_font.render(text, True, TITLE_SHADOW_COLOR)
    shadow_rect = shadow_surface.get_rect(center=(center_x + 6, center_y + 6))
    surface.blit(shadow_surface, shadow_rect)

    # ------------------------------------------------------------
    # PASO 2: Dibujar el contorno (borde)
    # ------------------------------------------------------------
    # Se dibuja el texto varias veces alrededor de la posicion central,
    # desplazado un par de pixeles en cada direccion (arriba, abajo,
    # izquierda, derecha y las cuatro diagonales). Las ocho copias
    # forman un borde negro alrededor de las letras.
    outline_surface = title_font.render(text, True, TITLE_OUTLINE_COLOR)

    # Cada par (dx, dy) indica cuanto se mueve el texto en el eje
    # horizontal (dx) y en el eje vertical (dy) para cada copia.
    offsets = [
        (-3, -3), (0, -3), (3, -3),
        (-3, 0),           (3, 0),
        (-3, 3),  (0, 3),  (3, 3),
    ]

    for dx, dy in offsets:
        outline_rect = outline_surface.get_rect(
            center=(center_x + dx, center_y + dy)
        )
        surface.blit(outline_surface, outline_rect)

    # ------------------------------------------------------------
    # PASO 3: Dibujar el texto principal, encima de todo lo anterior
    # ------------------------------------------------------------
    main_surface = title_font.render(text, True, TITLE_MAIN_COLOR)
    main_rect = main_surface.get_rect(center=(center_x, center_y))
    surface.blit(main_surface, main_rect)


# ============================================================
# MENU CLASS (pantalla de inicio)
# ============================================================


class Menu:
    """Pantalla de inicio con seleccion de personaje y nave."""

    def __init__(self, character_images, character_names, ship_images, ship_names):
        # character_images: lista de Surface (imagenes de personajes ya cargadas)
        # character_names: lista de strings con los nombres para mostrar
        # ship_images: lista de Surface (imagenes de naves ya cargadas y escaladas)
        # ship_names: lista de strings con los nombres para mostrar
        self.character_images = character_images
        self.character_names = character_names
        self.ship_images = ship_images
        self.ship_names = ship_names

        # Indice de la opcion seleccionada en cada fila
        self.selected_char = 0
        self.selected_ship = 0

        # 0 = fila de personajes, 1 = fila de naves
        self.selected_row = 0

        # Posiciones fijas en la pantalla para cada fila
        self.char_y = 240
        self.ship_y = 390
        self.preview_size = 80
        # preview_size es el tamano al que se muestran las imagenes
        # en el menu (80x80 pixeles), mas grande que en el juego
        # para que se vean bien durante la seleccion.

    def handle_event(self, event):
        """Procesa un evento de teclado y devuelve una accion.

        Acciones posibles:
            None   -> no paso nada
            "start" -> el jugador presiono Enter para comenzar
        """
        if event.type == pygame.KEYDOWN:
            # Flecha izquierda: opcion anterior en la fila actual
            if event.key == pygame.K_LEFT:
                if self.selected_row == 0:
                    # Cicla hacia atras en la lista de personajes
                    self.selected_char = (self.selected_char - 1) % len(self.character_images)
                else:
                    # Cicla hacia atras en la lista de naves
                    self.selected_ship = (self.selected_ship - 1) % len(self.ship_images)
                if audio.click:
                    audio.click.play()

            # Flecha derecha: opcion siguiente en la fila actual
            elif event.key == pygame.K_RIGHT:
                if self.selected_row == 0:
                    # Cicla hacia adelante en la lista de personajes
                    self.selected_char = (self.selected_char + 1) % len(self.character_images)
                else:
                    # Cicla hacia adelante en la lista de naves
                    self.selected_ship = (self.selected_ship + 1) % len(self.ship_images)
                if audio.click:
                    audio.click.play()

            # Flecha arriba: sube a la fila de personajes
            elif event.key == pygame.K_UP:
                self.selected_row = 0
                if audio.click:
                    audio.click.play()

            # Flecha abajo: baja a la fila de naves
            elif event.key == pygame.K_DOWN:
                self.selected_row = 1
                if audio.click:
                    audio.click.play()

            # Enter: confirma la seleccion y empieza el juego
            elif event.key == pygame.K_RETURN:
                if audio.click:
                    audio.click.play()
                return "start"

        return None

    def draw(self, surface, font_large, font_medium, font_small):
        """Dibuja el menu completo en la pantalla."""
        # Fondo negro
        surface.fill(BLACK)

        # Titulo del juego centrado en la parte superior.
        # Se usa draw_big_title, que dibuja el texto con sombra y
        # contorno para que el titulo se vea mas llamativo.
        draw_big_title(surface, "METEOR DODGE", WINDOW_WIDTH // 2, 75)

        # Dibujar una linea decorativa debajo del titulo
        pygame.draw.line(surface, GRAY, (200, 130), (600, 130), 2)

        # ---- SECCION DE PERSONAJES ----
        # Etiqueta de la seccion
        char_label = font_medium.render("SELECT CHARACTER", True, WHITE)
        char_label_rect = char_label.get_rect(center=(WINDOW_WIDTH // 2, 170))
        surface.blit(char_label, char_label_rect)

        # Flecha izquierda para personajes
        left_arrow = font_large.render("<", True, WHITE)
        left_rect = left_arrow.get_rect(
            right=(WINDOW_WIDTH // 2 - self.preview_size - 20),
            centery=self.char_y
        )
        surface.blit(left_arrow, left_rect)

        # Imagen del personaje actual centrada
        char_img = self.character_images[self.selected_char]
        char_rect = char_img.get_rect(center=(WINDOW_WIDTH // 2, self.char_y))
        surface.blit(char_img, char_rect)

        # Si esta fila esta seleccionada, dibujar un recuadro amarillo
        # alrededor de la imagen para indicar que se puede navegar aqui.
        if self.selected_row == 0:
            pygame.draw.rect(surface, YELLOW, char_rect.inflate(8, 8), 3)

        # Flecha derecha para personajes
        right_arrow = font_large.render(">", True, WHITE)
        right_rect = right_arrow.get_rect(
            left=(WINDOW_WIDTH // 2 + self.preview_size + 20),
            centery=self.char_y
        )
        surface.blit(right_arrow, right_rect)

        # Nombre del personaje debajo de la imagen
        char_name = font_small.render(
            self.character_names[self.selected_char], True, WHITE
        )
        char_name_rect = char_name.get_rect(
            center=(WINDOW_WIDTH // 2, self.char_y + self.preview_size // 2 + 20)
        )
        surface.blit(char_name, char_name_rect)

        # ---- SECCION DE NAVES ----
        # Etiqueta de la seccion
        ship_label = font_medium.render("SELECT SHIP", True, WHITE)
        ship_label_rect = ship_label.get_rect(center=(WINDOW_WIDTH // 2, 320))
        surface.blit(ship_label, ship_label_rect)

        # Flecha izquierda para naves
        left_arrow2 = font_large.render("<", True, WHITE)
        left_rect2 = left_arrow2.get_rect(
            right=(WINDOW_WIDTH // 2 - self.preview_size - 20),
            centery=self.ship_y
        )
        surface.blit(left_arrow2, left_rect2)

        # Imagen de la nave actual centrada
        ship_img = self.ship_images[self.selected_ship]
        ship_rect = ship_img.get_rect(center=(WINDOW_WIDTH // 2, self.ship_y))
        surface.blit(ship_img, ship_rect)

        # Si esta fila esta seleccionada, dibujar un recuadro amarillo
        if self.selected_row == 1:
            pygame.draw.rect(surface, YELLOW, ship_rect.inflate(8, 8), 3)

        # Flecha derecha para naves
        right_arrow2 = font_large.render(">", True, WHITE)
        right_rect2 = right_arrow2.get_rect(
            left=(WINDOW_WIDTH // 2 + self.preview_size + 20),
            centery=self.ship_y
        )
        surface.blit(right_arrow2, right_rect2)

        # Nombre de la nave debajo de la imagen
        ship_name = font_small.render(
            self.ship_names[self.selected_ship], True, WHITE
        )
        ship_name_rect = ship_name.get_rect(
            center=(WINDOW_WIDTH // 2, self.ship_y + self.preview_size // 2 + 20)
        )
        surface.blit(ship_name, ship_name_rect)

        # ---- INSTRUCCIONES AL PIE ----
        inst_text = font_small.render(
            "Use ARROW KEYS to navigate, ENTER to start", True, GRAY
        )
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, 520))
        surface.blit(inst_text, inst_rect)

        # Creditos
        cred_text = font_small.render("ESC to quit", True, GRAY)
        cred_rect = cred_text.get_rect(center=(WINDOW_WIDTH // 2, 550))
        surface.blit(cred_text, cred_rect)


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

        # ---- Cargar naves disponibles para el menu ----
        # Lista de archivos de naves (excluyendo ship1.png que es la nave enemiga)
        ship_files = [
            "ship.png", "e01.png", "e02.png", "e03.png",
            "fxt2.png", "fxt7.png", "KBUM.png", "mini1.png",
            "MK 1K.png", "moroder.png", "skyBlanc.png",
        ]
        self.ship_images = []
        self.ship_names = []
        for sf in ship_files:
            # Cargar cada nave escalada al tamano del jugador
            img = load_image(sf, (PLAYER_SIZE, PLAYER_SIZE), folder=SHIP_FOLDER, has_alpha=True)
            self.ship_images.append(img)
            # El nombre visible es el nombre del archivo sin extension
            name = sf.rsplit(".", 1)[0]  # Elimina la extension ".png"
            self.ship_names.append(name)
        # Nota: rsplit(".", 1) separa el string por el ultimo punto
        # y devuelve [nombre, "png"]. Con [0] tomamos solo el nombre.

        # ---- Cargar personajes disponibles para el menu ----
        character_files = [
            "AliceBlur.png", "mat.png", "stephen.png",
            "technician.png", "zotron.png",
        ]
        self.character_images = []
        self.character_names = []
        for cf in character_files:
            # Cargar cada personaje a 80x80 para que se vea bien en el menu
            img = load_image(cf, (80, 80), folder=CHARACTER_FOLDER, has_alpha=True)
            self.character_images.append(img)
            # Limpiar el nombre: quitar extension y "Blur" del final
            name = cf.rsplit(".", 1)[0]
            name = name.replace("Blur", "")  # "AliceBlur" -> "Alice"
            self.character_names.append(name)

        # ---- Menu de inicio ----
        # El menu usa las imagenes de naves SIN escalar (a 80x80 para
        # que se vean grandes en la pantalla de seleccion).
        menu_ship_images = []
        for sf in ship_files:
            img = load_image(sf, (80, 80), folder=SHIP_FOLDER, has_alpha=True)
            menu_ship_images.append(img)

        self.menu = Menu(
            self.character_images, self.character_names,
            menu_ship_images, self.ship_names
        )

        # Estado del juego: "menu" o "playing"
        self.state = "menu"

        # Variables de juego (se inicializan cuando empieza a jugar)
        self.player = None
        self.selected_char_idx = 0
        self.selected_ship_idx = 0
        self.meteors = []
        self.bullets = []
        self.enemy_ships = []
        self.enemy_bullets = []
        self.explosions = []
        self.level_notification = None
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.running = True
        self.frame_count = 0
        self.current_level = 1
        self.level_score = 0
        self.level_timer = 0
        self.shoot_cooldown_timer = 0
        self.paused = False

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

                # Si estamos en el menu, delegar los eventos al menu
                if self.state == "menu":
                    action = self.menu.handle_event(event)
                    if action == "start":
                        self.start_game()
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

    def start_game(self):
        """Inicia una partida con las selecciones del menu."""
        # Guardar los indices seleccionados
        self.selected_char_idx = self.menu.selected_char
        self.selected_ship_idx = self.menu.selected_ship

        # Crear el jugador con la nave y personaje seleccionados
        ship_img = self.ship_images[self.selected_ship_idx]
        char_img = self.character_images[self.selected_char_idx]
        char_name = self.character_names[self.selected_char_idx]
        self.player = Player(ship_img, character_image=char_img, character_name=char_name)

        # Reiniciar todas las variables del juego
        self.meteors = []
        self.bullets = []
        self.enemy_ships = []
        self.enemy_bullets = []
        self.explosions = []
        self.level_notification = None
        self.score = 0
        self.frame_count = 0
        self.current_level = 1
        self.level_score = 0
        self.level_timer = 0
        self.shoot_cooldown_timer = 0
        self.paused = False
        self.game_over = False
        self.state = "playing"

        # Generar los meteoros iniciales del nivel 1
        level_data = LEVELS[self.current_level]
        speed_range = (level_data["meteor_min_speed"], level_data["meteor_max_speed"])
        for _ in range(INITIAL_METEORS):
            self.spawn_meteor(speed=random.uniform(1, 3), speed_range=speed_range)

        # Empezar la musica del nivel 1
        audio.play_level_music(1)

    def update(self):
        """Update game state."""
        if self.state == "menu":
            return

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
                    if self.player.character_name == "Alice" and audio.hit_female:
                        audio.hit_female.play()
                    elif audio.hit:
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
                    if self.player.character_name == "Alice" and audio.hit_female:
                        audio.hit_female.play()
                    elif audio.hit:
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
                    if self.player.character_name == "Alice" and audio.hit_female:
                        audio.hit_female.play()
                    elif audio.hit:
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

        # Retrato del personaje seleccionado (esquina superior izquierda,
        # al lado del marcador de vidas)
        if self.player.character_image is not None:
            # Redimensionar el retrato a 25x25 para que encaje en el HUD
            portrait = pygame.transform.scale(self.player.character_image, (25, 25))
            self.screen.blit(portrait, (10, 33))
            # El texto de vidas se desplaza a la derecha del retrato
            lives_x = 42
        else:
            lives_x = 10
        lives_text = self.font_small.render(f"Lives: {self.player.lives}", True, GREEN)
        self.screen.blit(lives_text, (lives_x, 35))

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

        # Restart instruction (vuelve al menu para elegir de nuevo)
        restart_text = self.font_small.render(
            "Press SPACE or ENTER to return to menu", True, GRAY
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
        """Vuelve al menu de inicio despues de game over."""
        self.send_score_to_server()

        # Detener todos los sonidos
        audio.stop_all_sfx()
        audio.stop_music_immediate()

        # Volver al menu manteniendo el high_score
        self.state = "menu"
        self.player = None
        self.meteors = []
        self.bullets = []
        self.enemy_ships = []
        self.enemy_bullets = []
        self.explosions = []
        self.level_notification = None
        self.score = 0
        self.frame_count = 0
        self.game_over = False
        self.current_level = 1
        self.level_score = 0
        self.level_timer = 0
        self.shoot_cooldown_timer = 0
        self.paused = False

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()

            # Si estamos en el menu, dibujar el menu y saltar el resto
            if self.state == "menu":
                self.menu.draw(self.screen, self.font_large, self.font_medium, self.font_small)
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

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
