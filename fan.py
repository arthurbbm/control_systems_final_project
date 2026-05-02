from __future__ import annotations

from heater import TimeProportionedActuator


class Fan(TimeProportionedActuator):
    """MOSFET-switched fan driven by time proportioning."""
