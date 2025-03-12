import math
import random

import pygame

from Pendulum import DoublePendulum, Node, Pendulum, PendulumSystem


class PendulumSystemVisualizer:
    """
    Uses Pygame to visualize a collection of double pendulum systems.
    """

    def __init__(
        self,
        pendulum_system: PendulumSystem,
        screen_size=(800, 800),
        scale=200,
    ):
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Multi-Pendulum Simulation")
        pygame.font.init()
        self.font = pygame.font.SysFont("Courier New", 20)

        self.pendulum_system = pendulum_system
        self.num_pendulums = len(pendulum_system.double_pendulums)
        self.width, self.height = screen_size
        self.scale = scale
        self.origin = (self.width // 2, self.height // 3)
        self.colors = [self._random_color() for _ in range(self.num_pendulums)]
        self.clock = pygame.time.Clock()
        self.node_threshold = 5

    def _random_color(self):
        """Generates a random RGB color for each pendulum system."""
        return (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )

    def _convert_to_screen_coords(self, pendulum: DoublePendulum):
        """
        Converts a single double pendulum's angles to screen coordinates.
        """
        coords = [self.origin]
        x, y = self.origin
        for p in pendulum.pendulums:
            x += p.length * self.scale * math.sin(p.angle)
            y += p.length * self.scale * math.cos(p.angle)
            coords.append((x, y))
        return coords

    def _update_node_states(self, double_pendulum: DoublePendulum):
        """
        Updates the state of each node in the double pendulum.
        """
        origin_x, _ = self.origin
        coords = self._convert_to_screen_coords(double_pendulum)
        # Skip the fixed origin (index 0)
        for idx, (x, _) in enumerate(coords[1:]):
            p: Pendulum = double_pendulum.pendulums[idx]
            node: Node = p.node

            if node.last_x is not None:
                previous_side = node.last_x < origin_x
                current_side = x < origin_x

                if previous_side != current_side:
                    if not node.triggered:
                        node.active = True
                        node.triggered = True
                else:
                    node.active = False

                # Reset lock if the node moves sufficiently away from the origin.
                if abs(x - origin_x) > self.node_threshold * 2:
                    node.triggered = False

            node.last_x = x

    def _draw_double_pendulum(self, double_pendulum: DoublePendulum, color):
        """
        Draws a double pendulum.
        """
        coords = self._convert_to_screen_coords(double_pendulum)
        for start, end in zip(coords, coords[1:]):
            pygame.draw.line(self.screen, color, start, end, 3)
            pygame.draw.circle(
                self.screen, color, (int(end[0]), int(end[1])), 8
            )

    def draw(self, pendulum_system: PendulumSystem):
        """
        Draws all double pendulums in the system.
        """
        for color, double_pendulum in zip(
            self.colors, pendulum_system.double_pendulums
        ):
            self._draw_double_pendulum(double_pendulum, color)

    def render_text(self, text, position, color=(255, 255, 255)):
        """Render text on the screen at the given position."""
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def update(self, pendulum_system: PendulumSystem):
        """
        Updates node information for each double pendulum in the system.
        """
        for double_pendulum in pendulum_system.double_pendulums:
            self._update_node_states(double_pendulum)
