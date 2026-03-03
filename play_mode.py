import pygame
import time
from rocket import Rocket
from geometry import segments_intersect, distance

class PlayMode:
    def __init__(self, start_point, goal_point, obstacles):
        self.start_point = start_point
        self.goal_point = goal_point
        self.obstacles = obstacles
        self.rocket = Rocket(start_point[0], start_point[1])
        self.start_time = time.time()
        self.font = pygame.font.SysFont(None, 24)
        self.status = "PLAYING" # PLAYING, WIN, LOSS
        self.end_time = 0

    def handle_event(self, event):
        if self.status != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return "DESIGN"
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
            ((old_x, old_y), (new_x, new_y)) # Catch fast movements skipping through lines
        ]

        for obs in self.obstacles:
            for edge in edges:
                if segments_intersect(edge[0], edge[1], obs[0], obs[1]):
                    self.status = "LOSS"
                    self.end_time = time.time() - self.start_time
                    return

    def draw(self, surface):
        surface.fill((5, 5, 20)) # Very dark space

        # Stars
        for i in range(30):
            x = (i * 137 + 50) % surface.get_width()
            y = (i * 563 + 50) % surface.get_height()
            pygame.draw.circle(surface, (80, 80, 120), (x, y), 1)

        # Draw Goal glow
        glow_size = int(15 + math.sin(time.time() * 5) * 5)
        pygame.draw.circle(surface, (100, 0, 0), self.goal_point, glow_size + 5)
        pygame.draw.circle(surface, (255, 0, 0), self.goal_point, 10)
        pygame.draw.circle(surface, (255, 255, 255), self.goal_point, 12, 1)

        # Draw Start
        pygame.draw.circle(surface, (0, 100, 0), self.start_point, 15)
        pygame.draw.circle(surface, (0, 255, 0), self.start_point, 8)

        for obs in self.obstacles:
            pygame.draw.line(surface, (180, 50, 255), obs[0], obs[1], 4)
            # Add neon glow to obstacles
            pygame.draw.line(surface, (100, 0, 150), obs[0], obs[1], 8, 1)

        if self.status != "LOSS":
            self.rocket.draw(surface)

        current_time = self.end_time if self.status != "PLAYING" else (time.time() - self.start_time)
        
        # HUD Panel
        hud_rect = pygame.Rect(10, 10, 220, 110)
        pygame.draw.rect(surface, (20, 20, 40, 180), hud_rect, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 200), hud_rect, 1, border_radius=5)

        info_texts = [
            f"TIME: {current_time:.2f}s",
            f"SPEED: {self.rocket.speed:.1f}",
            "UP/DOWN: Vertical",
            "L/R: Speed"
        ]
        
        for i, text in enumerate(info_texts):
            img = self.font.render(text, True, (0, 255, 255))
            surface.blit(img, (20, 20 + i * 22))

        if self.status == "WIN":
            overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 50, 0, 150))
            surface.blit(overlay, (0, 0))
            msg = self.font.render(f"MISSION SUCCESS! Time: {current_time:.2f}s", True, (255, 255, 255))
            hint = self.font.render("Press ENTER to return to Architect Mode", True, (200, 255, 200))
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, surface.get_height()//2 - 20))
            surface.blit(hint, (surface.get_width()//2 - hint.get_width()//2, surface.get_height()//2 + 20))
        elif self.status == "LOSS":
            overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            msg = self.font.render("CRITICAL FAILURE - Rocket Destroyed", True, (255, 100, 100))
            hint = self.font.render("Press ENTER to Try Again", True, (255, 200, 200))
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, surface.get_height()//2 - 20))
            surface.blit(hint, (surface.get_width()//2 - hint.get_width()//2, surface.get_height()//2 + 20))