from __future__ import annotations

from dataclasses import dataclass
import time

import RPi.GPIO as GPIO

from controllers import ClimateSetpoints, ControlOutputs, HumidityController, TemperatureController
from fan import Fan
from heater import Heater
from thsensor import Sensor, SensorReading


@dataclass
class GPIOConfig:
    sensor_pin_name: str = "D4"
    heater_pin: int = 18
    fan_pin: int = 12


class ClimateController:
    def __init__(
        self,
        temperature_controller: TemperatureController,
        humidity_controller: HumidityController,
    ) -> None:
        self.temperature_controller = temperature_controller
        self.humidity_controller = humidity_controller

    def compute_outputs(
        self,
        reading: SensorReading,
        setpoints: ClimateSetpoints,
        dt: float,
    ) -> ControlOutputs:
        temp_effort = self.temperature_controller.update(
            setpoint=setpoints.temperature_c,
            measurement=reading.temperature_c,
            dt=dt,
        )
        ventilation_active = self.humidity_controller.update(
            setpoint=setpoints.humidity_pct,
            measurement=reading.humidity_pct,
            dt=dt,
        )

        heater_level = max(0.0, temp_effort)
        fan_level = max(0.0, -temp_effort)
        if ventilation_active:
            fan_level = max(fan_level, 1.0)

        return ControlOutputs(
            heater_level=heater_level,
            fan_level=fan_level,
            ventilation_active=ventilation_active,
        )

    def reset(self) -> None:
        self.temperature_controller.reset()
        self.humidity_controller.reset()


class ControlLoop:
    def __init__(
        self,
        sensor: Sensor,
        heater: Heater,
        fan: Fan,
        climate_controller: ClimateController,
        setpoints: ClimateSetpoints,
        sample_time: float = 1.0,
    ) -> None:
        self.sensor = sensor
        self.heater = heater
        self.fan = fan
        self.climate_controller = climate_controller
        self.setpoints = setpoints
        self.sample_time = sample_time
        self._last_reading_time: float | None = None

    def run_once(self) -> tuple[SensorReading, ControlOutputs]:
        reading = self.sensor.read()
        if self._last_reading_time is None:
            dt = self.sample_time
        else:
            dt = max(reading.timestamp - self._last_reading_time, 1e-6)
        self._last_reading_time = reading.timestamp

        outputs = self.climate_controller.compute_outputs(reading, self.setpoints, dt)
        self.apply_outputs(outputs, reading.timestamp)
        return reading, outputs

    def apply_outputs(self, outputs: ControlOutputs, timestamp: float) -> None:
        self.heater.set_level(outputs.heater_level)
        self.heater.apply_window(timestamp)

        self.fan.set_level(outputs.fan_level)
        self.fan.apply_window(timestamp)

    def run_forever(self) -> None:
        try:
            while True:
                loop_start = time.time()
                reading, outputs = self.run_once()
                print(
                    "Temp={:.1f} C RH={:.1f}% HeaterCmd={:.0f}% Heater={} FanCmd={:.0f}% Fan={} RHVent={}".format(
                        reading.temperature_c,
                        reading.humidity_pct,
                        outputs.heater_level * 100.0,
                        "ON" if self.heater.is_on() else "OFF",
                        outputs.fan_level * 100.0,
                        "ON" if self.fan.is_on() else "OFF",
                        "ON" if outputs.ventilation_active else "OFF",
                    )
                )
                elapsed = time.time() - loop_start
                time.sleep(max(0.0, self.sample_time - elapsed))
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self.heater.cleanup()
        self.fan.cleanup()
        self.sensor.close()
        GPIO.cleanup()
