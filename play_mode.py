import pygame
import time
import math
import random
import sqlite3
from rocket import Rocket
from geometry import segments_intersect, distance

def draw_lightning(surface, p1, p2, color, width=1, jitter=6, segs=5):
    pts = [p1]
    for i in range(1, segs):
        t = i / segs
        pts.append((
            p1[0]+(p2[0]-p1[0])*t + random.uniform(-jitter, jitter),
            p1[1]+(p2[1]-p1[1])*t + random.uniform(-jitter, jitter),
        ))
    pts.append(p2)
    pygame.draw.lines(surface, color, False, pts, width)


class PlayMode:
    def __init__(self, start_point, goal_point, obstacles, map_id=None, snd=None):
        self.start_point = start_point
        self.goal_point  = goal_point
        self.obstacles   = obstacles
        self.map_id      = map_id
        self.snd         = snd
        self.rocket      = Rocket(start_point[0], start_point[1])
        self.start_time  = time.time()

        try:
            self.font_hud = pygame.font.SysFont("monospace", 20, bold=True)
            self.font_msg = pygame.font.SysFont("Arial", 38, bold=True)
            self.font_sub = pygame.font.SysFont("Arial", 18)
        except:
            self.font_hud = pygame.font.SysFont(None, 20)
            self.font_msg = pygame.font.SysFont(None, 38)
            self.font_sub = pygame.font.SysFont(None, 18)

        self.status   = "PLAYING"
        self.end_time = 0

        self.stars = [(random.randint(0, 800), random.randint(0, 600),
                       random.uniform(0.5, 3.0)) for _ in range(60)]

        # ── Pre-built reusable surfaces ────────────────────────────────────────
        self.flash_surf   = pygame.Surface((800, 600))
        self.win_overlay  = pygame.Surface((800, 600))
        self.win_overlay.fill((0, 60, 30)); self.win_overlay.set_alpha(40)
        self.loss_overlay = pygame.Surface((800, 600))
        self.loss_overlay.fill((80, 0, 0)); self.loss_overlay.set_alpha(40)

        self.hud_bg = pygame.Surface((215, 115), pygame.SRCALPHA)
        pygame.draw.rect(self.hud_bg, (0, 0, 0, 160),    self.hud_bg.get_rect(), border_radius=10)
        pygame.draw.rect(self.hud_bg, (120, 0, 255, 200), self.hud_bg.get_rect(), 1, border_radius=10)

        # ── Pre-render static/semi-static text ────────────────────────────────
        self._surf_ctrl = self.font_sub.render("A/D Rotate   LEFT/RIGHT Speed", True, (110, 110, 170))
        self.lbl_s      = self.font_sub.render("S", True, (0, 255, 100))
        self.lbl_g      = self.font_sub.render("G", True, (255, 120, 0))

        # WIN / LOSS messages — pre-rendered once
        self._win_msg  = self.font_msg.render("MISSION ACCOMPLISHED!", True, (0, 255, 150))
        self._loss_msg = self.font_msg.render("CRITICAL COLLISION!",   True, (255, 60, 60))
        self._loss_sub = self.font_hud.render("PILOT LOST  |  ENTER to return", True, (255, 200, 200))

        # ── HUD text cache ────────────────────────────────────────────────────
        # Only re-render when the displayed value changes
        self._hud_time_str  = ""
        self._hud_speed_str = ""
        self._hud_angle_str = ""
        self._surf_time  = None
        self._surf_speed = None
        self._surf_angle = None
        self._win_sub    = None   # includes time so built on WIN

        # ── Misc ──────────────────────────────────────────────────────────────
        self.flash_timer  = 0
        self.flash_color  = (255, 255, 255)
        self.crash_sparks = []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def save_score(self):
        if self.map_id and self.status == "WIN":
            conn = sqlite3.connect('database.sqlite')
            c = conn.cursor()
            c.execute("INSERT INTO scores (map_id, time_taken) VALUES (?, ?)",
                      (self.map_id, self.end_time))
            conn.commit()
            conn.close()

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.status != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.save_score()
                return "DASHBOARD"
        return "PLAY"

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self):
        if self.status != "PLAYING":
            alive = []
            for sp in self.crash_sparks:
                sp[0]+=sp[2]; sp[1]+=sp[3]; sp[4]-=0.04
                if sp[4] > 0: alive.append(sp)
            self.crash_sparks = alive
            if self.flash_timer > 0:
                self.flash_timer -= 1
            return

        old_x = self.rocket.x
        old_y = self.rocket.y
        self.rocket.update(1.0/60.0)

        if self.snd:
            if self.rocket.speed > 0.3: self.snd.start_engine()
            else:                        self.snd.stop_engine()

        new_x = self.rocket.x
        new_y = self.rocket.y

        if distance((new_x, new_y), self.goal_point) < self.rocket.radius + 12:
            self.status      = "WIN"
            self.end_time    = time.time() - self.start_time
            self.flash_timer = 30
            self.flash_color = (0, 255, 150)
            # Pre-render win subtitle (contains final time)
            self._win_sub = self.font_hud.render(
                f"TIME: {self.end_time:.2f}s  |  ENTER to continue", True, (200, 255, 200))
            if self.snd:
                self.snd.stop_engine(); self.snd.play("win")
            return

        r = self.rocket.radius
        edges = [
            ((new_x-r, new_y-r),(new_x+r, new_y-r)),
            ((new_x+r, new_y-r),(new_x+r, new_y+r)),
            ((new_x+r, new_y+r),(new_x-r, new_y+r)),
            ((new_x-r, new_y+r),(new_x-r, new_y-r)),
            ((old_x, old_y),(new_x, new_y))
        ]
        SPARK_COLS = [(255,80,0),(255,200,0),(255,50,50),(0,200,255)]
        for obs in self.obstacles:
            for edge in edges:
                if segments_intersect(edge[0], edge[1], obs[0], obs[1]):
                    self.status      = "LOSS"
                    self.end_time    = time.time() - self.start_time
                    self.flash_timer = 25
                    self.flash_color = (255, 30, 30)
                    if self.snd:
                        self.snd.stop_engine(); self.snd.play("crash")
                    for _ in range(30):
                        ang = random.uniform(0, math.pi*2)
                        spd = random.uniform(1, 5)
                        rc, gc, bc = random.choice(SPARK_COLS)
                        self.crash_sparks.append(
                            [float(new_x), float(new_y),
                             math.cos(ang)*spd, math.sin(ang)*spd,
                             1.0, rc, gc, bc])
                    return

        if self.flash_timer > 0:
            self.flash_timer -= 1

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill((2, 2, 12))
        t = pygame.time.get_ticks()

        # Stars
        for sx, sy, freq in self.stars:
            b = int(90 + 120 * math.sin(t * 0.001 * freq))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy), 1)

        # Ambient lightning (rare)
        if self.obstacles and random.random() < 0.011:
            obs = random.choice(self.obstacles)
            draw_lightning(surface, obs[0], obs[1], (100, 0, 180), width=1, jitter=8)

        # Obstacles
        for obs in self.obstacles:
            pygame.draw.line(surface, (80, 0, 110),   obs[0], obs[1], 7)
            pygame.draw.line(surface, (190, 50, 255),  obs[0], obs[1], 2)
            pygame.draw.circle(surface, (210, 90, 255), obs[0], 3)
            pygame.draw.circle(surface, (210, 90, 255), obs[1], 3)

        # Markers
        pygame.draw.circle(surface, (0, 255, 100), self.start_point, 6)
        surface.blit(self.lbl_s, (self.start_point[0]-5, self.start_point[1]-22))

        pulse = int((math.cos(t * 0.01) + 1) * 4)
        pygame.draw.circle(surface, (255, 50, 50),  self.goal_point, 14+pulse, 2)
        pygame.draw.circle(surface, (255, 120, 0),   self.goal_point, 7)
        pygame.draw.circle(surface, (255, 255, 255), self.goal_point, 3)
        surface.blit(self.lbl_g, (self.goal_point[0]-5, self.goal_point[1]-24))

        # Crash sparks
        for sp in self.crash_sparks:
            life = max(0.0, sp[4])
            pygame.draw.circle(surface, (int(sp[5]*life), int(sp[6]*life), int(sp[7]*life)),
                               (int(sp[0]), int(sp[1])), 3)

        if self.status != "LOSS":
            self.rocket.draw(surface)

        # Flash overlay
        if self.flash_timer > 0:
            alpha = max(0, min(255, int(180 * self.flash_timer / 30)))
            self.flash_surf.fill(self.flash_color)
            self.flash_surf.set_alpha(alpha)
            surface.blit(self.flash_surf, (0, 0))

        # HUD — cache text surfaces, only re-render on value change
        current_time = self.end_time if self.status != "PLAYING" else (time.time() - self.start_time)

        time_str  = f"TIME:  {current_time:.1f}s"
        speed_str = f"SPEED: {self.rocket.speed:.1f}"
        angle_str = f"ANGLE: {int(self.rocket.angle % 360):>3}"

        if time_str  != self._hud_time_str:
            self._surf_time  = self.font_hud.render(time_str,  True, (0, 255, 255))
            self._hud_time_str = time_str
        if speed_str != self._hud_speed_str:
            self._surf_speed = self.font_hud.render(speed_str, True, (255, 220, 0))
            self._hud_speed_str = speed_str
        if angle_str != self._hud_angle_str:
            self._surf_angle = self.font_hud.render(angle_str, True, (200, 100, 255))
            self._hud_angle_str = angle_str

        surface.blit(self.hud_bg,    (8, 8))
        surface.blit(self._surf_time,  (22, 22))
        surface.blit(self._surf_speed, (22, 48))
        surface.blit(self._surf_angle, (22, 74))
        surface.blit(self._surf_ctrl,  (22, 100))

        # Win / Loss
        if self.status == "WIN":
            for _ in range(2):
                x1 = random.randint(50, 750)
                draw_lightning(surface, (x1, 0),
                               (x1+random.randint(-80, 80), 600),
                               (0, 220, 130), width=1, jitter=18)
            surface.blit(self.win_overlay, (0, 0))
            msg = self._win_msg
            sub = self._win_sub or self.font_hud.render(
                f"TIME: {current_time:.2f}s  |  ENTER to continue", True, (200, 255, 200))
            bx = 400 - msg.get_width()//2 - 15
            pygame.draw.rect(surface, (0, 0, 0),
                             pygame.Rect(bx, 235, msg.get_width()+30, 90), border_radius=8)
            surface.blit(msg, (400 - msg.get_width()//2, 245))
            surface.blit(sub, (400 - sub.get_width()//2,  298))

        elif self.status == "LOSS":
            for _ in range(3):
                x1 = random.randint(50, 750)
                draw_lightning(surface, (x1, 0),
                               (x1+random.randint(-60, 60), 600),
                               (220, 30, 30), width=1, jitter=12)
            surface.blit(self.loss_overlay, (0, 0))
            msg = self._loss_msg
            sub = self._loss_sub
            bx  = 400 - msg.get_width()//2 - 15
            pygame.draw.rect(surface, (0, 0, 0),
                             pygame.Rect(bx, 235, msg.get_width()+30, 90), border_radius=8)
            surface.blit(msg, (400 - msg.get_width()//2, 245))
            surface.blit(sub, (400 - sub.get_width()//2,  298))
