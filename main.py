import sys
import random
import collections

from sound_manager import pre_init, SoundManager
pre_init()

import pygame
from design_mode import DesignMode, draw_lightning
from play_mode import PlayMode
from dashboard import Dashboard, Leaderboard, PlayerNamesScreen, RoundBreakScreen, GameOverScreen


class FPSCounter:
    def __init__(self, samples=30):
        self._times = collections.deque(maxlen=samples)
        self._last  = pygame.time.get_ticks()
        try:
            self._font = pygame.font.SysFont("monospace", 14)
        except:
            self._font = pygame.font.SysFont(None, 14)
        self._surf  = None
        self._tick  = 0

    def update(self):
        now = pygame.time.get_ticks()
        dt  = now - self._last
        self._last = now
        if dt > 0: self._times.append(dt)
        self._tick += 1
        if self._tick % 20 == 0 and self._times:
            avg_ms = sum(self._times) / len(self._times)
            fps    = 1000.0 / avg_ms if avg_ms > 0 else 0
            self._surf = self._font.render(f"FPS {fps:.0f}", True, (100,255,100))

    def draw(self, surface):
        if self._surf:
            surface.blit(self._surf, (760 - self._surf.get_width(), 4))


class FlashTransition:
    def __init__(self, color=(0,180,255), duration=18):
        self.color    = color
        self.duration = duration
        self.timer    = duration
        self.done     = False
        self._surf    = pygame.Surface((800, 600))
        self._surf.fill(color)

    def update(self):
        if self.timer > 0: self.timer -= 1
        else: self.done = True

    def draw(self, surface):
        if self.done: return
        t = self.timer / self.duration
        self._surf.set_alpha(max(0, min(255, int(220*t))))
        surface.blit(self._surf, (0,0))
        if t > 0.5:
            for _ in range(2):
                x1 = random.randint(50,750); y1 = random.randint(0,150)
                draw_lightning(surface,(x1,y1),
                               (x1+random.randint(-100,100), y1+random.randint(100,400)),
                               self.color, width=2, jitter=12)


