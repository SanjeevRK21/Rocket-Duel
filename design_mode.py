import pygame
import random
import math
import sqlite3
import json

# Preset obstacle shape definitions (as list of (dx1,dy1,dx2,dy2) relative to drop point)
PRESET_SHAPES = {
    "Wall H":    [(-50, 0, 50, 0)],
    "Wall V":    [(0, -50, 0, 50)],
    "Diag /":    [(-50, 50, 50, -50)],
    "Diag BS":   [(-50, -50, 50, 50)],
    "Long H":    [(-80, 0, 80, 0)],
    "Long V":    [(0, -80, 0, 80)],
    "L-Shape":   [(-50, 0, 50, 0), (50, 0, 50, -60)],
    "T-Shape":   [(-50, 0, 50, 0), (0, 0, 0, 50)],
    "Z-Shape":   [(-50, -30, 0, -30), (0, -30, 0, 30), (0, 30, 50, 30)],
    "Cross":     [(-50, 0, 50, 0), (0, -50, 0, 50)],
}

PALETTE_COLORS = [
    (180, 0, 255), (255, 0, 180), (0, 180, 255),
    (255, 80, 0),  (0, 255, 150), (200, 0, 255),
    (255, 200, 0), (0, 255, 255), (255, 60, 120), (100, 200, 255)
]

def draw_lightning(surface, p1, p2, color, width=1, jitter=6, segs=6):
    """Draw a jagged lightning-style line between p1 and p2."""
    pts = [p1]
    for i in range(1, segs):
        t = i / segs
        mx = p1[0] + (p2[0] - p1[0]) * t + random.uniform(-jitter, jitter)
        my = p1[1] + (p2[1] - p1[1]) * t + random.uniform(-jitter, jitter)
        pts.append((mx, my))
    pts.append(p2)
    pygame.draw.lines(surface, color, False, pts, width)


