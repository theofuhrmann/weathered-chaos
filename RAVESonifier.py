import json

import numpy as np
import sounddevice as sd
import torch

from Config import Config
from EventManager import Event, EventType, event_manager
from PendulumSystem import PendulumSystem


class RAVESonifier:
    def __init__(
        self,
        pendulum_system: PendulumSystem,
        weights_path: str = None,
        latent_dim: int = None,
        sample_rate: int = 48000,
        buffer_size: int = 1024,
        scaling_factor: float = 1.0,
    ):
        self.moon_mode = Config.moon_mode
        self.weather_condition = Config.weather_condition

        if weights_path is None or latent_dim is None:
            self.update_settings()
        else:
            self.weights_path = weights_path
            self.latent_dim = latent_dim

        self.load_model()
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.scaling_factor = scaling_factor
        self.pendulum_system = pendulum_system

        self._register_event_handlers()

    def _register_event_handlers(self):
        event_manager.subscribe(
            EventType.MOON_MODE_CHANGED, self._on_moon_mode_changed
        )
        event_manager.subscribe(
            EventType.WEATHER_UPDATED, self._on_weather_changed
        )

    def _on_weather_changed(self, event: Event):
        self.update_settings()
        self.load_model()
        self.weather_condition = event.data

    def _on_moon_mode_changed(self, event: Event):
        self.update_settings()
        self.load_model()
        self.moon_mode = event.data

    def load_model(self):
        self.model = torch.jit.load(self.weights_path)
        self.model.eval()

    def update_settings(self):
        with open("rave_weights_mapping.json") as f:
            rave_weights_mapping = json.load(f)

        with open("weather_music_mapping.json") as f:
            weather_music_mapping = json.load(f)

        if Config.moon_mode:
            weights_path = "rave_model_weights/moon.ts"
        else:
            weights_path = weather_music_mapping[Config.weather_condition][
                "weights"
            ]

        with open("rave_weights_mapping.json") as f:
            rave_weights_mapping = json.load(f)
            rave_settings = rave_weights_mapping[weights_path]
            self.weights_path = weights_path
            self.latent_dim = rave_settings["latent_dim"]
            self.volume = rave_settings["volume"]

    def _fill_latent_column_with_random_values(
        self, latent_column: list
    ) -> list:
        missing_latents = self.latent_dim - len(latent_column)
        latent_column += [
            torch.randn(1).item() for _ in range(missing_latents)
        ]
        return latent_column

    def generate_latents(self) -> torch.Tensor:
        noise_factor = 0.5
        latents = []
        for double_pendulum in self.pendulum_system.double_pendulums:
            for pendulum in double_pendulum.pendulums:
                x_latent = (
                    pendulum.node.last_x - self.scaling_factor
                ) / self.scaling_factor
                x_latent = (
                    x_latent * (1 - noise_factor)
                    + torch.randn(1).item() * noise_factor
                )
                latents.append(x_latent)

                av_latent = pendulum.angular_velocity / double_pendulum.g
                av_latent = (
                    av_latent * (1 - noise_factor)
                    + torch.randn(1).item() * noise_factor
                )
                latents.append(av_latent)

        if len(latents) < self.latent_dim:
            latents += [
                torch.randn(1).item()
                for _ in range(self.latent_dim - len(latents))
            ]

        columns = -(-len(latents) // self.latent_dim)
        latent_columns = []
        for i in range(columns):
            start = i * self.latent_dim
            end = start + self.latent_dim
            latent_column = latents[start:end]
            if len(latent_column) < self.latent_dim:
                latent_column = self._fill_latent_column_with_random_values(
                    latent_column
                )
            latent_columns.append(latent_column)

        return torch.tensor(latent_columns).view(1, self.latent_dim, columns)

    def generate_audio(self, latents: torch.Tensor) -> np.ndarray:
        with torch.no_grad():
            return self.model.decode(latents).numpy().flatten()

    def stream_audio(self) -> None:
        def callback(outdata, frames, time, status):
            latents = self.generate_latents()
            audio = self.generate_audio(latents)
            audio *= self.volume
            outdata[:] = np.expand_dims(audio[:frames], axis=1)

        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            channels=1,
            callback=callback,
        )
        self.stream.start()
        print("Streaming audio...")

    def stop_audio(self) -> None:
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()
            print("Audio streaming stopped.")
