import math
import random

from Config import Config

MAX_ANGULAR_VELOCITY = 10.0


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
        """
        Initializes a pendulum.

        Args:
            length: The length of the pendulum.
            mass: The mass of the pendulum.
            angle: The angle of the pendulum.
            angular_velocity: The angular velocity of the pendulum.
        """
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
        g: float = 9.81,
        temperature: float = None,
        mass_range: float = 0.0,
        length_range: float = 0.0,
        angle_range: tuple[float, float] = (-0.1, 0.1),
    ):
        """
        Initializes a double pendulum system.

        Args:
            g: The acceleration due to gravity.
            temperature: The temperature in Celsius.
            mass_range: The range of mass variation around 1.0.
            length_range: The range of length variation around 1.0.
            angle_range: The range of angle variation.
        """
        self.pendulums = [
            Pendulum(
                mass=random.uniform(1 - mass_range, 1 + mass_range),
                length=random.uniform(1 - length_range, 1 + length_range),
                angle=math.pi / 2 + random.uniform(*angle_range),
            ),
            Pendulum(
                mass=random.uniform(1 - mass_range, 1 + mass_range),
                length=random.uniform(1 - length_range, 1 + length_range),
                angle=math.pi / 2 + random.uniform(*angle_range),
            ),
        ]
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
        Factor ranges from 0.25 (cold) to 2.0 (hot).
        """
        if Config.moon_mode:
            return 1.0

        min_temperature_factor = 0.25
        max_temperature_factor = 2.0
        min_temperature = 0
        max_temperature = 35

        if temperature_celsius <= min_temperature:
            return min_temperature_factor
        elif temperature_celsius >= max_temperature:
            return max_temperature_factor
        else:
            # Linear interpolation between 0°C (0.25) and 35°C (2.0)
            return min_temperature_factor + (
                temperature_celsius / max_temperature
            ) * (max_temperature_factor - min_temperature_factor)

    def step(self, dt) -> None:
        """
        Computes one simulation step for a double pendulum using Euler integration.
        """
        DAMPING_FACTOR = 0.90  # Reduce angular velocity by 10% on a full spin

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

        # Clamp angular velocity to prevent excessive spinning
        p1.angular_velocity = max(
            -MAX_ANGULAR_VELOCITY,
            min(p1.angular_velocity, MAX_ANGULAR_VELOCITY),
        )
        p2.angular_velocity = max(
            -MAX_ANGULAR_VELOCITY,
            min(p2.angular_velocity, MAX_ANGULAR_VELOCITY),
        )

        p1.angle += p1.angular_velocity * dt
        p2.angle += p2.angular_velocity * dt

        # Detect full spins for the first pendulum
        if abs(p1.angle) >= 2 * math.pi:
            # Reduce angular velocity by the damping factor
            p1.angular_velocity *= DAMPING_FACTOR

            # Normalize the angle to keep it within [-2π, 2π]
            p1.angle %= 2 * math.pi


class PendulumSystem:
    """
    Represents a collection of double pendulums.
    """

    def __init__(
        self,
        n: int = 1,
        g: float = 9.81,
        temperature: float = None,
        mass_range: float = 0.0,
        length_range: float = 0.0,
        angle_range: tuple[float, float] = (-0.1, 0.1),
    ):
        """
        Initializes a collection of double pendulums.

        Args:
            n: The number of double pendulums.
            g: The acceleration due to gravity.
            temperature: The temperature in Celsius.
            mass_range: The range of mass variation around 1.0.
            length_range: The range of length variation around 1.0.
            angle_range: The range of angle variation.
        """
        self.double_pendulums = [
            DoublePendulum(
                g=g,
                temperature=temperature,
                mass_range=mass_range,
                length_range=length_range,
                angle_range=angle_range,
            )
            for _ in range(n)
        ]
        self.g = g
        self.temperature = temperature
        self.mass_range = mass_range
        self.length_range = length_range
        self.angle_range = angle_range

    def step(self, dt: float) -> None:
        """
        Advances each double pendulum system by dt.
        """
        for double_pendulum in self.double_pendulums:
            double_pendulum.step(dt)

    def update_gravity(self, g: float) -> None:
        """
        Updates the gravity value for all of the double pendulums in the system
        and scales angular velocity to prevent excessive spinning when gravity
        changes.
        """
        # Scale factor for angular velocity
        gravity_ratio = math.sqrt(g / self.g)

        for double_pendulum in self.double_pendulums:
            double_pendulum.g = g
            for pendulum in double_pendulum.pendulums:
                # Scale angular velocity
                pendulum.angular_velocity *= gravity_ratio

        self.g = g

    def update_number_of_pendulums(self, n: int) -> None:
        """
        Updates the number of double pendulum systems.
        """
        if n < len(self.double_pendulums):
            self.double_pendulums = self.double_pendulums[:n]
        elif n > len(self.double_pendulums):
            missing_pendulums = n - len(self.double_pendulums)
            for _ in range(missing_pendulums):
                double_pendulum = DoublePendulum(
                    g=self.g,
                    temperature=self.temperature,
                    mass_range=self.mass_range,
                    length_range=self.length_range,
                    angle_range=self.angle_range,
                )
                self.double_pendulums.append(double_pendulum)

    def update_mass_range(self, mass_range: float) -> None:
        """
        Updates the mass range for all of the double pendulums in the system.
        """
        for double_pendulum in self.double_pendulums:
            for pendulum in double_pendulum.pendulums:
                pendulum.mass = random.uniform(1 - mass_range, 1 + mass_range)

        self.mass_range = mass_range

    def update_length_range(self, length_range: float) -> None:
        """
        Updates the length range for all of the double pendulums in the system.
        """
        for double_pendulum in self.double_pendulums:
            for pendulum in double_pendulum.pendulums:
                pendulum.length = random.uniform(
                    1 - length_range, 1 + length_range
                )

        self.length_range = length_range

    def update_temperature_factor(self, temperature: float) -> None:
        """
        Updates the temperature_factor of the double pendulums and scales angular velocity.
        """

        for double_pendulum in self.double_pendulums:
            # Calculate the new temperature factor
            new_temperature_factor = (
                double_pendulum.calculate_temperature_factor(temperature)
            )

            # Scale angular velocity based on the ratio of the new and old temperature factors
            factor_ratio = (
                new_temperature_factor / double_pendulum.temperature_factor
            )
            for pendulum in double_pendulum.pendulums:
                pendulum.angular_velocity *= factor_ratio

                # Clamp the angular velocity to prevent excessive spinning
                pendulum.angular_velocity = max(
                    -MAX_ANGULAR_VELOCITY,
                    min(pendulum.angular_velocity, MAX_ANGULAR_VELOCITY),
                )

            # Update the temperature factor
            double_pendulum.temperature_factor = new_temperature_factor
