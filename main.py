import os
import threading

import pygame
from dotenv import load_dotenv

from Config import Config
from PendulumSystem import PendulumSystem
from RAVESonifier import RAVESonifier
from Sonifier import PendulumSonifier
from Visualizer import PendulumSystemVisualizer
from WeatherAPI import WeatherAPI

load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


if __name__ == "__main__":
    # Fetch weather data
    weather_api = WeatherAPI(api_key=WEATHER_API_KEY, location=Config.location)
    weather_api.fetch_current_weather_data()

    # Initialize pendulum system, visualizer, and sonifiers
    pendulum_system = PendulumSystem(
        Config.num_double_pendulums,
        temperature=Config.temperature,
        g=(1.62 if Config.moon_mode else 9.81),
        mass_range=Config.mass_range,
        length_range=Config.length_range,
    )

    visualizer = PendulumSystemVisualizer(pendulum_system, size=(800, 800))

    sonifier = PendulumSonifier(
        scale_factor=visualizer.scale,
    )

    rave_sonifier = RAVESonifier(
        pendulum_system=pendulum_system,
        sample_rate=48000,
        buffer_size=512,
        scaling_factor=(visualizer.height + 50) / 2,
    )

    # Start audio thread
    audio_thread = threading.Thread(target=rave_sonifier.stream_audio)
    audio_thread.start()

    # Update visualizer texts
    visualizer.update_music_text()
    visualizer.update_location_weather_text()
    visualizer.update_gravity_text()

    running = True
    while running:
        time_delta = visualizer.clock.tick(60) / 1000.0
        visualizer.fill_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            visualizer.handle_event(event)

        pendulum_system.step(0.01)

        visualizer.update(pendulum_system, time_delta)
        sonifier.update(pendulum_system.double_pendulums)

        visualizer.draw(pendulum_system)

        pygame.display.flip()
        visualizer.clock.tick(60)

    rave_sonifier.stop_audio()
    audio_thread.join()

    pygame.quit()
