import pygame
import random
import math
import sqlite3
import json

PRESET_SHAPES = {
    "Wall H":  [(-50, 0, 50, 0)],
    "Wall V":  [(0, -50, 0, 50)],
    "Diag /":  [(-50, 50, 50, -50)],
    "Diag BS": [(-50, -50, 50, 50)],
    "Long H":  [(-80, 0, 80, 0)],
    "Long V":  [(0, -80, 0, 80)],
    "L-Shape": [(-50, 0, 50, 0), (50, 0, 50, -60)],
    "T-Shape": [(-50, 0, 50, 0), (0, 0, 0, 50)],
    "Z-Shape": [(-50,-30, 0,-30), (0,-30, 0,30), (0,30, 50,30)],
    "Cross":   [(-50, 0, 50, 0), (0, -50, 0, 50)],
}

PALETTE_COLORS = [
    (180, 0, 255), (255, 0, 180), (0, 180, 255),
    (255, 80, 0),  (0, 255, 150), (200, 0, 255),
    (255, 200, 0), (0, 255, 255), (255, 60, 120), (100, 200, 255)
]

def draw_lightning(surface, p1, p2, color, width=1, jitter=6, segs=5):
    pts = [p1]
    for i in range(1, segs):
        t = i / segs
        pts.append((
            p1[0] + (p2[0]-p1[0])*t + random.uniform(-jitter, jitter),
            p1[1] + (p2[1]-p1[1])*t + random.uniform(-jitter, jitter),
        ))
    pts.append(p2)
    pygame.draw.lines(surface, color, False, pts, width)


