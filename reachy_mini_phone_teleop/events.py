from collections import defaultdict
from typing import Any, Callable


class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        self._subs[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        if callback in self._subs[event]:
            self._subs[event].remove(callback)

    def publish(self, event: str, data: Any = None) -> None:
        for callback in self._subs[event]:
            callback(data)
