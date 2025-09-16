from __future__ import annotations

from dataclasses import dataclass, field

VALID_MODES = {"safe", "anon", "triad"}
DEFAULT_MODE = "safe"


@dataclass
class ModeState:
    per_room: dict[str, str] = field(default_factory=dict)


class ModeManager:
    def __init__(self) -> None:
        self._state = ModeState()

    def get_mode(self, room: str) -> str:
        return self._state.per_room.get(room, DEFAULT_MODE)

    def set_mode(self, room: str, mode: str) -> str:
        mode = mode.lower().strip()
        if mode not in VALID_MODES:
            raise ValueError(f"invalid mode: {mode}")
        self._state.per_room[room] = mode
        return mode

    def flags(self, room: str) -> dict[str, bool]:
        m = self.get_mode(room)
        return {
            "cautious_execution": m == "safe",
            "redact_pii": m == "anon",
            "fast_cadence": m == "triad",
        }
