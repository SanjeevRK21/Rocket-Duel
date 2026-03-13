import pygame
import math
import random

class Rocket:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        self.max_speed = 5.0
        self.radius = 10
        self.angle = 0.0       # degrees, 0 = right, 90 = down
        self.rot_speed = 3.0   # degrees per frame
        self.particles = []
        self.path_taken = [(float(x), float(y))]

    def update(self, dt):
        keys = pygame.key.get_pressed()

        # A = anticlockwise (decrease angle), D = clockwise (increase angle)
        if keys[pygame.K_a]:
            self.angle -= self.rot_speed
        if keys[pygame.K_d]:
            self.angle += self.rot_speed

        # RIGHT = accelerate, LEFT = decelerate
        if keys[pygame.K_RIGHT]:
            self.speed += 0.15
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        if keys[pygame.K_LEFT]:
            self.speed -= 0.15
            if self.speed < 0:
                self.speed = 0

        # Move in direction rocket is facing
        rad = math.radians(self.angle)
        dir_x = math.cos(rad)
        dir_y = math.sin(rad)
        self.x += dir_x * self.speed
        self.y += dir_y * self.speed

        # Record path
        if len(self.path_taken) == 0 or _dist((self.x, self.y), self.path_taken[-1]) > 3:
            self.path_taken.append((self.x, self.y))

        # Flame particles emitted behind the rocket
        if self.speed > 0.3:
            count = max(1, int(self.speed * 1.5))
            for _ in range(count):
                px = self.x - dir_x * 13 + random.uniform(-4, 4)
                py = self.y - dir_y * 13 + random.uniform(-4, 4)
                speed_factor = 1.0 + self.speed * 0.3
                self.particles.append({
                    "pos": [px, py],
                    "vel": [-dir_x * speed_factor + random.uniform(-0.5, 0.5),
                            -dir_y * speed_factor + random.uniform(-0.5, 0.5)],
                    "life": 1.0,
                    "color": random.choice([(255, 100, 0), (255, 200, 0), (0, 200, 255), (200, 50, 255)])
                })

        for p in self.particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 0.06
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        # Draw path trace with electric cyan
        if len(self.path_taken) > 1:
            pygame.draw.lines(surface, (0, 180, 255), False, self.path_taken, 1)

        # Particles
        for p in self.particles:
            alpha = int(max(0, min(255, p["life"] * 255)))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha), (3, 3), 3)
            surface.blit(s, (int(p["pos"][0] - 3), int(p["pos"][1] - 3)))

        # Rocket body as triangle pointing in angle direction
        rad = math.radians(self.angle)
        tip = (self.x + 15 * math.cos(rad), self.y + 15 * math.sin(rad))
        left = (self.x + 10 * math.cos(rad + math.radians(140)),
                self.y + 10 * math.sin(rad + math.radians(140)))
        right = (self.x + 10 * math.cos(rad - math.radians(140)),
                 self.y + 10 * math.sin(rad - math.radians(140)))

        # Outer glow (electric blue)
        glow_pts = [
            (tip[0] + 2*math.cos(rad), tip[1] + 2*math.sin(rad)),
            (left[0], left[1]),
            (right[0], right[1])
        ]
        pygame.draw.polygon(surface, (0, 100, 255), glow_pts, 3)
        # Body
        pygame.draw.polygon(surface, (220, 240, 255), [tip, left, right])
        pygame.draw.polygon(surface, (0, 200, 255), [tip, left, right], 2)


def _dist(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
