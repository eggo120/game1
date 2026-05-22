import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
HAZARD_COOLDOWN_FRAMES = FPS * 2   # Up Arrow: 2 seconds
TRAP_COOLDOWN_FRAMES = FPS * 5     # Spacebar: 5 seconds
HAZARD_DURATION_FRAMES = FPS // 2  # Up Arrow hazard active: 0.5 seconds
HAZARD_WIDTH = 75
HAZARD_HEIGHT = 50

# Colors (RGB)
BG_COLOR = (30, 30, 30)
PLAYER_COLOR = (255, 0, 0)
AI_COLOR = (0, 255, 255)       # Normal AI (Cyan)
TRAPPED_COLOR = (180, 50, 255) # Trapped AI (Purple)
BOX_COLOR = (200, 30, 30)       # Deep Red for Lingering Zone
BOX_BORDER = (255, 100, 100)   # Light Red border for hazard visibility
TRAP_PROJ_COLOR = (180, 50, 255)
TEXT_COLOR = (255, 255, 255)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Survival Game: The Power Role")
clock = pygame.time.Clock()


class TrapProjectile:
    """A fast projectile that freezes survivors for 3 seconds on impact (Spacebar)"""
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 8
        self.speed = 10

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, TRAP_PROJ_COLOR, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class LingeringRectangle:
    """A 75x50 hazard in front of the player that follows them for 0.5 seconds (Up Arrow)"""
    def __init__(self, player):
        self.player = player
        self.duration = HAZARD_DURATION_FRAMES
        self.width = HAZARD_WIDTH
        self.height = HAZARD_HEIGHT
        self.top_left_x = 0
        self.top_left_y = 0
        self._sync_position()

    def _orient_size(self, dx, dy):
        if abs(dy) > abs(dx):
            return HAZARD_HEIGHT, HAZARD_WIDTH
        return HAZARD_WIDTH, HAZARD_HEIGHT

    def _sync_position(self):
        dx, dy = self.player.last_dx, self.player.last_dy
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
        else:
            dx, dy = 0, -1

        self.width, self.height = self._orient_size(dx, dy)
        offset_distance = self.player.radius + max(self.width, self.height) // 2 + 8
        center_x = self.player.x + dx * offset_distance
        center_y = self.player.y + dy * offset_distance
        self.top_left_x = center_x - (self.width // 2)
        self.top_left_y = center_y - (self.height // 2)

    def update(self):
        self.duration -= 1
        self._sync_position()

    def draw(self, surface):
        # Draw the solid zone
        pygame.draw.rect(surface, BOX_COLOR, (int(self.top_left_x), int(self.top_left_y), self.width, self.height))
        # Draw the threat perimeter line
        pygame.draw.rect(surface, BOX_BORDER, (int(self.top_left_x), int(self.top_left_y), self.width, self.height), 2)

    def get_rect(self):
        return pygame.Rect(self.top_left_x, self.top_left_y, self.width, self.height)


class Character:
    """Base setup for entities"""
    def __init__(self, x, y, color, speed, radius=15):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.radius = radius

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


class Player(Character):
    """The Power Role (WASD to move, Spacebar to trap, Up Arrow to drop hazard)"""
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_COLOR, speed=4, radius=18)
        self.last_dx = 0
        self.last_dy = -1  # Default direction is looking up
        self.hazard_cooldown = 0
        self.trap_cooldown = 0

    def tick_cooldowns(self):
        if self.hazard_cooldown > 0:
            self.hazard_cooldown -= 1
        if self.trap_cooldown > 0:
            self.trap_cooldown -= 1

    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1

        # Keep diagonal speeds consistent
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx * self.speed
        self.y += dy * self.speed

        # Update looking vector if currently moving
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            self.last_dx = dx / length
            self.last_dy = dy / length

        # Boundary constraints
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))


class SurvivorAI(Character):
    """The 4 Weak Roles trying to avoid you"""
    def __init__(self, x, y):
        super().__init__(x, y, AI_COLOR, speed=3.5, radius=12)
        self.dx = 0
        self.dy = 0
        self.trap_timer = 0

    def update(self, player_x, player_y):
        # Freeze action loop if trapped
        if self.trap_timer > 0:
            self.trap_timer -= 1
            self.color = TRAPPED_COLOR
            return

        self.color = AI_COLOR
        distance = math.hypot(self.x - player_x, self.y - player_y)

        # Always flee from the hunter (no detection range limit)
        if distance > 0:
            self.dx = (self.x - player_x) / distance
            self.dy = (self.y - player_y) / distance
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


# ---- Initialize Objects ----
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
survivors = [SurvivorAI(random.randint(50, SCREEN_WIDTH-50), random.randint(50, SCREEN_HEIGHT-50)) for _ in range(4)]
active_hazards = []
trap_projectiles = []

running = True
font = pygame.font.SysFont(None, 36)

# ---- Main Engine Loop ----
while running:
    # 1. Inputs & Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # UP ARROW: Small hazard box in front that follows the player briefly
            if event.key == pygame.K_UP and player.hazard_cooldown <= 0:
                hazard_zone = LingeringRectangle(player)
                active_hazards.append(hazard_zone)
                player.hazard_cooldown = HAZARD_COOLDOWN_FRAMES

            # SPACEBAR: Shoots a freeze missile
            if event.key == pygame.K_SPACE and player.trap_cooldown <= 0:
                projectile = TrapProjectile(player.x, player.y, player.last_dx, player.last_dy)
                trap_projectiles.append(projectile)
                player.trap_cooldown = TRAP_COOLDOWN_FRAMES

    # 2. Update System Logic
    player.tick_cooldowns()
    player.handle_input()

    # Process hazard timelines
    for hazard in active_hazards[:]:
        hazard.update()
        if hazard.duration <= 0:
            active_hazards.remove(hazard)

    # Process trap flying physics
    for trap in trap_projectiles[:]:
        trap.update()
        if trap.x < 0 or trap.x > SCREEN_WIDTH or trap.y < 0 or trap.y > SCREEN_HEIGHT:
            trap_projectiles.remove(trap)

    # Process Survivor status and threat detection
    for survivor in survivors[:]:
        survivor.update(player.x, player.y)

        # Threat Check 1: Melee contact body collision
        dist_to_player = math.hypot(player.x - survivor.x, player.y - survivor.y)
        if dist_to_player < (player.radius + survivor.radius):
            survivors.remove(survivor)
            continue

        # Threat Check 2: Hit by a freezing trap projectile
        for trap in trap_projectiles[:]:
            if trap.get_rect().colliderect(survivor.get_rect()):
                survivor.trap_timer = 180  # Keeps them trapped for 180 frames (3 seconds)
                trap_projectiles.remove(trap)

        # Threat Check 3: Walked into a lingering death rectangle
        for hazard in active_hazards:
            if hazard.get_rect().colliderect(survivor.get_rect()):
                survivors.remove(survivor)
                break

    # 3. Frame Rendering Engine
    screen.fill(BG_COLOR)

    # Render environmental threats background-first
    for hazard in active_hazards:
        hazard.draw(screen)

    for trap in trap_projectiles:
        trap.draw(screen)

    # Render characters foreground-last
    player.draw(screen)
    for survivor in survivors:
        survivor.draw(screen)

    # UI Overlay display
    text = font.render(f"Survivors Left: {len(survivors)}", True, TEXT_COLOR)
    screen.blit(text, (10, 10))

    if len(survivors) == 0:
        win_text = font.render("YOU ELIMINATED EVERYONE! YOU WIN!", True, PLAYER_COLOR)
        screen.blit(win_text, (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
