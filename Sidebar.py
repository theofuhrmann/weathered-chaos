import pygame
import pygame_gui

from Config import Config
from EventManager import Event, EventType, event_manager


class Sidebar:
    """
    Contains UI elements for configuring the simulation. Allows users to adjust
    the number of double pendulums, pendulum length range, mass range, and
    weather location.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initializes the sidebar with the given position, width, and height.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            width: The width of the sidebar.
            height: The height of the sidebar.
        """
        self.width = width
        self.height = height
        self.manager = pygame_gui.UIManager((self.width, self.height))
        self.manager.ui_theme.load_theme(
            {
                "button": {
                    "font": {
                        "name": "Courier New",
                        "size": 16,
                    }
                },
                "text_entry_line": {
                    "font": {
                        "name": "Courier New",
                        "size": 16,
                    }
                },
            }
        )
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.font = pygame.font.SysFont("Courier New", 16)

        self.moon_checkbox = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 20), (self.width - 40, 30)),
            text="Moon Mode: OFF",
            manager=self.manager,
        )

        self.location_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 70), (self.width - 40, 30)),
            initial_text=Config.location,
            manager=self.manager,
        )

        self.n_double_pendulums = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((20, 120), (self.width - 40, 30)),
            start_value=Config.num_double_pendulums,
            value_range=(1, 50),
            manager=self.manager,
        )

        self.length_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((20, 170), (self.width - 40, 30)),
            start_value=Config.length_range,
            click_increment=0.05,
            value_range=(0, 0.5),
            manager=self.manager,
        )

        self.mass_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((20, 220), (self.width - 40, 30)),
            start_value=Config.mass_range,
            click_increment=0.05,
            value_range=(0, 0.5),
            manager=self.manager,
        )

    def process_event(self, event: pygame.event.Event):
        """
        Processes the given event. Update the config settings based on the
        user's input.
        """
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.moon_checkbox:
                self.moon_checkbox.set_text(
                    f"Moon Mode: {'OFF' if self.moon_mode else 'ON'}"
                )

                Config.moon_mode = self.moon_mode
                event_manager.publish(
                    Event(EventType.MOON_MODE_CHANGED, Config.moon_mode)
                )

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.mass_slider:
                if self.mass_range != Config.mass_range:
                    Config.mass_range = self.mass_range
                    event_manager.publish(
                        Event(EventType.MASS_RANGE_CHANGED, Config.mass_range)
                    )
            elif event.ui_element == self.length_slider:
                if self.length_range != Config.length_range:
                    Config.length_range = self.length_range
                    event_manager.publish(
                        Event(
                            EventType.LENGTH_RANGE_CHANGED, Config.length_range
                        )
                    )
            elif event.ui_element == self.n_double_pendulums:
                if self.num_double_pendulums != Config.num_double_pendulums:
                    Config.num_double_pendulums = self.num_double_pendulums
                    event_manager.publish(
                        Event(
                            EventType.PENDULUM_COUNT_CHANGED,
                            Config.num_double_pendulums,
                        )
                    )

        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.location_entry:
                Config.location = self.location
                event_manager.publish(
                    Event(EventType.LOCATION_CHANGED, Config.location)
                )

    def update(self, time_delta: float):
        """
        Updates the UI manager.
        """
        self.manager.update(time_delta)

    def draw(self, surface: pygame.Surface, color: tuple[int, int, int]):
        """
        Draws the sidebar on the given surface.
        """
        pygame.draw.rect(
            surface,
            tuple([min(255, c + 50) for c in color]),
            pygame.Rect(0, 0, self.width, self.height),
        )
        self.manager.draw_ui(surface)
        self.render_slider_values(surface)

    def render_slider_values(self, surface: pygame.Surface) -> None:
        """
        Renders the current values of the sliders on the given surface.
        """
        location_text = "Location:"
        num_pendulums_text = f"Double Pendulums: {self.num_double_pendulums}"
        length_text = f"Length Range: {self.length_range:.2f}"
        mass_text = f"Mass Range: {self.mass_range:.2f}"

        location_surface = self.font.render(
            location_text, False, (255, 255, 255)
        )
        num_pendulums_surface = self.font.render(
            num_pendulums_text, False, (255, 255, 255)
        )
        length_surface = self.font.render(length_text, False, (255, 255, 255))
        mass_surface = self.font.render(mass_text, False, (255, 255, 255))

        surface.blit(location_surface, (20, 50))
        surface.blit(num_pendulums_surface, (20, 100))
        surface.blit(length_surface, (20, 150))
        surface.blit(mass_surface, (20, 200))

    @property
    def moon_mode(self) -> bool:
        return "ON" in self.moon_checkbox.text

    @property
    def mass_range(self) -> float:
        return self.mass_slider.get_current_value()

    @property
    def length_range(self) -> float:
        return self.length_slider.get_current_value()

    @property
    def location(self) -> str:
        return self.location_entry.get_text()

    @property
    def num_double_pendulums(self) -> int:
        return int(self.n_double_pendulums.get_current_value())
