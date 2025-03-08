from enum import Enum

import mido

from Pendulum import Pendulum, PendulumSystem


class ScaleType(Enum):
    MAJOR = "major"
    MINOR = "minor"


class Key(Enum):
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    A = "A"
    B = "B"


MIDI_PORT = "IAC Driver Bus 1"


class PendulumSonifier:
    """
    Sends MIDI notes to a DAW (e.g. Ableton) using the mido library.
    Each note's pitch is determined by a musical scale and key, and
    its velocity is modulated by the pendulum node’s angular velocity.
    A note is sent when a node crosses the vertical center line defined by origin[0].
    """

    # Predefined scales as semitone intervals:
    SCALES = {
        ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11, 12],
        ScaleType.MINOR: [0, 2, 3, 5, 7, 8, 10, 12],
    }
    # Predefined base MIDI note numbers for keys; here we use middle C=60 for key C.
    KEYS = {
        Key.C: 60,
        Key.D: 62,
        Key.E: 64,
        Key.F: 65,
        Key.G: 67,
        Key.A: 69,
        Key.B: 71,
    }

    def __init__(
        self,
        scale_type: ScaleType = ScaleType.MAJOR,
        key: Key = Key.C,
        scale_factor=200,
        midi_port_name: str = MIDI_PORT,
    ):
        """
        midi_port_name: specify a MIDI port name if desired;
                        if None, the default output port is opened.
        """
        self.scale_type = scale_type
        self.key = key
        self.scale_factor = scale_factor

        self.midi_out = mido.open_output(midi_port_name)

        self.prev_state = {}
        self.scale_intervals = self.SCALES[self.scale_type]
        self.base_note = self.KEYS[self.key]

    def update(self, system: PendulumSystem) -> None:
        """
        For each double pendulum in the system, if any pendulum's node is active,
        send a MIDI note. Node active state is expected to be updated by the visualizer.
        """
        for double_pendulum_idx, double_pendulum in enumerate(system):
            pendulums: list[Pendulum] = double_pendulum.pendulums
            for node_idx, pendulum in enumerate(pendulums):
                if pendulum.node.active:
                    note_idx = double_pendulum_idx % len(self.scale_intervals)
                    semitone_offset = self.scale_intervals[note_idx]
                    pitch = self.base_note + semitone_offset

                    ang_vel = abs(pendulum.angular_velocity)
                    velocity = min(127, max(30, int(ang_vel * 20)))

                    print(
                        f"Playing note: {pitch}, velocity: {velocity}, channel: {node_idx}"
                    )
                    self.play_note_on(node_idx, pitch, velocity)
                else:
                    prev_state = self.prev_state.get(
                        (double_pendulum, node_idx)
                    )
                    if prev_state:
                        self.play_note_off(node_idx, prev_state)
                        self.prev_state.pop((double_pendulum, node_idx))

    def play_note_on(self, channel: int, pitch: int, velocity: int) -> None:
        note_on = mido.Message(
            "note_on", channel=channel, note=pitch, velocity=velocity
        )
        self.midi_out.send(note_on)

    def play_note_off(self, channel: int, pitch: int) -> None:
        note_off = mido.Message("note_off", channel=channel, note=pitch)
        self.midi_out.send(note_off)
