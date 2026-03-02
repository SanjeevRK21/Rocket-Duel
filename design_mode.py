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
        surface.fill((20, 20, 20)) # Dark background
        
        instructions = [
            "DESIGN MODE (Player 1 - Architect)",
            "1. Click anywhere to set START point",
            "2. Click again to set GOAL point",
            "3. Click + drag to draw obstacles",
            "Press ENTER when ready to switch to Play Mode"
        ]
        for i, text in enumerate(instructions):
            img = self.font.render(text, True, (200, 200, 200))
            surface.blit(img, (10, 10 + i * 25))

        if self.start_point:
            pygame.draw.circle(surface, (0, 255, 0), self.start_point, 8)
        if self.goal_point:
            pygame.draw.circle(surface, (255, 0, 0), self.goal_point, 8)

        for obs in self.obstacles:
            pygame.draw.line(surface, (128, 0, 128), obs[0], obs[1], 4)

        if self.current_drawing_start:
            pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, (128, 0, 128), self.current_drawing_start, pos, 4)