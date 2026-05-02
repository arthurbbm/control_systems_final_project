from __future__ import annotations

import csv
from collections import deque
from dataclasses import dataclass
from datetime import datetime
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
    fan_pin: int = 17


class RealtimePlotter:
    def __init__(self, history_points: int = 300) -> None:
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise RuntimeError(
                "Real-time plotting requires matplotlib. Install dependencies from requirements.txt first."
            ) from exc

        self._mdates = mdates
        self._plt = plt
        self._timestamps: deque[datetime] = deque(maxlen=history_points)
        self._temperatures: deque[float] = deque(maxlen=history_points)
        self._humidities: deque[float] = deque(maxlen=history_points)
        self._heater_commands: deque[float] = deque(maxlen=history_points)
        self._fan_commands: deque[float] = deque(maxlen=history_points)

        plt.style.use("seaborn-v0_8-darkgrid")
        self._figure, self._axis = plt.subplots(figsize=(11, 6))
        self._command_axis = self._axis.twinx()
        self._figure.patch.set_facecolor("#0f172a")
        self._axis.set_facecolor("#111827")
        self._command_axis.set_facecolor("#111827")

        self._temperature_line, = self._axis.plot([], [], color="#f97316", linewidth=2.4, label="Temperature (C)")
        self._humidity_line, = self._axis.plot([], [], color="#38bdf8", linewidth=2.4, label="Relative Humidity (%)")
        self._heater_line, = self._command_axis.plot([], [], color="#facc15", linewidth=2.0, linestyle="--", label="Heater Command")
        self._fan_line, = self._command_axis.plot([], [], color="#34d399", linewidth=2.0, linestyle="--", label="Fan Command")

        self._axis.set_title("Climate Control Signals", color="white", fontsize=16, pad=14)
        self._axis.set_xlabel("Time", color="white")
        self._axis.set_ylabel("Temperature / Relative Humidity", color="white")
        self._command_axis.set_ylabel("Command", color="white")
        self._command_axis.set_ylim(-0.05, 1.05)

        self._axis.tick_params(colors="white")
        self._command_axis.tick_params(colors="white")
        self._axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        for spine in self._axis.spines.values():
            spine.set_color("#94a3b8")
        for spine in self._command_axis.spines.values():
            spine.set_color("#94a3b8")

        legend_lines = [
            self._temperature_line,
            self._humidity_line,
            self._heater_line,
            self._fan_line,
        ]
        legend = self._axis.legend(
            legend_lines,
            [line.get_label() for line in legend_lines],
            loc="upper left",
            frameon=True,
            facecolor="#0f172a",
            edgecolor="#334155",
        )
        for text in legend.get_texts():
            text.set_color("white")

        plt.ion()
        plt.show(block=False)

    def update(self, reading: SensorReading, outputs: ControlOutputs) -> None:
        timestamp = datetime.fromtimestamp(reading.timestamp)
        self._timestamps.append(timestamp)
        self._temperatures.append(reading.temperature_c)
        self._humidities.append(reading.humidity_pct)
        self._heater_commands.append(outputs.heater_level)
        self._fan_commands.append(outputs.fan_level)

        self._temperature_line.set_data(self._timestamps, self._temperatures)
        self._humidity_line.set_data(self._timestamps, self._humidities)
        self._heater_line.set_data(self._timestamps, self._heater_commands)
        self._fan_line.set_data(self._timestamps, self._fan_commands)

        if self._timestamps:
            self._axis.set_xlim(self._timestamps[0], self._timestamps[-1])

        if self._temperatures or self._humidities:
            combined = list(self._temperatures) + list(self._humidities)
            lower = min(combined)
            upper = max(combined)
            margin = max(1.0, 0.1 * (upper - lower if upper > lower else 1.0))
            self._axis.set_ylim(lower - margin, upper + margin)

        self._axis.figure.autofmt_xdate()
        self._figure.canvas.draw_idle()
        self._figure.canvas.flush_events()
        self._plt.pause(0.001)

    def close(self) -> None:
        self._plt.close(self._figure)


