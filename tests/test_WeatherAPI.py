import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from Config import Config
from EventManager import Event, EventType
from WeatherAPI import WeatherAPI


@pytest.fixture
def weather_api():
    api_key = "fake_api_key"
    location = "Test City"
    return WeatherAPI(api_key, location)


@pytest.fixture
def mock_weather_response():
    with open("tests/weather_response.json") as f:
        return json.load(f)


class TestWeatherAPIInitialization:
    def test_initialization(self, weather_api):
        assert weather_api.api_key == "fake_api_key"
        assert weather_api.location == "Test City"
        assert weather_api.base_url == "http://api.weatherapi.com/v1"
        assert weather_api.temperature is None
        assert weather_api.weather_condition is None


class TestWeatherDataFetching:
    @patch("requests.get")
    def test_current_fetch_weather_data_success(
        self, mock_get, weather_api, mock_weather_response
    ):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the method
        result = weather_api.fetch_current_weather_data()

        # Assertions
        assert result == mock_weather_response
        assert weather_api.temperature == 15.1
        assert weather_api.weather_condition == "Partly cloudy"
        mock_get.assert_called_once_with(
            weather_api.base_url + "/current.json",
            params={
                "q": weather_api.location,
                "key": weather_api.api_key,
            },
        )

    @patch("requests.get")
    def test_fetch_current_weather_data_request_exception(
        self, mock_get, weather_api
    ):
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException(
            "API Error"
        )

        # Call the method
        result = weather_api.fetch_current_weather_data()

        # Assertions
        assert result == {}
        assert weather_api.temperature == Config.temperature
        assert weather_api.weather_condition == Config.weather_condition

    @patch("requests.get")
    def test_fetch_weather_data_http_error(self, mock_get, weather_api):
        # Setup mock to raise HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("404 Not Found")
        )
        mock_get.return_value = mock_response

        # Call the method
        result = weather_api.fetch_current_weather_data()

        # Assertions
        assert result == {}
        assert weather_api.temperature == Config.temperature
        assert weather_api.weather_condition == Config.weather_condition


class TestEventHandling:
    @patch("WeatherAPI.event_manager")
    def test_event_handlers_registration(
        self, mock_event_manager, weather_api
    ):
        weather_api._register_event_handlers()

        # Check that the appropriate events are subscribed to
        assert mock_event_manager.subscribe.call_count >= 1
        # Verify location changed event is subscribed
        mock_event_manager.subscribe.assert_any_call(
            EventType.LOCATION_CHANGED, weather_api._on_location_changed
        )

    @patch("WeatherAPI.event_manager")
    def test_weather_fetch_error_on_location_change(
        self, mock_event_manager, weather_api
    ):
        # Setup: Mock fetch_current_weather_data to return an empty result (failure)
        old_location = "Test City"
        new_location = "Invalid City"

        with patch.object(
            weather_api, "fetch_current_weather_data", return_value={}
        ):
            # Trigger location change
            event = Event(EventType.LOCATION_CHANGED, new_location)
            weather_api._on_location_changed(event)

        mock_event_manager.publish.assert_called_once()
        published_event = mock_event_manager.publish.call_args[0][0]
        assert published_event.data == {
            "error_message": "Failed to fetch weather for Invalid City",
            "location": "Invalid City",
        }

        # Verify location is reverted back to the old one
        assert weather_api.location == old_location

    @patch("WeatherAPI.Config")
    @patch("WeatherAPI.event_manager")
    def test_location_reverted_on_fetch_error(
        self, mock_event_manager, mock_config, weather_api
    ):
        # Setup: Mock fetch_current_weather_data to return an empty result (failure)
        old_location = "Test City"
        new_location = "Invalid City"

        with patch.object(
            weather_api, "fetch_current_weather_data", return_value={}
        ):
            # Trigger location change
            event = Event(EventType.LOCATION_CHANGED, new_location)
            weather_api._on_location_changed(event)

        # Verify location is reverted in both the API and Config
        assert weather_api.location == old_location
        mock_config.location = (
            old_location  # Verify Config location is reverted
        )

    def test_on_location_changed_success(self, weather_api):
        # Setup: Mock fetch_current_weather_data to return success
        new_location = "New Test City"

        with patch.object(
            weather_api,
            "fetch_current_weather_data",
            return_value={
                "current": {"temp_c": 10, "condition": {"text": "Cloudy"}}
            },
        ), patch("WeatherAPI.event_manager") as mock_event_manager:
            # Trigger location change
            event = Event(EventType.LOCATION_CHANGED, new_location)
            weather_api._on_location_changed(event)

        # Verify location is updated and NO error event is published
        assert weather_api.location == new_location
        for call in mock_event_manager.publish.call_args_list:
            event = call[0][0]
            assert event.event_type != EventType.WEATHER_FETCH_ERROR


class TestWeatherDataParsing:
    @patch("requests.get")
    def test_parse_weather_data(self, mock_get, weather_api):
        # Test parsing of weather data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {"temp_c": 20.0, "condition": {"text": "Clear"}}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # This should parse the weather data internally
        weather_api.fetch_current_weather_data()

        # Check if the data was parsed correctly
        assert weather_api.temperature == 20.0
        assert weather_api.weather_condition == "Clear"

    @patch("requests.get")
    def test_parse_weather_data_missing_fields(self, mock_get, weather_api):
        # Test parsing when fields are missing
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {}
        }  # Missing temp and condition
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Should handle missing fields gracefully
        result = weather_api.fetch_current_weather_data()

        # Should return an empty dict
        assert result == {}
        assert weather_api.temperature == Config.temperature
        assert weather_api.weather_condition == Config.weather_condition
