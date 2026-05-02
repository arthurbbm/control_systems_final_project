from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import time

import adafruit_dht
import board


@dataclass
class SensorReading:
    temperature_c: float
    humidity_pct: float
    timestamp: float


class Sensor(ABC):
    @abstractmethod
    def read(self) -> SensorReading:
        """Return the latest measurement from the physical sensor."""

    @abstractmethod
    def close(self) -> None:
        """Release any sensor resources."""


class DHT11Sensor(Sensor):
    def __init__(
        self,
        pin: object = board.D4,
        retry_delay_s: float = 2.0,
    ) -> None:
        self._device = adafruit_dht.DHT11(pin)
        self._retry_delay_s = retry_delay_s

    def read(self) -> SensorReading:
        while True:
            try:
                temperature_c = self._device.temperature
                humidity_pct = self._device.humidity
                if temperature_c is None or humidity_pct is None:
                    raise RuntimeError("Failed to retrieve data from the DHT11 sensor.")
                return SensorReading(
                    temperature_c=float(temperature_c),
                    humidity_pct=float(humidity_pct),
                    timestamp=time.time(),
                )
            except RuntimeError:
                # DHT11 reads are noisy, so retry transient read failures.
                time.sleep(self._retry_delay_s)

    def close(self) -> None:
        self._device.exit()