class DesignMode:
    CANVAS_RIGHT = 640

    def __init__(self, snd=None):
        self.start_point = None
        self.goal_point  = None
        self.obstacles   = []
        self.current_drawing_start = None
        self.saving  = False
        self.snd     = snd

        self.preset_names   = list(PRESET_SHAPES.keys())
        self.selected_preset = None
        self.palette_hover   = -1
        self.lightning_bolts = []

        try:
            self.font_main = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_sub  = pygame.font.SysFont("Arial", 15)
            self.font_pal  = pygame.font.SysFont("Arial", 13, bold=True)
        except:
            self.font_main = pygame.font.SysFont(None, 22)
            self.font_sub  = pygame.font.SysFont(None, 15)
            self.font_pal  = pygame.font.SysFont(None, 13)

        # Reduced star count
        self.stars = [(random.randint(0, 800), random.randint(0, 600),
                       random.random()) for _ in range(60)]

        # ── Pre-compute palette rects (avoid creating Rect objects every frame) ──
        self._pal_rects = [
            pygame.Rect(self.CANVAS_RIGHT + 8, 160 + i*38, 144, 32)
            for i in range(len(self.preset_names))
        ]

        # ── Pre-render static sidebar texts ──────────────────────────────────
        self._surf_pal_title = self.font_main.render("OBSTACLES", True, (150, 50, 255))
        self._surf_drag      = self.font_sub.render("Drag=Draw",  True, (120,120,120))
        self._surf_undo      = self.font_sub.render("RClick=Undo",True, (120,120,120))
        self._surf_sep       = self.font_sub.render("-- PRESETS --", True, (80, 0, 160))
        self._surf_ctrl      = self.font_sub.render(
            "PILOT: A/D=Rotate  LEFT/RIGHT=Speed", True, (80, 80, 150))

        # ── Pre-render palette item labels ────────────────────────────────────
        self._pal_label_surfs = [
            self.font_pal.render(name, True, PALETTE_COLORS[i % len(PALETTE_COLORS)])
            for i, name in enumerate(self.preset_names)
        ]

        # ── Instruction bar overlay (pre-built, updated when text changes) ────
        self._inst_bar = pygame.Surface((self.CANVAS_RIGHT, 110))
        self._inst_bar.set_alpha(175)
        self._inst_bar.fill((0, 0, 0))
        self._last_inst_key = None   # track when instruction changes

        # Cached instruction and mode text surfaces
        self._surf_inst = None
        self._surf_mode = None
        self._surf_title_bar = self.font_main.render("ARCHITECT MODE", True, (0, 200, 255))

        # ── Preset preview surface (reused every frame, not re-allocated) ─────
        self._preview_surf = pygame.Surface((self.CANVAS_RIGHT, 600), pygame.SRCALPHA)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _palette_rect(self, idx):
        return self._pal_rects[idx]

    def _place_preset(self, cx, cy):
        name = self.selected_preset
        if name not in PRESET_SHAPES:
            return
        new_segs = []
        for dx1, dy1, dx2, dy2 in PRESET_SHAPES[name]:
            new_segs.append(((int(cx+dx1), int(cy+dy1)), (int(cx+dx2), int(cy+dy2))))
        self.obstacles.extend(new_segs)
        if self.snd:
            self.snd.play("place")
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

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            mx, my = pos
            for i, r in enumerate(self._pal_rects):
                if r.collidepoint(pos):
                    name = self.preset_names[i]
                    self.selected_preset = None if self.selected_preset == name else name
                    if self.snd:
                        self.snd.play("click")
                    return "DESIGN"
            if mx < self.CANVAS_RIGHT:
                if self.selected_preset:
                    self._place_preset(mx, my)
                elif self.start_point is None:
                    self.start_point = pos
                    if self.snd: self.snd.play("click")
                elif self.goal_point is None:
                    self.goal_point = pos
                    if self.snd: self.snd.play("click")
                else:
                    self.current_drawing_start = pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.current_drawing_start is not None:
                pos = event.pos
                if self.current_drawing_start != pos and pos[0] < self.CANVAS_RIGHT:
                    self.obstacles.append((self.current_drawing_start, pos))
                    if self.snd: self.snd.play("place")
                    self.lightning_bolts.append([15, self.current_drawing_start, pos, (180, 0, 255)])
                self.current_drawing_start = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.obstacles:
                self.obstacles.pop()
                if self.snd: self.snd.play("click")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and not self.saving:
                self.save_map()
                self.saving = True
                if self.snd: self.snd.play("click")
            if event.key == pygame.K_RETURN and self.start_point and self.goal_point:
                return "PLAY"

        return "DESIGN"

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self):
        mouse = pygame.mouse.get_pos()
        self.palette_hover = -1
        for i, r in enumerate(self._pal_rects):
            if r.collidepoint(mouse):
                self.palette_hover = i
                break
        self.lightning_bolts = [
            [t-1, p1, p2, c] for t, p1, p2, c in self.lightning_bolts if t > 1
        ]

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill((5, 5, 18))

        t = pygame.time.get_ticks()

        # Stars (reduced to 60)
        for sx, sy, size in self.stars:
            b = int(120 + 100 * math.sin(t * 0.001 * size))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy), 1 if size < 0.7 else 2)

        # Ambient lightning (reduced probability)
        if random.random() < 0.02:
            x1 = random.randint(0, self.CANVAS_RIGHT)
            y1 = random.randint(0, 600)
            draw_lightning(surface, (x1, y1),
                           (x1+random.randint(-120,120), y1+random.randint(-80,80)),
                           (80, 0, 160), width=1, jitter=8)

        # Palette sidebar background
        pygame.draw.rect(surface, (10, 0, 30), (self.CANVAS_RIGHT, 0, 160, 600))
        pygame.draw.line(surface, (120, 0, 255), (self.CANVAS_RIGHT, 0), (self.CANVAS_RIGHT, 600), 2)

        surface.blit(self._surf_pal_title, (self.CANVAS_RIGHT + 10, 10))
        surface.blit(self._surf_drag,      (self.CANVAS_RIGHT + 8, 60))
        surface.blit(self._surf_undo,      (self.CANVAS_RIGHT + 8, 76))
        surface.blit(self._surf_sep,       (self.CANVAS_RIGHT + 6, 130))

        # Palette buttons
        for i, name in enumerate(self.preset_names):
            r         = self._pal_rects[i]
            is_sel    = (self.selected_preset == name)
            is_hover  = (self.palette_hover == i)
            bg_col    = (60, 0, 120) if is_sel else (30, 0, 50) if is_hover else (15, 0, 30)
            brd_col   = (220, 0, 255) if is_sel else (100, 0, 200) if is_hover else (60, 0, 120)
            pygame.draw.rect(surface, bg_col, r, border_radius=4)
            pygame.draw.rect(surface, brd_col, r, 1, border_radius=4)
            surface.blit(self._pal_label_surfs[i], (r.x+6, r.y+9))
            # Mini preview
            col   = PALETTE_COLORS[i % len(PALETTE_COLORS)]
            scale = 0.18
            cx, cy = r.right - 28, r.centery
            for dx1, dy1, dx2, dy2 in PRESET_SHAPES[name]:
                pygame.draw.line(surface, col,
                                 (int(cx+dx1*scale), int(cy+dy1*scale)),
                                 (int(cx+dx2*scale), int(cy+dy2*scale)), 2)

        # Instruction bar — re-render text only when it changes
        if self.saving:
            inst_key = "saved"
            inst_str = "MAP SAVED!  PRESS ENTER TO START"
            icol = (0, 255, 150)
        elif self.start_point is None:
            inst_key = "no_start"
            inst_str = "CLICK CANVAS -> SET START POINT"
            icol = (255, 255, 200)
        elif self.goal_point is None:
            inst_key = "no_goal"
            inst_str = "CLICK CANVAS -> SET GOAL POINT"
            icol = (255, 200, 100)
        elif self.selected_preset:
            inst_key = f"place_{self.selected_preset}"
            inst_str = f"CLICK TO PLACE [{self.selected_preset}] | ENTER=GO | S=SAVE"
            icol = (200, 100, 255)
        else:
            inst_key = "draw"
            inst_str = "DRAG TO DRAW | ENTER=GO | S=SAVE | RClick=UNDO"
            icol = (200, 200, 200)

        if inst_key != self._last_inst_key:
            self._surf_inst   = self.font_sub.render(inst_str, True, icol)
            mode_str = "MODE: DRAW" if not self.selected_preset else f"PLACE: {self.selected_preset[:8]}"
            self._surf_mode   = self.font_sub.render(mode_str, True, (200, 200, 200))
            self._last_inst_key = inst_key

        surface.blit(self._inst_bar, (0, 0))
        surface.blit(self._surf_title_bar, (12, 10))
        surface.blit(self._surf_inst,      (12, 42))
        surface.blit(self._surf_ctrl,      (12, 65))

        if self._surf_mode:
            surface.blit(self._surf_mode, (self.CANVAS_RIGHT + 8, 40))

        # Obstacles
        for obs in self.obstacles:
            pygame.draw.line(surface, (70, 0, 90),   obs[0], obs[1], 8)
            pygame.draw.line(surface, (200, 0, 255),  obs[0], obs[1], 3)
            pygame.draw.circle(surface, (255, 80, 255), obs[0], 4)
            pygame.draw.circle(surface, (255, 80, 255), obs[1], 4)

        # Lightning bolts on fresh placements
        for timer, p1, p2, col in self.lightning_bolts:
            draw_lightning(surface, p1, p2, col[:3], width=2, jitter=6)

        # Live drawing preview
        if self.current_drawing_start:
            pos = pygame.mouse.get_pos()
            if pos[0] < self.CANVAS_RIGHT:
                draw_lightning(surface, self.current_drawing_start, pos,
                               (255, 255, 255), width=1, jitter=3)

        # Preset preview under cursor — reuse one surface, no re-allocation
        if self.selected_preset:
            mx, my = pygame.mouse.get_pos()
            if mx < self.CANVAS_RIGHT:
                self._preview_surf.fill((0, 0, 0, 0))
                for dx1, dy1, dx2, dy2 in PRESET_SHAPES[self.selected_preset]:
                    p1 = (int(mx+dx1), int(my+dy1))
                    p2 = (int(mx+dx2), int(my+dy2))
                    pygame.draw.line(self._preview_surf, (200, 100, 255, 130), p1, p2, 3)
                surface.blit(self._preview_surf, (0, 0))

        # Markers
        if self.start_point:
            pulse = int((math.sin(t * 0.01) + 1) * 3)
            pygame.draw.circle(surface, (0, 255, 100), self.start_point, 10+pulse, 2)
            pygame.draw.circle(surface, (0, 255, 100), self.start_point, 5)
            surface.blit(self.font_sub.render("START", True, (0, 255, 100)),
                         (self.start_point[0]-18, self.start_point[1]+13))

        if self.goal_point:
            pulse = int((math.cos(t * 0.01) + 1) * 3)
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 12+pulse, 2)
            pygame.draw.circle(surface, (255, 50, 50), self.goal_point, 5)
            surface.blit(self.font_sub.render("GOAL", True, (255, 50, 50)),
                         (self.goal_point[0]-14, self.goal_point[1]+13))