def _fresh_ctx():
    return {
        'p1': 'Player 1', 'p2': 'Player 2',
        'round': 0,
        'p1_won': False, 'p1_time': None,
        'p2_won': False, 'p2_time': None,
        'preloaded_map': None,   # set when LOAD MAP chosen
    }


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Rocket Duel – Architect vs Pilot")
    clock = pygame.time.Clock()
    fps   = FPSCounter()
    snd   = SoundManager()

    state            = "DASHBOARD"
    next_state       = None
    transition       = None
    dashboard        = Dashboard()
    leaderboard      = None
    player_names_scr = None
    design_mode      = None
    play_mode        = None
    round_break_scr  = None
    game_over_scr    = None
    ctx              = _fresh_ctx()

    def go(to, color=(0,150,255)):
        nonlocal next_state, transition
        next_state = to
        transition = FlashTransition(color=color, duration=20)

    while True:
        clock.tick(60)
        fps.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if transition and not transition.done:
                continue

            # ── DASHBOARD ─────────────────────────────────────────────────────
            if state == "DASHBOARD":
                action, data = dashboard.handle_event(event)
                if action == "NEW":
                    ctx = _fresh_ctx()
                    ctx['preloaded_map'] = None
                    player_names_scr = PlayerNamesScreen()
                    go("PLAYER_NAMES", (0,120,255))
                elif action == "LOAD":
                    ctx = _fresh_ctx()
                    ctx['preloaded_map'] = data   # map data dict
                    player_names_scr = PlayerNamesScreen()
                    go("PLAYER_NAMES", (0,120,255))
                elif action == "LEADERBOARD":
                    leaderboard = Leaderboard()
                    go("LEADERBOARD", (255,180,0))

            # ── PLAYER NAMES ──────────────────────────────────────────────────
            elif state == "PLAYER_NAMES":
                result = player_names_scr.handle_event(event)
                if result:
                    ctx['p1'], ctx['p2'] = result
                    ctx['round'] = 1
                    if ctx['preloaded_map']:
                        # Round 1: skip design, P2 pilots the loaded map
                        m = ctx['preloaded_map']
                        play_mode = PlayMode(
                            tuple(m['start']), tuple(m['goal']),
                            [(tuple(o[0]),tuple(o[1])) for o in m['obstacles']],
                            map_id=m['map_id'], snd=snd,
                            pilot_name=ctx['p2'], architect_name=ctx['p1'])
                        go("PLAY", (0,255,150))
                    else:
                        # Round 1: P1 designs
                        design_mode = DesignMode(snd=snd, architect_name=ctx['p1'])
                        go("DESIGN", (0,120,255))

            # ── DESIGN ────────────────────────────────────────────────────────
            elif state == "DESIGN":
                if design_mode.handle_event(event) == "PLAY":
                    if ctx['round'] == 1:
                        pilot_n, arch_n = ctx['p2'], ctx['p1']
                    else:
                        pilot_n, arch_n = ctx['p1'], ctx['p2']
                    play_mode = PlayMode(
                        design_mode.start_point, design_mode.goal_point,
                        design_mode.obstacles, snd=snd,
                        obstacle_colors=design_mode.obstacle_colors,
                        pilot_name=pilot_n, architect_name=arch_n)
                    go("PLAY", (0,255,150))

            # ── PLAY ──────────────────────────────────────────────────────────
            elif state == "PLAY":
                if play_mode.handle_event(event) == "DASHBOARD":
                    if ctx['round'] == 1:
                        ctx['p2_won']  = (play_mode.status == "WIN")
                        ctx['p2_time'] = play_mode.end_time if play_mode.status == "WIN" else None
                        round_break_scr = RoundBreakScreen(
                            ctx['p1'], ctx['p2'], ctx['p2_won'], ctx['p2_time'])
                        go("ROUND_BREAK", (255,180,0))
                    elif ctx['round'] == 2:
                        ctx['p1_won']  = (play_mode.status == "WIN")
                        ctx['p1_time'] = play_mode.end_time if play_mode.status == "WIN" else None
                        game_over_scr = GameOverScreen(
                            ctx['p1'], ctx['p2'],
                            ctx['p1_won'], ctx['p1_time'],
                            ctx['p2_won'], ctx['p2_time'])
                        go("GAME_OVER", (200,50,255))
                    else:
                        # Fallback (shouldn't happen in normal flow)
                        dashboard = Dashboard()
                        go("DASHBOARD", (0,120,255))

            # ── ROUND BREAK ───────────────────────────────────────────────────
            elif state == "ROUND_BREAK":
                if round_break_scr.handle_event(event) == "CONTINUE":
                    ctx['round'] = 2
                    design_mode  = DesignMode(snd=snd, architect_name=ctx['p2'])
                    go("DESIGN", (0,200,255))

            # ── GAME OVER ─────────────────────────────────────────────────────
            elif state == "GAME_OVER":
                if game_over_scr.handle_event(event) == "DASHBOARD":
                    ctx       = _fresh_ctx()
                    dashboard = Dashboard()
                    go("DASHBOARD", (0,120,255))

            # ── LEADERBOARD ───────────────────────────────────────────────────
            elif state == "LEADERBOARD":
                if leaderboard.handle_event(event) == "DASHBOARD":
                    dashboard = Dashboard()
                    go("DASHBOARD", (200,100,0))

        # ── Advance transition ─────────────────────────────────────────────────
        if transition:
            transition.update()
            if transition.done:
                state, next_state, transition = next_state, None, None

        # ── Update ────────────────────────────────────────────────────────────
        if   state == "DESIGN":      design_mode.update()
        elif state == "PLAY":        play_mode.update()

        # ── Draw ──────────────────────────────────────────────────────────────
        if   state == "DASHBOARD":    dashboard.draw(screen)
        elif state == "PLAYER_NAMES": player_names_scr.draw(screen)
        elif state == "DESIGN":       design_mode.draw(screen)
        elif state == "PLAY":         play_mode.draw(screen)
        elif state == "ROUND_BREAK":  round_break_scr.draw(screen)
        elif state == "GAME_OVER":    game_over_scr.draw(screen)
        elif state == "LEADERBOARD":  leaderboard.draw(screen)

        if transition:
            transition.draw(screen)

        fps.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