class ClimateController:
    def __init__(
        self,
        temperature_controller: TemperatureController,
        humidity_controller: HumidityController,
        cooling_on_above_setpoint_c: float = 0.5,
        cooling_off_above_setpoint_c: float = 0.0,
    ) -> None:
        if cooling_off_above_setpoint_c > cooling_on_above_setpoint_c:
            raise ValueError("cooling_off_above_setpoint_c must be less than or equal to cooling_on_above_setpoint_c.")

        self.temperature_controller = temperature_controller
        self.humidity_controller = humidity_controller
        self.cooling_on_above_setpoint_c = cooling_on_above_setpoint_c
        self.cooling_off_above_setpoint_c = cooling_off_above_setpoint_c
        self._temperature_cooling_active = False

    def _update_temperature_cooling_state(
        self,
        temperature_c: float,
        setpoint_c: float,
    ) -> bool:
        upper = setpoint_c + self.cooling_on_above_setpoint_c
        lower = setpoint_c + self.cooling_off_above_setpoint_c

        if temperature_c >= upper:
            self._temperature_cooling_active = True
        elif temperature_c <= lower:
            self._temperature_cooling_active = False

        return self._temperature_cooling_active

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
        temperature_cooling_active = self._update_temperature_cooling_state(
            temperature_c=reading.temperature_c,
            setpoint_c=setpoints.temperature_c,
        )

        heater_level = max(0.0, temp_effort)
        if temperature_cooling_active:
            heater_level = 0.0

        fan_level = 1.0 if temperature_cooling_active else 0.0
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
        self._temperature_cooling_active = False


class ControlLoop:
    def __init__(
        self,
        sensor: Sensor,
        heater: Heater,
        fan: Fan,
        climate_controller: ClimateController,
        setpoints: ClimateSetpoints,
        sample_time: float = 1.0,
        log_csv_path: str | None = None,
        plot_realtime: bool = False,
        plot_history_points: int = 300,
    ) -> None:
        self.sensor = sensor
        self.heater = heater
        self.fan = fan
        self.climate_controller = climate_controller
        self.setpoints = setpoints
        self.sample_time = sample_time
        self._last_reading_time: float | None = None
        self._log_file = None
        self._log_writer: csv.writer | None = None
        self._plotter = RealtimePlotter(history_points=plot_history_points) if plot_realtime else None

        if log_csv_path is not None:
            self._log_file = open(log_csv_path, "a", newline="", encoding="utf-8")
            self._log_writer = csv.writer(self._log_file)
            if self._log_file.tell() == 0:
                self._log_writer.writerow(
                    [
                        "timestamp",
                        "temperature",
                        "relative_humidity",
                        "heater_command",
                        "fan_command",
                    ]
                )
                self._log_file.flush()

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
                self.log_reading(reading, outputs)
                self.update_plot(reading, outputs)
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

    def log_reading(self, reading: SensorReading, outputs: ControlOutputs) -> None:
        if self._log_writer is None or self._log_file is None:
            return

        self._log_writer.writerow(
            [
                f"{reading.timestamp:.3f}",
                f"{reading.temperature_c:.3f}",
                f"{reading.humidity_pct:.3f}",
                f"{outputs.heater_level:.3f}",
                f"{outputs.fan_level:.3f}",
            ]
        )
        self._log_file.flush()

    def update_plot(self, reading: SensorReading, outputs: ControlOutputs) -> None:
        if self._plotter is not None:
            self._plotter.update(reading, outputs)

    def shutdown(self) -> None:
        self.heater.cleanup()
        self.fan.cleanup()
        self.sensor.close()
        if self._log_file is not None:
            self._log_file.close()
        if self._plotter is not None:
            self._plotter.close()
        GPIO.cleanup()
