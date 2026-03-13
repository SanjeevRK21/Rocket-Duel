import sys
import random
import collections

from sound_manager import pre_init, SoundManager
pre_init()

import pygame
from design_mode import DesignMode, draw_lightning
from play_mode import PlayMode
from dashboard import Dashboard, Leaderboard


class FPSCounter:
    """Lightweight rolling-average FPS display."""
    def __init__(self, samples=30):
        self._times  = collections.deque(maxlen=samples)
        self._last   = pygame.time.get_ticks()
        try:
            self._font = pygame.font.SysFont("monospace", 14)
        except:
            self._font = pygame.font.SysFont(None, 14)
        self._surf   = None
        self._tick   = 0

    def update(self):
        now = pygame.time.get_ticks()
        dt  = now - self._last
        self._last = now
        if dt > 0:
            self._times.append(dt)
        self._tick += 1
        # Re-render text only every 20 frames
        if self._tick % 20 == 0 and self._times:
            avg_ms = sum(self._times) / len(self._times)
            fps    = 1000.0 / avg_ms if avg_ms > 0 else 0
            self._surf = self._font.render(f"FPS {fps:.0f}", True, (100, 255, 100))

    def draw(self, surface):
        if self._surf:
            surface.blit(self._surf, (760 - self._surf.get_width(), 4))


class FlashTransition:
    def __init__(self, color=(0, 180, 255), duration=18):
        self.color    = color
        self.duration = duration
        self.timer    = duration
        self.done     = False
        self._surf    = pygame.Surface((800, 600))
        self._surf.fill(color)

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        else:
            self.done = True

    def draw(self, surface):
        if self.done:
            return
        t     = self.timer / self.duration
        alpha = max(0, min(255, int(220 * t)))
        self._surf.set_alpha(alpha)
        surface.blit(self._surf, (0, 0))
        if t > 0.5:
            for _ in range(2):
                x1 = random.randint(50, 750)
                y1 = random.randint(0, 150)
                draw_lightning(surface, (x1, y1),
                               (x1+random.randint(-100, 100), y1+random.randint(100, 400)),
                               self.color, width=2, jitter=12)


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Rocket Duel – Architect vs Pilot")
    clock = pygame.time.Clock()
    fps   = FPSCounter()

    snd = SoundManager()

    state       = "DASHBOARD"
    next_state  = None
    transition  = None
    dashboard   = Dashboard()
    leaderboard = None
    design_mode = None
    play_mode   = None

    def go(to, color=(0, 150, 255)):
        nonlocal next_state, transition
        next_state = to
        transition = FlashTransition(color=color, duration=20)

    while True:
        clock.tick(60)
        fps.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if transition and not transition.done:
                continue

            if state == "DASHBOARD":
                action, data = dashboard.handle_event(event)
                if action == "NEW":
                    design_mode = DesignMode(snd=snd)
                    go("DESIGN", (0, 120, 255))
                elif action == "LOAD":
                    play_mode = PlayMode(
                        tuple(data["start"]), tuple(data["goal"]),
                        [(tuple(o[0]), tuple(o[1])) for o in data["obstacles"]],
                        map_id=data["map_id"], snd=snd)
                    go("PLAY", (0, 255, 150))
                elif action == "LEADERBOARD":
                    leaderboard = Leaderboard()
                    go("LEADERBOARD", (255, 180, 0))

            elif state == "DESIGN":
                if design_mode.handle_event(event) == "PLAY":
                    play_mode = PlayMode(
                        design_mode.start_point, design_mode.goal_point,
                        design_mode.obstacles, snd=snd)
                    go("PLAY", (0, 255, 150))

            elif state == "PLAY":
                if play_mode.handle_event(event) == "DASHBOARD":
                    dashboard = Dashboard()
                    go("DASHBOARD", (0, 120, 255))

            elif state == "LEADERBOARD":
                if leaderboard.handle_event(event) == "DASHBOARD":
                    dashboard = Dashboard()
                    go("DASHBOARD", (200, 100, 0))

        # Advance transition
        if transition:
            transition.update()
            if transition.done:
                state, next_state, transition = next_state, None, None

        # Update
        if   state == "DESIGN": design_mode.update()
        elif state == "PLAY":   play_mode.update()

        # Draw
        if   state == "DASHBOARD":   dashboard.draw(screen)
        elif state == "LEADERBOARD": leaderboard.draw(screen)
        elif state == "DESIGN":      design_mode.draw(screen)
        elif state == "PLAY":        play_mode.draw(screen)

        if transition:
            transition.draw(screen)

        fps.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
