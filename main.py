import json
import math
import os
import random

import pygame
from dotenv import load_dotenv

from Pendulum import DoublePendulum, Pendulum, PendulumSystem
from PendulumSonifier import Key, Mode, PendulumSonifier, Scale
from PendulumVisualizer import PendulumSystemVisualizer
from WeatherAPI import WeatherAPI

load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
N_DOUBLE_PENDULUMS = 10


def get_key_scale_mode_from_weather(
    weather_condition: str,
) -> tuple[Key, Scale, Mode]:
    with open("weather_music_mapping.json") as f:
        weather_music_mapping = json.load(f)
        key = weather_music_mapping[weather_condition]["key"]
        scale = weather_music_mapping[weather_condition]["scale"]
        mode = weather_music_mapping[weather_condition]["mode"]

    return key, scale, mode


def initialize_pendulum_system(n: int, temperature: float) -> PendulumSystem:
    double_pendulums = []

    for _ in range(n):
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
        double_pendulum = DoublePendulum(
            [pendulum_1, pendulum_2], temperature=temperature
        )
        double_pendulums.append(double_pendulum)

    return PendulumSystem(double_pendulums)


if __name__ == "__main__":

    weather_api = WeatherAPI(api_key=WEATHER_API_KEY, location="Helsinki")
    weather_api.fetch_current_weather_data()

    pendulum_system = initialize_pendulum_system(
        N_DOUBLE_PENDULUMS, weather_api.temperature
    )

    visualizer = PendulumSystemVisualizer(pendulum_system)
    key, scale, mode = get_key_scale_mode_from_weather(
        weather_api.weather_condition
    )
    sonifier = PendulumSonifier(
        scale=scale, key=key, mode=mode, scale_factor=visualizer.scale
    )

    background_color = weather_api.get_background_color()
    running = True
    while running:
        visualizer.screen.fill(background_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        temperature_text = f"{weather_api.location}: {weather_api.weather_condition}, {weather_api.temperature}°C"
        music_text = (
            f"Playing: {sonifier.key} {sonifier.scale} {sonifier.mode}"
        )
        visualizer.render_text(temperature_text, (10, 10))
        visualizer.render_text(music_text, (10, visualizer.height - 30))

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
