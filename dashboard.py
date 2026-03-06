import pygame
import sqlite3
import json

class Dashboard:
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
            self.font_btn = pygame.font.SysFont("Arial", 24, bold=True)
            self.font_list = pygame.font.SysFont("Arial", 18)
        except:
            self.font_title = pygame.font.SysFont(None, 48)
            self.font_btn = pygame.font.SysFont(None, 24)
            self.font_list = pygame.font.SysFont(None, 18)
        
        self.maps = self.load_maps()
        self.selected_map_idx = -1
        self.buttons = [
            {"text": "NEW CUSTOM GAME", "rect": pygame.Rect(300, 200, 200, 50), "action": "NEW"},
            {"text": "LOAD SELECTED MAP", "rect": pygame.Rect(300, 480, 200, 50), "action": "LOAD"}
        ]

    def load_maps(self):
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, start_point, goal_point, obstacles FROM maps ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.buttons:
                    if btn["rect"].collidepoint(event.pos):
                        if btn["action"] == "NEW":
                            return "NEW", None
                        if btn["action"] == "LOAD" and self.selected_map_idx != -1:
                            m = self.maps[self.selected_map_idx]
                            return "LOAD", {
                                "start": json.loads(m[2]),
                                "goal": json.loads(m[3]),
                                "obstacles": json.loads(m[4])
                            }
                
                # Check list clicks
                for i in range(len(self.maps)):
                    rect = pygame.Rect(250, 280 + i*30, 300, 25)
                    if rect.collidepoint(event.pos):
                        self.selected_map_idx = i
        return None, None

    def draw(self, surface):
        surface.fill((10, 10, 30))
        
        title = self.font_title.render("ROCKET DUEL", True, (0, 255, 255))
        surface.blit(title, (400 - title.get_width()//2, 80))

        for btn in self.buttons:
            color = (0, 150, 255) if btn["action"] == "NEW" else (0, 200, 100)
            if btn["action"] == "LOAD" and self.selected_map_idx == -1:
                color = (100, 100, 100)
            pygame.draw.rect(surface, color, btn["rect"], border_radius=5)
            txt = self.font_btn.render(btn["text"], True, (255, 255, 255))
            surface.blit(txt, (btn["rect"].centerx - txt.get_width()//2, btn["rect"].centery - txt.get_height()//2))

        # Map list
        list_label = self.font_btn.render("SAVED MAPS:", True, (255, 255, 255))
        surface.blit(list_label, (250, 255))
        
        for i, m in enumerate(self.maps):
            color = (255, 255, 0) if i == self.selected_map_idx else (200, 200, 200)
            txt = self.font_list.render(f"{i+1}. {m[1]}", True, color)
            surface.blit(txt, (260, 285 + i*30))
