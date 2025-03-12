from unittest.mock import Mock, patch

import pygame
import pytest

from Pendulum import DoublePendulum, Node, Pendulum, PendulumSystem
from PendulumVisualizer import PendulumSystemVisualizer


class TestUpdateNodeStates:
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
            pendulum_system=pendulum_system, screen_size=screen_size, scale=200
        )

        origin_x = screen_size[0] // 2

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
