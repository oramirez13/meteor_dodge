#!/usr/bin/env python3
"""
Meteor Dodge - A survival game where you dodge falling meteors.

Controls:
    Arrow keys or WASD to move the player
    SPACE to shoot
    ESC to quit
    SPACE or ENTER to restart after game over

Author: Orami
"""

import pygame
import random
import sys
import math
import os

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

# Game settings
PLAYER_SIZE = 40
PLAYER_SPEED = 8
METEOR_MIN_SPEED = 3
METEOR_MAX_SPEED = 7
METEOR_SPAWN_RATE = 30  # frames between spawns
INITIAL_METEORS = 8
MAX_METEORS = 60
SCORE_PER_SECOND = 1
SCORE_PER_DODGE = 5

# Bullet settings
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_SPEED = 12
SHOOT_COOLDOWN = 15  # cuadros de espera entre disparo y disparo
SCORE_PER_METEOR_DESTROYED = 15

# Images
# Todas las imagenes deben estar dentro de esta carpeta, junto al archivo .py
ASSETS_FOLDER = "assets/images"
BACKGROUND_IMAGE_FILE = "background.png"
SHIP_IMAGE_FILE = "player.png"
METEOR_IMAGE_FILES = ["meteor.png"]
# La lista tiene un solo archivo por ahora. Si mas adelante agregas mas
# variantes (por ejemplo meteor2.png), solo agrega el nombre a esta lista
# y el juego los elegira al azar automaticamente.


# ============================================================
# IMAGE LOADING
# ============================================================


def load_image(filename, size=None, has_alpha=True):
    """Load a single image file from the assets folder.

    filename: nombre del archivo dentro de la carpeta assets.
    size: tupla (ancho, alto) opcional para redimensionar la imagen.
    has_alpha: True si la imagen tiene transparencia (PNG con fondo transparente).
    """
    path = os.path.join(ASSETS_FOLDER, filename)
    # os.path.join arma la ruta completa uniendo la carpeta y el nombre
    # del archivo, respetando el separador correcto del sistema operativo.
    try:
        image = pygame.image.load(path)
        # pygame.image.load lee el archivo de imagen desde el disco.
    except (pygame.error, FileNotFoundError):
        # Si el archivo no existe o esta danado, se avisa con un mensaje
        # claro en vez de mostrar un traceback dificil de entender.
        print(f"No se pudo cargar la imagen: {path}")
        print("Verifica que el archivo exista dentro de la carpeta assets.")
        pygame.quit()
        sys.exit()

    if has_alpha:
        image = image.convert_alpha()
        # convert_alpha() prepara la imagen para dibujarse rapido y
        # respeta las partes transparentes del PNG.
    else:
        image = image.convert()
        # convert() prepara la imagen para dibujarse rapido, sin transparencia.
        # Se usa para el fondo, que ocupa toda la pantalla.

    if size is not None:
        image = pygame.transform.scale(image, size)
        # pygame.transform.scale cambia el tamano de la imagen al indicado.

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
        # Guarda la imagen de la nave, ya cargada y escalada por el juego.
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

        # Movimiento con flechas o WASD
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
        """Handle player being hit by a meteor."""
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
        # El rastro se sigue dibujando con rectangulos simples, para
        # mantener el efecto sin complicar el codigo con imagenes semi-transparentes.
        for i, (tx, ty) in enumerate(self.trail):
            size = int(self.size * (i / len(self.trail)) * 0.5)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, BLUE, trail_rect)

        # Draw player image (blink when invincible)
        if not self.invincible or self.invincible_timer % 10 < 5:
            image_rect = self.image.get_rect(center=(self.x, self.y))
            # get_rect(center=...) ubica la imagen centrada en la posicion
            # actual de la nave, en vez de usar la esquina superior izquierda.
            surface.blit(self.image, image_rect)
            # blit dibuja la imagen de la nave sobre la pantalla.


# ============================================================
# BULLET CLASS
# ============================================================


