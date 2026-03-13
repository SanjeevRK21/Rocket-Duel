import pygame
import sys
import random
import math
from design_mode import DesignMode, draw_lightning
from play_mode import PlayMode
from dashboard import Dashboard, Leaderboard
from sound_manager import SoundManager


class FlashTransition:
    """A brief electric flash when changing game states."""
    def __init__(self, color=(0, 180, 255), duration=18):
        self.color    = color
        self.duration = duration
        self.timer    = duration
        self.done     = False

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        else:
            self.done = True

    def draw(self, surface):
        if self.done:
            return
        t = self.timer / self.duration
        # Strong flash at start, fade out
        alpha = int(220 * t)
        alpha = max(0, min(255, alpha))
        flash = pygame.Surface((800, 600), pygame.SRCALPHA)
        flash.fill((*self.color, alpha))
        surface.blit(flash, (0, 0))
        # Lightning bolts during flash
        if t > 0.4:
            for _ in range(3):
                x1 = random.randint(50, 750)
                y1 = random.randint(0, 200)
                draw_lightning(surface, (x1, y1),
                               (x1 + random.randint(-100, 100), y1 + random.randint(100, 400)),
                               self.color, width=2, jitter=15)


def main():
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Rocket Duel – Architect vs Pilot")
    clock = pygame.time.Clock()

    snd = SoundManager()

    state       = "DASHBOARD"
    next_state  = None
    transition  = None
    dashboard   = Dashboard()
    leaderboard = None
    design_mode = None
    play_mode   = None

    def trigger_transition(to_state, color=(0, 150, 255)):
        nonlocal next_state, transition
        next_state = to_state
        transition = FlashTransition(color=color, duration=20)

    while True:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Block input during transition
            if transition and not transition.done:
                continue

            if state == "DASHBOARD":
                action, data = dashboard.handle_event(event)
                if action == "NEW":
                    design_mode = DesignMode(snd=snd)
                    trigger_transition("DESIGN", color=(0, 120, 255))
                elif action == "LOAD":
                    play_mode = PlayMode(
                        tuple(data["start"]), tuple(data["goal"]),
                        [(tuple(o[0]), tuple(o[1])) for o in data["obstacles"]],
                        map_id=data["map_id"], snd=snd)
                    trigger_transition("PLAY", color=(0, 255, 150))
                elif action == "LEADERBOARD":
                    leaderboard = Leaderboard()
                    trigger_transition("LEADERBOARD", color=(255, 180, 0))

            elif state == "DESIGN":
                result = design_mode.handle_event(event)
                if result == "PLAY":
                    play_mode = PlayMode(
                        design_mode.start_point, design_mode.goal_point,
                        design_mode.obstacles, snd=snd)
                    trigger_transition("PLAY", color=(0, 255, 150))

            elif state == "PLAY":
                result = play_mode.handle_event(event)
                if result == "DASHBOARD":
                    dashboard = Dashboard()
                    trigger_transition("DASHBOARD", color=(0, 120, 255))

            elif state == "LEADERBOARD":
                result = leaderboard.handle_event(event)
                if result == "DASHBOARD":
                    dashboard = Dashboard()
                    trigger_transition("DASHBOARD", color=(200, 100, 0))

        # Advance transition
        if transition:
            transition.update()
            if transition.done:
                state      = next_state
                next_state = None
                transition = None

        # Update
        if state == "DESIGN":
            design_mode.update()
        elif state == "PLAY":
            play_mode.update()

        # Draw
        if state == "DASHBOARD":
            dashboard.draw(screen)
        elif state == "LEADERBOARD":
            leaderboard.draw(screen)
        elif state == "DESIGN":
            design_mode.draw(screen)
        elif state == "PLAY":
            play_mode.draw(screen)

        # Draw transition overlay on top
        if transition:
            transition.draw(screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()
