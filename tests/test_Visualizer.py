import math
from unittest.mock import Mock, patch

import pygame
import pytest

from EventManager import Event, EventType
from PendulumSystem import DoublePendulum, Node, Pendulum, PendulumSystem
from Visualizer import PendulumSystemVisualizer


@pytest.fixture
def visualizer():
    with patch("pygame.init"), patch("pygame.display.set_mode"), patch(
        "pygame.font.init"
    ), patch("pygame.font.SysFont"), patch(
        "Visualizer.Sidebar"
    ) as mock_sidebar:
        mock_pendulum_system = Mock(spec=PendulumSystem)
        mock_pendulum_system.double_pendulums = [
            Mock(spec=DoublePendulum) for _ in range(2)
        ]
        sidebar_instance = Mock()
        mock_sidebar.return_value = sidebar_instance
        return PendulumSystemVisualizer(mock_pendulum_system, (800, 800), 150)


class TestVisualizerInitialization:
    def test_initialization(self, visualizer):
        assert visualizer.num_pendulums == 2
        assert visualizer.sidebar_width == 250
        assert visualizer.size == (800 + 250, 800)
        assert visualizer.scale == 150
        assert visualizer.node_threshold == 5
        assert len(visualizer.pendulum_colors) == 2


class TestEventHandling:
    def test_event_handlers_registration(self, visualizer):
        test_event_manager = Mock()
        with patch("Visualizer.event_manager", test_event_manager):
            visualizer._register_event_handlers()
        assert test_event_manager.subscribe.call_count == 6
        subscribed_events = [
            call[0][0] for call in test_event_manager.subscribe.call_args_list
        ]
        expected_events = [
            EventType.WEATHER_UPDATED,
            EventType.MOON_MODE_CHANGED,
            EventType.PENDULUM_COUNT_CHANGED,
            EventType.MASS_RANGE_CHANGED,
            EventType.LENGTH_RANGE_CHANGED,
            EventType.MUSIC_SETTINGS_CHANGED,
        ]
        assert all(event in subscribed_events for event in expected_events)

    def test_weather_updated_event_handler(self, visualizer):
        visualizer.update_location_weather_text = Mock()
        visualizer.get_background_color = Mock(return_value=(0, 0, 0))
        visualizer.pendulum_system.update_temperature_factor = Mock()
        event = Event(EventType.WEATHER_UPDATED, {"temperature": 25})
        visualizer._on_weather_updated(event)
        visualizer.update_location_weather_text.assert_called_once()
        visualizer.get_background_color.assert_called_once()
        visualizer.pendulum_system.update_temperature_factor.assert_called_once_with(
            25
        )

    def test_moon_mode_changed_event_handler(self, visualizer):
        visualizer.update_gravity_text = Mock()
        visualizer.update_location_weather_text = Mock()
        visualizer.pendulum_system.update_gravity = Mock()
        visualizer.get_background_color = Mock(return_value=(0, 0, 0))
        event = Event(EventType.MOON_MODE_CHANGED, True)
        visualizer._on_moon_mode_changed(event)
        visualizer.pendulum_system.update_gravity.assert_called_once_with(1.62)

    def test_process_pygame_events(self, visualizer):
        with patch("Visualizer.event_manager") as mock_event_manager:
            event1 = Mock(type=pygame.MOUSEMOTION)
            event2 = Mock(type=pygame.KEYDOWN)
            quit_event = Mock(type=pygame.QUIT)
            assert visualizer.process_pygame_events([event1, event2]) is True
            assert mock_event_manager.publish.call_count == 2
            assert visualizer.process_pygame_events([quit_event]) is False


class TestRendering:
    def test_convert_to_screen_coords(self, visualizer):
        mock_dp = Mock(spec=DoublePendulum)
        p1 = Mock(spec=Pendulum, angle=math.pi / 4, length=1.0)
        p2 = Mock(spec=Pendulum, angle=math.pi / 2, length=1.0)
        mock_dp.pendulums = [p1, p2]
        visualizer.origin = (400, 300)
        visualizer.scale = 100
        coords = visualizer._convert_to_screen_coords(mock_dp)
        assert coords[0] == (400, 300)
        assert math.isclose(
            coords[1][0], 400 + 100 * math.sin(math.pi / 4), abs_tol=1
        )
        assert math.isclose(
            coords[2][0], coords[1][0] + 100 * math.sin(math.pi / 2), abs_tol=1
        )

    def test_draw_double_pendulum(self, visualizer):
        with patch("pygame.draw.line") as mock_line, patch(
            "pygame.draw.circle"
        ) as mock_circle:
            mock_dp = Mock(spec=DoublePendulum)
            p1, p2 = Mock(spec=Pendulum, mass=2.0), Mock(
                spec=Pendulum, mass=1.0
            )
            mock_dp.pendulums = [p1, p2]
            visualizer._convert_to_screen_coords = Mock(
                return_value=[(400, 300), (450, 350), (500, 400)]
            )
            visualizer._draw_double_pendulum(mock_dp, (255, 0, 0))
            assert mock_line.call_count == 2
            assert mock_circle.call_count == 2
            assert mock_circle.call_args_list[0][0][2] == (450, 350)

    def test_get_background_color(self, visualizer):
        with patch("Visualizer.Config") as mock_config:
            mock_config.moon_mode = True
            assert visualizer.get_background_color() == (0, 0, 0)
            mock_config.moon_mode = False
            mock_config.temperature = -10
            assert visualizer.get_background_color() == (0, 0, 180)


