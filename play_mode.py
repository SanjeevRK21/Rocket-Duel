import pygame
import time
import math
import random
import sqlite3
from rocket import Rocket
from geometry import segments_intersect, distance

def draw_lightning(surface, p1, p2, color, width=1, jitter=6, segs=6):
    pts = [p1]
    for i in range(1, segs):
        t = i / segs
        mx = p1[0] + (p2[0] - p1[0]) * t + random.uniform(-jitter, jitter)
        my = p1[1] + (p2[1] - p1[1]) * t + random.uniform(-jitter, jitter)
        pts.append((mx, my))
    pts.append(p2)
    if len(pts) >= 2:
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
        self.stars    = [(random.randint(0, 800), random.randint(0, 600), random.random())
                         for _ in range(120)]
        # Electric effects
        self.flash_timer  = 0
        self.flash_color  = (255, 255, 255)
        self.arc_timer    = 0
        self.crash_sparks = []

    def save_score(self):
        if self.map_id and self.status == "WIN":
            conn = sqlite3.connect('database.sqlite')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scores (map_id, time_taken) VALUES (?, ?)",
                           (self.map_id, self.end_time))
            conn.commit()
            conn.close()

    def handle_event(self, event):
        if self.status != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.save_score()
                return "DASHBOARD"
        return "PLAY"

    def update(self):
        if self.status != "PLAYING":
            # Update crash sparks
            for sp in self.crash_sparks[:]:
                sp["pos"][0] += sp["vel"][0]
                sp["pos"][1] += sp["vel"][1]
                sp["life"] -= 0.04
                if sp["life"] <= 0:
                    self.crash_sparks.remove(sp)
            return

        old_x = self.rocket.x
        old_y = self.rocket.y

        self.rocket.update(1.0 / 60.0)

        # Engine sound
        if self.snd:
            if self.rocket.speed > 0.3:
                self.snd.start_engine()
            else:
                self.snd.stop_engine()

        new_x = self.rocket.x
        new_y = self.rocket.y

        # Win condition
        if distance((new_x, new_y), self.goal_point) < self.rocket.radius + 12:
            self.status    = "WIN"
            self.end_time  = time.time() - self.start_time
            self.flash_timer = 30
            self.flash_color = (0, 255, 150)
            if self.snd:
                self.snd.stop_engine()
                self.snd.play("win")
            return

        # Collision detection (unchanged geometry logic)
        r = self.rocket.radius
        edges = [
            ((new_x-r, new_y-r), (new_x+r, new_y-r)),
            ((new_x+r, new_y-r), (new_x+r, new_y+r)),
            ((new_x+r, new_y+r), (new_x-r, new_y+r)),
            ((new_x-r, new_y+r), (new_x-r, new_y-r)),
            ((old_x, old_y), (new_x, new_y))
        ]
        for obs in self.obstacles:
            for edge in edges:
                if segments_intersect(edge[0], edge[1], obs[0], obs[1]):
                    self.status    = "LOSS"
                    self.end_time  = time.time() - self.start_time
                    self.flash_timer = 25
                    self.flash_color = (255, 30, 30)
                    if self.snd:
                        self.snd.stop_engine()
                        self.snd.play("crash")
                    # Spawn crash sparks
                    for _ in range(40):
                        angle = random.uniform(0, math.pi * 2)
                        spd   = random.uniform(1, 6)
                        self.crash_sparks.append({
                            "pos": [float(new_x), float(new_y)],
                            "vel": [math.cos(angle)*spd, math.sin(angle)*spd],
                            "life": 1.0,
                            "color": random.choice([(255,80,0),(255,200,0),(255,50,50),(0,200,255)])
                        })
                    return

        # Tick flash
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        surface.fill((2, 2, 12))

        t = pygame.time.get_ticks()

        # Stars
        for sx, sy, size in self.stars:
            b = int(90 + 130 * math.sin(t * 0.001 * size))
            b = max(0, min(255, b))
            pygame.draw.circle(surface, (b, b, b), (sx, sy),
                               1 if size < 0.7 else 2)

        # Ambient lightning arcs between obstacles
        if self.obstacles and random.random() < 0.04:
            obs = random.choice(self.obstacles)
            draw_lightning(surface, obs[0], obs[1],
                           (120, 0, 200), width=1, jitter=10)

        # Obstacles with neon glow
        for obs in self.obstacles:
            pygame.draw.line(surface, (80, 0, 110), obs[0], obs[1], 8)
            pygame.draw.line(surface, (190, 50, 255), obs[0], obs[1], 3)
            pygame.draw.circle(surface, (220, 100, 255), obs[0], 4)
            pygame.draw.circle(surface, (220, 100, 255), obs[1], 4)

        # Start marker
        pygame.draw.circle(surface, (0, 255, 100), self.start_point, 6)
        lbl = self.font_sub.render("S", True, (0, 255, 100))
        surface.blit(lbl, (self.start_point[0]-5, self.start_point[1]-20))

        # Goal marker — pulsing rings
        pulse = (math.cos(t * 0.01) + 1) * 4
        pygame.draw.circle(surface, (255, 50, 50), self.goal_point, int(14 + pulse), 2)
        pygame.draw.circle(surface, (255, 120, 0), self.goal_point, 7)
        pygame.draw.circle(surface, (255, 255, 255), self.goal_point, 3)
        lbl = self.font_sub.render("G", True, (255, 120, 0))
        surface.blit(lbl, (self.goal_point[0]-5, self.goal_point[1]-22))

        # Crash sparks
        for sp in self.crash_sparks:
            alpha = int(max(0, sp["life"] * 255))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*sp["color"], alpha), (3, 3), 3)
            surface.blit(s, (int(sp["pos"][0]-3), int(sp["pos"][1]-3)))

        # Rocket
        if self.status != "LOSS":
            self.rocket.draw(surface)

        # Flash overlay
        if self.flash_timer > 0:
            alpha = int(180 * self.flash_timer / 30)
            alpha = max(0, min(255, alpha))
            flash = pygame.Surface((800, 600), pygame.SRCALPHA)
            flash.fill((*self.flash_color, alpha))
            surface.blit(flash, (0, 0))

        # HUD panel
        current_time = self.end_time if self.status != "PLAYING" else (time.time() - self.start_time)
        hud_bg = pygame.Surface((215, 115), pygame.SRCALPHA)
        pygame.draw.rect(hud_bg, (0, 0, 0, 160), hud_bg.get_rect(), border_radius=10)
        pygame.draw.rect(hud_bg, (120, 0, 255, 200), hud_bg.get_rect(), 1, border_radius=10)
        surface.blit(hud_bg, (8, 8))

        time_txt  = self.font_hud.render(f"TIME:  {current_time:.2f}s", True, (0, 255, 255))
        speed_txt = self.font_hud.render(f"SPEED: {self.rocket.speed:.1f}", True, (255, 220, 0))
        angle_txt = self.font_hud.render(f"ANGLE: {int(self.rocket.angle % 360):>3}°", True, (200, 100, 255))
        ctrl_txt  = self.font_sub.render("A/D=Rotate  ◄/►=Speed", True, (120, 120, 180))
        surface.blit(time_txt,  (22, 22))
        surface.blit(speed_txt, (22, 48))
        surface.blit(angle_txt, (22, 74))
        surface.blit(ctrl_txt,  (22, 100))

        # Win / Loss overlay
        if self.status == "WIN":
            for _ in range(3):
                x1 = random.randint(0, 800)
                draw_lightning(surface, (x1, 0), (x1 + random.randint(-80,80), 600),
                               (0, 255, 150), width=1, jitter=20)
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 255, 100, 25))
            surface.blit(overlay, (0,0))
            msg = self.font_msg.render("MISSION ACCOMPLISHED!", True, (0, 255, 150))
            sub = self.font_hud.render(f"TIME: {current_time:.2f}s  |  ENTER to continue", True, (200, 255, 200))
            pygame.draw.rect(surface, (0,0,0,200),
                             pygame.Rect(400-msg.get_width()//2-15, 235, msg.get_width()+30, 90),
                             border_radius=8)
            surface.blit(msg, (400 - msg.get_width()//2, 245))
            surface.blit(sub, (400 - sub.get_width()//2, 298))

        elif self.status == "LOSS":
            for _ in range(4):
                x1 = random.randint(0, 800)
                draw_lightning(surface, (x1, 0), (x1 + random.randint(-60,60), 600),
                               (255, 30, 30), width=1, jitter=15)
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((200, 0, 0, 25))
            surface.blit(overlay, (0,0))
            msg = self.font_msg.render("CRITICAL COLLISION!", True, (255, 60, 60))
            sub = self.font_hud.render("PILOT LOST  |  ENTER to return", True, (255, 200, 200))
            pygame.draw.rect(surface, (0,0,0,200),
                             pygame.Rect(400-msg.get_width()//2-15, 235, msg.get_width()+30, 90),
                             border_radius=8)
            surface.blit(msg, (400 - msg.get_width()//2, 245))
            surface.blit(sub, (400 - sub.get_width()//2, 298))
