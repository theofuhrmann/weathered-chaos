import json
from enum import Enum

import mido

from Config import Config
from EventManager import Event, EventType, event_manager
from PendulumSystem import Pendulum, PendulumSystem


class Scale(Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class Mode(Enum):
    IONIAN = "IONIAN"
    DORIAN = "DORIAN"
    PHRYGIAN = "PHRYGIAN"
    LYDIAN = "LYDIAN"
    MIXOLYDIAN = "MIXOLYDIAN"
    AEOLIAN = "AEOLIAN"
    LOCRIAN = "LOCRIAN"


class Key(Enum):
    C = "C"
    C_SHARP = "C_SHARP"
    D_FLAT = "D_FLAT"
    D = "D"
    D_SHARP = "D_SHARP"
    E_FLAT = "E_FLAT"
    E = "E"
    F = "F"
    F_SHARP = "F_SHARP"
    G_FLAT = "G_FLAT"
    G = "G"
    A_FLAT = "A_FLAT"
    A = "A"
    B_FLAT = "B_FLAT"
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
        Key.C_SHARP: 61,
        Key.D_FLAT: 61,
        Key.D: 62,
        Key.E_FLAT: 63,
        Key.E: 64,
        Key.F: 65,
        Key.F_SHARP: 66,
        Key.G_FLAT: 66,
        Key.G: 67,
        Key.A_FLAT: 68,
        Key.A: 69,
        Key.B_FLAT: 70,
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

        Config.key = key.value
        Config.scale = scale.value
        Config.mode = mode.value

        self.scale_factor: int = scale_factor

        self.midi_out = mido.open_output(midi_port_name)

        self.prev_state: dict = {}

        # Compute allowed MIDI note numbers from the given key and scale.
        base_key: int = self.KEYS[self.key]
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

        self._register_event_handlers()

    def _register_event_handlers(self):
        event_manager.subscribe(
            EventType.WEATHER_UPDATED, self._on_weather_changed
        )

    def _on_weather_changed(self, event: Event):
        self.set_key_scale_mode_from_weather(event.data["condition"])
        Config.key = self.key.value
        Config.scale = self.scale.value
        Config.mode = self.mode.value
        event_manager.publish(Event(EventType.MUSIC_SETTINGS_CHANGED))

    def set_key_scale_mode_from_weather(
        self,
        weather_condition: str,
    ):
        with open("weather_music_mapping.json") as f:
            weather_music_mapping = json.load(f)
            self.key = Key[weather_music_mapping[weather_condition]["key"]]
            self.scale = Scale[
                weather_music_mapping[weather_condition]["scale"]
            ]
            self.mode = Mode[weather_music_mapping[weather_condition]["mode"]]

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

                    gravity_scaling = 9.81 / double_pendulum.g
                    scaled_ang_vel = ang_vel * gravity_scaling
                    # Map angular velocity to a MIDI velocity in a chosen range (30–127)
                    velocity: int = min(127, max(30, int(scaled_ang_vel * 20)))
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
        self.midi_out.send(note_off)
        self.midi_out.send(note_off)
