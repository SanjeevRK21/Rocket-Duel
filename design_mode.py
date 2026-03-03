import pygame

class DesignMode:
    def __init__(self):
        self.start_point = None
        self.goal_point = None
        self.obstacles = []
        self.current_drawing_start = None
        self.font = pygame.font.SysFont(None, 24)

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
        surface.fill((10, 10, 25)) # Deep space blue
        
        # Draw some stars for atmosphere
        for i in range(20):
            x = (i * 137) % surface.get_width()
            y = (i * 563) % surface.get_height()
            pygame.draw.circle(surface, (100, 100, 150), (x, y), 1)

        instructions = [
            "DESIGN MODE",
            "Player 1: Architect",
            "",
            "1. Click for START (Green)",
            "2. Click for GOAL (Red)",
            "3. Drag to draw OBSTACLES (Purple)",
            "",
            "Press ENTER to Start the Duel"
        ]
        
        # Draw instruction panel
        panel_rect = pygame.Rect(10, 10, 300, 220)
        pygame.draw.rect(surface, (30, 30, 50), panel_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 60, 100), panel_rect, 2, border_radius=8)

        for i, text in enumerate(instructions):
            color = (0, 255, 0) if "START" in text else (255, 100, 100) if "GOAL" in text else (200, 200, 255)
            img = self.font.render(text, True, color)
            surface.blit(img, (25, 25 + i * 22))

        if self.start_point:
            pygame.draw.circle(surface, (0, 255, 0), self.start_point, 10)
            pygame.draw.circle(surface, (255, 255, 255), self.start_point, 12, 2)
        if self.goal_point:
            pygame.draw.circle(surface, (255, 0, 0), self.goal_point, 10)
            pygame.draw.circle(surface, (255, 255, 255), self.goal_point, 12, 2)

        for obs in self.obstacles:
            pygame.draw.line(surface, (180, 50, 255), obs[0], obs[1], 5)
            pygame.draw.circle(surface, (200, 100, 255), obs[0], 3)
            pygame.draw.circle(surface, (200, 100, 255), obs[1], 3)

        if self.current_drawing_start:
            pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, (220, 150, 255), self.current_drawing_start, pos, 3)