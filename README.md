# Climate Control System

Python control loop for a Raspberry Pi climate-control setup with:

- DHT11 temperature and humidity sensing
- Proportional heater control via time proportioning
- Binary fan control for hardware that only runs reliably at 100%
- Optional CSV logging
- Optional real-time plotting

## Files

- `main.py`: entry point for the controller
- `climate_control.py`: control loop, CSV logging, and plotting
- `controllers.py`: PID and humidity control logic
- `heater.py`: actuator abstractions and heater time-proportioning logic
- `fan.py`: binary fan actuator
- `thsensor.py`: DHT11 sensor wrapper
- `test_fan.py`: standalone fan test utility

## Hardware Defaults

- Sensor pin: `board.D4`
- Heater GPIO pin (BCM): `18`
- Fan GPIO pin (BCM): `17`

## Install

Create a virtual environment if you want one, then install dependencies:

```bash
pip install -r requirements.txt
```

If you are running on Raspberry Pi OS, you may also need system packages for `matplotlib` depending on your Python environment.

## Run

Basic run:

```bash
python3 main.py
```

Example with custom setpoints:

```bash
python3 main.py \
  --temperature-setpoint 15.0 \
  --humidity-threshold 60.0 \
  --sample-time 1.0
```

## CSV Logging

Write one row per control sample to a CSV file:

```bash
python3 main.py --log-csv climate_log.csv
```

CSV columns:

- `timestamp`
- `temperature`
- `relative_humidity`
- `heater_command`
- `fan_command`

The file is flushed after every sample so data is preserved even if the program is interrupted.

## Real-Time Plot

Show a live single-window plot with:

- temperature
- relative humidity
- heater command
- fan command

Run:

```bash
python3 main.py --plot
```

Use with CSV logging:

```bash
python3 main.py --plot --log-csv climate_log.csv
```

Control how many recent samples are kept in the plot:

```bash
python3 main.py --plot --plot-history-points 300
```

## Fan Control Behavior

The fan is treated as a binary actuator because the hardware only turns reliably at full power. Any nonzero fan command becomes fully `ON`.

Temperature-based cooling uses hysteresis:

- `--cooling-on-above`: turns cooling on when temperature rises this far above the setpoint
- `--cooling-off-above`: turns cooling off when temperature falls back to this level above the setpoint

Defaults:

- `--cooling-on-above 0.5`
- `--cooling-off-above 0.0`

## Useful Options

- `--mode {pid,fuzzy}`
- `--temperature-setpoint <degC>`
- `--humidity-threshold <percent>`
- `--sample-time <seconds>`
- `--heater-pin <bcm-pin>`
- `--fan-pin <bcm-pin>`
- `--heater-window <seconds>`
- `--fan-window <seconds>`
- `--humidity-hysteresis <percent>`
- `--cooling-on-above <degC>`
- `--cooling-off-above <degC>`
- `--log-csv <path>`
- `--plot`
- `--plot-history-points <count>`

## Fan Test

To test the fan output directly:

```bash
python3 test_fan.py
```

The test utility now defaults to fan GPIO pin `17`.
