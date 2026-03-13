import pygame
import math
import random

MAX_PATH = 300   # cap path trace length to avoid slow polyline drawing

class Rocket:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        self.max_speed = 5.0
        self.radius = 10
        self.angle = 0.0       # degrees, 0 = right, 90 = down
        self.rot_speed = 3.0
        # particles stored as flat lists for speed: [x, y, vx, vy, life, r, g, b]
        self.particles = []
        self.path_taken = [(float(x), float(y))]

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.angle -= self.rot_speed
        if keys[pygame.K_d]:
            self.angle += self.rot_speed
        if keys[pygame.K_RIGHT]:
            self.speed = min(self.speed + 0.15, self.max_speed)
        if keys[pygame.K_LEFT]:
            self.speed = max(self.speed - 0.15, 0.0)

        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)
        self.x += dir_x * self.speed
        self.y += dir_y * self.speed

        # Path trace — capped
        lx, ly = self.path_taken[-1]
        dx, dy = self.x - lx, self.y - ly
        if dx*dx + dy*dy > 9:   # distance > 3
            self.path_taken.append((self.x, self.y))
            if len(self.path_taken) > MAX_PATH:
                self.path_taken = self.path_taken[-MAX_PATH:]

        # Emit flame particles (flat list, no dicts)
        if self.speed > 0.3:
            count = max(1, int(self.speed))
            sf = 1.0 + self.speed * 0.25
            COLORS = [(255, 100, 0), (255, 200, 0), (0, 200, 255), (200, 50, 255)]
            for _ in range(count):
                r, g, b = random.choice(COLORS)
                px = self.x - dir_x * 13 + random.uniform(-4, 4)
                py = self.y - dir_y * 13 + random.uniform(-4, 4)
                vx = -dir_x * sf + random.uniform(-0.4, 0.4)
                vy = -dir_y * sf + random.uniform(-0.4, 0.4)
                self.particles.append([px, py, vx, vy, 1.0, r, g, b])

        # Update particles (in-place, remove dead ones at end)
        alive = []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 0.07
            if p[4] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface):
        # Path trace
        if len(self.path_taken) > 1:
            pygame.draw.lines(surface, (0, 150, 220), False, self.path_taken, 1)

        # Particles — draw directly as circles, colour faded by life (no SRCALPHA per particle)
        for p in self.particles:
            life = p[4]
            # Dim the colour by life fraction for fade effect
            fade = max(0.0, min(1.0, life))
            col = (int(p[5]*fade), int(p[6]*fade), int(p[7]*fade))
            pygame.draw.circle(surface, col, (int(p[0]), int(p[1])), 3)

        # Rocket triangle
        rad = math.radians(self.angle)
        tip   = (self.x + 15*math.cos(rad),               self.y + 15*math.sin(rad))
        left  = (self.x + 10*math.cos(rad+math.radians(140)), self.y + 10*math.sin(rad+math.radians(140)))
        right = (self.x + 10*math.cos(rad-math.radians(140)), self.y + 10*math.sin(rad-math.radians(140)))

        pygame.draw.polygon(surface, (220, 240, 255), [tip, left, right])
        pygame.draw.polygon(surface, (0, 200, 255), [tip, left, right], 2)


def _dist(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
