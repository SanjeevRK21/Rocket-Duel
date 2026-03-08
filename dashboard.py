import pygame
import sqlite3
import json

class Dashboard:
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
            self.font_btn = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_list = pygame.font.SysFont("Arial", 16)
        except:
            self.font_title = pygame.font.SysFont(None, 48)
            self.font_btn = pygame.font.SysFont(None, 20)
            self.font_list = pygame.font.SysFont(None, 16)
        
        self.maps = self.load_maps()
        self.selected_map_idx = -1
        self.buttons = [
            {"text": "NEW CUSTOM GAME", "rect": pygame.Rect(50, 180, 160, 45), "action": "NEW"},
            {"text": "LOAD SELECTED MAP", "rect": pygame.Rect(50, 235, 160, 45), "action": "LOAD"},
            {"text": "VIEW LEADERBOARD", "rect": pygame.Rect(50, 290, 160, 45), "action": "LEADERBOARD"}
        ]

    def load_maps(self):
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, start_point, goal_point, obstacles FROM maps ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_best_time(self, map_id):
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(time_taken) FROM scores WHERE map_id = ?", (map_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0]:
            return result[0]
        return None

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
                                "map_id": m[0],
                                "start": json.loads(m[2]),
                                "goal": json.loads(m[3]),
                                "obstacles": json.loads(m[4])
                            }
                        if btn["action"] == "LEADERBOARD":
                            return "LEADERBOARD", None
                
                # Check list clicks
                for i in range(len(self.maps)):
                    rect = pygame.Rect(250, 180 + i*28, 500, 25)
                    if rect.collidepoint(event.pos):
                        self.selected_map_idx = i
        return None, None

    def draw(self, surface):
        surface.fill((10, 10, 30))
        
        title = self.font_title.render("ROCKET DUEL", True, (0, 255, 255))
        surface.blit(title, (400 - title.get_width()//2, 50))

        for btn in self.buttons:
            color = (0, 150, 255) if btn["action"] == "NEW" else (0, 200, 100) if btn["action"] == "LOAD" else (200, 100, 0)
            if btn["action"] == "LOAD" and self.selected_map_idx == -1:
                color = (100, 100, 100)
            pygame.draw.rect(surface, color, btn["rect"], border_radius=5)
            txt = self.font_btn.render(btn["text"], True, (255, 255, 255))
            surface.blit(txt, (btn["rect"].centerx - txt.get_width()//2, btn["rect"].centery - txt.get_height()//2))

        # Map list
        list_label = self.font_btn.render("SAVED MAPS:", True, (255, 255, 255))
        surface.blit(list_label, (250, 155))
        
        for i, m in enumerate(self.maps):
            if i >= 12:
                break
            color = (255, 255, 0) if i == self.selected_map_idx else (200, 200, 200)
            best_time = self.get_best_time(m[0])
            time_str = f" [Best: {best_time:.2f}s]" if best_time else ""
            txt = self.font_list.render(f"{i+1}. {m[1]}{time_str}", True, color)
            surface.blit(txt, (260, 185 + i*28))


class Leaderboard:
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
            self.font_label = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_score = pygame.font.SysFont("monospace", 16)
            self.font_btn = pygame.font.SysFont("Arial", 18, bold=True)
        except:
            self.font_title = pygame.font.SysFont(None, 40)
            self.font_label = pygame.font.SysFont(None, 20)
            self.font_score = pygame.font.SysFont(None, 16)
            self.font_btn = pygame.font.SysFont(None, 18)
        
        self.back_btn = pygame.Rect(350, 550, 100, 40)
        self.leaderboards = self.load_leaderboards()

    def load_leaderboards(self):
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.name, s.time_taken, s.created_at
            FROM maps m
            LEFT JOIN scores s ON m.id = s.map_id
            ORDER BY m.name, s.time_taken ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        boards = {}
        for row in rows:
            map_id, map_name, time, created = row
            if map_id not in boards:
                boards[map_id] = {"name": map_name, "scores": []}
            if time is not None:
                boards[map_id]["scores"].append((time, created))
        
        return boards

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.collidepoint(event.pos):
                return "DASHBOARD"
        return "LEADERBOARD"

    def draw(self, surface):
        surface.fill((10, 10, 30))
        
        title = self.font_title.render("LEADERBOARD", True, (255, 200, 0))
        surface.blit(title, (400 - title.get_width()//2, 30))

        y = 80
        for map_id in sorted(self.leaderboards.keys()):
            board = self.leaderboards[map_id]
            map_label = self.font_label.render(f"📍 {board['name']}", True, (0, 255, 100))
            surface.blit(map_label, (100, y))
            y += 30
            
            if board['scores']:
                for rank, (time, _) in enumerate(board['scores'][:5]):
                    medal = "🥇" if rank == 0 else "🥈" if rank == 1 else "🥉" if rank == 2 else f"#{rank+1}"
                    score_txt = self.font_score.render(f"{medal:>3} {time:.2f}s", True, (255, 255, 255))
                    surface.blit(score_txt, (120, y))
                    y += 22
            else:
                no_scores = self.font_score.render("No times recorded yet", True, (150, 150, 150))
                surface.blit(no_scores, (120, y))
                y += 22
            
            y += 10
            if y > 480:
                break
        
        pygame.draw.rect(surface, (0, 150, 200), self.back_btn, border_radius=5)
        btn_txt = self.font_btn.render("BACK", True, (255, 255, 255))
        surface.blit(btn_txt, (self.back_btn.centerx - btn_txt.get_width()//2, self.back_btn.centery - btn_txt.get_height()//2))
