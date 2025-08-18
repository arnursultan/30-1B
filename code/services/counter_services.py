from __future__ import annotations

class CounterService:
    def __init__(self, start: int = 0) -> None:
        self._value = start

    @property
    def value(self) -> int:
        return self._value

    def increment(self, step: int = 1) -> int:
        self._value += step
        return self._value

    def decrement(self, step: int = 1) -> int:
        self._value -= step
        return self._value

    def reset(self) -> int:
        self._value = 0
        return self._value
