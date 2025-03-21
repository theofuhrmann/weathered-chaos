from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    """
    Event types that can be published in the system
    """

    LOCATION_CHANGED = auto()
    WEATHER_UPDATED = auto()
    MOON_MODE_CHANGED = auto()
    PENDULUM_COUNT_CHANGED = auto()
    MASS_RANGE_CHANGED = auto()
    LENGTH_RANGE_CHANGED = auto()
    MUSIC_SETTINGS_CHANGED = auto()
    PYGAME_EVENT = auto()
    WEATHER_FETCH_ERROR = auto()


class Event:
    """
    Event class containing the event type and data
    """

    def __init__(self, event_type: EventType, data: Any = None):
        self.type = event_type
        self.data = data


class EventManager:
    """
    Central event manager that handles pub/sub pattern for events
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._subscribers = {}
            for event_type in EventType:
                cls._instance._subscribers[event_type] = set()
        return cls._instance

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to an event type with a callback function
        """
        self._subscribers[event_type].add(callback)

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from an event type
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        """
        for callback in self._subscribers[event.type]:
            callback(event)


# Create a singleton instance that can be imported
event_manager = EventManager()
