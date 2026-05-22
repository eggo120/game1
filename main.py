import pygame
import random
import math

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

HAZARD_COOLDOWN_FRAMES = FPS * 2
TRAP_COOLDOWN_FRAMES = FPS * 5
HAZARD_DURATION_FRAMES = FPS // 2
HAZARD_WIDTH = 75
HAZARD_HEIGHT = 50
SURVIVOR_BURST_CLOSE_RANGE = 120
SURVIVOR_BURST_CHANCE = 0.5
SURVIVOR_BURST_WINDUP_FRAMES = FPS // 2
SURVIVOR_BURST_DURATION_FRAMES = FPS
SURVIVOR_BURST_SIZE = 150
SURVIVOR_BURST_COOLDOWN_FRAMES = FPS * 7
PLAYER_STUN_FRAMES = FPS * 3
SKELETON_STUN_FRAMES = FPS * 5
SKELETON_SPEED = 10
KNOCKBACK_FORCE = 14
HEAVY_KNOCKBACK_FORCE = 28
STUN_IMMUNITY_FRAMES = FPS * 10
DASH_DURATION_FRAMES = FPS * 3
DASH_SPEED = 10
DASH_HITBOX_SIZE = 100
DASH_COOLDOWN_FRAMES = FPS * 8
DASH_STEER_MULT = 0.4  # 40% steering control during dash
DASH_BURST_RADIUS = 120
PORTAL_EDGE_WIDTH = 10
PORTAL_BUFFER = 30
PORTAL_WARP_COOLDOWN_FRAMES = FPS

HEALER_MAX_HP = 3
SHIELD_DURATION_FRAMES = FPS * 3
SHIELD_COOLDOWN_FRAMES = FPS * 8
SHIELD_RADIUS = 100
HEAL_ORB_COOLDOWN_FRAMES = FPS * 6
HEAL_ORB_SPEED = 4
NECROMANCER_SPEED = 2.8
MARK_PICKUP_RANGE = 18

# Colors
BG_COLOR = (30, 30, 30)
PLAYER_COLOR = (255, 0, 0)
ATTACKER_COLOR = (0, 255, 255)
LIFESAVER_COLOR = (100, 200, 255)
NECROMANCER_COLOR = (160, 80, 255)
HEALER_COLOR = (80, 255, 120)
TRAPPED_COLOR = (180, 50, 255)
BOX_COLOR = (200, 30, 30)
BOX_BORDER = (255, 100, 100)
TRAP_PROJ_COLOR = (180, 50, 255)
SURVIVOR_BURST_COLOR = (255, 180, 40)
SURVIVOR_BURST_BORDER = (255, 230, 120)
SURVIVOR_WINDUP_COLOR = (255, 120, 0)
PORTAL_COLOR = (70, 70, 200)
TEXT_COLOR = (255, 255, 255)
STUNNED_PLAYER_COLOR = (160, 160, 160)
SHIELD_COLOR = (120, 220, 255)
HEAL_ORB_COLOR = (50, 255, 100)
DEATH_MARK_COLOR = (200, 200, 200)
SKELETON_COLOR = (220, 220, 180)
HEART_COLOR = (255, 60, 80)
DEAD_X_COLOR = (255, 80, 80)
DASH_COLOR = (255, 80, 80, 80)
IMMUNITY_COLOR = (255, 255, 100)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Survival Game: The Power Role")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)


def _clamp_inside_screen(x, y):
    buf = PORTAL_BUFFER
    return (
        max(buf, min(SCREEN_WIDTH - buf, x)),
        max(buf, min(SCREEN_HEIGHT - buf, y)),
    )


def apply_portal(entity):
    if entity.warp_cooldown > 0:
        entity.warp_cooldown -= 1
        entity.x, entity.y = _clamp_inside_screen(entity.x, entity.y)
        return

    buf = PORTAL_BUFFER
    x, y = entity.x, entity.y
    warped = False
    if x < 0:
        x = SCREEN_WIDTH - buf
        warped = True
    elif x >= SCREEN_WIDTH:
        x = buf
        warped = True
    if y < 0:
        y = SCREEN_HEIGHT - buf
        warped = True
    elif y >= SCREEN_HEIGHT:
        y = buf
        warped = True

    entity.x, entity.y = x, y
    if warped:
        entity.warp_cooldown = PORTAL_WARP_COOLDOWN_FRAMES


