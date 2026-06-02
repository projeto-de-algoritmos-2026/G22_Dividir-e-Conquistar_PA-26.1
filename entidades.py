import math
import random
import os
import pygame
from constantes import LARGURA, ALTURA


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# Module-level sprite cache (loaded on demand)
_ZOMBIE_SPRITE = None
_ZOMBIE_ALPHA_SPRITE = None
_SHOOTER_SPRITE = None

# scale multiplier for zombie sprites (increase to make zombies larger)
ZOMBIE_SCALE = 2.5


def _load_sprites():
    """Load sprite images from the local assets/ directory into module globals.

    This is safe to call multiple times; it will no-op after the first successful load.
    """
    global _ZOMBIE_SPRITE, _ZOMBIE_ALPHA_SPRITE, _SHOOTER_SPRITE
    if _ZOMBIE_SPRITE is not None or _ZOMBIE_ALPHA_SPRITE is not None or _SHOOTER_SPRITE is not None:
        return
    try:
        base = os.path.dirname(__file__)
        assets = os.path.join(base, 'assets')
        zpath = os.path.join(assets, 'zombie.png')
        apath = os.path.join(assets, 'zombie_alpha.png')
        spath = os.path.join(assets, 'shooter.png')
        if os.path.exists(zpath):
            _ZOMBIE_SPRITE = pygame.image.load(zpath).convert_alpha()
        if os.path.exists(apath):
            _ZOMBIE_ALPHA_SPRITE = pygame.image.load(apath).convert_alpha()
        if os.path.exists(spath):
            _SHOOTER_SPRITE = pygame.image.load(spath).convert_alpha()
    except Exception:
        # If anything goes wrong, leave sprites as None and rely on fallback drawing
        _ZOMBIE_SPRITE = None
        _ZOMBIE_ALPHA_SPRITE = None
        _SHOOTER_SPRITE = None


class Player:
    def __init__(self):
        _load_sprites()
        self.pos = [LARGURA // 2, ALTURA // 2]
        self.radius = 20
        self.speed = 4
        self.health = 100
        self.weapon_angle = 0.0
        self.invulnerable_timer = 0.0
        self.invulnerable_duration = 0.8

    def set_aim(self, target_pos):
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        self.weapon_angle = math.atan2(dy, dx)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.pos[1] -= self.speed
        if keys[pygame.K_s]:
            self.pos[1] += self.speed
        if keys[pygame.K_a]:
            self.pos[0] -= self.speed
        if keys[pygame.K_d]:
            self.pos[0] += self.speed
        self.pos[0] = max(0, min(LARGURA, self.pos[0]))
        self.pos[1] = max(0, min(ALTURA, self.pos[1]))
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer < 0:
                self.invulnerable_timer = 0

    def draw(self, surf):
        try:
            _load_sprites()
            if _SHOOTER_SPRITE is not None:
                size = 48
                sprite = pygame.transform.smoothscale(_SHOOTER_SPRITE, (size, size))
                deg = -math.degrees(self.weapon_angle)
                rotated = pygame.transform.rotate(sprite, deg)
                rect = rotated.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
                surf.blit(rotated, rect)
                return
        except Exception:
            pass
        pygame.draw.circle(surf, (60, 180, 75), (int(self.pos[0]), int(self.pos[1])), self.radius)
        gun_length = 20
        gx = self.pos[0] + math.cos(self.weapon_angle) * gun_length
        gy = self.pos[1] + math.sin(self.weapon_angle) * gun_length
        pygame.draw.line(surf, (200, 200, 50), (int(self.pos[0]), int(self.pos[1])), (int(gx), int(gy)), 4)

    def take_damage(self, amount):
        if self.invulnerable_timer > 0:
            return False
        self.health -= amount
        if self.health < 0:
            self.health = 0
        self.invulnerable_timer = self.invulnerable_duration
        return True


class Bullet:
    def __init__(self, x, y, tx, ty):
        self.pos = [x, y]
        angle = math.atan2(ty - y, tx - x)
        self.vel = [math.cos(angle) * 12, math.sin(angle) * 12]
        self.radius = 4
        # store angle for drawing rotated sprite
        self.angle = angle

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def draw(self, surf):
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        length = 12
        width = 5
        x, y = self.pos
        dx = cos_a * length
        dy = sin_a * length
        px = -sin_a * width / 2
        py = cos_a * width / 2
        points = [(x + dx, y + dy), (x - dx/3 + px, y - dy/3 + py), (x - dx/3 - px, y - dy/3 - py)]
        pygame.draw.polygon(surf, (255, 200, 50), points)
        pygame.draw.polygon(surf, (200, 150, 0), points, 1)


class Zombie:
    def __init__(self, x, y, strength=10):
        self.pos = [x, y]
        self.base_speed = 0.7 + random.random() * 0.6
        self.speed = self.base_speed
        self.radius = 8
        self.health = 20 + int(strength / 2)
        self.strength = strength
        self.group_id = None
        self.is_alpha = False
        # sprite caching per-instance (will be created on first draw if assets exist)
        self._sprite = None
        self._sprite_alpha = None

    def update(self, player_pos):
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        d = math.hypot(dx, dy)
        if d > 0:
            self.pos[0] += dx / d * self.speed
            self.pos[1] += dy / d * self.speed

    def draw(self, surf):
        # Try to use external sprite images if available (assets/zombie.png, assets/zombie_alpha.png)
        try:
            base = os.path.dirname(__file__)
            assets_dir = os.path.join(base, 'assets')
            zombie_path = os.path.join(assets_dir, 'zombie.png')
            alpha_path = os.path.join(assets_dir, 'zombie_alpha.png')
            # load global images from disk if present
            if os.path.exists(zombie_path) or os.path.exists(alpha_path):
                # determine desired pixel size from radius (apply scale multiplier)
                diameter = max(16, int(self.radius * 2 * ZOMBIE_SCALE))
                # normal zombie sprite
                if os.path.exists(zombie_path) and self._sprite is None:
                    try:
                        img = pygame.image.load(zombie_path).convert_alpha()
                        self._sprite = pygame.transform.smoothscale(img, (diameter, diameter))
                    except Exception:
                        self._sprite = None
                # alpha zombie sprite
                if os.path.exists(alpha_path) and self._sprite_alpha is None:
                    try:
                        img2 = pygame.image.load(alpha_path).convert_alpha()
                        self._sprite_alpha = pygame.transform.smoothscale(img2, (diameter, diameter))
                    except Exception:
                        self._sprite_alpha = None

                sprite = self._sprite_alpha if self.is_alpha and self._sprite_alpha is not None else self._sprite
                if sprite is not None:
                    w, h = sprite.get_size()
                    surf.blit(sprite, (int(self.pos[0] - w / 2), int(self.pos[1] - h / 2)))
                    return
        except Exception:
            # if anything goes wrong with image loading, fall back to simple drawing below
            pass

        # Fallback: simple circle drawing (original behavior)
        color = (220, 50, 50) if not self.is_alpha else (200, 30, 200)
        pygame.draw.circle(surf, color, (int(self.pos[0]), int(self.pos[1])), self.radius)
        if self.is_alpha:
            cx = int(self.pos[0])
            cy = int(self.pos[1]) - self.radius - 6
            points = [
                (cx - 10, cy + 6),
                (cx - 5, cy - 2),
                (cx, cy + 6),
                (cx + 5, cy - 2),
                (cx + 10, cy + 6),
            ]
            pygame.draw.polygon(surf, (255, 215, 0), points)
            pygame.draw.polygon(surf, (180, 140, 0), points, 2)
