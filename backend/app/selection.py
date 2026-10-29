"""Pick which forecast a buyer would actually have had in hand.

Rule: for a target time T and a horizon H hours, use the most recent forecast
for T whose publish time is at or before T - H. Forecasts published later than
that were not available when the decision had to be made, so using them would
make the forecast look better than it really was.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import Iterable, Mapping

HOUR_S = 3600


@dataclass(frozen=True)
class Selected:
    target: int
    publish: int
    generation: float

    @property
    def lead_hours(self) -> float:
        return (self.target - self.publish) / HOUR_S


def select_forecast(
    publish_times: list[int],
    generations: list[float],
    target: int,
    horizon_h: float,
    max_horizon_h: float | None = None,
) -> Selected | None:
    """Latest forecast for `target` published at least `horizon_h` hours before it.

    `publish_times` must be sorted ascending. Returns None when no forecast was
    available that early, or when the only one available is older than
    `max_horizon_h` (too stale to be in scope).
    """
    if horizon_h < 0:
        raise ValueError("horizon must be >= 0")
    cutoff = target - int(round(horizon_h * HOUR_S))
    idx = bisect_right(publish_times, cutoff) - 1
    if idx < 0:
        return None
    publish = publish_times[idx]
    if max_horizon_h is not None and target - publish > max_horizon_h * HOUR_S:
        return None
    return Selected(target=target, publish=publish, generation=generations[idx])


def select_series(
    forecasts_by_target: Mapping[int, tuple[list[int], list[float]]],
    targets: Iterable[int],
    horizon_h: float,
    max_horizon_h: float | None = None,
) -> list[Selected]:
    out: list[Selected] = []
    for target in targets:
        entry = forecasts_by_target.get(target)
        if entry is None:
            continue
        chosen = select_forecast(entry[0], entry[1], target, horizon_h, max_horizon_h)
        if chosen is not None:
            out.append(chosen)
    return out
