from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate report-ready plots from climate-control CSV logs.")
    parser.add_argument("--pid-log", type=Path, default=Path("climate_log_pid.csv"))
    parser.add_argument("--fuzzy-log", type=Path, default=Path("climate_log_fuzzy.csv"))
    parser.add_argument("--temperature-setpoint", type=float, default=23.0)
    parser.add_argument("--humidity-threshold", type=float, default=65.0)
    parser.add_argument("--output-dir", type=Path, default=Path("figures/report"))
    return parser.parse_args()


def load_rows(path: Path) -> dict[str, list[float]]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} is empty.")

    t0 = float(rows[0]["timestamp"])
    data = {
        "time_s": [],
        "temperature": [],
        "relative_humidity": [],
        "heater_command": [],
        "fan_command": [],
    }
    for row in rows:
        data["time_s"].append(float(row["timestamp"]) - t0)
        data["temperature"].append(float(row["temperature"]))
        data["relative_humidity"].append(float(row["relative_humidity"]))
        data["heater_command"].append(float(row["heater_command"]))
        data["fan_command"].append(float(row["fan_command"]))
    return data


def plot_single_run(label: str, data: dict[str, list[float]], output_dir: Path, temperature_setpoint: float, humidity_threshold: float) -> None:
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    figure.patch.set_facecolor("white")

    axes[0].plot(data["time_s"], data["temperature"], color="#d97706", linewidth=2.0, label="Temperature")
    axes[0].axhline(temperature_setpoint, color="#1d4ed8", linestyle="--", linewidth=1.5, label="Setpoint")
    axes[0].set_ylabel("Temp (C)")
    axes[0].set_title(f"{label} Response")
    axes[0].legend(loc="best")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(data["time_s"], data["relative_humidity"], color="#0891b2", linewidth=2.0, label="Relative Humidity")
    axes[1].axhline(humidity_threshold, color="#7c3aed", linestyle="--", linewidth=1.5, label="RH Threshold")
    axes[1].set_ylabel("RH (%)")
    axes[1].legend(loc="best")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(data["time_s"], data["heater_command"], color="#dc2626", linewidth=2.0)
    axes[2].set_ylabel("Heater Cmd")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(data["time_s"], data["fan_command"], color="#16a34a", linewidth=2.0)
    axes[3].set_ylabel("Fan Cmd")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_ylim(-0.05, 1.05)
    axes[3].grid(True, alpha=0.3)

    figure.tight_layout()
    slug = label.lower().replace(" ", "_").replace("-", "_")
    figure.savefig(output_dir / f"{slug}_response.png", dpi=200, bbox_inches="tight")
    figure.savefig(output_dir / f"{slug}_response.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_comparison(
    pid_data: dict[str, list[float]],
    fuzzy_data: dict[str, list[float]],
    output_dir: Path,
    temperature_setpoint: float,
    humidity_threshold: float,
) -> None:
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=False)

    axes[0].plot(pid_data["time_s"], pid_data["temperature"], color="#b45309", linewidth=2.0, label="PID")
    axes[0].plot(fuzzy_data["time_s"], fuzzy_data["temperature"], color="#f59e0b", linewidth=2.0, label="Fuzzy PID")
    axes[0].axhline(temperature_setpoint, color="#1d4ed8", linestyle="--", linewidth=1.5, label="Setpoint")
    axes[0].set_ylabel("Temp (C)")
    axes[0].set_title("PID vs Fuzzy-PID Comparison")
    axes[0].legend(loc="best")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(pid_data["time_s"], pid_data["relative_humidity"], color="#0369a1", linewidth=2.0, label="PID")
    axes[1].plot(fuzzy_data["time_s"], fuzzy_data["relative_humidity"], color="#38bdf8", linewidth=2.0, label="Fuzzy PID")
    axes[1].axhline(humidity_threshold, color="#7c3aed", linestyle="--", linewidth=1.5, label="RH Threshold")
    axes[1].set_ylabel("RH (%)")
    axes[1].legend(loc="best")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(pid_data["time_s"], pid_data["heater_command"], color="#991b1b", linewidth=2.0, label="PID")
    axes[2].plot(fuzzy_data["time_s"], fuzzy_data["heater_command"], color="#ef4444", linewidth=2.0, label="Fuzzy PID")
    axes[2].set_ylabel("Heater Cmd")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].legend(loc="best")
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(pid_data["time_s"], pid_data["fan_command"], color="#166534", linewidth=2.0, label="PID")
    axes[3].plot(fuzzy_data["time_s"], fuzzy_data["fan_command"], color="#22c55e", linewidth=2.0, label="Fuzzy PID")
    axes[3].set_ylabel("Fan Cmd")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_ylim(-0.05, 1.05)
    axes[3].legend(loc="best")
    axes[3].grid(True, alpha=0.3)

    figure.tight_layout()
    figure.savefig(output_dir / "pid_vs_fuzzy_comparison.png", dpi=200, bbox_inches="tight")
    figure.savefig(output_dir / "pid_vs_fuzzy_comparison.pdf", bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot  # noqa: F401
    except ImportError as exc:
        raise SystemExit("matplotlib is required to generate report figures.") from exc

    pid_data = load_rows(args.pid_log)
    fuzzy_data = load_rows(args.fuzzy_log)

    plot_single_run("PID", pid_data, args.output_dir, args.temperature_setpoint, args.humidity_threshold)
    plot_single_run("Fuzzy PID", fuzzy_data, args.output_dir, args.temperature_setpoint, args.humidity_threshold)
    plot_comparison(pid_data, fuzzy_data, args.output_dir, args.temperature_setpoint, args.humidity_threshold)

    print(f"Saved report figures to {args.output_dir}")


if __name__ == "__main__":
    main()
