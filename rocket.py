import pygame
import math
import random

MAX_PATH = 250

# Precomputed wing angle offsets in radians (constant)
_WING_A = math.radians(140)
_WING_B = math.radians(-140)

PARTICLE_COLORS = [(255, 100, 0), (255, 200, 0), (0, 200, 255), (200, 50, 255)]


class Rocket:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed     = 0.0
        self.max_speed = 5.0
        self.radius    = 10
        self.angle     = 0.0    # degrees
        self.rot_speed = 3.0
        self.particles = []     # flat list: [x, y, vx, vy, life, r, g, b]
        self.path_taken = [(float(x), float(y))]
        # Cache last trig result to avoid recomputing when angle unchanged
        self._last_angle = None
        self._cached_rad = 0.0
        self._cached_cos = 1.0
        self._cached_sin = 0.0

    def _get_trig(self):
        if self.angle != self._last_angle:
            self._last_angle = self.angle
            self._cached_rad = math.radians(self.angle)
            self._cached_cos = math.cos(self._cached_rad)
            self._cached_sin = math.sin(self._cached_rad)
        return self._cached_cos, self._cached_sin, self._cached_rad

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]: self.angle -= self.rot_speed
        if keys[pygame.K_d]: self.angle += self.rot_speed
        if keys[pygame.K_RIGHT]: self.speed = min(self.speed + 0.15, self.max_speed)
        if keys[pygame.K_LEFT]:  self.speed = max(self.speed - 0.15, 0.0)

        dir_x, dir_y, _ = self._get_trig()
        self.x += dir_x * self.speed
        self.y += dir_y * self.speed

        # Path trace — capped
        lx, ly = self.path_taken[-1]
        dx, dy = self.x - lx, self.y - ly
        if dx*dx + dy*dy > 9:
            self.path_taken.append((self.x, self.y))
            if len(self.path_taken) > MAX_PATH:
                del self.path_taken[0]   # faster than slice for small deletes

        # Emit flame particles
        if self.speed > 0.3:
            count = max(1, int(self.speed))
            sf = 1.0 + self.speed * 0.25
            for _ in range(count):
                cr, cg, cb = random.choice(PARTICLE_COLORS)
                px = self.x - dir_x * 13 + random.uniform(-4, 4)
                py = self.y - dir_y * 13 + random.uniform(-4, 4)
                self.particles.append([
                    px, py,
                    -dir_x*sf + random.uniform(-0.4, 0.4),
                    -dir_y*sf + random.uniform(-0.4, 0.4),
                    1.0, cr, cg, cb
                ])

        # Update particles in-place
        alive = []
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 0.07
            if p[4] > 0: alive.append(p)
        self.particles = alive

    def draw(self, surface):
        # Path trace
        if len(self.path_taken) > 1:
            pygame.draw.lines(surface, (0, 150, 220), False, self.path_taken, 1)

        # Particles
        for p in self.particles:
            life = p[4]
            pygame.draw.circle(surface,
                               (int(p[5]*life), int(p[6]*life), int(p[7]*life)),
                               (int(p[0]), int(p[1])), 3)

        # Rocket triangle (cached trig)
        dir_x, dir_y, rad = self._get_trig()
        cx, cy = self.x, self.y
        tip   = (cx + 15*dir_x, cy + 15*dir_y)
        left  = (cx + 10*math.cos(rad+_WING_A), cy + 10*math.sin(rad+_WING_A))
        right = (cx + 10*math.cos(rad+_WING_B), cy + 10*math.sin(rad+_WING_B))

        pygame.draw.polygon(surface, (220, 240, 255), [tip, left, right])
        pygame.draw.polygon(surface, (0, 200, 255),   [tip, left, right], 2)


def _dist(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
