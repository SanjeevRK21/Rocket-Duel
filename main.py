import pygame
import sys
from design_mode import DesignMode
from play_mode import PlayMode

def main():
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Rocket Duel – Architect vs Pilot")
    clock = pygame.time.Clock()

    state = "DESIGN"
    design_mode = DesignMode()
    play_mode = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "DESIGN":
                next_state = design_mode.handle_event(event)
                if next_state == "PLAY":
                    play_mode = PlayMode(design_mode.start_point, design_mode.goal_point, design_mode.obstacles)
                    state = "PLAY"
            elif state == "PLAY":
                next_state = play_mode.handle_event(event)
                if next_state == "DESIGN":
                    design_mode = DesignMode() # Reset and swap back to design
                    state = "DESIGN"

        if state == "DESIGN":
            design_mode.update()
            design_mode.draw(screen)
        elif state == "PLAY":
            play_mode.update()
            play_mode.draw(screen)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()