class TestNodeStates:
    @pytest.fixture
    def setup(self):
        pygame.init()

        node1 = Node()
        node2 = Node()

        pendulum1 = Mock(spec=Pendulum)
        pendulum1.node = node1
        pendulum1.length = 1.0
        pendulum1.angle = 0.0

        pendulum2 = Mock(spec=Pendulum)
        pendulum2.node = node2
        pendulum2.length = 1.0
        pendulum2.angle = 0.0

        double_pendulum = Mock(spec=DoublePendulum)
        double_pendulum.pendulums = [pendulum1, pendulum2]

        pendulum_system = Mock(spec=PendulumSystem)
        pendulum_system.double_pendulums = [double_pendulum]

        screen_size = (800, 800)
        visualizer = PendulumSystemVisualizer(
            pendulum_system=pendulum_system, size=screen_size, scale=200
        )

        origin_x = screen_size[0] // 2 + visualizer.sidebar_width

        yield {
            "visualizer": visualizer,
            "origin_x": origin_x,
            "screen_size": screen_size,
            "node1": node1,
            "node2": node2,
            "pendulum1": pendulum1,
            "pendulum2": pendulum2,
            "double_pendulum": double_pendulum,
        }

        pygame.quit()

    def test_node_activation_on_origin_crossing(self, setup):
        """Test that a node becomes active and triggered only once when crossing the origin."""
        visualizer = setup["visualizer"]
        origin_x = setup["origin_x"]
        screen_size = setup["screen_size"]
        node1 = setup["node1"]
        node2 = setup["node2"]
        double_pendulum = setup["double_pendulum"]

        # Mock the _convert_to_screen_coords method to return controlled coordinates
        # We'll simulate a pendulum crossing the origin from right to left

        # First position: to the right of origin
        right_coords = [
            (origin_x, screen_size[1] // 3),  # Origin
            (origin_x + 10, 400),  # First pendulum
            (origin_x + 20, 500),
        ]  # Second pendulum

        # Second position: to the left of origin (crossed)
        left_coords = [
            (origin_x, screen_size[1] // 3),
            (origin_x - 4, 400),
            (origin_x - 8, 500),
        ]

        # Third position: still on the left (no new crossing)
        left_coords2 = [
            (origin_x, screen_size[1] // 3),
            (origin_x - 5, 400),
            (origin_x - 10, 500),
        ]

        # Fourth position: far left (to reset triggered state)
        far_left_coords = [
            (origin_x, screen_size[1] // 3),
            (origin_x - 50, 400),
            (origin_x - 60, 500),
        ]

        # Fifth position: back to right (another crossing)
        right_coords2 = [
            (origin_x, screen_size[1] // 3),
            (origin_x + 10, 400),
            (origin_x + 20, 500),
        ]

        # Setting up initial state (nodes should have last_x=None)
        assert node1.last_x is None
        assert node2.last_x is None

        # Test sequence of movements:
        # 1. First update - initializes last_x but no crossing yet
        with patch.object(
            visualizer, "_convert_to_screen_coords", return_value=right_coords
        ):
            visualizer._update_node_states(double_pendulum)

        assert node1.last_x == right_coords[1][0]
        assert node2.last_x == right_coords[2][0]
        assert not node1.active
        assert not node2.active
        assert not node1.triggered
        assert not node2.triggered

        # 2. Cross the origin from right to left - should activate and trigger nodes
        with patch.object(
            visualizer, "_convert_to_screen_coords", return_value=left_coords
        ):
            visualizer._update_node_states(double_pendulum)

        assert node1.last_x == left_coords[1][0]
        assert node2.last_x == left_coords[2][0]
        assert node1.active
        assert node2.active
        assert abs(node1.last_x - origin_x) <= visualizer.node_threshold * 2
        assert abs(node2.last_x - origin_x) <= visualizer.node_threshold * 2
        assert node2.last_x < origin_x
        assert node1.triggered
        assert node2.triggered

        # 3. Continue moving left (no new crossing) - should deactivate and remain triggered
        with patch.object(
            visualizer, "_convert_to_screen_coords", return_value=left_coords2
        ):
            visualizer._update_node_states(double_pendulum)

        assert node1.last_x == left_coords2[1][0]
        assert node2.last_x == left_coords2[2][0]
        assert not node1.active
        assert not node2.active
        assert node1.triggered
        assert node2.triggered

        # 4. Move far left (beyond threshold) - should reset triggered state
        with patch.object(
            visualizer,
            "_convert_to_screen_coords",
            return_value=far_left_coords,
        ):
            visualizer._update_node_states(double_pendulum)

        assert node1.last_x == far_left_coords[1][0]
        assert node2.last_x == far_left_coords[2][0]
        assert not node1.active
        assert not node2.active
        assert not node1.triggered
        assert not node2.triggered

        # 5. Cross back to the right - should activate but only trigger the first node
        with patch.object(
            visualizer, "_convert_to_screen_coords", return_value=right_coords2
        ):
            visualizer._update_node_states(double_pendulum)

        assert node1.last_x == right_coords2[1][0]
        assert node2.last_x == right_coords2[2][0]
        assert node1.active
        assert node2.active
        assert node1.triggered
        assert not node2.triggered
