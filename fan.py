from __future__ import annotations

from heater import BinaryActuator


class Fan(BinaryActuator):
    """
    Binary fan actuator.

    The fan hardware only runs reliably at full power, so any nonzero command is
    treated as a full-on request.
    """

    def __init__(self, pin: int, active_high: bool = True, window_seconds: float = 10.0) -> None:
        super().__init__(pin=pin, active_high=active_high)
        self.window_seconds = window_seconds
        self._level = 0.0

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, level))

    def get_level(self) -> float:
        return self._level

    def apply_window(self, timestamp: float) -> None:
        del timestamp
        if self._level > 0.0:
            self.on()
        else:
            self.off()
