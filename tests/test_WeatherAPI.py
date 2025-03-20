import json
from unittest.mock import MagicMock, patch

import requests

from Config import Config
from WeatherAPI import WeatherAPI


class TestWeatherAPI:
    def setup_method(self):
        self.api_key = "fake_api_key"
        self.location = "Test City"
        self.weather_api = WeatherAPI(self.api_key, self.location)

    @patch("requests.get")
    def test_current_fetch_weather_data_success(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        with open("tests/weather_response.json") as f:
            mock_response.json.return_value = json.load(f)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

        # Call the method
        self.weather_api.fetch_current_weather_data()

        assert self.weather_api.temperature == 15.1
        assert self.weather_api.weather_condition == "Partly cloudy"
        mock_get.assert_called_once_with(
            self.weather_api.base_url + "/current.json",
            params={
                "q": self.location,
                "key": self.api_key,
            },
        )

    @patch("requests.get")
    def test_fetch_current_weather_data_request_exception(self, mock_get):
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException(
            "API Error"
        )

        # Call the method
        result = self.weather_api.fetch_current_weather_data()

        # Assertions
        assert result == {}
        assert self.weather_api.temperature == Config.temperature
        assert self.weather_api.weather_condition == Config.weather_condition

    @patch("requests.get")
    def test_fetch_weather_data_http_error(self, mock_get):
        # Setup mock to raise HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("404 Not Found")
        )
        mock_get.return_value = mock_response

        # Call the method
        result = self.weather_api.fetch_current_weather_data()

        # Assertions
        assert result == {}
        assert self.weather_api.temperature == Config.temperature
        assert self.weather_api.weather_condition == Config.weather_condition