def portal_wrap_projectile(x, y):
    buf = PORTAL_BUFFER
    if x < 0:
        x = SCREEN_WIDTH - buf
    elif x >= SCREEN_WIDTH:
        x = buf
    if y < 0:
        y = SCREEN_HEIGHT - buf
    elif y >= SCREEN_HEIGHT:
        y = buf
    return x, y


def random_spawn_pos():
    return (
        random.randint(PORTAL_BUFFER + 20, SCREEN_WIDTH - PORTAL_BUFFER - 20),
        random.randint(PORTAL_BUFFER + 20, SCREEN_HEIGHT - PORTAL_BUFFER - 20),
    )


class TrapProjectile:
    def __init__(self, x, y, dx, dy):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.radius = 8
        self.speed = 10

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.x, self.y = portal_wrap_projectile(self.x, self.y)

    def draw(self, surface):
        pygame.draw.circle(surface, TRAP_PROJ_COLOR, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class LingeringRectangle:
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
        offset = self.player.radius + max(self.width, self.height) // 2 + 8
        cx = self.player.x + dx * offset
        cy = self.player.y + dy * offset
        self.top_left_x = cx - self.width // 2
        self.top_left_y = cy - self.height // 2

    def update(self):
        self.duration -= 1
        self._sync_position()

    def draw(self, surface):
        r = (int(self.top_left_x), int(self.top_left_y), self.width, self.height)
        pygame.draw.rect(surface, BOX_COLOR, r)
        pygame.draw.rect(surface, BOX_BORDER, r, 2)

    def get_rect(self):
        return pygame.Rect(self.top_left_x, self.top_left_y, self.width, self.height)


class SurvivorBurst:
    def __init__(self, center_x, center_y):
        self.duration = SURVIVOR_BURST_DURATION_FRAMES
        self.size = SURVIVOR_BURST_SIZE
        half = self.size // 2
        self.top_left_x = center_x - half
        self.top_left_y = center_y - half

    def update(self):
        self.duration -= 1

    def draw(self, surface):
        r = (int(self.top_left_x), int(self.top_left_y), self.size, self.size)
        pygame.draw.rect(surface, SURVIVOR_BURST_COLOR, r)
        pygame.draw.rect(surface, SURVIVOR_BURST_BORDER, r, 3)

    def get_rect(self):
        return pygame.Rect(self.top_left_x, self.top_left_y, self.size, self.size)


class DeathMark:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        size = 14
        pygame.draw.line(surface, DEATH_MARK_COLOR, (x - size, y - size), (x + size, y + size), 3)
        pygame.draw.line(surface, DEATH_MARK_COLOR, (x + size, y - size), (x - size, y + size), 3)


class HealOrb:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 10
        self.used_on = set()

    def update(self, survivors):
        target = None
        best_dist = float("inf")
        for s in survivors:
            if not s.alive or s.health >= s.max_health:
                continue
            if id(s) in self.used_on:
                continue
            d = math.hypot(s.x - self.x, s.y - self.y)
            if d < best_dist:
                best_dist = d
                target = s

        if target is None:
            return

        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < target.radius + self.radius:
            target.health = min(target.max_health, target.health + 1)
            self.used_on.add(id(target))
            return

        if dist > 0:
            self.x += (dx / dist) * HEAL_ORB_SPEED
            self.y += (dy / dist) * HEAL_ORB_SPEED

    def draw(self, surface):
        pygame.draw.circle(surface, HEAL_ORB_COLOR, (int(self.x), int(self.y)), self.radius)


class Skeleton:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 10
        self.speed = SKELETON_SPEED
        self.alive = True

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, SKELETON_COLOR, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Character:
    def __init__(self, x, y, color, speed, radius=15):
        self.x, self.y = x, y
        self.color = color
        self.speed = speed
        self.radius = radius

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Player(Character):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_COLOR, speed=4, radius=18)
        self.last_dx, self.last_dy = 0, -1
        self.hazard_cooldown = 0
        self.trap_cooldown = 0
        self.stun_timer = 0
        self.stun_immunity_timer = 0
        self.warp_cooldown = 0
        self.knockback_x = 0.0
        self.knockback_y = 0.0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dx = 0.0
        self.dash_dy = -1.0

    def tick_cooldowns(self):
        was_stunned = self.stun_timer > 0
        if self.hazard_cooldown > 0:
            self.hazard_cooldown -= 1
        if self.trap_cooldown > 0:
            self.trap_cooldown -= 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if was_stunned and self.stun_timer == 0:
            self.stun_immunity_timer = STUN_IMMUNITY_FRAMES
        if self.stun_immunity_timer > 0:
            self.stun_immunity_timer -= 1
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

    def is_stunned(self):
        return self.stun_timer > 0

    def is_dashing(self):
        return self.dash_timer > 0

    def can_be_stunned(self):
        return self.stun_immunity_timer <= 0 and not self.is_dashing()

    def apply_stun(self, frames):
        if not self.can_be_stunned():
            return
        self.stun_timer = frames

    def apply_knockback(self, from_x, from_y, force=KNOCKBACK_FORCE):
        dx = self.x - from_x
        dy = self.y - from_y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.knockback_x = (dx / dist) * force
            self.knockback_y = (dy / dist) * force
        else:
            self.knockback_x, self.knockback_y = force, 0

    def start_dash(self):
        if self.dash_cooldown > 0 or self.is_stunned() or self.is_dashing():
            return
        length = math.hypot(self.last_dx, self.last_dy)
        if length > 0:
            self.dash_dx = self.last_dx / length
            self.dash_dy = self.last_dy / length
        self.dash_timer = DASH_DURATION_FRAMES
        self.dash_cooldown = DASH_COOLDOWN_FRAMES

    def get_dash_hitbox(self):
        half = DASH_HITBOX_SIZE // 2
        return pygame.Rect(
            int(self.x - half), int(self.y - half), DASH_HITBOX_SIZE, DASH_HITBOX_SIZE
        )

    def dash_end_burst(self, survivors, death_marks):
        for survivor in survivors:
            if not survivor.alive:
                continue
            dist = math.hypot(survivor.x - self.x, survivor.y - self.y)
            if dist <= DASH_BURST_RADIUS:
                survivor.apply_knockback(self.x, self.y, HEAVY_KNOCKBACK_FORCE)

    def draw_dash_hitbox(self, surface):
        hitbox = self.get_dash_hitbox()
        dash_surf = pygame.Surface((hitbox.width, hitbox.height), pygame.SRCALPHA)
        dash_surf.fill((255, 60, 60, 70))
        surface.blit(dash_surf, (hitbox.x, hitbox.y))

    def handle_input(self):
        if self.is_stunned():
            self.x += self.knockback_x
            self.y += self.knockback_y
            self.knockback_x *= 0.85
            self.knockback_y *= 0.85
            apply_portal(self)
            return

        if self.is_dashing():
            self.dash_timer -= 1
            self.x += self.dash_dx * DASH_SPEED
            self.y += self.dash_dy * DASH_SPEED

            keys = pygame.key.get_pressed()
            steer_x, steer_y = 0, 0
            if keys[pygame.K_a]:
                steer_x = -1
            if keys[pygame.K_d]:
                steer_x = 1
            if keys[pygame.K_w]:
                steer_y = -1
            if keys[pygame.K_s]:
                steer_y = 1
            if steer_x != 0 and steer_y != 0:
                steer_x *= 0.707
                steer_y *= 0.707

            steer_speed = self.speed * DASH_STEER_MULT
            self.x += steer_x * steer_speed
            self.y += steer_y * steer_speed
            apply_portal(self)

            if steer_x != 0 or steer_y != 0:
                slen = math.hypot(steer_x, steer_y)
                blend = 0.35
                self.dash_dx = self.dash_dx * (1 - blend) + (steer_x / slen) * blend
                self.dash_dy = self.dash_dy * (1 - blend) + (steer_y / slen) * blend
                dlen = math.hypot(self.dash_dx, self.dash_dy)
                if dlen > 0:
                    self.dash_dx /= dlen
                    self.dash_dy /= dlen
            return

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_s]:
            dy = 1
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx * self.speed + self.knockback_x
        self.y += dy * self.speed + self.knockback_y
        self.knockback_x *= 0.7
        self.knockback_y *= 0.7
        apply_portal(self)

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            self.last_dx = dx / length
            self.last_dy = dy / length


