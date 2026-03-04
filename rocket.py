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
        self.color = (255, 255, 255)
        self.angle = 0
        self.particles = []

    def update(self, goal_pos, dt):
        dx = goal_pos[0] - self.x
        dy = goal_pos[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
            self.angle = math.degrees(math.atan2(dy, dx))
        else:
            dir_x, dir_y = 1, 0

        # Automatic forward movement toward goal based on speed
        self.x += dir_x * self.speed
        self.y += dir_y * self.speed

        # Player vertical adjustments and speed control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.y -= 4.0
        if keys[pygame.K_DOWN]:
            self.y += 4.0
        if keys[pygame.K_RIGHT]:
            self.speed += 0.2
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        if keys[pygame.K_LEFT]:
            self.speed -= 0.2
            if self.speed < 0:
                self.speed = 0

        # Particle logic (visual only)
        if self.speed > 0.5:
            for _ in range(int(self.speed)):
                # Emit behind rocket
                px = self.x - dir_x * 12 + random.uniform(-3, 3)
                py = self.y - dir_y * 12 + random.uniform(-3, 3)
                self.particles.append({
                    "pos": [px, py],
                    "vel": [-dir_x * 2, -dir_y * 2],
                    "life": 1.0,
                    "color": random.choice([(255, 100, 0), (255, 200, 0), (255, 50, 0)])
                })
        
        for p in self.particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 0.05
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        # Draw particles
        for p in self.particles:
            alpha = int(p["life"] * 255)
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha), (2, 2), 2)
            surface.blit(s, (int(p["pos"][0]-2), int(p["pos"][1]-2)))

        # Draw Rocket body (triangle)
        points = [
            (self.x + 15 * math.cos(math.radians(self.angle)), self.y + 15 * math.sin(math.radians(self.angle))),
            (self.x + 10 * math.cos(math.radians(self.angle + 140)), self.y + 10 * math.sin(math.radians(self.angle + 140))),
            (self.x + 10 * math.cos(math.radians(self.angle - 140)), self.y + 10 * math.sin(math.radians(self.angle - 140)))
        ]
        pygame.draw.polygon(surface, (255, 255, 255), points)
        pygame.draw.polygon(surface, (0, 150, 255), points, 2) # Neon glow outline
