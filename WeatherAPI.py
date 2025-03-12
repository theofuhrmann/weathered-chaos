from typing import Tuple

import requests


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
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            # Return default values if API call fails
            self.temperature = 20  # Default to room temperature
            self.weather_condition = "Clear"
            return {}

    def get_background_color(self) -> Tuple[int, int, int]:
        """
        Map temperature to background color.

        Returns:
            RGB color tuple (warmer for higher temps, cooler for lower temps)
        """
        if self.temperature is None:
            self.fetch_current_weather_data()

        # Map temperature range to color
        # Cold: blueish (0, 0, 255) to warm: reddish (255, 0, 0)
        if self.temperature <= 0:
            return (0, 0, 180)  # Cold blue
        elif 0 < self.temperature <= 10:
            return (0, 0, 255 - int(self.temperature * 5))  # Blue to cyan
        elif 10 < self.temperature <= 20:
            return (
                0,
                int((self.temperature - 10) * 20),
                200 - int((self.temperature - 10) * 20),
            )  # Cyan to green
        elif 20 < self.temperature <= 30:
            return (
                int((self.temperature - 20) * 20),
                200 - int((self.temperature - 20) * 10),
                0,
            )  # Green to yellow/orange
        else:
            return (
                200 + min(55, int((self.temperature - 30) * 5)),
                50,
                0,
            )  # Orange to red
