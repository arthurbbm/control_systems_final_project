from __future__ import annotations

import argparse
import time

import RPi.GPIO as GPIO

from fan import Fan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone MOSFET fan test.")
    parser.add_argument("--pin", type=int, default=17, help="BCM GPIO connected to the fan MOSFET gate.")
    parser.add_argument("--window", type=float, default=10.0, help="Time-proportioning window in seconds.")
    parser.add_argument("--step-seconds", type=float, default=5.0, help="Seconds to hold each fan speed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fan = Fan(pin=args.pin, window_seconds=args.window)

    try:
        start_time = time.time()
        for level in (0.0, 0.25, 0.5, 0.75, 1.0, 0.0):
            print(f"Setting fan to {level * 100:.0f}%")
            fan.set_level(level)
            step_start = time.time()
            while time.time() - step_start < args.step_seconds:
                fan.apply_window(time.time() - start_time)
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        fan.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
