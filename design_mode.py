import pygame
import random

class DesignMode:
    def __init__(self):
        self.start_point = None
        self.goal_point = None
        self.obstacles = []
        self.current_drawing_start = None
        try:
            self.font_main = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_sub = pygame.font.SysFont("Arial", 18)
        except:
            self.font_main = pygame.font.SysFont(None, 28)
            self.font_sub = pygame.font.SysFont(None, 18)
        
        self.stars = [(random.randint(0, 800), random.randint(0, 600), random.random()) for _ in range(100)]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                pos = event.pos
                if self.start_point is None:
                    self.start_point = pos
                elif self.goal_point is None:
                    self.goal_point = pos
                else:
                    self.current_drawing_start = pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.current_drawing_start is not None:
                pos = event.pos
                if self.current_drawing_start != pos: # prevent zero length obstacle
                    self.obstacles.append((self.current_drawing_start, pos))
                self.current_drawing_start = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.start_point and self.goal_point:
                    return "PLAY"
        return "DESIGN"

    def update(self):
        pass

    def draw(self, surface):
        surface.fill((5, 5, 15)) # Deep space blue
        
        # Stars
        for x, y, size in self.stars:
            brightness = int(150 + 105 * math.sin(pygame.time.get_ticks() * 0.001 * size))
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), 1 if size < 0.8 else 2)

        # UI Overlay
        overlay = pygame.Surface((800, 140), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, 800, 140))
        surface.blit(overlay, (0, 0))

        title = self.font_main.render("PHASE 1: ARCHITECT MODE", True, (0, 200, 255))
        surface.blit(title, (20, 15))

        instruction = ""
        if self.start_point is None:
            instruction = "CLICK TO SET START POINT"
        elif self.goal_point is None:
            instruction = "CLICK TO SET GOAL POINT"
        else:
            instruction = "CLICK + DRAG TO DRAW OBSTACLES | PRESS ENTER TO FINISH"
        
        inst_img = self.font_sub.render(instruction, True, (255, 255, 255))
        surface.blit(inst_img, (20, 50))

        # Markers
        if self.start_point:
            # Pulsing start marker
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 2
            pygame.draw.circle(surface, (0, 255, 100), self.start_point, 10 + pulse)
            pygame.draw.circle(surface, (255, 255, 255), self.start_point, 4)
            label = self.font_sub.render("START", True, (0, 255, 100))
            surface.blit(label, (self.start_point[0] - 20, self.start_point[1] + 15))

        if self.goal_point:
            pulse = (math.cos(pygame.time.get_ticks() * 0.01) + 1) * 2
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 12 + pulse, 2)
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 6)
            label = self.font_sub.render("GOAL", True, (255, 50, 50))
            surface.blit(label, (self.goal_point[0] - 15, self.goal_point[1] + 15))

        # Obstacles
        for obs in self.obstacles:
            # Glow effect
            pygame.draw.line(surface, (80, 0, 80), obs[0], obs[1], 8)
            pygame.draw.line(surface, (180, 0, 255), obs[0], obs[1], 3)
            pygame.draw.circle(surface, (180, 0, 255), obs[0], 3)
            pygame.draw.circle(surface, (180, 0, 255), obs[1], 3)

        if self.current_drawing_start:
            pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, (255, 255, 255), self.current_drawing_start, pos, 2)

import math # Ensure math is available for stars/pulses