class DesignMode:
    CANVAS_RIGHT = 640  # canvas area width; right 160px is palette

    def __init__(self, snd=None):
        self.start_point = None
        self.goal_point = None
        self.obstacles = []          # list of ((x1,y1),(x2,y2))
        self.current_drawing_start = None
        self.saving = False
        self.snd = snd

        # Palette state
        self.preset_names = list(PRESET_SHAPES.keys())
        self.selected_preset = None  # None = draw-line mode
        self.palette_hover = -1

        # Lightning flash data
        self.lightning_bolts = []  # list of (timer, p1, p2, color)

        try:
            self.font_main = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_sub  = pygame.font.SysFont("Arial", 15)
            self.font_pal  = pygame.font.SysFont("Arial", 13, bold=True)
        except:
            self.font_main = pygame.font.SysFont(None, 22)
            self.font_sub  = pygame.font.SysFont(None, 15)
            self.font_pal  = pygame.font.SysFont(None, 13)

        self.stars = [(random.randint(0, 800), random.randint(0, 600), random.random())
                      for _ in range(120)]

    # ------------------------------------------------------------------ helpers
    def _palette_rect(self, idx):
        return pygame.Rect(self.CANVAS_RIGHT + 8, 160 + idx * 38, 144, 32)

    def _place_preset(self, cx, cy):
        name = self.selected_preset
        if name not in PRESET_SHAPES:
            return
        new_segs = []
        for dx1, dy1, dx2, dy2 in PRESET_SHAPES[name]:
            p1 = (int(cx + dx1), int(cy + dy1))
            p2 = (int(cx + dx2), int(cy + dy2))
            new_segs.append((p1, p2))
        self.obstacles.extend(new_segs)
        if self.snd:
            self.snd.play("place")
        # Spawn lightning flash at placement point
        for seg in new_segs:
            self.lightning_bolts.append([15, seg[0], seg[1], (180, 0, 255)])

    def save_map(self):
        if not self.start_point or not self.goal_point:
            return
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        name = f"Map {random.randint(100, 999)}"
        c.execute("INSERT INTO maps (name, start_point, goal_point, obstacles) VALUES (?,?,?,?)",
                  (name, json.dumps(self.start_point), json.dumps(self.goal_point),
                   json.dumps(self.obstacles)))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------ events
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            mx, my = pos

            # Palette click
            for i, name in enumerate(self.preset_names):
                if self._palette_rect(i).collidepoint(pos):
                    if self.selected_preset == name:
                        self.selected_preset = None   # deselect → draw mode
                    else:
                        self.selected_preset = name
                    if self.snd:
                        self.snd.play("click")
                    return "DESIGN"

            # Canvas click
            if mx < self.CANVAS_RIGHT:
                if self.selected_preset:
                    # Place preset shape
                    self._place_preset(mx, my)
                else:
                    # Set start/goal or start drawing
                    if self.start_point is None:
                        self.start_point = pos
                        if self.snd:
                            self.snd.play("click")
                    elif self.goal_point is None:
                        self.goal_point = pos
                        if self.snd:
                            self.snd.play("click")
                    else:
                        self.current_drawing_start = pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.current_drawing_start is not None:
                pos = event.pos
                if self.current_drawing_start != pos and pos[0] < self.CANVAS_RIGHT:
                    self.obstacles.append((self.current_drawing_start, pos))
                    if self.snd:
                        self.snd.play("place")
                    self.lightning_bolts.append(
                        [15, self.current_drawing_start, pos, (180, 0, 255)])
                self.current_drawing_start = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # Right-click removes last obstacle
            if self.obstacles:
                self.obstacles.pop()
                if self.snd:
                    self.snd.play("click")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and not self.saving:
                self.save_map()
                self.saving = True
                if self.snd:
                    self.snd.play("click")
            if event.key == pygame.K_RETURN:
                if self.start_point and self.goal_point:
                    return "PLAY"

        return "DESIGN"

    # ------------------------------------------------------------------ update
    def update(self):
        mouse = pygame.mouse.get_pos()
        self.palette_hover = -1
        for i in range(len(self.preset_names)):
            if self._palette_rect(i).collidepoint(mouse):
                self.palette_hover = i
                break
        # Tick down lightning bolts
        self.lightning_bolts = [[t - 1, p1, p2, c]
                                 for t, p1, p2, c in self.lightning_bolts if t > 0]

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        surface.fill((5, 5, 18))

        # Stars
        t = pygame.time.get_ticks()
        for sx, sy, size in self.stars:
            b = int(120 + 100 * math.sin(t * 0.001 * size))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy), 1 if size < 0.7 else 2)

        # Background ambient lightning arcs (slow random)
        if random.random() < 0.03:
            x1 = random.randint(0, self.CANVAS_RIGHT)
            y1 = random.randint(0, 600)
            x2 = x1 + random.randint(-120, 120)
            y2 = y1 + random.randint(-80, 80)
            draw_lightning(surface, (x1, y1), (x2, y2),
                           (80, 0, 160), width=1, jitter=8)

        # Palette panel background
        pygame.draw.rect(surface, (10, 0, 30), (self.CANVAS_RIGHT, 0, 160, 600))
        pygame.draw.line(surface, (120, 0, 255), (self.CANVAS_RIGHT, 0), (self.CANVAS_RIGHT, 600), 2)

        pal_title = self.font_main.render("OBSTACLES", True, (150, 50, 255))
        surface.blit(pal_title, (self.CANVAS_RIGHT + 10, 10))
        mode_lbl = self.font_sub.render(
            "MODE: DRAW" if not self.selected_preset else f"PLACE: {self.selected_preset[:8]}",
            True, (200, 200, 200))
        surface.blit(mode_lbl, (self.CANVAS_RIGHT + 8, 40))

        # Palette controls hint
        hint = self.font_sub.render("Drag=Draw", True, (120,120,120))
        hint2 = self.font_sub.render("RClick=Undo", True, (120,120,120))
        surface.blit(hint,  (self.CANVAS_RIGHT + 8, 60))
        surface.blit(hint2, (self.CANVAS_RIGHT + 8, 76))

        header_sep = self.font_sub.render("── PRESETS ──", True, (80, 0, 160))
        surface.blit(header_sep, (self.CANVAS_RIGHT + 6, 130))

        for i, name in enumerate(self.preset_names):
            r = self._palette_rect(i)
            is_selected = (self.selected_preset == name)
            is_hover    = (self.palette_hover == i)
            bg_col = (60, 0, 120) if is_selected else (30, 0, 50) if is_hover else (15, 0, 30)
            border_col = (220, 0, 255) if is_selected else (100, 0, 200) if is_hover else (60, 0, 120)
            pygame.draw.rect(surface, bg_col, r, border_radius=4)
            pygame.draw.rect(surface, border_col, r, 1, border_radius=4)
            col = PALETTE_COLORS[i % len(PALETTE_COLORS)]
            txt = self.font_pal.render(name, True, col)
            surface.blit(txt, (r.x + 6, r.y + 9))
            # Mini preview line
            segs = PRESET_SHAPES[name]
            scale = 0.18
            cx, cy = r.right - 28, r.centery
            for dx1, dy1, dx2, dy2 in segs:
                pygame.draw.line(surface, col,
                                 (int(cx + dx1*scale), int(cy + dy1*scale)),
                                 (int(cx + dx2*scale), int(cy + dy2*scale)), 2)

        # Instruction bar (top of canvas)
        overlay = pygame.Surface((self.CANVAS_RIGHT, 110), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 170), overlay.get_rect())
        surface.blit(overlay, (0, 0))

        title = self.font_main.render("ARCHITECT MODE", True, (0, 200, 255))
        surface.blit(title, (12, 10))

        if self.saving:
            inst = "MAP SAVED!  PRESS ENTER TO START"
            icol = (0, 255, 150)
        elif self.start_point is None:
            inst = "CLICK CANVAS → SET START POINT"
            icol = (255, 255, 200)
        elif self.goal_point is None:
            inst = "CLICK CANVAS → SET GOAL POINT"
            icol = (255, 200, 100)
        elif self.selected_preset:
            inst = f"CLICK TO PLACE  [{self.selected_preset}]  | ENTER=GO | S=SAVE"
            icol = (200, 100, 255)
        else:
            inst = "DRAG TO DRAW OBSTACLE | ENTER=GO | S=SAVE | RClick=UNDO"
            icol = (200, 200, 200)
        inst_img = self.font_sub.render(inst, True, icol)
        surface.blit(inst_img, (12, 42))

        # Controls reminder
        ctrl = self.font_sub.render("PILOT: A/D=Rotate  LEFT/RIGHT=Speed", True, (80, 80, 150))
        surface.blit(ctrl, (12, 65))

        # Obstacles
        for obs in self.obstacles:
            pygame.draw.line(surface, (70, 0, 90), obs[0], obs[1], 8)
            pygame.draw.line(surface, (200, 0, 255), obs[0], obs[1], 3)
            pygame.draw.circle(surface, (255, 80, 255), obs[0], 4)
            pygame.draw.circle(surface, (255, 80, 255), obs[1], 4)

        # Active lightning bolts on freshly-placed obstacles
        for timer, p1, p2, col in self.lightning_bolts:
            alpha = int(255 * timer / 15)
            draw_lightning(surface, p1, p2, (*col[:3], alpha), width=2, jitter=6)

        # Live drawing preview
        if self.current_drawing_start:
            pos = pygame.mouse.get_pos()
            if pos[0] < self.CANVAS_RIGHT:
                draw_lightning(surface, self.current_drawing_start, pos,
                               (255, 255, 255), width=1, jitter=3)

        # Live preset preview under cursor
        if self.selected_preset:
            mx, my = pygame.mouse.get_pos()
            if mx < self.CANVAS_RIGHT:
                for dx1, dy1, dx2, dy2 in PRESET_SHAPES[self.selected_preset]:
                    p1 = (int(mx + dx1), int(my + dy1))
                    p2 = (int(mx + dx2), int(my + dy2))
                    s = pygame.Surface((800, 600), pygame.SRCALPHA)
                    pygame.draw.line(s, (200, 100, 255, 130), p1, p2, 3)
                    surface.blit(s, (0, 0))

        # Start / Goal markers
        if self.start_point:
            pulse = int((math.sin(t * 0.01) + 1) * 3)
            pygame.draw.circle(surface, (0, 255, 100), self.start_point, 10 + pulse, 2)
            pygame.draw.circle(surface, (0, 255, 100), self.start_point, 5)
            lbl = self.font_sub.render("START", True, (0, 255, 100))
            surface.blit(lbl, (self.start_point[0] - 18, self.start_point[1] + 13))

        if self.goal_point:
            pulse = int((math.cos(t * 0.01) + 1) * 3)
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 12 + pulse, 2)
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 5)
            lbl = self.font_sub.render("GOAL", True, (255, 50, 50))
            surface.blit(lbl, (self.goal_point[0] - 14, self.goal_point[1] + 13))
