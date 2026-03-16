import pygame
import math
import random
import sqlite3
import json

# ─────────────────────────────────────────────────────────────────────────────
# Cosmic background (same as before)
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
             random.uniform(0.8, 3.5)) for _ in range(45)
        ]
        self._shots      = []
        self._shot_timer = random.randint(60, 120)
        self._disk_angle = 0.0
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
            (210, 160, 110, 70, (100,20,180,22), 6),
            (680, 200, 90,  55, (20,70,180,18),  5),
            (120, 430, 80,  55, (180,30,20,18),  5),
            (440, 530, 95,  60, (20,110,130,16), 5),
            (730,  90, 65,  45, (140,130,10,18), 4),
            (310, 380, 70,  45, (60,20,140,14),  4),
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
                pcol  = (max(0,min(255,int(cr*b))), max(0,min(255,int(cg*b))), max(0,min(255,int(cb*b))))
                particles.append([angle, radius + random.uniform(-14,14), size, pcol, speed])
        for _ in range(55):
            b = random.uniform(0.2, 0.55)
            pcol = (int(180*b), int(185*b), int(210*b))
            particles.append([random.uniform(0,2*math.pi), random.uniform(30,230), 1, pcol,
                               random.uniform(0.00004, 0.00018)])
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
            self._shots.append([random.uniform(-30, self.W+30), random.uniform(-30, 180),
                                 spd*math.cos(ang), spd*math.sin(ang), 1.0, random.randint(35,90)])
            self._shot_timer = random.randint(60, 220)
        alive = []
        for s in self._shots:
            s[0]+=s[2]; s[1]+=s[3]; s[4]-=0.018
            if s[4]>0 and s[0]<self.W+60 and s[1]<self.H+60: alive.append(s)
        self._shots = alive

    def draw(self, surface):
        surface.blit(self._static, (0,0))
        for s in self._shots:
            a = max(0, min(255, int(255*s[4])))
            col = (a, a, int(a*0.85))
            pygame.draw.line(surface, col,
                (int(s[0]-s[2]*(s[5]/5)), int(s[1]-s[3]*(s[5]/5))),
                (int(s[0]), int(s[1])), 2)
            pygame.draw.circle(surface, (255,255,255), (int(s[0]),int(s[1])), 2)
        bx, by = self.BH_X, self.BH_Y
        bhr2   = (self.BH_R * 1.15)**2
        for p in self._galaxy:
            ang, r = p[0], p[1]
            px = bx + r*math.cos(ang)
            py = by + r*math.sin(ang)*0.38
            dx, dy = px-bx, py-by
            if dx*dx+dy*dy < bhr2: continue
            pygame.draw.circle(surface, p[3], (int(px),int(py)), p[2])
        ibx, iby = int(bx), int(by)
        for hr, hcol in self._halo_rings:
            pygame.draw.ellipse(surface, hcol,
                (ibx-hr, iby-int(hr*0.32), hr*2, int(hr*0.64)), 1)
        da = self._disk_angle
        for i in range(6, 0, -1):
            dr = self.BH_R + i*7
            heat  = 1.0 - i/7.0
            phase = (da + i*0.6) % (2*math.pi)
            pulse = 0.85 + 0.15*math.sin(phase)
            R = min(255, int((200+55*heat)*pulse))
            G = min(255, int(( 80+80*heat)*pulse))
            B = min(255, int(( 10+20*heat)*pulse))
            pygame.draw.ellipse(surface, (R,G,B),
                (ibx-dr, iby-int(dr*0.28), dr*2, int(dr*0.56)), 3 if i<=2 else 2)
        hs_ang = da*1.4; hs_r = self.BH_R+20
        hsx = int(bx+hs_r*math.cos(hs_ang)); hsy = int(by+hs_r*math.sin(hs_ang)*0.32)
        pygame.draw.circle(surface, (255,240,180), (hsx,hsy), 5)
        pygame.draw.circle(surface, (255,255,255), (hsx,hsy), 2)
        pygame.draw.circle(surface, (0,0,0),       (ibx,iby), self.BH_R)
        pygame.draw.circle(surface, (60,10,100),   (ibx,iby), self.BH_R, 3)
        pygame.draw.circle(surface, (30,5,60),     (ibx,iby), self.BH_R+3, 2)
        f = self.frame
        for i, (sx, sy, freq) in enumerate(self._twinklers):
            b = int(140 + 115*math.sin(f*0.025*freq + i*1.7))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b,b,b), (sx,sy), 2)
            if b > 220:
                pygame.draw.line(surface, (b,b,b), (sx-5,sy), (sx+5,sy), 1)
                pygame.draw.line(surface, (b,b,b), (sx,sy-5), (sx,sy+5), 1)


