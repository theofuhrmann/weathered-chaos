import math
import random

import pygame

from Config import Config
from EventManager import Event, EventType, event_manager
from PendulumSystem import DoublePendulum, Node, Pendulum, PendulumSystem
from Sidebar import Sidebar


class PendulumSystemVisualizer:
    """
    Uses Pygame to visualize a collection of double pendulum systems.
    """

    def __init__(
        self,
        pendulum_system: PendulumSystem,
        size=(800, 800),
        scale=150,
    ):
        pygame.init()
        self.sidebar_width = 250
        self.size = size[0] + self.sidebar_width, size[1]
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Weathered Chaos")
        pygame.font.init()
        self.font = pygame.font.SysFont("Courier New", 20)

        self.pendulum_system = pendulum_system
        self.num_pendulums = len(pendulum_system.double_pendulums)
        self.width, self.height = self.size
        self.scale = scale
        self.sidebar = Sidebar(0, 0, self.sidebar_width, self.height)
        self.origin = (
            (self.width + self.sidebar_width) // 2,
            self.height // 3,
        )
        self.pendulum_colors = [
            self._random_color() for _ in range(self.num_pendulums)
        ]
        self.background_color = self.get_background_color()
        self.clock = pygame.time.Clock()
        self.node_threshold = 5

        self._register_event_handlers()

    def _register_event_handlers(self):
        """Register all event handlers for this class"""
        event_manager.subscribe(
            EventType.LOCATION_CHANGED, self._on_location_changed
        )
        event_manager.subscribe(
            EventType.WEATHER_UPDATED, self._on_weather_updated
        )
        event_manager.subscribe(
            EventType.MOON_MODE_CHANGED, self._on_moon_mode_changed
        )
        event_manager.subscribe(
            EventType.PENDULUM_COUNT_CHANGED, self._on_pendulum_count_changed
        )
        event_manager.subscribe(
            EventType.MASS_RANGE_CHANGED, self._on_mass_range_changed
        )
        event_manager.subscribe(
            EventType.LENGTH_RANGE_CHANGED, self._on_length_range_changed
        )
        event_manager.subscribe(
            EventType.MUSIC_SETTINGS_CHANGED, self._on_music_settings_changed
        )

    def _on_location_changed(self, event: Event):
        """Handle the LOCATION_CHANGED event"""
        self.update_location_weather_text()

    def _on_weather_updated(self, event: Event):
        """Handle weather update events"""
        self.update_location_weather_text()
        self.background_color = self.get_background_color()

    def _on_moon_mode_changed(self, event: Event):
        """Handle moon mode change events"""
        moon_mode = event.data
        new_gravity = 1.62 if moon_mode else 9.81
        self.pendulum_system.update_gravity(new_gravity)
        self.background_color = self.get_background_color()
        self.update_gravity_text()
        self.update_location_weather_text()

    def _on_pendulum_count_changed(self, event: Event):
        """Handle pendulum count change events"""
        current_n_pendulums = event.data
        self.pendulum_system.update_number_of_pendulums(current_n_pendulums)
        self.num_pendulums = current_n_pendulums
        if current_n_pendulums > len(self.pendulum_colors):
            self.pendulum_colors += [
                self._random_color()
                for _ in range(current_n_pendulums - len(self.pendulum_colors))
            ]

    def _on_mass_range_changed(self, event: Event):
        """Handle mass range change events"""
        self.pendulum_system.update_mass_range(event.data)

    def _on_length_range_changed(self, event: Event):
        """Handle length range change events"""
        self.pendulum_system.update_length_range(event.data)

    def _on_music_settings_changed(self, event: Event):
        """Handle music settings change events"""
        self.update_music_text()

    def process_pygame_events(self, events):
        """Process all pygame events and publish them to the event system"""
        for event in events:
            if event.type == pygame.QUIT:
                return False

            # Publish the pygame event for other components to handle
            event_manager.publish(Event(EventType.PYGAME_EVENT, event))

        return True

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
        for i, (start, end) in enumerate(zip(coords, coords[1:])):
            pygame.draw.line(self.screen, color, start, end, 3)
            pendulum = double_pendulum.pendulums[i]
            pygame.draw.circle(
                self.screen,
                color,
                (int(end[0]), int(end[1])),
                self.scale / 25 * pendulum.mass,
            )

    def update_location_weather_text(self):
        if Config.moon_mode:
            self.location_weather_text = "Moon"
        else:
            self.location_weather_text = f"{Config.location}: {Config.weather_condition}, {Config.temperature}°C"

    def update_gravity_text(self):
        self.gravity_text = (
            f"Gravity: {1.62 if Config.moon_mode else 9.81} m/s²"
        )

    def update_music_text(self):
        """
        Updates the music text to display the current key, scale, and mode.
        Converts keys ending in _SHARP or _FLAT to their respective symbols (# or b).
        """
        key = Config.key
        if key.endswith("_SHARP"):
            key = key.replace("_SHARP", "#")
        elif key.endswith("_FLAT"):
            key = key.replace("_FLAT", "b")

        self.music_text = f"Playing: {key} {Config.scale.capitalize()} {Config.mode.capitalize()}"

    def render_text(self, text, position, color=(255, 255, 255)):
        """Render text on the screen at the given position."""
        text_surface = self.font.render(text, False, color)
        self.screen.blit(text_surface, position)

    def draw_texts(self):
        self.render_text(
            self.location_weather_text, (self.sidebar_width + 10, 10)
        )
        self.render_text(
            self.music_text,
            (self.sidebar_width + 10, self.height - 30),
        )
        self.render_text(
            self.gravity_text, (self.width - 230, self.height - 30)
        )

    def draw(self, pendulum_system: PendulumSystem):
        """
        Draws all double pendulums in the system.
        """
        for color, double_pendulum in zip(
            self.pendulum_colors, pendulum_system.double_pendulums
        ):
            self._draw_double_pendulum(double_pendulum, color)

        self.sidebar.draw(self.screen, self.background_color)
        self.draw_texts()

    def update(self, pendulum_system: PendulumSystem, time_delta: float):
        """
        Updates node information for each double pendulum in the system and
        updates the sidebar.
        """
        for double_pendulum in pendulum_system.double_pendulums:
            self._update_node_states(double_pendulum)

        self.sidebar.update(time_delta)

    def fill_background(self):
        self.screen.fill(self.background_color)

    def get_background_color(self) -> tuple:
        """
        Map temperature to background color.
        """
        if Config.moon_mode:
            return (0, 0, 0)

        if Config.temperature <= 0:
            return (0, 0, 180)  # Cold blue
        elif 0 < Config.temperature <= 10:
            return (0, 0, 255 - int(Config.temperature * 5))  # Blue to cyan
        elif 10 < Config.temperature <= 20:
            return (
                0,
                int((Config.temperature - 10) * 20),
                200 - int((Config.temperature - 10) * 20),
            )  # Cyan to green
        elif 20 < Config.temperature <= 30:
            return (
                int((Config.temperature - 20) * 20),
                200 - int((Config.temperature - 20) * 10),
                0,
            )  # Green to yellow/orange
        else:
            return (
                200 + min(55, int((Config.temperature - 30) * 5)),
                50,
                0,
            )  # Orange to red

    def handle_event(self, event):
        self.sidebar.process_event(event)
