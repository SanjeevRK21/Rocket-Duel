import pygame
import time
import math
import random
import sqlite3
from rocket import Rocket
from geometry import segments_intersect, distance

class PlayMode:
    def __init__(self, start_point, goal_point, obstacles, map_id=None):
        self.start_point = start_point
        self.goal_point = goal_point
        self.obstacles = obstacles
        self.map_id = map_id
        self.rocket = Rocket(start_point[0], start_point[1])
        self.start_time = time.time()
        try:
            self.font_hud = pygame.font.SysFont("monospace", 20, bold=True)
            self.font_msg = pygame.font.SysFont("Arial", 36, bold=True)
        except:
            self.font_hud = pygame.font.SysFont(None, 20)
            self.font_msg = pygame.font.SysFont(None, 36)
        self.status = "PLAYING" # PLAYING, WIN, LOSS
        self.end_time = 0
        self.stars = [(random.randint(0, 800), random.randint(0, 600), random.random()) for _ in range(100)]

    def save_score(self):
        if self.map_id and self.status == "WIN":
            conn = sqlite3.connect('database.sqlite')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scores (map_id, time_taken) VALUES (?, ?)",
                           (self.map_id, self.end_time))
            conn.commit()
            conn.close()

    def handle_event(self, event):
        if self.status != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.save_score()
                return "DASHBOARD"
        return "PLAY"

    def update(self):
        if self.status != "PLAYING":
            return

        dt = 1.0/60.0
        
        old_x = self.rocket.x
        old_y = self.rocket.y

        self.rocket.update(self.goal_point, dt)

        new_x = self.rocket.x
        new_y = self.rocket.y

        # Check win condition
        if distance((new_x, new_y), self.goal_point) < self.rocket.radius + 8:
            self.status = "WIN"
            self.end_time = time.time() - self.start_time
            return

        # Check collision with obstacles
        r = self.rocket.radius
        edges = [
            ((new_x-r, new_y-r), (new_x+r, new_y-r)),
            ((new_x+r, new_y-r), (new_x+r, new_y+r)),
            ((new_x+r, new_y+r), (new_x-r, new_y+r)),
            ((new_x-r, new_y+r), (new_x-r, new_y-r)),
            ((old_x, old_y), (new_x, new_y))
        ]

        for obs in self.obstacles:
            for edge in edges:
                if segments_intersect(edge[0], edge[1], obs[0], obs[1]):
                    self.status = "LOSS"
                    self.end_time = time.time() - self.start_time
                    return

    def draw(self, surface):
        surface.fill((2, 2, 10)) # Very dark space

        # Stars
        for x, y, size in self.stars:
            brightness = int(100 + 155 * math.sin(pygame.time.get_ticks() * 0.001 * size))
            brightness = max(0, min(255, brightness)) # Clamp color values
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), 1 if size < 0.8 else 2)

        # Markers
        # Start
        pygame.draw.circle(surface, (0, 255, 100), self.start_point, 6)
        # Goal
        pulse = (math.cos(pygame.time.get_ticks() * 0.01) + 1) * 2
        pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 12 + pulse, 2)
        pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 6)

        # Obstacles
        for obs in self.obstacles:
            pygame.draw.line(surface, (100, 0, 150), obs[0], obs[1], 6)
            pygame.draw.line(surface, (200, 100, 255), obs[0], obs[1], 2)

        if self.status != "LOSS":
            self.rocket.draw(surface)

        # HUD
        current_time = self.end_time if self.status != "PLAYING" else (time.time() - self.start_time)
        
        hud_bg = pygame.Surface((200, 100), pygame.SRCALPHA)
        pygame.draw.rect(hud_bg, (0, 0, 0, 150), (0, 0, 200, 100), border_radius=10)
        surface.blit(hud_bg, (10, 10))

        time_txt = self.font_hud.render(f"TIME:  {current_time:.2f}s", True, (0, 255, 255))
        speed_txt = self.font_hud.render(f"SPEED: {self.rocket.speed:.1f}", True, (255, 255, 0))
        surface.blit(time_txt, (25, 25))
        surface.blit(speed_txt, (25, 55))

        if self.status == "WIN":
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 255, 0, 40))
            surface.blit(overlay, (0,0))
            msg = self.font_msg.render("MISSION ACCOMPLISHED", True, (0, 255, 100))
            sub = self.font_hud.render(f"TIME: {current_time:.2f}s | PRESS ENTER TO CONTINUE", True, (255, 255, 255))
            surface.blit(msg, (400 - msg.get_width()//2, 250))
            surface.blit(sub, (400 - sub.get_width()//2, 310))
        elif self.status == "LOSS":
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 40))
            surface.blit(overlay, (0,0))
            msg = self.font_msg.render("CRITICAL COLLISION", True, (255, 50, 50))
            sub = self.font_hud.render("PILOT LOST | PRESS ENTER TO RETURN", True, (255, 255, 255))
            surface.blit(msg, (400 - msg.get_width()//2, 250))
            surface.blit(sub, (400 - sub.get_width()//2, 310))