class SurvivorAI(Character):
    ROLE_COLORS = {
        "attacker": ATTACKER_COLOR,
        "lifesaver": LIFESAVER_COLOR,
        "necromancer": NECROMANCER_COLOR,
        "healer": HEALER_COLOR,
    }

    def __init__(self, x, y, role):
        speed = NECROMANCER_SPEED if role == "necromancer" else 3.5
        super().__init__(x, y, self.ROLE_COLORS[role], speed=speed, radius=12)
        self.role = role
        self.alive = True
        self.dx, self.dy = 0, 0
        self.trap_timer = 0
        self.windup_timer = 0
        self.burst_cooldown = 0
        self.warp_cooldown = 0
        self.shield_timer = 0
        self.shield_cooldown = 0
        self.heal_orb_cooldown = 0
        self.max_health = HEALER_MAX_HP if role == "healer" else 1
        self.health = self.max_health
        self.kb_x = 0.0
        self.kb_y = 0.0

    def apply_knockback(self, from_x, from_y, force=HEAVY_KNOCKBACK_FORCE):
        dx = self.x - from_x
        dy = self.y - from_y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.kb_x += (dx / dist) * force
            self.kb_y += (dy / dist) * force

    def is_shielded(self, all_survivors):
        if self.shield_timer > 0:
            return True
        for s in all_survivors:
            if not s.alive or s.role != "lifesaver":
                continue
            if s.shield_timer > 0 and math.hypot(s.x - self.x, s.y - self.y) <= SHIELD_RADIUS:
                return True
        return False

    def die(self, death_marks):
        if not self.alive:
            return
        self.alive = False
        death_marks.append(DeathMark(self.x, self.y))

    def take_hunter_hit(self, death_marks, all_survivors):
        if not self.alive or self.is_shielded(all_survivors):
            return
        self.health -= 1
        if self.health <= 0:
            self.die(death_marks)

    def draw(self, surface):
        if not self.alive:
            x, y = int(self.x), int(self.y)
            size = 14
            pygame.draw.line(surface, DEAD_X_COLOR, (x - size, y - size), (x + size, y + size), 3)
            pygame.draw.line(surface, DEAD_X_COLOR, (x + size, y - size), (x - size, y + size), 3)
            return

        super().draw(surface)

        if self.role == "healer" and self.health > 0:
            for i in range(self.max_health):
                hx = int(self.x - 18 + i * 14)
                hy = int(self.y - self.radius - 18)
                if i < self.health:
                    pygame.draw.circle(surface, HEART_COLOR, (hx, hy), 5)
                else:
                    pygame.draw.circle(surface, (60, 60, 60), (hx, hy), 5, 1)

        if self.role == "lifesaver" and self.shield_timer > 0:
            pygame.draw.circle(surface, SHIELD_COLOR, (int(self.x), int(self.y)), self.radius + 8, 2)

    def _flee(self, player_x, player_y):
        dist = math.hypot(self.x - player_x, self.y - player_y)
        if dist > 0:
            self.dx = (self.x - player_x) / dist
            self.dy = (self.y - player_y) / dist
        self.x += self.dx * self.speed + self.kb_x
        self.y += self.dy * self.speed + self.kb_y
        self.kb_x *= 0.85
        self.kb_y *= 0.85
        apply_portal(self)

    def _move_toward(self, tx, ty):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed + self.kb_x
            self.y += (dy / dist) * self.speed + self.kb_y
        self.kb_x *= 0.85
        self.kb_y *= 0.85
        apply_portal(self)

    def update(self, player_x, player_y, survivor_bursts, death_marks, all_survivors, heal_orbs):
        if not self.alive:
            return

        if self.burst_cooldown > 0:
            self.burst_cooldown -= 1
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
        if self.heal_orb_cooldown > 0:
            self.heal_orb_cooldown -= 1

        if self.role == "lifesaver":
            if self.shield_timer > 0:
                self.shield_timer -= 1
            elif self.shield_cooldown <= 0:
                self.shield_timer = SHIELD_DURATION_FRAMES
                self.shield_cooldown = SHIELD_COOLDOWN_FRAMES

        if self.trap_timer > 0:
            self.trap_timer -= 1
            self.color = TRAPPED_COLOR
            apply_portal(self)
            return

        distance = math.hypot(self.x - player_x, self.y - player_y)

        # Necromancer: seek death marks
        if self.role == "necromancer" and death_marks:
            nearest = min(death_marks, key=lambda m: math.hypot(m.x - self.x, m.y - self.y))
            md = math.hypot(nearest.x - self.x, nearest.y - self.y)
            if md <= MARK_PICKUP_RANGE:
                death_marks.remove(nearest)
                return "spawn_skeleton", nearest.x, nearest.y
            self.color = NECROMANCER_COLOR
            self._move_toward(nearest.x, nearest.y)
            return None

        # Attacker burst
        if self.role == "attacker":
            if self.windup_timer > 0:
                self.windup_timer -= 1
                self.color = SURVIVOR_WINDUP_COLOR
                if self.windup_timer <= 0:
                    survivor_bursts.append(SurvivorBurst(self.x, self.y))
                    self.burst_cooldown = SURVIVOR_BURST_COOLDOWN_FRAMES
                apply_portal(self)
                return None

            if (
                distance <= SURVIVOR_BURST_CLOSE_RANGE
                and self.burst_cooldown <= 0
                and random.random() < SURVIVOR_BURST_CHANCE
            ):
                self.windup_timer = SURVIVOR_BURST_WINDUP_FRAMES
                apply_portal(self)
                return None

        # Healer: spawn tracking heal orb
        if self.role == "healer" and self.heal_orb_cooldown <= 0:
            heal_orbs.append(HealOrb(self.x, self.y))
            self.heal_orb_cooldown = HEAL_ORB_COOLDOWN_FRAMES

        self.color = self.ROLE_COLORS[self.role]
        self._flee(player_x, player_y)
        return None


