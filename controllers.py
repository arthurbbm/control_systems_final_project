from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass
class ClimateSetpoints:
    temperature_c: float
    humidity_pct: float


@dataclass
class ControlOutputs:
    heater_level: float
    fan_level: float
    ventilation_active: bool


class TemperatureController(ABC):
    @abstractmethod
    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """
        Return a signed control effort in the range [-1.0, 1.0].

        Positive values request heating, while negative values request cooling.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset controller state."""


class PIDController(TemperatureController):
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        output_limit: float = 1.0,
        integral_limit: float = 1.0,
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = abs(output_limit)
        self.integral_limit = abs(integral_limit)
        self._integral = 0.0
        self._previous_error = 0.0
        self._has_previous_error = False

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        error = setpoint - measurement
        if dt <= 0.0:
            dt = 1e-6

        self._integral += error * dt
        self._integral = clamp(
            self._integral,
            -self.integral_limit,
            self.integral_limit,
        )

        derivative = 0.0
        if self._has_previous_error:
            derivative = (error - self._previous_error) / dt

        output = (
            self.kp * error
            + self.ki * self._integral
            + self.kd * derivative
        )
        output = clamp(output, -self.output_limit, self.output_limit)

        self._previous_error = error
        self._has_previous_error = True
        return output

    def reset(self) -> None:
        self._integral = 0.0
        self._previous_error = 0.0
        self._has_previous_error = False


class FuzzyPIDController(PIDController):
    def __init__(
        self,
        base_kp: float,
        base_ki: float,
        base_kd: float,
        output_limit: float = 1.0,
        integral_limit: float = 1.0,
        error_scale: float = 5.0,
        delta_scale: float = 1.0,
    ) -> None:
        super().__init__(
            kp=base_kp,
            ki=base_ki,
            kd=base_kd,
            output_limit=output_limit,
            integral_limit=integral_limit,
        )
        self.base_kp = base_kp
        self.base_ki = base_ki
        self.base_kd = base_kd
        self.error_scale = error_scale
        self.delta_scale = delta_scale

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        error = setpoint - measurement
        delta_error = 0.0 if not self._has_previous_error else (error - self._previous_error) / max(dt, 1e-6)
        kp_factor, ki_factor, kd_factor = self._infer_gain_adjustments(error, delta_error)

        original = (self.kp, self.ki, self.kd)
        self.kp = self.base_kp * kp_factor
        self.ki = self.base_ki * ki_factor
        self.kd = self.base_kd * kd_factor
        output = super().update(setpoint, measurement, dt)
        self.kp, self.ki, self.kd = original
        return output

    def _infer_gain_adjustments(self, error: float, delta_error: float) -> tuple[float, float, float]:
        normalized_error = clamp(error / self.error_scale, -1.0, 1.0)
        normalized_delta = clamp(delta_error / self.delta_scale, -1.0, 1.0)

        magnitude = abs(normalized_error)
        trend = abs(normalized_delta)

        kp_factor = 1.0 + 0.7 * magnitude
        ki_factor = 1.0 - 0.5 * trend
        kd_factor = 1.0 + 0.8 * trend

        if normalized_error * normalized_delta < 0:
            ki_factor += 0.2

        return (
            clamp(kp_factor, 0.5, 2.0),
            clamp(ki_factor, 0.2, 1.5),
            clamp(kd_factor, 0.5, 2.0),
        )


class HumidityController(ABC):
    @abstractmethod
    def update(self, setpoint: float, measurement: float, dt: float) -> bool:
        """Return True when humidity control should force ventilation on."""

    @abstractmethod
    def reset(self) -> None:
        """Reset controller state."""


class ThresholdHumidityController(HumidityController):
    def __init__(self, threshold: float, hysteresis: float) -> None:
        self.threshold = threshold
        self.hysteresis = hysteresis
        self._state = False

    def update(self, setpoint: float, measurement: float, dt: float) -> bool:
        del setpoint, dt
        lower = self.threshold - self.hysteresis / 2.0
        upper = self.threshold + self.hysteresis / 2.0
        if measurement > upper:
            self._state = True
        elif measurement < lower:
            self._state = False
        return self._state

    def reset(self) -> None:
        self._state = False
