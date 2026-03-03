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
        surface.fill((20, 20, 20))

        pygame.draw.circle(surface, (0, 255, 0), self.start_point, 8)
        pygame.draw.circle(surface, (255, 0, 0), self.goal_point, 8)

        for obs in self.obstacles:
            pygame.draw.line(surface, (128, 0, 128), obs[0], obs[1], 4)

        if self.status != "LOSS":
            self.rocket.draw(surface)

        current_time = self.end_time if self.status != "PLAYING" else (time.time() - self.start_time)
        
        info_texts = [
            f"Time: {current_time:.2f}s",
            f"Speed: {self.rocket.speed:.1f}",
            "UP/DOWN: Move vertically",
            "RIGHT/LEFT: Change speed"
        ]
        
        for i, text in enumerate(info_texts):
            img = self.font.render(text, True, (255, 255, 255))
            surface.blit(img, (10, 10 + i * 25))

        if self.status == "WIN":
            msg = self.font.render(f"YOU WIN in {current_time:.2f}s! Press ENTER to design again.", True, (0, 255, 0))
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, surface.get_height()//2))
        elif self.status == "LOSS":
            msg = self.font.render("CRASHED! Press ENTER to design again.", True, (255, 0, 0))
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, surface.get_height()//2))