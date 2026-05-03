from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean


@dataclass
class RunMetrics:
    label: str
    duration_s: float
    initial_temperature_c: float
    peak_temperature_c: float
    peak_time_s: float
    overshoot_c: float
    overshoot_pct_of_setpoint: float
    rise_time_10_90_s: float | None
    settling_time_s: float | None
    steady_state_temperature_c: float
    steady_state_error_c: float
    max_relative_humidity_pct: float
    min_relative_humidity_pct: float
    mean_heater_command: float
    mean_fan_command: float
    fan_on_fraction: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze climate-control CSV logs.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=["climate_log_pid.csv", "climate_log_fuzzy.csv"],
        help="CSV files to analyze.",
    )
    parser.add_argument("--temperature-setpoint", type=float, default=23.0)
    parser.add_argument("--humidity-threshold", type=float, default=65.0)
    parser.add_argument(
        "--settling-band",
        type=float,
        default=0.5,
        help="Absolute temperature band in deg C used for settling time.",
    )
    parser.add_argument(
        "--steady-state-samples",
        type=int,
        default=20,
        help="Number of final samples used to estimate steady state.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures/report"),
        help="Directory for summary outputs.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, float]]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} is empty.")

    t0 = float(rows[0]["timestamp"])
    parsed: list[dict[str, float]] = []
    for row in rows:
        parsed_row = {key: float(value) for key, value in row.items()}
        parsed_row["time_s"] = parsed_row["timestamp"] - t0
        parsed.append(parsed_row)
    return parsed


def first_crossing_time(times: list[float], values: list[float], threshold: float) -> float | None:
    for time_s, value in zip(times, values):
        if value >= threshold:
            return time_s
    return None


def settling_time(times: list[float], values: list[float], target: float, band: float) -> float | None:
    for idx, time_s in enumerate(times):
        if all(abs(value - target) <= band for value in values[idx:]):
            return time_s
    return None


def derive_label(path: Path) -> str:
    stem = path.stem.lower()
    if "fuzzy" in stem:
        return "Fuzzy PID"
    if "pid" in stem:
        return "PID"
    return path.stem


def compute_metrics(
    path: Path,
    temperature_setpoint: float,
    settling_band: float,
    steady_state_samples: int,
) -> RunMetrics:
    rows = load_rows(path)
    times = [row["time_s"] for row in rows]
    temperatures = [row["temperature"] for row in rows]
    humidities = [row["relative_humidity"] for row in rows]
    heater_commands = [row["heater_command"] for row in rows]
    fan_commands = [row["fan_command"] for row in rows]

    initial_temperature = temperatures[0]
    peak_temperature = max(temperatures)
    peak_index = temperatures.index(peak_temperature)
    peak_time = times[peak_index]

    overshoot_c = max(0.0, peak_temperature - temperature_setpoint)
    overshoot_pct = 100.0 * overshoot_c / temperature_setpoint if temperature_setpoint else 0.0

    target_10 = initial_temperature + 0.1 * (temperature_setpoint - initial_temperature)
    target_90 = initial_temperature + 0.9 * (temperature_setpoint - initial_temperature)
    t10 = first_crossing_time(times, temperatures, target_10)
    t90 = first_crossing_time(times, temperatures, target_90)
    rise_time = None if t10 is None or t90 is None else t90 - t10

    settle_time = settling_time(times, temperatures, temperature_setpoint, settling_band)

    last_n = min(steady_state_samples, len(temperatures))
    steady_state_temperature = mean(temperatures[-last_n:])
    steady_state_error = steady_state_temperature - temperature_setpoint

    return RunMetrics(
        label=derive_label(path),
        duration_s=times[-1],
        initial_temperature_c=initial_temperature,
        peak_temperature_c=peak_temperature,
        peak_time_s=peak_time,
        overshoot_c=overshoot_c,
        overshoot_pct_of_setpoint=overshoot_pct,
        rise_time_10_90_s=rise_time,
        settling_time_s=settle_time,
        steady_state_temperature_c=steady_state_temperature,
        steady_state_error_c=steady_state_error,
        max_relative_humidity_pct=max(humidities),
        min_relative_humidity_pct=min(humidities),
        mean_heater_command=mean(heater_commands),
        mean_fan_command=mean(fan_commands),
        fan_on_fraction=mean(1.0 if value >= 0.5 else 0.0 for value in fan_commands),
    )


def write_summary_csv(path: Path, metrics_list: list[RunMetrics]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(metrics_list[0]).keys()))
        writer.writeheader()
        for item in metrics_list:
            writer.writerow(asdict(item))


def write_summary_md(
    path: Path,
    metrics_list: list[RunMetrics],
    temperature_setpoint: float,
    humidity_threshold: float,
    settling_band: float,
) -> None:
    lines = [
        "# Climate Log Metrics",
        "",
        f"- Temperature setpoint: `{temperature_setpoint:.1f} C`",
        f"- Humidity threshold: `{humidity_threshold:.1f} %`",
        f"- Settling band: `±{settling_band:.1f} C`",
        "",
        "| Controller | Rise Time 10-90% (s) | Settling Time (s) | Peak Temp (C) | Overshoot (C) | Steady-State Error (C) | Max RH (%) | Mean Heater | Mean Fan | Fan On Fraction |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in metrics_list:
        lines.append(
            "| {label} | {rise} | {settle} | {peak:.2f} | {overshoot:.2f} | {sse:.2f} | {max_rh:.1f} | {mean_heater:.3f} | {mean_fan:.3f} | {fan_frac:.3f} |".format(
                label=item.label,
                rise="n/a" if item.rise_time_10_90_s is None else f"{item.rise_time_10_90_s:.1f}",
                settle="n/a" if item.settling_time_s is None else f"{item.settling_time_s:.1f}",
                peak=item.peak_temperature_c,
                overshoot=item.overshoot_c,
                sse=item.steady_state_error_c,
                max_rh=item.max_relative_humidity_pct,
                mean_heater=item.mean_heater_command,
                mean_fan=item.mean_fan_command,
                fan_frac=item.fan_on_fraction,
            )
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metrics = [
        compute_metrics(Path(input_path), args.temperature_setpoint, args.settling_band, args.steady_state_samples)
        for input_path in args.inputs
    ]

    write_summary_csv(args.output_dir / "metrics_summary.csv", metrics)
    write_summary_md(
        args.output_dir / "metrics_summary.md",
        metrics,
        args.temperature_setpoint,
        args.humidity_threshold,
        args.settling_band,
    )

    with (args.output_dir / "metrics_summary.json").open("w") as handle:
        json.dump([asdict(item) for item in metrics], handle, indent=2)

    for item in metrics:
        print(f"{item.label}:")
        print(f"  Rise time (10-90%): {item.rise_time_10_90_s:.1f} s" if item.rise_time_10_90_s is not None else "  Rise time (10-90%): n/a")
        print(f"  Settling time: {item.settling_time_s:.1f} s" if item.settling_time_s is not None else "  Settling time: n/a")
        print(f"  Overshoot: {item.overshoot_c:.2f} C")
        print(f"  Steady-state error: {item.steady_state_error_c:.2f} C")
        print(f"  Max RH: {item.max_relative_humidity_pct:.1f} %")


if __name__ == "__main__":
    main()
