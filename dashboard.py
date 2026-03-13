import pygame
import math
import random
import sqlite3
import json

# ─────────────────────────────────────────────────────────────────────────────
# Cosmic background
# ─────────────────────────────────────────────────────────────────────────────

class CosmicBackground:
    W, H   = 800, 600
    BH_X, BH_Y = 570, 305
    BH_R   = 38

    def __init__(self):
        self.frame = 0
        self._static  = self._build_static()
        self._galaxy  = self._build_galaxy()
        self._twinklers = [
            (random.randint(0, self.W), random.randint(0, self.H),
             random.uniform(0.8, 3.5))
            for _ in range(45)   # reduced from 55
        ]
        self._shots      = []
        self._shot_timer = random.randint(60, 120)
        self._disk_angle = 0.0
        # Precompute halo ring data (static geometry)
        self._halo_rings = []
        for i in range(7, 1, -1):
            hr = self.BH_R + 10 + i * 13
            intensity = max(0, 55 - i * 6)
            hcol = (min(255, intensity*3), min(255, intensity), intensity // 2)
            self._halo_rings.append((hr, hcol))

    def _build_static(self):
        surf = pygame.Surface((self.W, self.H))
        surf.fill((0, 0, 6))
        nb = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        nebulae = [
            (210, 160, 110, 70,  (100, 20, 180, 22), 6),
            (680, 200, 90,  55,  (20,  70, 180, 18), 5),
            (120, 430, 80,  55,  (180, 30,  20, 18), 5),
            (440, 530, 95,  60,  (20, 110, 130, 16), 5),
            (730,  90, 65,  45,  (140, 130,  10, 18), 4),
            (310, 380, 70,  45,  (60,  20, 140, 14), 4),
        ]
        for cx, cy, rx, ry, col, cnt in nebulae:
            for _ in range(cnt):
                ex = cx + random.randint(-rx//3, rx//3)
                ey = cy + random.randint(-ry//3, ry//3)
                er = rx + random.randint(-rx//4, rx//4)
                eh = ry + random.randint(-ry//4, ry//4)
                pygame.draw.ellipse(nb, col, (ex-er, ey-eh//2, er*2, eh))
        surf.blit(nb, (0, 0))
        for _ in range(400):
            x = random.randint(0, self.W)
            y = random.randint(0, self.H)
            b = random.randint(50, 170)
            tc = random.randint(0, 3)
            if   tc == 0: col = (b, b, b)
            elif tc == 1: col = (b, int(b*0.75), int(b*0.5))
            elif tc == 2: col = (int(b*0.6), int(b*0.7), b)
            else:         col = (b, b, int(b*0.6))
            pygame.draw.circle(surf, col, (x, y), 1)
        return surf

    def _build_galaxy(self):
        particles = []
        for arm in range(3):
            arm_off = (2 * math.pi / 3) * arm
            for i in range(90):
                t = i / 90
                radius = 55 + t * 195
                angle  = arm_off + t * 4.2 * math.pi + random.gauss(0, 0.28)
                if   t < 0.25: cr, cg, cb = 160, 180, 255
                elif t < 0.55: cr, cg, cb = 255, 255, 230
                else:           cr, cg, cb = 255, 170,  90
                b = random.uniform(0.35, 1.0)
                speed = max(0.00008, 0.00025 / (t + 0.05))
                size  = 1 if t > 0.25 else 2
                # Pre-multiply colour by brightness — avoids per-frame multiply
                pcol = (max(0,min(255,int(cr*b))), max(0,min(255,int(cg*b))), max(0,min(255,int(cb*b))))
                particles.append([angle, radius + random.uniform(-14, 14), size, pcol, speed])
        for _ in range(55):
            b = random.uniform(0.2, 0.55)
            pcol = (int(180*b), int(185*b), int(210*b))
            particles.append([
                random.uniform(0, 2*math.pi),
                random.uniform(30, 230),
                1, pcol,
                random.uniform(0.00004, 0.00018),
            ])
        return particles

    def update(self):
        self.frame += 1
        for p in self._galaxy:
            p[0] += p[4]
        self._disk_angle += 0.018
        self._shot_timer -= 1
        if self._shot_timer <= 0:
            spd = random.uniform(4, 9)
            ang = random.uniform(0.3, 0.7)
            self._shots.append([
                random.uniform(-30, self.W+30),
                random.uniform(-30, 180),
                spd * math.cos(ang), spd * math.sin(ang),
                1.0, random.randint(35, 90)
            ])
            self._shot_timer = random.randint(60, 220)
        alive = []
        for s in self._shots:
            s[0] += s[2]; s[1] += s[3]; s[4] -= 0.018
            if s[4] > 0 and s[0] < self.W+60 and s[1] < self.H+60:
                alive.append(s)
        self._shots = alive

    def draw(self, surface):
        surface.blit(self._static, (0, 0))

        # Shooting stars
        for s in self._shots:
            a = max(0, min(255, int(255 * s[4])))
            col = (a, a, int(a * 0.85))
            tx = int(s[0] - s[2] * (s[5] / 5))
            ty = int(s[1] - s[3] * (s[5] / 5))
            pygame.draw.line(surface, col, (tx, ty), (int(s[0]), int(s[1])), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(s[0]), int(s[1])), 2)

        # Galaxy (pre-multiplied colours, no per-frame multiply)
        bx, by = self.BH_X, self.BH_Y
        bhr2   = (self.BH_R * 1.15) ** 2
        for p in self._galaxy:
            ang, r = p[0], p[1]
            px = bx + r * math.cos(ang)
            py = by + r * math.sin(ang) * 0.38
            dx, dy = px - bx, py - by
            if dx*dx + dy*dy < bhr2:
                continue
            pygame.draw.circle(surface, p[3], (int(px), int(py)), p[2])

        # Black hole halo (pre-computed rings)
        ibx, iby = int(bx), int(by)
        for hr, hcol in self._halo_rings:
            pygame.draw.ellipse(surface, hcol,
                (ibx-hr, iby-int(hr*0.32), hr*2, int(hr*0.64)), 1)

        # Accretion disk
        da = self._disk_angle
        for i in range(6, 0, -1):
            dr    = self.BH_R + i * 7
            heat  = 1.0 - i / 7.0
            phase = (da + i * 0.6) % (2 * math.pi)
            pulse = 0.85 + 0.15 * math.sin(phase)
            R = min(255, int((200 + 55*heat)*pulse))
            G = min(255, int(( 80 + 80*heat)*pulse))
            B = min(255, int(( 10 + 20*heat)*pulse))
            pygame.draw.ellipse(surface, (R, G, B),
                (ibx-dr, iby-int(dr*0.28), dr*2, int(dr*0.56)),
                3 if i <= 2 else 2)

        # Hot-spot
        hs_ang = da * 1.4
        hs_r   = self.BH_R + 20
        hsx = int(bx + hs_r * math.cos(hs_ang))
        hsy = int(by + hs_r * math.sin(hs_ang) * 0.32)
        pygame.draw.circle(surface, (255, 240, 180), (hsx, hsy), 5)
        pygame.draw.circle(surface, (255, 255, 255), (hsx, hsy), 2)

        # Event horizon
        pygame.draw.circle(surface, (0, 0, 0),    (ibx, iby), self.BH_R)
        pygame.draw.circle(surface, (60, 10, 100), (ibx, iby), self.BH_R,     3)
        pygame.draw.circle(surface, (30,  5,  60), (ibx, iby), self.BH_R + 3, 2)

        # Twinkling foreground stars
        f = self.frame
        for i, (sx, sy, freq) in enumerate(self._twinklers):
            b = int(140 + 115 * math.sin(f * 0.025 * freq + i * 1.7))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy), 2)
            if b > 220:
                pygame.draw.line(surface, (b, b, b), (sx-5, sy), (sx+5, sy), 1)
                pygame.draw.line(surface, (b, b, b), (sx, sy-5), (sx, sy+5), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class Dashboard:
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
            self.font_sub   = pygame.font.SysFont("Arial", 13)
            self.font_btn   = pygame.font.SysFont("Arial", 17, bold=True)
            self.font_list  = pygame.font.SysFont("Arial", 15)
            self.font_label = pygame.font.SysFont("Arial", 13, bold=True)
        except:
            self.font_title = pygame.font.SysFont(None, 50)
            self.font_sub   = pygame.font.SysFont(None, 13)
            self.font_btn   = pygame.font.SysFont(None, 17)
            self.font_list  = pygame.font.SysFont(None, 15)
            self.font_label = pygame.font.SysFont(None, 13)

        self.bg = CosmicBackground()
        self.maps = self._load_maps()
        self.selected_map_idx = -1
        self.frame = 0

        self.buttons = [
            {"text": "NEW CUSTOM GAME",   "rect": pygame.Rect(28, 185, 175, 42), "action": "NEW"},
            {"text": "LOAD SELECTED MAP", "rect": pygame.Rect(28, 237, 175, 42), "action": "LOAD"},
            {"text": "VIEW LEADERBOARD",  "rect": pygame.Rect(28, 289, 175, 42), "action": "LEADERBOARD"},
        ]

        self._left_panel  = self._make_panel(222, 460)
        self._right_panel = self._make_panel(310, 430)

        # ── One-time text pre-renders ──────────────────────────────────────────
        # Static text
        self._surf_sub   = self.font_sub.render("ARCHITECT  vs  PILOT", True, (180, 120, 255))
        self._surf_hint  = self.font_sub.render(
            "PILOT CONTROLS:  A / D  =  Rotate      < / >  =  Speed",
            True, (100, 100, 160))
        self._surf_lbl   = self.font_label.render("SAVED MAPS", True, (200, 160, 255))

        # Pre-render button text (text doesn't change)
        for btn in self.buttons:
            btn["surf"]     = self.font_btn.render(btn["text"], True, (255, 255, 255))
            btn["surf_dim"] = self.font_btn.render(btn["text"], True, (160, 160, 160))

        # ── Fetch best times once (not per-frame) ─────────────────────────────
        self._best_times = self._load_best_times()

        # ── Pre-render map list entries (re-built when selection changes) ──────
        self._map_surfs = []
        self._sel_cache = -2   # force first build
        self._rebuild_map_surfs()

        # Glow title cache
        self._glow_frame  = -99
        self._glow_surfs  = []   # list of (surf, x, y)
        self._title_surf  = self.font_title.render("ROCKET DUEL", True, (255, 255, 255))
        self._title_x     = 400 - self._title_surf.get_width()//2

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 175), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def _load_maps(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT id, name, start_point, goal_point, obstacles "
                  "FROM maps ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def _load_best_times(self):
        """Fetch all best times in one query — called once at init."""
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT map_id, MIN(time_taken) FROM scores GROUP BY map_id")
        result = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return result

    def _rebuild_map_surfs(self):
        """Pre-render the map list. Only called when selection changes."""
        self._map_surfs = []
        for i, m in enumerate(self.maps):
            if i >= 14:
                break
            is_sel = (i == self.selected_map_idx)
            best   = self._best_times.get(m[0])
            time_str = f"  [{best:.1f}s]" if best else ""
            col    = (255, 220, 50) if is_sel else (200, 200, 220)
            surf   = self.font_list.render(f"{i+1}.  {m[1]}{time_str}", True, col)
            self._map_surfs.append((surf, i, is_sel))
        self._sel_cache = self.selected_map_idx

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    if btn["action"] == "NEW":
                        return "NEW", None
                    if btn["action"] == "LOAD" and self.selected_map_idx != -1:
                        m = self.maps[self.selected_map_idx]
                        return "LOAD", {
                            "map_id": m[0],
                            "start":  json.loads(m[2]),
                            "goal":   json.loads(m[3]),
                            "obstacles": json.loads(m[4])
                        }
                    if btn["action"] == "LEADERBOARD":
                        return "LEADERBOARD", None

            for i in range(min(14, len(self.maps))):
                rect = pygame.Rect(238, 195 + i*26, 295, 22)
                if rect.collidepoint(event.pos):
                    self.selected_map_idx = i

        return None, None

    def draw(self, surface):
        self.frame += 1
        f = self.frame

        self.bg.update()
        self.bg.draw(surface)

        # Rebuild map list only when selection changes
        if self._sel_cache != self.selected_map_idx:
            self._rebuild_map_surfs()

        # ── Left panel ────────────────────────────────────────────────────────
        surface.blit(self._left_panel, (15, 155))

        mx, my = pygame.mouse.get_pos()
        for btn in self.buttons:
            is_load  = btn["action"] == "LOAD"
            disabled = is_load and self.selected_map_idx == -1
            if disabled:
                base = (70, 70, 90)
            elif btn["action"] == "NEW":
                base = (0, 100, 200)
            elif btn["action"] == "LOAD":
                base = (0, 150, 80)
            else:
                base = (160, 70, 0)

            hover = btn["rect"].collidepoint((mx, my)) and not disabled
            if hover:
                pulse = int(20 * math.sin(f * 0.15))
                base  = tuple(min(255, c + 50 + pulse) for c in base)

            pygame.draw.rect(surface, base, btn["rect"], border_radius=6)
            pygame.draw.rect(surface, (150, 80, 255) if hover else (80, 20, 150),
                             btn["rect"], 1, border_radius=6)
            txt_surf = btn["surf_dim"] if disabled else btn["surf"]
            surface.blit(txt_surf, (btn["rect"].centerx - txt_surf.get_width()//2,
                                    btn["rect"].centery - txt_surf.get_height()//2))

        # ── Title glow (re-render glow only every 4 frames) ───────────────────
        if f - self._glow_frame >= 4:
            self._glow_frame = f
            glow_col = (0, int(180 + 75 * math.sin(f * 0.05)), 255)
            g_surf   = self.font_title.render("ROCKET DUEL", True, glow_col)
            gx       = 400 - g_surf.get_width()//2
            self._glow_surfs = [(g_surf, gx+ox, 68+oy) for ox, oy in ((-2,0),(2,0),(0,-2),(0,2))]

        for gs, gx, gy in self._glow_surfs:
            surface.blit(gs, (gx, gy))
        surface.blit(self._title_surf, (self._title_x, 68))
        surface.blit(self._surf_sub,   (400 - self._surf_sub.get_width()//2, 122))

        # ── Right panel (map list) ────────────────────────────────────────────
        surface.blit(self._right_panel, (230, 155))
        surface.blit(self._surf_lbl, (244, 163))

        for surf, i, is_sel in self._map_surfs:
            y = 195 + i * 26
            if is_sel:
                sr = pygame.Rect(236, y-2, 296, 22)
                pygame.draw.rect(surface, (60, 0, 130), sr, border_radius=4)
                pygame.draw.rect(surface, (180, 60, 255), sr, 1, border_radius=4)
            surface.blit(surf, (244, y))

        # ── Controls hint ─────────────────────────────────────────────────────
        surface.blit(self._surf_hint, (400 - self._surf_hint.get_width()//2, 575))


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard
# ─────────────────────────────────────────────────────────────────────────────

class Leaderboard:
    def __init__(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
            self.font_label = pygame.font.SysFont("Arial", 18, bold=True)
            self.font_score = pygame.font.SysFont("monospace", 15)
            self.font_btn   = pygame.font.SysFont("Arial", 17, bold=True)
        except:
            self.font_title = pygame.font.SysFont(None, 40)
            self.font_label = pygame.font.SysFont(None, 18)
            self.font_score = pygame.font.SysFont(None, 15)
            self.font_btn   = pygame.font.SysFont(None, 17)

        self.bg       = CosmicBackground()
        self.back_btn = pygame.Rect(340, 550, 120, 38)
        self.boards   = self._load()
        self.frame    = 0
        self._panel   = self._make_panel(620, 470)
        # Pre-build button text
        self._btn_surf = self.font_btn.render("BACK", True, (255, 255, 255))
        # Pre-render all score rows
        self._rows = self._build_rows()

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def _load(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("""
            SELECT m.id, m.name, s.time_taken
            FROM maps m
            LEFT JOIN scores s ON m.id = s.map_id
            ORDER BY m.name, s.time_taken ASC
        """)
        rows = c.fetchall()
        conn.close()
        boards = {}
        for map_id, map_name, t in rows:
            if map_id not in boards:
                boards[map_id] = {"name": map_name, "scores": []}
            if t is not None:
                boards[map_id]["scores"].append(t)
        return boards

    def _build_rows(self):
        """Pre-render all text rows for the leaderboard."""
        MEDALS = {0: (255, 215, 0), 1: (180, 180, 180), 2: (180, 100, 40)}
        rows = []   # list of (surf, indent_x, y_offset_within_section)
        y = 0
        for map_id in sorted(self.boards.keys()):
            board = self.boards[map_id]
            lbl   = self.font_label.render(f"  {board['name']}", True, (80, 255, 160))
            rows.append(("map", lbl, y))
            y += 26
            if board["scores"]:
                for rank, t in enumerate(board["scores"][:5]):
                    col    = MEDALS.get(rank, (200, 200, 200))
                    prefix = ["#1","#2","#3","#4","#5"][rank]
                    s = self.font_score.render(f"   {prefix}   {t:.3f}s", True, col)
                    rows.append(("score", s, y))
                    y += 20
            else:
                s = self.font_score.render("   No runs recorded yet", True, (110, 110, 130))
                rows.append(("score", s, y))
                y += 20
            y += 8
        return rows

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.collidepoint(event.pos):
                return "DASHBOARD"
        return "LEADERBOARD"

    def draw(self, surface):
        self.frame += 1
        f = self.frame
        self.bg.update()
        self.bg.draw(surface)

        surface.blit(self._panel, (90, 65))

        # Title glow (every 4 frames)
        glow_col = (255, int(160 + 60 * math.sin(f * 0.05)), 0)
        g = self.font_title.render("LEADERBOARD", True, glow_col)
        gx = 400 - g.get_width()//2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            surface.blit(g, (gx+ox, 72+oy))
        title = self.font_title.render("LEADERBOARD", True, (255, 230, 80))
        surface.blit(title, (400 - title.get_width()//2, 72))

        # Pre-rendered rows
        base_y = 125
        for kind, surf, y_off in self._rows:
            y = base_y + y_off
            if y > 490:
                break
            surface.blit(surf, (108 if kind == "map" else 115, y))

        # Back button
        mx, my = pygame.mouse.get_pos()
        hover  = self.back_btn.collidepoint((mx, my))
        bcol   = (0, 180, 240) if hover else (0, 130, 180)
        pygame.draw.rect(surface, bcol, self.back_btn, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), self.back_btn, 1, border_radius=6)
        surface.blit(self._btn_surf,
                     (self.back_btn.centerx - self._btn_surf.get_width()//2,
                      self.back_btn.centery - self._btn_surf.get_height()//2))