def build_survivor_roster():
    roles = ["attacker"] * 4 + ["lifesaver"] * 2 + ["necromancer"] * 2 + ["healer"] * 2
    random.shuffle(roles)
    roster = []
    for role in roles:
        x, y = random_spawn_pos()
        roster.append(SurvivorAI(x, y, role))
    return roster


def count_alive(survivors):
    return sum(1 for s in survivors if s.alive)


# ---- Initialize ----
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
survivors = build_survivor_roster()
active_hazards = []
trap_projectiles = []
survivor_bursts = []
death_marks = []
heal_orbs = []
skeletons = []

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and not player.is_stunned():
            if event.key == pygame.K_UP and player.hazard_cooldown <= 0 and not player.is_dashing():
                active_hazards.append(LingeringRectangle(player))
                player.hazard_cooldown = HAZARD_COOLDOWN_FRAMES
            if event.key == pygame.K_SPACE and player.trap_cooldown <= 0 and not player.is_dashing():
                trap_projectiles.append(TrapProjectile(player.x, player.y, player.last_dx, player.last_dy))
                player.trap_cooldown = TRAP_COOLDOWN_FRAMES
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                player.start_dash()

    player.tick_cooldowns()
    was_dashing = player.is_dashing()
    player.handle_input()
    if was_dashing and not player.is_dashing():
        player.dash_end_burst(survivors, death_marks)

    if player.is_dashing():
        dash_box = player.get_dash_hitbox()
        for survivor in survivors:
            if survivor.alive and dash_box.colliderect(survivor.get_rect()):
                survivor.die(death_marks)

    for hazard in active_hazards[:]:
        hazard.update()
        if hazard.duration <= 0:
            active_hazards.remove(hazard)

    for burst in survivor_bursts[:]:
        burst.update()
        if burst.duration <= 0:
            survivor_bursts.remove(burst)
        elif burst.get_rect().colliderect(player.get_rect()) and player.can_be_stunned():
            player.apply_stun(PLAYER_STUN_FRAMES)
            player.apply_knockback(burst.top_left_x + burst.size / 2, burst.top_left_y + burst.size / 2, HEAVY_KNOCKBACK_FORCE)

    for trap in trap_projectiles[:]:
        trap.update()

    for orb in heal_orbs[:]:
        orb.update(survivors)

    for skeleton in skeletons[:]:
        if not skeleton.alive:
            continue
        skeleton.update(player)
        if skeleton.get_rect().colliderect(player.get_rect()) and player.can_be_stunned():
            player.apply_stun(SKELETON_STUN_FRAMES)
            player.apply_knockback(skeleton.x, skeleton.y, HEAVY_KNOCKBACK_FORCE)
            skeleton.alive = False

    for survivor in survivors:
        result = survivor.update(
            player.x, player.y, survivor_bursts, death_marks, survivors, heal_orbs
        )
        if result and result[0] == "spawn_skeleton":
            skeletons.append(Skeleton(result[1], result[2]))

        if not survivor.alive:
            continue

        for trap in trap_projectiles[:]:
            if trap.get_rect().colliderect(survivor.get_rect()):
                if not survivor.is_shielded(survivors):
                    survivor.trap_timer = 180
                trap_projectiles.remove(trap)
                break

        for hazard in active_hazards:
            if hazard.get_rect().colliderect(survivor.get_rect()):
                survivor.take_hunter_hit(death_marks, survivors)
                break

    # Draw
    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, PORTAL_COLOR, (0, 0, PORTAL_EDGE_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(screen, PORTAL_COLOR, (SCREEN_WIDTH - PORTAL_EDGE_WIDTH, 0, PORTAL_EDGE_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(screen, PORTAL_COLOR, (0, 0, SCREEN_WIDTH, PORTAL_EDGE_WIDTH))
    pygame.draw.rect(screen, PORTAL_COLOR, (0, SCREEN_HEIGHT - PORTAL_EDGE_WIDTH, SCREEN_WIDTH, PORTAL_EDGE_WIDTH))

    for hazard in active_hazards:
        hazard.draw(screen)
    for burst in survivor_bursts:
        burst.draw(screen)
    for trap in trap_projectiles:
        trap.draw(screen)
    for orb in heal_orbs:
        orb.draw(screen)

    for survivor in survivors:
        if survivor.is_shielded(survivors) and survivor.alive:
            pygame.draw.circle(
                screen, SHIELD_COLOR, (int(survivor.x), int(survivor.y)), SHIELD_RADIUS, 1
            )
        survivor.draw(screen)

    for skeleton in skeletons:
        if skeleton.alive:
            skeleton.draw(screen)

    if player.is_dashing():
        player.draw_dash_hitbox(screen)
    if player.is_stunned():
        pygame.draw.circle(screen, STUNNED_PLAYER_COLOR, (int(player.x), int(player.y)), player.radius)
    else:
        player.draw(screen)
    if player.stun_immunity_timer > 0:
        pygame.draw.circle(screen, IMMUNITY_COLOR, (int(player.x), int(player.y)), player.radius + 12, 2)

    alive = count_alive(survivors)
    screen.blit(small_font.render(f"Alive: {alive}/10", True, TEXT_COLOR), (10, 10))
    legend = "Shift=Dash | Cyan=Atk | Blue=Save | Purple=Necro | Green=Heal"
    screen.blit(small_font.render(legend, True, TEXT_COLOR), (10, 34))
    if player.dash_cooldown > 0 and not player.is_dashing():
        cd = player.dash_cooldown // FPS + 1
        screen.blit(small_font.render(f"Dash CD: {cd}s", True, TEXT_COLOR), (10, 58))
    if player.stun_immunity_timer > 0:
        sec = player.stun_immunity_timer // FPS + 1
        screen.blit(small_font.render(f"Stun immune: {sec}s", True, IMMUNITY_COLOR), (10, 82))

    if alive == 0:
        win = font.render("YOU ELIMINATED EVERYONE! YOU WIN!", True, PLAYER_COLOR)
        screen.blit(win, (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
