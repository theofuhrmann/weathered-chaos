import requests

from Config import Config
from EventManager import Event, EventType, event_manager


class WeatherAPI:
    def __init__(self, api_key: str, location: str = "Barcelona"):
        """
        Initialize WeatherAPI with API key and location.

        Args:
            api_key: API key for weather service (e.g., OpenWeatherMap)
            location: City name or location
        """
        self.api_key = api_key
        self.location = location
        self.base_url = "http://api.weatherapi.com/v1"
        self.temperature = None
        self.weather_condition = None

        self._register_event_handlers()

    def _register_event_handlers(self):
        event_manager.subscribe(
            EventType.LOCATION_CHANGED, self._on_location_changed
        )

    def _on_location_changed(self, event: Event):
        self.location = Config.location
        self.fetch_current_weather_data()

    def fetch_current_weather_data(self) -> dict:
        """Fetch current weather data from API"""
        params = {
            "q": self.location,
            "key": self.api_key,
        }
        current_weather_endpoint = "/current.json"
        try:
            url = f"{self.base_url}{current_weather_endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.temperature = data["current"]["temp_c"]
            self.weather_condition = data["current"]["condition"]["text"]

            Config.weather_condition = self.weather_condition
            Config.temperature = self.temperature

            event_manager.publish(
                Event(
                    EventType.WEATHER_UPDATED,
                    {
                        "condition": self.weather_condition,
                        "temperature": self.temperature,
                    },
                )
            )

            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            # Return default values if API call fails
            self.temperature = 20  # Default to room temperature
            self.weather_condition = "Clear"

            return {}
