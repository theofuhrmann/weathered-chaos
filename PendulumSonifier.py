from enum import Enum

import mido

from Pendulum import Pendulum, PendulumSystem


class Scale(Enum):
    MAJOR = "major"
    MINOR = "minor"


class Mode(Enum):
    IONIAN = "Ionian"
    DORIAN = "Dorian"
    PHRYGIAN = "Phrygian"
    LYDIAN = "Lydian"
    MIXOLYDIAN = "Mixolydian"
    AEOLIAN = "Aeolian"
    LOCRIAN = "Locrian"


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

    INTERVALS = {
        # Major scale modes (derived from C major)
        (Scale.MAJOR, Mode.IONIAN): [
            0,
            2,
            4,
            5,
            7,
            9,
            11,
            12,
        ],
        (Scale.MAJOR, Mode.DORIAN): [0, 2, 3, 5, 7, 9, 10, 12],
        (Scale.MAJOR, Mode.PHRYGIAN): [0, 1, 3, 5, 7, 8, 10, 12],
        (Scale.MAJOR, Mode.LYDIAN): [0, 2, 4, 6, 7, 9, 11, 12],
        (Scale.MAJOR, Mode.MIXOLYDIAN): [
            0,
            2,
            4,
            5,
            7,
            9,
            10,
            12,
        ],
        (Scale.MAJOR, Mode.AEOLIAN): [
            0,
            2,
            3,
            5,
            7,
            8,
            10,
            12,
        ],
        (Scale.MAJOR, Mode.LOCRIAN): [0, 1, 3, 5, 6, 8, 10, 12],
        (Scale.MINOR, Mode.IONIAN): [
            0,
            2,
            3,
            5,
            7,
            8,
            10,
            12,
        ],
        (Scale.MINOR, Mode.DORIAN): [0, 2, 3, 5, 7, 9, 10, 12],
        (Scale.MINOR, Mode.PHRYGIAN): [0, 1, 3, 5, 7, 8, 10, 12],
        (Scale.MINOR, Mode.LYDIAN): [0, 2, 4, 6, 7, 9, 11, 12],
        (Scale.MINOR, Mode.MIXOLYDIAN): [
            0,
            2,
            4,
            5,
            7,
            9,
            10,
            12,
        ],
        (Scale.MINOR, Mode.AEOLIAN): [
            0,
            2,
            3,
            5,
            7,
            8,
            10,
            12,
        ],
        (Scale.MINOR, Mode.LOCRIAN): [0, 1, 3, 5, 6, 8, 10, 12],
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
        key: Key = Key.C,
        scale: Scale = Scale.MAJOR,
        mode: Mode = Mode.IONIAN,
        scale_factor=200,
        midi_port_name: str = MIDI_PORT,
    ):
        """
        midi_port_name: specify a MIDI port name if desired;
                        if None, the default output port is opened.
        """
        self.key: Key = key
        self.scale: Scale = scale
        self.mode: Mode = mode
        self.scale_factor: int = scale_factor

        self.midi_out = mido.open_output(midi_port_name)

        self.prev_state: dict = {}

        # Compute allowed MIDI note numbers from the given key and scale.
        base_key: int = self.KEYS[Key[self.key]]
        # Get the intervals for the selected scale and mode
        selected_intervals = self.INTERVALS.get(
            (self.scale, self.mode), self.INTERVALS[(Scale.MAJOR, Mode.IONIAN)]
        )

        # Allowed pitch classes (0-11) are determined by adding scale offsets modulo 12
        allowed_classes = {
            (base_key + offset) % 12 for offset in selected_intervals
        }
        # List of allowed notes in the lower half (0-63)
        self.lower_notes = [
            note for note in range(0, 64) if note % 12 in allowed_classes
        ]
        # List of allowed notes in the upper half (64-127)
        self.upper_notes = [
            note for note in range(64, 128) if note % 12 in allowed_classes
        ]
        # For the first node we want reverse order.
        self.lower_notes_reversed = list(reversed(self.lower_notes))

    def update(self, system: PendulumSystem) -> None:
        """
        For each double pendulum in the system, if any pendulum's node is active,
        send a MIDI note. Node active state is expected to be updated by the visualizer.
        """
        for double_pendulum_idx, double_pendulum in enumerate(system):
            pendulums: list[Pendulum] = double_pendulum.pendulums
            for node_idx, pendulum in enumerate(pendulums):
                if pendulum.node.active:
                    if node_idx % 2 == 0:
                        allowed = self.lower_notes_reversed
                    else:
                        allowed = self.upper_notes

                    assign_idx = double_pendulum_idx % len(allowed)
                    pitch: int = allowed[assign_idx]

                    ang_vel: float = abs(pendulum.angular_velocity)
                    # Map angular velocity to a MIDI velocity in a chosen range (30–127)
                    velocity: int = min(127, max(30, int(ang_vel * 20)))
                    self.play_note_on(node_idx, pitch, velocity)
                else:
                    prev_state = self.prev_state.get(
                        (double_pendulum, node_idx)
                    )
                    if prev_state is not None:
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