class Bullet:
    """Bullet fired by the player to destroy meteors."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.speed = BULLET_SPEED

    def update(self):
        """Move bullet upward."""
        self.y -= self.speed

    def is_off_screen(self):
        """Check if bullet has left the top of the screen."""
        return self.y < -self.height

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

    def __init__(self, meteor_images, speed=None):
        self.size = random.randint(15, 35)
        self.x = random.randint(self.size, WINDOW_WIDTH - self.size)
        self.y = -self.size
        self.speed = speed or random.uniform(METEOR_MIN_SPEED, METEOR_MAX_SPEED)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)
        self.trail = []

        # Elige una imagen al azar de la lista y la escala al tamano de este meteorito
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

        # Draw meteor image, rotada segun su rotacion actual
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        # pygame.transform.rotate gira la imagen el numero de grados indicado.
        image_rect = rotated_image.get_rect(center=(self.x, self.y))
        # Se vuelve a centrar despues de rotar, porque al girar la imagen
        # su rectangulo contenedor cambia de tamano.
        surface.blit(rotated_image, image_rect)


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
# GAME CLASS
# ============================================================


class Game:
    """Main game controller."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts (using Font instead of SysFont for Python 3.14 compatibility)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        # Cargar todas las imagenes del juego una sola vez, al iniciar.
        # Cargarlas aqui (y no en cada cuadro) evita que el juego se vuelva lento.
        self.background_image = load_image(
            BACKGROUND_IMAGE_FILE, (WINDOW_WIDTH, WINDOW_HEIGHT), has_alpha=False
        )
        self.ship_image = load_image(
            SHIP_IMAGE_FILE, (PLAYER_SIZE, PLAYER_SIZE), has_alpha=True
        )
        self.meteor_images = []
        for filename in METEOR_IMAGE_FILES:
            meteor_image = load_image(filename, has_alpha=True)
            self.meteor_images.append(meteor_image)
            # Aqui no se redimensiona todavia: cada meteorito escala su
            # propia copia al tamano que le toco al azar (ver clase Meteor).

        self.player = Player(self.ship_image)
        self.meteors = []
        self.bullets = []
        # Lista de balas actualmente en pantalla.
        self.shoot_cooldown_timer = 0
        # Cuenta cuantos cuadros faltan para poder disparar de nuevo.
        self.explosions = []
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.running = True
        self.frame_count = 0
        self.difficulty_level = 1
        self.spawn_rate = METEOR_SPAWN_RATE

        # Spawn initial meteors
        for _ in range(INITIAL_METEORS):
            self.spawn_meteor(speed=random.uniform(1, 3))

    def spawn_meteor(self, speed=None):
        """Spawn a new meteor at the top."""
        if len(self.meteors) < MAX_METEORS:
            self.meteors.append(Meteor(self.meteor_images, speed))

    def shoot(self):
        """Create a new bullet at the player's position, respecting the cooldown."""
        if self.shoot_cooldown_timer <= 0:
            bullet_x = self.player.x
            bullet_y = self.player.y - self.player.size // 2
            self.bullets.append(Bullet(bullet_x, bullet_y))
            self.shoot_cooldown_timer = SHOOT_COOLDOWN

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
                        self.restart()
                    return

                if event.key == pygame.K_SPACE:
                    self.shoot()

    def update(self):
        """Update game state."""
        if self.game_over:
            # Update explosions
            for exp in self.explosions:
                exp.update()
            self.explosions = [e for e in self.explosions if e.is_alive()]
            return

        self.frame_count += 1

        # Update score
        if self.frame_count % FPS == 0:
            self.score += SCORE_PER_SECOND

        # Update difficulty
        self.difficulty_level = 1 + self.score // 100
        self.spawn_rate = max(10, METEOR_SPAWN_RATE - self.difficulty_level * 2)

        # Spawn new meteors
        if self.frame_count % self.spawn_rate == 0:
            self.spawn_meteor()

        # Update shoot cooldown
        if self.shoot_cooldown_timer > 0:
            self.shoot_cooldown_timer -= 1

        # Update player
        keys_pressed = pygame.key.get_pressed()
        self.player.update(keys_pressed)

        # Update bullets
        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if not b.is_off_screen()]

        # Update meteors
        for meteor in self.meteors:
            meteor.update()

        # Remove off-screen meteors
        self.meteors = [m for m in self.meteors if not m.is_off_screen()]

        # Check bullet vs meteor collisions
        for bullet in self.bullets[:]:
            bullet_rect = bullet.get_rect()
            for meteor in self.meteors[:]:
                if bullet_rect.colliderect(meteor.get_rect()):
                    self.explosions.append(Explosion(meteor.x, meteor.y))
                    self.meteors.remove(meteor)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.score += SCORE_PER_METEOR_DESTROYED
                    break

        # Check player vs meteor collisions
        player_rect = self.player.get_rect()
        for meteor in self.meteors[:]:
            if player_rect.colliderect(meteor.get_rect()):
                if self.player.hit():
                    # Create explosion
                    self.explosions.append(Explosion(meteor.x, meteor.y))
                    self.meteors.remove(meteor)
                    self.score += SCORE_PER_DODGE

                    if self.player.lives <= 0:
                        self.game_over = True
                        if self.score > self.high_score:
                            self.high_score = self.score
                break

        # Update explosions
        for exp in self.explosions:
            exp.update()
        self.explosions = [e for e in self.explosions if e.is_alive()]

    def draw_background(self):
        """Draw the background image."""
        self.screen.blit(self.background_image, (0, 0))
        # Se dibuja la imagen de fondo completa, empezando en la esquina (0, 0).

    def draw_hud(self):
        """Draw heads-up display (score, lives, level)."""
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

        # Level
        level_text = self.font_small.render(
            f"Level: {self.difficulty_level}", True, BLUE
        )
        self.screen.blit(level_text, (WINDOW_WIDTH - level_text.get_width() - 10, 35))

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
        level_text = self.font_small.render(
            f"Level Reached: {self.difficulty_level}", True, BLUE
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

    def restart(self):
        """Restart the game."""
        self.player = Player(self.ship_image)
        self.meteors = []
        self.bullets = []
        self.shoot_cooldown_timer = 0
        self.explosions = []
        self.score = 0
        self.frame_count = 0
        self.difficulty_level = 1
        self.spawn_rate = METEOR_SPAWN_RATE
        self.game_over = False

        # Spawn initial meteors
        for _ in range(INITIAL_METEORS):
            self.spawn_meteor(speed=random.uniform(1, 3))

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

            # Draw bullets
            for bullet in self.bullets:
                bullet.draw(self.screen)

            # Draw explosions
            for exp in self.explosions:
                exp.draw(self.screen)

            # Draw player
            self.player.draw(self.screen)

            # Draw HUD
            self.draw_hud()

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
