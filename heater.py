from __future__ import annotations

from abc import ABC, abstractmethod

import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)


class Actuator(ABC):
    @abstractmethod
    def on(self) -> None:
        """Turn the actuator on."""

    @abstractmethod
    def off(self) -> None:
        """Turn the actuator off."""

    @abstractmethod
    def is_on(self) -> bool:
        """Return the last commanded state."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release actuator resources."""


class BinaryActuator(Actuator):
    def __init__(self, pin: int, active_high: bool = True) -> None:
        self.pin = pin
        self.active_high = active_high
        self._state = False
        GPIO.setup(self.pin, GPIO.OUT, initial=self._off_signal())

    def _on_signal(self) -> int:
        return GPIO.HIGH if self.active_high else GPIO.LOW

    def _off_signal(self) -> int:
        return GPIO.LOW if self.active_high else GPIO.HIGH

    def on(self) -> None:
        GPIO.output(self.pin, self._on_signal())
        self._state = True

    def off(self) -> None:
        GPIO.output(self.pin, self._off_signal())
        self._state = False

    def is_on(self) -> bool:
        return self._state

    def cleanup(self) -> None:
        self.off()


class TimeProportionedActuator(BinaryActuator):
    def __init__(
        self,
        pin: int,
        active_high: bool = True,
        window_seconds: float = 10.0,
    ) -> None:
        super().__init__(pin=pin, active_high=active_high)
        self.window_seconds = window_seconds
        self._level = 0.0

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, level))

    def get_level(self) -> float:
        return self._level

    def apply_window(self, timestamp: float) -> None:
        if self._level <= 0.0:
            self.off()
            return
        if self._level >= 1.0:
            self.on()
            return

        on_time = self.window_seconds * self._level
        position_in_window = timestamp % self.window_seconds
        if position_in_window < on_time:
            self.on()
        else:
            self.off()


class Heater(TimeProportionedActuator):
    """MOSFET-switched heater driven by time proportioning."""


class Humidifier(BinaryActuator):
    """Bang-bang humidifier."""
