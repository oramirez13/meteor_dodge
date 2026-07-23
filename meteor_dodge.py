#!/usr/bin/env python3
"""
Meteor Dodge - A survival game where you dodge falling meteors.

Controls:
    Mouse to move the player
    ESC to quit
    SPACE or ENTER to restart after game over

Author: Orami
"""

import pygame
import random
import sys
import math

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
DARK_GRAY = (40, 40, 40)
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


# ============================================================
# PLAYER CLASS
# ============================================================

class Player:
    """Player controlled by mouse movement."""

    def __init__(self):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT - 80
        self.size = PLAYER_SIZE
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.trail = []

    def update(self, mouse_pos):
        """Update player position based on mouse."""
        # Store trail positions
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)

        self.x = mouse_pos[0]
        self.y = mouse_pos[1]

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
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size
        )

    def draw(self, surface):
        """Draw the player with trail effect."""
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3)
            size = int(self.size * (i / len(self.trail)) * 0.5)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, BLUE, trail_rect)

        # Draw player (blink when invincible)
        if not self.invincible or self.invincible_timer % 10 < 5:
            rect = self.get_rect()
            pygame.draw.rect(surface, BLUE, rect)
            pygame.draw.rect(surface, WHITE, rect, 2)

            # Draw cockpit
            cockpit = pygame.Rect(self.x - 5, self.y - 8, 10, 12)
            pygame.draw.rect(surface, WHITE, cockpit)


# ============================================================
# METEOR CLASS
# ============================================================

class Meteor:
    """Falling meteor that the player must dodge."""

    def __init__(self, speed=None):
        self.size = random.randint(15, 35)
        self.x = random.randint(self.size, WINDOW_WIDTH - self.size)
        self.y = -self.size
        self.speed = speed or random.uniform(METEOR_MIN_SPEED, METEOR_MAX_SPEED)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)
        self.color = random.choice([RED, ORANGE, YELLOW])
        self.trail = []

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
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size
        )

    def draw(self, surface):
        """Draw the meteor with trail."""
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3)
            size = int(self.size * (i / len(self.trail)) * 0.6)
            if size > 0:
                trail_rect = pygame.Rect(tx - size // 2, ty - size // 2, size, size)
                pygame.draw.rect(surface, GRAY, trail_rect)

        # Draw meteor
        rect = self.get_rect()
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)


# ============================================================
# EXPLOSION CLASS
# ============================================================

class Explosion:
    """Visual effect when a meteor hits the player."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = []
        self.lifetime = 30

        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.randint(2, 6),
                "color": random.choice([RED, ORANGE, YELLOW, WHITE]),
            })

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
                    surface, p["color"],
                    (int(p["x"]), int(p["y"]), p["size"], p["size"])
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
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Liberation Sans", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Liberation Sans", 28)
        self.font_small = pygame.font.SysFont("Liberation Sans", 20)

        self.player = Player()
        self.meteors = []
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
            self.meteors.append(Meteor(speed))

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

        # Update player
        mouse_pos = pygame.mouse.get_pos()
        self.player.update(mouse_pos)

        # Update meteors
        for meteor in self.meteors:
            meteor.update()

        # Remove off-screen meteors
        self.meteors = [m for m in self.meteors if not m.is_off_screen()]

        # Check collisions
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

    def draw_stars(self):
        """Draw background stars."""
        # Use deterministic positions based on frame count for twinkling
        random.seed(42)  # Fixed seed for consistent star positions
        for _ in range(100):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(0, WINDOW_HEIGHT)
            brightness = random.randint(100, 255)
            size = random.choice([1, 1, 1, 2])
            twinkle = math.sin(self.frame_count * 0.05 + x) * 30
            color = (brightness + int(twinkle),) * 3
            color = tuple(max(0, min(255, c)) for c in color)
            pygame.draw.rect(self.screen, color, (x, y, size, size))
        random.seed()  # Reset random seed

    def draw_hud(self):
        """Draw heads-up display (score, lives, level)."""
        # Score
        score_text = self.font_small.render(
            f"Score: {self.score}", True, WHITE
        )
        self.screen.blit(score_text, (10, 10))

        # High Score
        high_text = self.font_small.render(
            f"High Score: {self.high_score}", True, YELLOW
        )
        self.screen.blit(high_text, (WINDOW_WIDTH - high_text.get_width() - 10, 10))

        # Lives
        lives_text = self.font_small.render(
            f"Lives: {self.player.lives}", True, GREEN
        )
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
        go_rect = go_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)
        )
        self.screen.blit(go_text, go_rect)

        # Final score
        score_text = self.font_medium.render(
            f"Score: {self.score}", True, WHITE
        )
        score_rect = score_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
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
        self.player = Player()
        self.meteors = []
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
            self.screen.fill(BLACK)
            self.draw_stars()

            # Draw meteors
            for meteor in self.meteors:
                meteor.draw(self.screen)

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
