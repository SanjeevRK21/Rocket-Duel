import pygame
import math

class Rocket:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        self.max_speed = 5.0
        self.radius = 10
        self.color = (255, 255, 255)

    def update(self, goal_pos, dt):
        dx = goal_pos[0] - self.x
        dy = goal_pos[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
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

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)