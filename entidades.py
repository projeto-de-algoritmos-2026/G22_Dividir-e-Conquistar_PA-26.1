import math
import random
import pygame
from constantes import LARGURA, ALTURA


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


class Player:
    def __init__(self):
        self.pos = [LARGURA//2, ALTURA//2]
        self.radius = 10
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
        if keys[pygame.K_w]: self.pos[1] -= self.speed
        if keys[pygame.K_s]: self.pos[1] += self.speed
        if keys[pygame.K_a]: self.pos[0] -= self.speed
        if keys[pygame.K_d]: self.pos[0] += self.speed
        self.pos[0] = max(0, min(LARGURA, self.pos[0]))
        self.pos[1] = max(0, min(ALTURA, self.pos[1]))
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer < 0:
                self.invulnerable_timer = 0

    def draw(self, surf):
        pygame.draw.circle(surf, (60,180,75), (int(self.pos[0]), int(self.pos[1])), self.radius)
        gun_length = 20
        gx = self.pos[0] + math.cos(self.weapon_angle) * gun_length
        gy = self.pos[1] + math.sin(self.weapon_angle) * gun_length
        pygame.draw.line(surf, (200,200,50), (int(self.pos[0]), int(self.pos[1])), (int(gx), int(gy)), 4)

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
        angle = math.atan2(ty-y, tx-x)
        self.vel = [math.cos(angle)*12, math.sin(angle)*12]
        self.radius = 4

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def draw(self, surf):
        pygame.draw.circle(surf, (255,200,50), (int(self.pos[0]), int(self.pos[1])), self.radius)


class Zombie:
    def __init__(self, x, y, strength=10):
        self.pos = [x, y]
        self.base_speed = 0.7 + random.random()*0.6
        self.speed = self.base_speed
        self.radius = 8
        self.health = 20 + int(strength/2)
        self.strength = strength
        self.group_id = None
        self.is_alpha = False

    def update(self, player_pos):
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        d = math.hypot(dx, dy)
        if d > 0:
            self.pos[0] += dx/d * self.speed
            self.pos[1] += dy/d * self.speed

    def draw(self, surf):
        color = (220,50,50) if not self.is_alpha else (200,30,200)
        pygame.draw.circle(surf, color, (int(self.pos[0]), int(self.pos[1])), self.radius)
        if self.is_alpha:
            cx = int(self.pos[0])
            cy = int(self.pos[1]) - self.radius - 6
            points = [
                (cx-10, cy+6),
                (cx-5, cy-2),
                (cx, cy+6),
                (cx+5, cy-2),
                (cx+10, cy+6)
            ]
            pygame.draw.polygon(surf, (255,215,0), points)
            pygame.draw.polygon(surf, (180,140,0), points, 2)
