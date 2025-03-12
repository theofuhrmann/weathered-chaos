import math


class Node:
    """
    Represents a node in a pendulum system.
    """

    def __init__(self) -> None:
        self.active: bool = False
        self.triggered: bool = False
        self.last_x: float = None


class Pendulum:
    """
    Represents a single pendulum in an N-pendulum system.
    """

    def __init__(
        self,
        length: float = 1.0,
        mass: float = 1.0,
        angle: float = math.pi / 2,
        angular_velocity: float = 0.0,
    ):
        self.length = length
        self.mass = mass
        self.angle = angle
        self.angular_velocity = angular_velocity
        self.node = Node()


class DoublePendulum:
    """
    Represents a double pendulum system.
    """

    def __init__(
        self,
        pendulums: list[Pendulum],
        g: float = 9.81,
        temperature: float = None,
    ):
        if len(pendulums) != 2:
            raise ValueError("DoublePendulum must have exactly 2 pendulums.")

        self.pendulums = pendulums
        self.g = g

        if temperature is not None:
            self.temperature_factor = self.calculate_temperature_factor(
                temperature
            )
        else:
            self.temperature_factor = 1.0

    def calculate_temperature_factor(
        self, temperature_celsius: float
    ) -> float:
        """
        Calculates the temperature factor based on the provided temperature in Celsius.
        Factor ranges from 0.5 (cold) to 2.0 (hot).
        """
        if temperature_celsius <= 0:
            return 0.5
        elif temperature_celsius >= 35:
            return 2.0
        else:
            # Linear interpolation between 0°C (0.5) and 35°C (2.0)
            return 0.5 + (temperature_celsius / 35) * 1.5

    def step(self, dt) -> None:
        """
        Computes one simulation step for a double pendulum using Euler integration.
        """
        p1: Pendulum = self.pendulums[0]
        p2: Pendulum = self.pendulums[1]
        m1, m2 = p1.mass, p2.mass
        L1, L2 = p1.length, p2.length
        a1, a2 = p1.angle, p2.angle
        w1, w2 = p1.angular_velocity, p2.angular_velocity
        g = self.g

        # Precompute common terms
        delta = a1 - a2
        sin_delta = math.sin(delta)
        cos_delta = math.cos(delta)
        cos2delta = math.cos(2 * delta)
        common_mass = 2 * m1 + m2

        # Denominators
        denom1 = L1 * (common_mass - m2 * cos2delta)
        denom2 = L2 * (common_mass - m2 * cos2delta)

        # Angular accelerations
        d_w1 = (
            -g * common_mass * math.sin(a1)
            - m2 * g * math.sin(a1 - 2 * a2)
            - 2 * sin_delta * m2 * (w2**2 * L2 + w1**2 * L1 * cos_delta)
        ) / denom1

        d_w2 = (
            2
            * sin_delta
            * (
                w1**2 * L1 * (m1 + m2)
                + g * (m1 + m2) * math.cos(a1)
                + w2**2 * L2 * m2 * cos_delta
            )
        ) / denom2

        # Apply temperature factor to the acceleration, not to the accumulated velocity
        # This prevents continuous acceleration over time
        d_w1 *= self.temperature_factor
        d_w2 *= self.temperature_factor

        # Euler integration
        p1.angular_velocity += d_w1 * dt
        p2.angular_velocity += d_w2 * dt

        p1.angle += p1.angular_velocity * dt
        p2.angle += p2.angular_velocity * dt


class PendulumSystem:
    """
    Represents a collection of double pendulum systems.
    """

    def __init__(self, double_pendulums: list[DoublePendulum] = None):
        self.double_pendulums = (
            double_pendulums if double_pendulums is not None else []
        )

    def add_system(self, double_pendulums: DoublePendulum) -> None:
        """Adds a new DoublePendulum to the collection."""
        self.double_pendulums.append(double_pendulums)

    def step(self, dt: float) -> None:
        """Advances each double pendulum system by dt."""
        for double_pendulum in self.double_pendulums:
            double_pendulum.step(dt)
