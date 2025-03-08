import math
import random

import pygame

from Pendulum import DoublePendulum, Pendulum, PendulumSystem
from PendulumSonifier import Key, PendulumSonifier, ScaleType
from PendulumVisualizer import PendulumSystemVisualizer

N_DOUBLE_PENDULUMS = 10

if __name__ == "__main__":
    double_pendulums = []

    for _ in range(N_DOUBLE_PENDULUMS):
        pendulum_1 = Pendulum(
            mass=1,
            length=1,
            angle=math.pi / 2 + random.uniform(-0.1, 0.1),
            angular_velocity=0,
        )
        pendulum_2 = Pendulum(
            mass=1,
            length=1,
            angle=math.pi / 2 + random.uniform(-0.1, 0.1),
            angular_velocity=0,
        )
        pendulums = []
        double_pendulum = DoublePendulum([pendulum_1, pendulum_2])
        double_pendulums.append(double_pendulum)

    pendulum_system = PendulumSystem(double_pendulums)
    visualizer = PendulumSystemVisualizer(pendulum_system)
    sonifier = PendulumSonifier(
        scale_type=ScaleType.MAJOR, key=Key.C, scale_factor=visualizer.scale
    )

    running = True
    while running:
        visualizer.screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pendulum_system.step(0.01)
        """
        for color, double_pendulum in zip(
            visualizer.colors, pendulum_system.double_pendulums
        ):
            visualizer._draw_double_pendulum(double_pendulum, color)
            visualizer._update_node_states(double_pendulum)
        """
        visualizer.draw(pendulum_system)
        visualizer.update(pendulum_system)
        sonifier.update(pendulum_system.double_pendulums)

        pygame.display.flip()
        visualizer.clock.tick(60)
    pygame.quit()
