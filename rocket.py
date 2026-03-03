import pygame
import math

class Rocket:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        self.max_speed = 5.0
        self.radius = 12
        self.color = (255, 255, 255)
        self.angle = 0
        try:
            self.original_image = pygame.image.load("rocket.png").convert_alpha()
            self.image = pygame.transform.scale(self.original_image, (32, 32))
            self.has_image = True
        except:
            self.has_image = False

    def update(self, goal_pos, dt):
        dx = goal_pos[0] - self.x
        dy = goal_pos[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
            # Calculate angle for rotation (in degrees, pygame uses counter-clockwise)
            # Math.atan2 returns radians, 0 is right. Pygame 0 is up.
            self.angle = -math.degrees(math.atan2(dy, dx)) - 90
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
        if self.has_image:
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated_image, rect)
        else:
            # Fallback to a triangle if image fails
            points = [
                (self.x, self.y - 15),
                (self.x - 10, self.y + 10),
                (self.x + 10, self.y + 10)
            ]
            # Simple rotation for fallback
            rad = math.radians(self.angle + 90)
            rot_points = []
            for px, py in points:
                tx, ty = px - self.x, py - self.y
                rx = tx * math.cos(rad) - ty * math.sin(rad)
                ry = tx * math.sin(rad) + ty * math.cos(rad)
                rot_points.append((rx + self.x, ry + self.y))
            pygame.draw.polygon(surface, self.color, rot_points)