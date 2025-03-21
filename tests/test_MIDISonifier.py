from unittest.mock import MagicMock, patch

import pytest

from MIDISonifier import Key, MIDISonifier, Mode, Scale


class TestMIDISonifier:
    @pytest.fixture
    def mock_mido(self):
        with patch("MIDISonifier.mido") as mock_mido:
            # Set up the mock for open_output
            mock_midi_out = MagicMock()
            mock_mido.open_output.return_value = mock_midi_out
            yield mock_mido

    @pytest.fixture
    def mock_config(self):
        with patch("MIDISonifier.Config") as mock_config:
            # Initialize mock Config with default values
            mock_config.key = "C"
            mock_config.scale = "MAJOR"
            mock_config.mode = "IONIAN"
            yield mock_config

    @pytest.fixture
    def mock_event_manager(self):
        with patch("MIDISonifier.event_manager") as mock_event_manager:
            yield mock_event_manager

    def test_init_with_defaults(
        self, mock_mido, mock_config, mock_event_manager
    ):
        """Test initialization with default values from Config."""
        sonifier = MIDISonifier()

        # Check that the internal state matches expected defaults
        assert sonifier.key == Key.C
        assert sonifier.scale == Scale.MAJOR
        assert sonifier.mode == Mode.IONIAN
        assert sonifier.scale_factor == 200

        # Check that Config was updated
        assert mock_config.key == "C"
        assert mock_config.scale == "MAJOR"
        assert mock_config.mode == "IONIAN"

        # Check MIDI port was opened
        mock_mido.open_output.assert_called_once_with("IAC Driver Bus 1")

        # Check event handler registration
        mock_event_manager.subscribe.assert_called_once()

    def test_init_with_custom_values(
        self, mock_mido, mock_config, mock_event_manager
    ):
        """Test initialization with custom key, scale, and mode values."""
        sonifier = MIDISonifier(
            key=Key.D,
            scale=Scale.MINOR,
            mode=Mode.DORIAN,
            scale_factor=300,
            midi_port_name="Test MIDI Port",
        )

        # Check that the internal state matches expected values
        assert sonifier.key == Key.D
        assert sonifier.scale == Scale.MINOR
        assert sonifier.mode == Mode.DORIAN
        assert sonifier.scale_factor == 300

        # Check that Config was updated
        assert mock_config.key == "D"
        assert mock_config.scale == "MINOR"
        assert mock_config.mode == "DORIAN"

        # Check MIDI port was opened with custom name
        mock_mido.open_output.assert_called_once_with("Test MIDI Port")

    def test_allowed_notes_generation(
        self, mock_mido, mock_config, mock_event_manager
    ):
        """Test that allowed notes are correctly generated based on key, scale, and mode."""
        # Test with C Major Ionian
        sonifier = MIDISonifier(key=Key.C, scale=Scale.MAJOR, mode=Mode.IONIAN)

        # C Major scale should have notes C, D, E, F, G, A, B (MIDI 60, 62, 64, 65, 67, 69, 71)
        c_major_pitch_classes = {0, 2, 4, 5, 7, 9, 11}  # C, D, E, F, G, A, B

        # Check upper notes
        for note in sonifier.upper_notes:
            assert note >= 64  # Should be in upper half
            assert (
                note % 12 in c_major_pitch_classes
            )  # Should be part of C major

        # Check lower notes (reversed)
        for note in sonifier.lower_notes_reversed:
            assert note < 64  # Should be in lower half
            assert (
                note % 12 in c_major_pitch_classes
            )  # Should be part of C major

        # Check order of lower_notes_reversed (should be descending)
        assert sonifier.lower_notes_reversed == sorted(
            sonifier.lower_notes_reversed, reverse=True
        )

    def test_different_scales(
        self, mock_mido, mock_config, mock_event_manager
    ):
        """Test that different scales produce different note sets."""
        # C Major
        c_major = MIDISonifier(key=Key.C, scale=Scale.MAJOR, mode=Mode.IONIAN)

        # C Minor
        c_minor = MIDISonifier(key=Key.C, scale=Scale.MINOR, mode=Mode.AEOLIAN)

        # Major and minor scales should be different
        assert set(note % 12 for note in c_major.upper_notes) != set(
            note % 12 for note in c_minor.upper_notes
        )

        # C Major Ionian = [0, 2, 4, 5, 7, 9, 11] (C, D, E, F, G, A, B)
        # C Minor Aeolian = [0, 2, 3, 5, 7, 8, 10] (C, D, Eb, F, G, Ab, Bb)
        c_major_pitch_classes = {0, 2, 4, 5, 7, 9, 11}
        c_minor_pitch_classes = {0, 2, 3, 5, 7, 8, 10}

        # Verify C Major
        for note in c_major.upper_notes:
            assert note % 12 in c_major_pitch_classes

        # Verify C Minor
        for note in c_minor.upper_notes:
            assert note % 12 in c_minor_pitch_classes
