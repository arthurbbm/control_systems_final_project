from __future__ import annotations

import argparse

import board

from climate_control import ClimateController, ControlLoop
from controllers import ClimateSetpoints, FuzzyPIDController, PIDController, ThresholdHumidityController
from fan import Fan
from heater import Heater
from thsensor import DHT11Sensor


def build_temperature_controller(mode: str) -> PIDController | FuzzyPIDController:
    if mode == "fuzzy":
        return FuzzyPIDController(
            base_kp=0.35,
            base_ki=0.03,
            base_kd=0.10,
            output_limit=1.0,
            integral_limit=10.0,
            error_scale=5.0,
            delta_scale=2.0,
        )
    return PIDController(
        kp=0.35,
        ki=0.03,
        kd=0.10,
        output_limit=1.0,
        integral_limit=10.0,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Climate controller for heater and fan.")
    parser.add_argument("--mode", choices=("pid", "fuzzy"), default="pid")
    parser.add_argument("--temperature-setpoint", type=float, default=15.0)
    parser.add_argument("--humidity-threshold", type=float, default=60.0)
    parser.add_argument("--sample-time", type=float, default=1.0)
    parser.add_argument("--heater-pin", type=int, default=18)
    parser.add_argument("--fan-pin", type=int, default=12)
    parser.add_argument("--heater-window", type=float, default=10.0)
    parser.add_argument("--fan-window", type=float, default=10.0)
    parser.add_argument("--humidity-hysteresis", type=float, default=4.0)
    parser.add_argument("--cooling-on-above", type=float, default=0.5)
    parser.add_argument("--cooling-off-above", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sensor = DHT11Sensor(pin=board.D4)
    heater = Heater(pin=args.heater_pin, window_seconds=args.heater_window)
    fan = Fan(pin=args.fan_pin, window_seconds=args.fan_window)

    climate_controller = ClimateController(
        temperature_controller=build_temperature_controller(args.mode),
        humidity_controller=ThresholdHumidityController(
            threshold=args.humidity_threshold,
            hysteresis=args.humidity_hysteresis,
        ),
        cooling_on_above_setpoint_c=args.cooling_on_above,
        cooling_off_above_setpoint_c=args.cooling_off_above,
    )

    loop = ControlLoop(
        sensor=sensor,
        heater=heater,
        fan=fan,
        climate_controller=climate_controller,
        setpoints=ClimateSetpoints(
            temperature_c=args.temperature_setpoint,
            humidity_pct=args.humidity_threshold,
        ),
        sample_time=args.sample_time,
    )
    loop.run_forever()


if __name__ == "__main__":
    main()