# ─────────────────────────────────────────────────────────────────────────────
# TextInput — reusable text-entry widget
# ─────────────────────────────────────────────────────────────────────────────

class TextInput:
    def __init__(self, x, y, w, h, font, placeholder='', max_len=25):
        self.rect        = pygame.Rect(x, y, w, h)
        self.font        = font
        self.placeholder = placeholder
        self.max_len     = max_len
        self.text        = ''
        self.active      = False
        self._tick       = 0

    def handle_event(self, event):
        """Returns True when Enter is pressed (submit signal)."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
            elif len(self.text) < self.max_len and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def draw(self, surface):
        self._tick += 1
        bg = (30, 0, 60) if self.active else (12, 0, 25)
        bd = (180, 60, 255) if self.active else (60, 0, 120)
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, bd, self.rect, 1, border_radius=6)
        display = self.text or self.placeholder
        col     = (255, 255, 255) if self.text else (80, 80, 110)
        ts      = self.font.render(display, True, col)
        surface.blit(ts, (self.rect.x + 8, self.rect.centery - ts.get_height()//2))
        if self.active and (self._tick // 25) % 2 == 0:
            cx = self.rect.x + 8 + self.font.size(self.text)[0]
            pygame.draw.line(surface, (200, 100, 255),
                             (cx, self.rect.y+5), (cx, self.rect.bottom-5), 2)


# ─────────────────────────────────────────────────────────────────────────────
# Player Names Screen
# ─────────────────────────────────────────────────────────────────────────────

class PlayerNamesScreen:
    """Enter Player 1 and Player 2 names before the game starts."""

    def __init__(self):
        self.bg    = CosmicBackground()
        self.frame = 0
        try:
            self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
            self.font_label = pygame.font.SysFont("Arial", 17, bold=True)
            self.font_role  = pygame.font.SysFont("Arial", 13)
            self.font_inp   = pygame.font.SysFont("Arial", 20)
            self.font_btn   = pygame.font.SysFont("Arial", 18, bold=True)
        except:
            self.font_title = pygame.font.SysFont(None, 40)
            self.font_label = pygame.font.SysFont(None, 17)
            self.font_role  = pygame.font.SysFont(None, 13)
            self.font_inp   = pygame.font.SysFont(None, 20)
            self.font_btn   = pygame.font.SysFont(None, 18)

        self.inp_p1 = TextInput(260, 225, 280, 42, self.font_inp, "e.g. Alice", max_len=20)
        self.inp_p2 = TextInput(260, 330, 280, 42, self.font_inp, "e.g. Bob",   max_len=20)
        self.inp_p1.active = True

        self.start_btn  = pygame.Rect(305, 430, 190, 46)
        self._panel     = self._make_panel(440, 330)

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 175), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def _check_submit(self):
        p1 = self.inp_p1.text.strip() or "Player 1"
        p2 = self.inp_p2.text.strip() or "Player 2"
        return (p1, p2)

    def handle_event(self, event):
        """Returns (p1_name, p2_name) tuple when ready, else None."""
        self.inp_p1.handle_event(event)
        self.inp_p2.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                if self.inp_p1.active:
                    self.inp_p1.active = False; self.inp_p2.active = True
                else:
                    self.inp_p2.active = False; self.inp_p1.active = True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.inp_p1.active:
                    self.inp_p1.active = False; self.inp_p2.active = True
                elif self.inp_p2.active:
                    return self._check_submit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn.collidepoint(event.pos):
                return self._check_submit()

        return None

    def draw(self, surface):
        self.frame += 1
        self.bg.update()
        self.bg.draw(surface)
        f = self.frame

        surface.blit(self._panel, (180, 155))

        glow = (0, int(180+60*math.sin(f*0.05)), 255)
        gt   = self.font_title.render("ENTER PLAYER NAMES", True, glow)
        gx   = 400 - gt.get_width()//2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            surface.blit(gt, (gx+ox, 162+oy))
        title = self.font_title.render("ENTER PLAYER NAMES", True, (255,255,255))
        surface.blit(title, (gx, 162))

        # Player 1
        lbl1 = self.font_label.render("PLAYER 1", True, (0, 200, 255))
        surface.blit(lbl1, (260, 200))
        rol1 = self.font_role.render("Architect in Round 1  →  Pilot in Round 2", True, (100,150,200))
        surface.blit(rol1, (260, 217))
        self.inp_p1.draw(surface)

        # Player 2
        lbl2 = self.font_label.render("PLAYER 2", True, (255, 150, 50))
        surface.blit(lbl2, (260, 305))
        rol2 = self.font_role.render("Pilot in Round 1  →  Architect in Round 2", True, (200,140,80))
        surface.blit(rol2, (260, 320))
        self.inp_p2.draw(surface)

        hint = self.font_role.render("TAB or ENTER to switch fields", True, (100, 80, 150))
        surface.blit(hint, (400 - hint.get_width()//2, 388))

        mx, my = pygame.mouse.get_pos()
        hover  = self.start_btn.collidepoint((mx, my))
        bcol   = (0, 180, 80) if hover else (0, 130, 60)
        pygame.draw.rect(surface, bcol, self.start_btn, border_radius=8)
        pygame.draw.rect(surface, (0, 255, 120), self.start_btn, 1, border_radius=8)
        bt = self.font_btn.render("START GAME  >", True, (255,255,255))
        surface.blit(bt, (self.start_btn.centerx - bt.get_width()//2,
                          self.start_btn.centery - bt.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
# Round Break Screen
# ─────────────────────────────────────────────────────────────────────────────

class RoundBreakScreen:
    """Shown after Round 1 — displays result and sets up Round 2."""

    def __init__(self, p1, p2, p2_won, p2_time):
        self.p1 = p1; self.p2 = p2
        self.p2_won  = p2_won
        self.p2_time = p2_time
        self.bg    = CosmicBackground()
        self.frame = 0
        try:
            self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
            self.font_body  = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_sub   = pygame.font.SysFont("Arial", 16)
            self.font_btn   = pygame.font.SysFont("Arial", 18, bold=True)
        except:
            self.font_title = pygame.font.SysFont(None, 40)
            self.font_body  = pygame.font.SysFont(None, 20)
            self.font_sub   = pygame.font.SysFont(None, 16)
            self.font_btn   = pygame.font.SysFont(None, 18)
        self.cont_btn = pygame.Rect(295, 500, 210, 46)
        self._panel   = self._make_panel(520, 310)

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.cont_btn.collidepoint(event.pos):
                return "CONTINUE"
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "CONTINUE"
        return None

    def draw(self, surface):
        self.frame += 1
        self.bg.update(); self.bg.draw(surface)
        f = self.frame

        surface.blit(self._panel, (140, 140))

        glow = (255, int(160+60*math.sin(f*0.05)), 0)
        gt   = self.font_title.render("ROUND 1 COMPLETE", True, glow)
        gx   = 400 - gt.get_width()//2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            surface.blit(gt, (gx+ox, 148+oy))
        surface.blit(self.font_title.render("ROUND 1 COMPLETE", True, (255,230,80)), (gx, 148))

        # Result
        if self.p2_won:
            res_str = f"{self.p2} completed the map in {self.p2_time:.2f}s"
            res_col = (0, 255, 150)
        else:
            res_str = f"{self.p2} did not complete the map"
            res_col = (255, 100, 100)
        res = self.font_body.render(res_str, True, res_col)
        surface.blit(res, (400 - res.get_width()//2, 210))

        div = self.font_sub.render("─" * 55, True, (60, 0, 120))
        surface.blit(div, (400 - div.get_width()//2, 245))

        # Round 2 info
        r2_title = self.font_body.render("ROUND 2 — ROLES SWAP", True, (180, 120, 255))
        surface.blit(r2_title, (400 - r2_title.get_width()//2, 260))

        arch = self.font_sub.render(f"ARCHITECT  :  {self.p2}", True, (0, 200, 255))
        pilot = self.font_sub.render(f"PILOT      :  {self.p1}", True, (255, 160, 50))
        surface.blit(arch,  (400 - arch.get_width()//2, 295))
        surface.blit(pilot, (400 - pilot.get_width()//2, 318))

        hint = self.font_sub.render(f"{self.p2} will now design a new map for {self.p1} to fly!", True, (140,140,180))
        surface.blit(hint, (400 - hint.get_width()//2, 350))

        mx, my = pygame.mouse.get_pos()
        hover  = self.cont_btn.collidepoint((mx, my))
        bcol   = (0, 150, 220) if hover else (0, 100, 170)
        pygame.draw.rect(surface, bcol, self.cont_btn, border_radius=8)
        pygame.draw.rect(surface, (0, 200, 255), self.cont_btn, 1, border_radius=8)
        bt = self.font_btn.render("START ROUND 2  >", True, (255,255,255))
        surface.blit(bt, (self.cont_btn.centerx - bt.get_width()//2,
                          self.cont_btn.centery - bt.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
# Game Over Screen
# ─────────────────────────────────────────────────────────────────────────────

class GameOverScreen:
    """Final scoreboard after both rounds."""

    def __init__(self, p1, p2, p1_won, p1_time, p2_won, p2_time):
        self.p1 = p1; self.p2 = p2
        self.p1_won  = p1_won;  self.p1_time = p1_time
        self.p2_won  = p2_won;  self.p2_time = p2_time
        self.bg    = CosmicBackground()
        self.frame = 0
        try:
            self.font_title  = pygame.font.SysFont("Arial", 44, bold=True)
            self.font_winner = pygame.font.SysFont("Arial", 28, bold=True)
            self.font_body   = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_sub    = pygame.font.SysFont("Arial", 15)
            self.font_btn    = pygame.font.SysFont("Arial", 18, bold=True)
        except:
            self.font_title  = pygame.font.SysFont(None, 44)
            self.font_winner = pygame.font.SysFont(None, 28)
            self.font_body   = pygame.font.SysFont(None, 20)
            self.font_sub    = pygame.font.SysFont(None, 15)
            self.font_btn    = pygame.font.SysFont(None, 18)

        self.again_btn = pygame.Rect(295, 510, 210, 46)
        self._panel    = self._make_panel(540, 380)
        self._winner_str, self._winner_col = self._calc_winner()

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, (80, 0, 180, 200), (0, 0, w, h), 1, border_radius=10)
        return s

    def _calc_winner(self):
        if self.p1_won and self.p2_won:
            if self.p1_time < self.p2_time:
                return f"{self.p1} WINS!", (0, 255, 150)
            elif self.p2_time < self.p1_time:
                return f"{self.p2} WINS!", (0, 255, 150)
            else:
                return "IT'S A TIE!", (255, 220, 0)
        elif self.p1_won:
            return f"{self.p1} WINS!", (0, 255, 150)
        elif self.p2_won:
            return f"{self.p2} WINS!", (0, 255, 150)
        else:
            return "DRAW — Both crashed!", (255, 200, 0)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.again_btn.collidepoint(event.pos):
                return "DASHBOARD"
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "DASHBOARD"
        return None

    def _score_line(self, name, won, t, y, surface):
        if won:
            col  = (0, 220, 140)
            tstr = f"{t:.3f}s"
            icon = "[WIN]"
        else:
            col  = (220, 80, 80)
            tstr = "DNF"
            icon = "[CRASH]"
        line = self.font_body.render(f"{name:<20} {icon}   {tstr}", True, col)
        surface.blit(line, (400 - line.get_width()//2, y))

    def draw(self, surface):
        self.frame += 1
        self.bg.update(); self.bg.draw(surface)
        f = self.frame

        surface.blit(self._panel, (130, 110))

        glow = (255, int(100+80*math.sin(f*0.06)), 200)
        gt   = self.font_title.render("GAME OVER", True, glow)
        gx   = 400 - gt.get_width()//2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            surface.blit(gt, (gx+ox, 118+oy))
        surface.blit(self.font_title.render("GAME OVER", True, (255,255,255)), (gx, 118))

        div = self.font_sub.render("─" * 60, True, (60, 0, 120))
        surface.blit(div, (400 - div.get_width()//2, 175))

        # Round results
        r1 = self.font_sub.render(f"Round 1  —  {self.p2} as Pilot  (map by {self.p1})", True, (160,120,220))
        surface.blit(r1, (400 - r1.get_width()//2, 195))
        self._score_line(self.p2, self.p2_won, self.p2_time, 218, surface)

        r2 = self.font_sub.render(f"Round 2  —  {self.p1} as Pilot  (map by {self.p2})", True, (160,120,220))
        surface.blit(r2, (400 - r2.get_width()//2, 258))
        self._score_line(self.p1, self.p1_won, self.p1_time, 281, surface)

        surface.blit(div, (400 - div.get_width()//2, 318))

        pulse = 0.85 + 0.15*math.sin(f*0.08)
        wc = tuple(min(255, int(c*pulse)) for c in self._winner_col)
        ws = self.font_winner.render(self._winner_str, True, wc)
        surface.blit(ws, (400 - ws.get_width()//2, 338))

        role_hint = self.font_sub.render("Lower time wins", True, (100, 100, 140))
        surface.blit(role_hint, (400 - role_hint.get_width()//2, 375))

        mx, my = pygame.mouse.get_pos()
        hover  = self.again_btn.collidepoint((mx, my))
        bcol   = (160, 0, 200) if hover else (100, 0, 140)
        pygame.draw.rect(surface, bcol, self.again_btn, border_radius=8)
        pygame.draw.rect(surface, (220, 50, 255), self.again_btn, 1, border_radius=8)
        bt = self.font_btn.render("PLAY AGAIN", True, (255,255,255))
        surface.blit(bt, (self.again_btn.centerx - bt.get_width()//2,
                          self.again_btn.centery - bt.get_height()//2))


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
            self.font_inp   = pygame.font.SysFont("Arial", 18)
        except:
            self.font_title = pygame.font.SysFont(None, 50)
            self.font_sub   = pygame.font.SysFont(None, 13)
            self.font_btn   = pygame.font.SysFont(None, 17)
            self.font_list  = pygame.font.SysFont(None, 15)
            self.font_label = pygame.font.SysFont(None, 13)
            self.font_inp   = pygame.font.SysFont(None, 18)

        self.bg = CosmicBackground()
        self.maps = self._load_maps()
        self.selected_map_idx = -1
        self.frame = 0

        self.buttons = [
            {"text": "NEW CUSTOM GAME",   "rect": pygame.Rect(28,185,175,42), "action": "NEW"},
            {"text": "LOAD SELECTED MAP", "rect": pygame.Rect(28,237,175,42), "action": "LOAD"},
            {"text": "VIEW LEADERBOARD",  "rect": pygame.Rect(28,289,175,42), "action": "LEADERBOARD"},
            {"text": "RENAME MAP",        "rect": pygame.Rect(28,341,175,42), "action": "RENAME"},
        ]

        self._left_panel  = self._make_panel(222, 230)
        self._right_panel = self._make_panel(310, 430)

        self._surf_sub   = self.font_sub.render("ARCHITECT  vs  PILOT", True, (180,120,255))
        self._surf_hint  = self.font_sub.render(
            "PILOT CONTROLS:  A / D  =  Rotate      < / >  =  Speed", True, (100,100,160))
        self._surf_lbl   = self.font_label.render("SAVED MAPS", True, (200,160,255))

        for btn in self.buttons:
            btn["surf"]     = self.font_btn.render(btn["text"], True, (255,255,255))
            btn["surf_dim"] = self.font_btn.render(btn["text"], True, (160,160,160))

        self._best_times = self._load_best_times()
        self._map_surfs  = []
        self._sel_cache  = -2
        self._rebuild_map_surfs()

        self._glow_frame = -99
        self._glow_surfs = []
        self._title_surf = self.font_title.render("ROCKET DUEL", True, (255,255,255))
        self._title_x    = 400 - self._title_surf.get_width()//2

        # Rename state
        self.rename_mode  = False
        self.rename_input = None
        self._rename_panel = self._make_rename_panel()

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0,0,0,175), (0,0,w,h), border_radius=10)
        pygame.draw.rect(s, (80,0,180,200), (0,0,w,h), 1, border_radius=10)
        return s

    def _make_rename_panel(self):
        s = pygame.Surface((360, 150), pygame.SRCALPHA)
        pygame.draw.rect(s, (0,0,0,210), (0,0,360,150), border_radius=10)
        pygame.draw.rect(s, (180,60,255,220), (0,0,360,150), 2, border_radius=10)
        return s

    def _load_maps(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT id, name, start_point, goal_point, obstacles FROM maps ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def _load_best_times(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("SELECT map_id, MIN(time_taken) FROM scores GROUP BY map_id")
        result = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return result

    def _rename_map_in_db(self, map_id, new_name):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("UPDATE maps SET name=? WHERE id=?", (new_name, map_id))
        conn.commit()
        conn.close()

    def _rebuild_map_surfs(self):
        self._map_surfs = []
        for i, m in enumerate(self.maps):
            if i >= 14: break
            is_sel  = (i == self.selected_map_idx)
            best    = self._best_times.get(m[0])
            time_str = f"  [{best:.1f}s]" if best else ""
            col     = (255,220,50) if is_sel else (200,200,220)
            surf    = self.font_list.render(f"{i+1}.  {m[1]}{time_str}", True, col)
            self._map_surfs.append((surf, i, is_sel))
        self._sel_cache = self.selected_map_idx

    def handle_event(self, event):
        # Route to rename popup first if active
        if self.rename_mode and self.rename_input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rename_mode = False; return None, None
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    new_name = self.rename_input.text.strip()
                    if new_name and self.selected_map_idx != -1:
                        m = self.maps[self.selected_map_idx]
                        self._rename_map_in_db(m[0], new_name)
                        self.maps = self._load_maps()
                        self._rebuild_map_surfs()
                    self.rename_mode = False; return None, None
            self.rename_input.handle_event(event)

            # Save / Cancel buttons in popup
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                px, py = 220, 235  # panel origin
                save_rect   = pygame.Rect(px+50,  py+105, 100, 32)
                cancel_rect = pygame.Rect(px+210, py+105, 100, 32)
                if save_rect.collidepoint(event.pos):
                    new_name = self.rename_input.text.strip()
                    if new_name and self.selected_map_idx != -1:
                        m = self.maps[self.selected_map_idx]
                        self._rename_map_in_db(m[0], new_name)
                        self.maps = self._load_maps()
                        self._rebuild_map_surfs()
                    self.rename_mode = False
                elif cancel_rect.collidepoint(event.pos):
                    self.rename_mode = False
            return None, None

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
                    if btn["action"] == "RENAME" and self.selected_map_idx != -1:
                        m = self.maps[self.selected_map_idx]
                        self.rename_input = TextInput(230, 295, 300, 38, self.font_inp, max_len=30)
                        self.rename_input.text   = m[1]
                        self.rename_input.active = True
                        self.rename_mode = True

            for i in range(min(14, len(self.maps))):
                rect = pygame.Rect(238, 195+i*26, 295, 22)
                if rect.collidepoint(event.pos):
                    self.selected_map_idx = i

        return None, None

    def draw(self, surface):
        self.frame += 1
        f = self.frame
        self.bg.update(); self.bg.draw(surface)

        if self._sel_cache != self.selected_map_idx:
            self._rebuild_map_surfs()

        # Left panel
        surface.blit(self._left_panel, (15, 155))
        mx, my = pygame.mouse.get_pos()

        for btn in self.buttons:
            is_load    = btn["action"] == "LOAD"
            is_rename  = btn["action"] == "RENAME"
            no_map     = self.selected_map_idx == -1
            disabled   = (is_load or is_rename) and no_map

            if disabled:
                base = (70, 70, 90)
            elif btn["action"] == "NEW":
                base = (0, 100, 200)
            elif btn["action"] == "LOAD":
                base = (0, 150, 80)
            elif btn["action"] == "RENAME":
                base = (120, 60, 0)
            else:
                base = (160, 70, 0)

            hover = btn["rect"].collidepoint((mx, my)) and not disabled
            if hover:
                pulse = int(20*math.sin(f*0.15))
                base  = tuple(min(255, c+50+pulse) for c in base)

            pygame.draw.rect(surface, base, btn["rect"], border_radius=6)
            pygame.draw.rect(surface, (150,80,255) if hover else (80,20,150),
                             btn["rect"], 1, border_radius=6)
            ts = btn["surf_dim"] if disabled else btn["surf"]
            surface.blit(ts, (btn["rect"].centerx - ts.get_width()//2,
                              btn["rect"].centery - ts.get_height()//2))

        # Title glow (every 4 frames)
        if f - self._glow_frame >= 4:
            self._glow_frame = f
            glow_col = (0, int(180+75*math.sin(f*0.05)), 255)
            g_surf   = self.font_title.render("ROCKET DUEL", True, glow_col)
            gx       = 400 - g_surf.get_width()//2
            self._glow_surfs = [(g_surf, gx+ox, 68+oy) for ox, oy in ((-2,0),(2,0),(0,-2),(0,2))]
        for gs, gx, gy in self._glow_surfs:
            surface.blit(gs, (gx, gy))
        surface.blit(self._title_surf, (self._title_x, 68))
        surface.blit(self._surf_sub,   (400 - self._surf_sub.get_width()//2, 122))

        # Right panel
        surface.blit(self._right_panel, (230, 155))
        surface.blit(self._surf_lbl, (244, 163))

        for surf, i, is_sel in self._map_surfs:
            y = 195 + i*26
            if is_sel:
                sr = pygame.Rect(236, y-2, 296, 22)
                pygame.draw.rect(surface, (60,0,130), sr, border_radius=4)
                pygame.draw.rect(surface, (180,60,255), sr, 1, border_radius=4)
            surface.blit(surf, (244, y))

        surface.blit(self._surf_hint, (400 - self._surf_hint.get_width()//2, 575))

        # Rename popup overlay
        if self.rename_mode and self.rename_input:
            px, py = 220, 235
            surface.blit(self._rename_panel, (px, py))
            title = self.font_btn.render("RENAME MAP", True, (200,160,255))
            surface.blit(title, (px+15, py+12))
            lbl = self.font_sub.render("New name:", True, (180,180,200))
            surface.blit(lbl, (px+15, py+50))
            self.rename_input.draw(surface)

            save_rect   = pygame.Rect(px+50,  py+105, 100, 32)
            cancel_rect = pygame.Rect(px+210, py+105, 100, 32)
            shover = save_rect.collidepoint((mx, my))
            chover = cancel_rect.collidepoint((mx, my))
            pygame.draw.rect(surface, (0,160,80) if shover else (0,110,55), save_rect, border_radius=5)
            pygame.draw.rect(surface, (0,220,100), save_rect, 1, border_radius=5)
            st = self.font_btn.render("SAVE", True, (255,255,255))
            surface.blit(st, (save_rect.centerx-st.get_width()//2, save_rect.centery-st.get_height()//2))
            pygame.draw.rect(surface, (140,0,0) if chover else (90,0,0), cancel_rect, border_radius=5)
            pygame.draw.rect(surface, (220,50,50), cancel_rect, 1, border_radius=5)
            ct = self.font_btn.render("CANCEL", True, (255,255,255))
            surface.blit(ct, (cancel_rect.centerx-ct.get_width()//2, cancel_rect.centery-ct.get_height()//2))
            esc_hint = self.font_sub.render("ESC to cancel", True, (100,80,130))
            surface.blit(esc_hint, (px+15, py+145))


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
        self._btn_surf = self.font_btn.render("BACK", True, (255,255,255))
        self._rows    = self._build_rows()

    def _make_panel(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0,0,0,180), (0,0,w,h), border_radius=10)
        pygame.draw.rect(s, (80,0,180,200), (0,0,w,h), 1, border_radius=10)
        return s

    def _load(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute("""
            SELECT m.id, m.name, s.time_taken
            FROM maps m LEFT JOIN scores s ON m.id=s.map_id
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
        MEDALS = {0: (255,215,0), 1: (180,180,180), 2: (180,100,40)}
        rows = []
        y = 0
        for map_id in sorted(self.boards.keys()):
            board = self.boards[map_id]
            lbl   = self.font_label.render(f"  {board['name']}", True, (80,255,160))
            rows.append(("map", lbl, y)); y += 26
            if board["scores"]:
                for rank, t in enumerate(board["scores"][:5]):
                    col    = MEDALS.get(rank, (200,200,200))
                    prefix = ["#1","#2","#3","#4","#5"][rank]
                    s = self.font_score.render(f"   {prefix}   {t:.3f}s", True, col)
                    rows.append(("score", s, y)); y += 20
            else:
                s = self.font_score.render("   No runs recorded yet", True, (110,110,130))
                rows.append(("score", s, y)); y += 20
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
        self.bg.update(); self.bg.draw(surface)
        surface.blit(self._panel, (90, 65))
        glow_col = (255, int(160+60*math.sin(f*0.05)), 0)
        g  = self.font_title.render("LEADERBOARD", True, glow_col)
        gx = 400 - g.get_width()//2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            surface.blit(g, (gx+ox, 72+oy))
        surface.blit(self.font_title.render("LEADERBOARD", True, (255,230,80)), (gx, 72))
        base_y = 125
        for kind, surf, y_off in self._rows:
            y = base_y + y_off
            if y > 490: break
            surface.blit(surf, (108 if kind=="map" else 115, y))
        mx, my = pygame.mouse.get_pos()
        hover  = self.back_btn.collidepoint((mx, my))
        bcol   = (0,180,240) if hover else (0,130,180)
        pygame.draw.rect(surface, bcol, self.back_btn, border_radius=6)
        pygame.draw.rect(surface, (0,220,255), self.back_btn, 1, border_radius=6)
        surface.blit(self._btn_surf,
                     (self.back_btn.centerx - self._btn_surf.get_width()//2,
                      self.back_btn.centery - self._btn_surf.get_height()//2))
