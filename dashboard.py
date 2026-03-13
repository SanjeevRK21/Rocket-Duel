import pygame
import math
import random
import sqlite3
import json

# ─────────────────────────────────────────────────────────────────────────────
# Cosmic background — galaxy, black hole, nebula, shooting stars
# ─────────────────────────────────────────────────────────────────────────────

class CosmicBackground:
    W, H = 800, 600
    # Black hole sits centre-right so the left UI panel is clear
    BH_X, BH_Y = 570, 305
    BH_R = 38           # event horizon radius

    def __init__(self):
        self.frame = 0

        # ── Static layer (nebula + distant stars) — built once ──────────────
        self._static = self._build_static()

        # ── Galaxy particles [angle, radius, size, (r,g,b), speed] ─────────
        self._galaxy = self._build_galaxy()

        # ── Bright foreground twinkle stars ─────────────────────────────────
        self._twinklers = [
            (random.randint(0, self.W), random.randint(0, self.H),
             random.uniform(0.8, 3.5))
            for _ in range(55)
        ]

        # ── Shooting stars ───────────────────────────────────────────────────
        self._shots = []
        self._shot_timer = random.randint(40, 100)

        # ── Accretion disk angle (for hot-spot rotation) ─────────────────────
        self._disk_angle = 0.0

    # ── Static surface ────────────────────────────────────────────────────────
    def _build_static(self):
        surf = pygame.Surface((self.W, self.H))
        surf.fill((0, 0, 6))

        # Nebula blobs (alpha-blended once onto the static surface)
        nb = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        nebulae = [
            # (cx, cy, rx, ry, (R,G,B,A), count)
            (210, 160, 110, 70,  (100, 20, 180, 22), 6),   # purple
            (680, 200, 90,  55,  (20,  70, 180, 18), 5),   # blue
            (120, 430, 80,  55,  (180, 30,  20, 18), 5),   # red
            (440, 530, 95,  60,  (20, 110, 130, 16), 5),   # teal
            (730,  90, 65,  45,  (140, 130,  10, 18), 4),  # yellow
            (310, 380, 70,  45,  (60,  20, 140, 14), 4),   # violet
        ]
        for cx, cy, rx, ry, col, cnt in nebulae:
            for _ in range(cnt):
                ex = cx + random.randint(-rx//3, rx//3)
                ey = cy + random.randint(-ry//3, ry//3)
                er = rx + random.randint(-rx//4, rx//4)
                eh = ry + random.randint(-ry//4, ry//4)
                pygame.draw.ellipse(nb, col, (ex-er, ey-eh//2, er*2, eh))
        surf.blit(nb, (0, 0))

        # Distant dim stars
        for _ in range(420):
            x = random.randint(0, self.W)
            y = random.randint(0, self.H)
            b = random.randint(50, 170)
            # slight colour tint
            tc = random.randint(0, 3)
            if   tc == 0: col = (b, b, b)
            elif tc == 1: col = (b, int(b*0.75), int(b*0.5))
            elif tc == 2: col = (int(b*0.6), int(b*0.7), b)
            else:         col = (b, b, int(b*0.6))
            pygame.draw.circle(surf, col, (x, y), 1)

        return surf

    # ── Galaxy spiral particles ───────────────────────────────────────────────
    def _build_galaxy(self):
        particles = []
        num_arms  = 3

        for arm in range(num_arms):
            arm_off = (2 * math.pi / num_arms) * arm
            for i in range(90):
                t = i / 90
                radius = 55 + t * 195
                # logarithmic spiral
                angle  = arm_off + t * 4.2 * math.pi + random.gauss(0, 0.28)

                # colour: hot blue core → white mid → warm orange outer
                if   t < 0.25: col = (160, 180, 255)
                elif t < 0.55: col = (255, 255, 230)
                else:           col = (255, 170,  90)

                brightness = random.uniform(0.35, 1.0)
                # inner stars rotate faster (Keplerian)
                speed = max(0.00008, 0.00025 / (t + 0.05))
                size  = 1 if t > 0.25 else 2

                particles.append([
                    angle,           # 0  current angle (mutable)
                    radius + random.uniform(-14, 14),  # 1  radius
                    size,            # 2
                    col,             # 3  (r,g,b)
                    brightness,      # 4
                    speed,           # 5  rad/frame
                ])

        # Scatter halo
        for _ in range(65):
            particles.append([
                random.uniform(0, 2 * math.pi),
                random.uniform(30, 230),
                1,
                (180, 185, 210),
                random.uniform(0.2, 0.55),
                random.uniform(0.00004, 0.00018),
            ])

        return particles

    # ── Per-frame update ─────────────────────────────────────────────────────
    def update(self):
        self.frame += 1

        # Rotate galaxy
        for p in self._galaxy:
            p[0] += p[5]

        # Accretion disk hot-spot
        self._disk_angle += 0.018

        # Shooting stars
        self._shot_timer -= 1
        if self._shot_timer <= 0:
            sx = random.uniform(-30, self.W + 30)
            sy = random.uniform(-30, 180)
            spd = random.uniform(4, 9)
            ang = random.uniform(0.3, 0.7)   # downward-ish
            self._shots.append({
                'x': sx, 'y': sy,
                'vx': spd * math.cos(ang), 'vy': spd * math.sin(ang),
                'life': 1.0, 'trail': random.randint(35, 90)
            })
            self._shot_timer = random.randint(55, 200)

        alive = []
        for s in self._shots:
            s['x'] += s['vx']; s['y'] += s['vy']; s['life'] -= 0.018
            if s['life'] > 0 and s['x'] < self.W + 60 and s['y'] < self.H + 60:
                alive.append(s)
        self._shots = alive

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.blit(self._static, (0, 0))

        # Shooting stars
        for s in self._shots:
            alpha = max(0, min(255, int(255 * s['life'])))
            col = (alpha, alpha, int(alpha * 0.85))
            tx = s['x'] - s['vx'] * (s['trail'] / 5)
            ty = s['y'] - s['vy'] * (s['trail'] / 5)
            pygame.draw.line(surface, col, (int(tx), int(ty)), (int(s['x']), int(s['y'])), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(s['x']), int(s['y'])), 2)

        # ── Galaxy ────────────────────────────────────────────────────────────
        bx, by = self.BH_X, self.BH_Y
        bhr2   = (self.BH_R * 1.15) ** 2
        for p in self._galaxy:
            ang = p[0]
            r   = p[1]
            # Project onto tilted ellipse (galaxy inclination)
            px = bx + r * math.cos(ang)
            py = by + r * math.sin(ang) * 0.38
            # Hide stars swallowed by event horizon
            dx, dy = px - bx, py - by
            if dx*dx + dy*dy < bhr2:
                continue
            b = p[4]
            c = p[3]
            col = (max(0, min(255, int(c[0]*b))),
                   max(0, min(255, int(c[1]*b))),
                   max(0, min(255, int(c[2]*b))))
            pygame.draw.circle(surface, col, (int(px), int(py)), p[2])

        # ── Black hole ────────────────────────────────────────────────────────
        ibx, iby = int(bx), int(by)

        # Outer diffuse halo (multiple faint rings)
        for i in range(7, 1, -1):
            hr = self.BH_R + 10 + i * 13
            intensity = max(0, 55 - i * 6)
            hcol = (min(255, intensity*3), min(255, intensity), intensity // 2)
            pygame.draw.ellipse(surface, hcol,
                (ibx - hr, iby - int(hr * 0.32),
                 hr * 2,   int(hr * 0.64)), 1)

        # Accretion disk — concentric tilted ellipses with heat cycle
        da = self._disk_angle
        for i in range(6, 0, -1):
            dr = self.BH_R + i * 7
            # Colour: inner blazing white-orange, outer dim red
            heat  = 1.0 - i / 7.0
            phase = (da + i * 0.6) % (2 * math.pi)
            pulse = 0.85 + 0.15 * math.sin(phase)
            R = min(255, int((200 + 55 * heat) * pulse))
            G = min(255, int((80  + 80 * heat) * pulse))
            B = min(255, int((10  + 20 * heat) * pulse))
            w = 3 if i <= 2 else 2
            pygame.draw.ellipse(surface, (R, G, B),
                (ibx - dr, iby - int(dr * 0.28),
                 dr * 2,   int(dr * 0.56)), w)

        # Hot-spot (bright patch rotating around the disk)
        hs_ang = da * 1.4
        hs_r   = self.BH_R + 20
        hsx = int(bx + hs_r * math.cos(hs_ang))
        hsy = int(by + hs_r * math.sin(hs_ang) * 0.32)
        pygame.draw.circle(surface, (255, 240, 180), (hsx, hsy), 5)
        pygame.draw.circle(surface, (255, 255, 255), (hsx, hsy), 2)

        # Event horizon — pure black
        pygame.draw.circle(surface, (0, 0, 0), (ibx, iby), self.BH_R)
        # Purple rim glow
        pygame.draw.circle(surface, (60, 10, 100), (ibx, iby), self.BH_R,     3)
        pygame.draw.circle(surface, (30,  5,  60), (ibx, iby), self.BH_R + 3, 2)

        # ── Foreground twinkling stars ────────────────────────────────────────
        f = self.frame
        for i, (sx, sy, freq) in enumerate(self._twinklers):
            b = int(140 + 115 * math.sin(f * 0.025 * freq + i * 1.7))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy), 2)
            if b > 220:
                # Star flare cross
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
        self.maps = self.load_maps()
        self.selected_map_idx = -1
        self.frame = 0

        self.buttons = [
            {"text": "NEW CUSTOM GAME",  "rect": pygame.Rect(28, 185, 175, 42), "action": "NEW"},
            {"text": "LOAD SELECTED MAP","rect": pygame.Rect(28, 237, 175, 42), "action": "LOAD"},
            {"text": "VIEW LEADERBOARD", "rect": pygame.Rect(28, 289, 175, 42), "action": "LEADERBOARD"},
        ]

        # Pre-build panel background surfaces (drawn once)
        self._left_panel  = self._make_panel(222, 460)
        self._right_panel = self._make_panel(310, 430)

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 175), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def load_maps(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT id, name, start_point, goal_point, obstacles "
                  "FROM maps ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def get_best_time(self, map_id):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT MIN(time_taken) FROM scores WHERE map_id = ?", (map_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

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

            for i in range(len(self.maps)):
                rect = pygame.Rect(238, 195 + i * 26, 295, 22)
                if rect.collidepoint(event.pos):
                    self.selected_map_idx = i

        return None, None

    def draw(self, surface):
        self.frame += 1
        self.bg.update()
        self.bg.draw(surface)

        f = self.frame

        # ── Left panel (buttons) ──────────────────────────────────────────────
        surface.blit(self._left_panel, (15, 155))

        for btn in self.buttons:
            is_load = btn["action"] == "LOAD"
            disabled = is_load and self.selected_map_idx == -1
            if disabled:
                base = (70, 70, 90)
            elif btn["action"] == "NEW":
                base = (0, 100, 200)
            elif btn["action"] == "LOAD":
                base = (0, 150, 80)
            else:
                base = (160, 70, 0)

            # Pulsing glow on hover
            mx, my = pygame.mouse.get_pos()
            hover = btn["rect"].collidepoint((mx, my)) and not disabled
            if hover:
                pulse = int(20 * math.sin(f * 0.15))
                base = tuple(min(255, c + 50 + pulse) for c in base)

            pygame.draw.rect(surface, base, btn["rect"], border_radius=6)
            pygame.draw.rect(surface, (150, 80, 255) if hover else (80, 20, 150),
                             btn["rect"], 1, border_radius=6)
            col = (160, 160, 160) if disabled else (255, 255, 255)
            txt = self.font_btn.render(btn["text"], True, col)
            surface.blit(txt, (btn["rect"].centerx - txt.get_width()//2,
                               btn["rect"].centery - txt.get_height()//2))

        # ── Title (electric glow) ─────────────────────────────────────────────
        # Halo pass (slightly offset, coloured)
        glow_col = (0, int(180 + 75 * math.sin(f * 0.05)), 255)
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            g = self.font_title.render("ROCKET DUEL", True, glow_col)
            surface.blit(g, (400 - g.get_width()//2 + ox, 68 + oy))
        title = self.font_title.render("ROCKET DUEL", True, (255, 255, 255))
        surface.blit(title, (400 - title.get_width()//2, 68))

        sub = self.font_sub.render("ARCHITECT  vs  PILOT", True, (180, 120, 255))
        surface.blit(sub, (400 - sub.get_width()//2, 122))

        # ── Right panel (saved maps) ──────────────────────────────────────────
        surface.blit(self._right_panel, (230, 155))

        lbl = self.font_label.render("SAVED MAPS", True, (200, 160, 255))
        surface.blit(lbl, (244, 163))

        for i, m in enumerate(self.maps):
            if i >= 14:
                break
            y = 195 + i * 26
            is_sel = (i == self.selected_map_idx)

            if is_sel:
                sel_rect = pygame.Rect(236, y - 2, 296, 22)
                pygame.draw.rect(surface, (60, 0, 130), sel_rect, border_radius=4)
                pygame.draw.rect(surface, (180, 60, 255), sel_rect, 1, border_radius=4)

            best = self.get_best_time(m[0])
            time_str = f"  [{best:.1f}s]" if best else ""
            txt_col = (255, 220, 50) if is_sel else (200, 200, 220)
            name_txt = self.font_list.render(f"{i+1}.  {m[1]}{time_str}", True, txt_col)
            surface.blit(name_txt, (244, y))

        # ── Controls hint (bottom) ────────────────────────────────────────────
        hint = self.font_sub.render(
            "PILOT CONTROLS:  A / D  =  Rotate      ◄ / ►  =  Speed",
            True, (100, 100, 160))
        surface.blit(hint, (400 - hint.get_width()//2, 575))


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard  (also gets the cosmic background)
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

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def _load(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("""
            SELECT m.id, m.name, s.time_taken, s.created_at
            FROM maps m
            LEFT JOIN scores s ON m.id = s.map_id
            ORDER BY m.name, s.time_taken ASC
        """)
        rows = c.fetchall()
        conn.close()
        boards = {}
        for map_id, map_name, t, created in rows:
            if map_id not in boards:
                boards[map_id] = {"name": map_name, "scores": []}
            if t is not None:
                boards[map_id]["scores"].append(t)
        return boards

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.collidepoint(event.pos):
                return "DASHBOARD"
        return "LEADERBOARD"

    def draw(self, surface):
        self.frame += 1
        self.bg.update()
        self.bg.draw(surface)

        surface.blit(self._panel, (90, 65))

        f = self.frame
        glow_col = (255, int(160 + 60 * math.sin(f * 0.05)), 0)
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            g = self.font_title.render("LEADERBOARD", True, glow_col)
            surface.blit(g, (400 - g.get_width()//2 + ox, 72 + oy))
        title = self.font_title.render("LEADERBOARD", True, (255, 230, 80))
        surface.blit(title, (400 - title.get_width()//2, 72))

        MEDALS = {0: (255, 215, 0), 1: (180, 180, 180), 2: (180, 100, 40)}
        y = 125
        for map_id in sorted(self.boards.keys()):
            board = self.boards[map_id]
            map_lbl = self.font_label.render(f"  {board['name']}", True, (80, 255, 160))
            surface.blit(map_lbl, (108, y))
            y += 26

            if board['scores']:
                for rank, t in enumerate(board['scores'][:5]):
                    rank_col = MEDALS.get(rank, (200, 200, 200))
                    prefix   = ["#1", "#2", "#3", "#4", "#5"][rank]
                    line = self.font_score.render(f"   {prefix}   {t:.3f}s", True, rank_col)
                    surface.blit(line, (115, y))
                    y += 20
            else:
                ns = self.font_score.render("   No runs recorded yet", True, (110, 110, 130))
                surface.blit(ns, (115, y))
                y += 20

            y += 8
            if y > 490:
                break

        # Back button
        mx, my = pygame.mouse.get_pos()
        hover = self.back_btn.collidepoint((mx, my))
        bcol = (0, 180, 240) if hover else (0, 130, 180)
        pygame.draw.rect(surface, bcol, self.back_btn, border_radius=6)
        pygame.draw.rect(surface, (0, 220, 255), self.back_btn, 1, border_radius=6)
        bt = self.font_btn.render("BACK", True, (255, 255, 255))
        surface.blit(bt, (self.back_btn.centerx - bt.get_width()//2,
                          self.back_btn.centery - bt.get_height()//2))
