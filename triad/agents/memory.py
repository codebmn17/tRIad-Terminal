from __future__ import annotations

import datetime as _dt
import json as _json
import os as _os
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .core import Message


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


@dataclass
class RoomMemory:
    name: str
    maxlen: int
    buffer: deque[Message]
    file: Path


class MemoryStore:
    """Persist room histories (JSONL) and maintain core memory topics.

    Layout (data_dir default: .triad):
      rooms/<room>.jsonl   # append‑only per message
      core_memory.json     # dict of topic -> list[{ts, text}]
    """

    def __init__(self, data_dir: str | Path = ".triad", *, maxlen: int = 10_000) -> None:
        self.root = Path(data_dir)
        self.rooms_dir = self.root / "rooms"
        self.core_path = self.root / "core_memory.json"
        self.maxlen = int(maxlen)
        self._rooms: dict[str, RoomMemory] = {}
        self._ensure_dirs()
        self._core_cache: dict[str, list[dict[str, str]]] = self._load_core()

    # setup
    def _ensure_dirs(self) -> None:
        self.rooms_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def _room_file(self, room: str) -> Path:
        return self.rooms_dir / f"{room}.jsonl"

    def _get_room(self, room: str) -> RoomMemory:
        if room not in self._rooms:
            f = self._room_file(room)
            buf: deque[Message] = deque(maxlen=self.maxlen)
            # warm buffer from tail of file (optional, best‑effort)
            if f.exists():
                try:
                    with f.open("r", encoding="utf-8") as fh:
                        # only keep last maxlen lines
                        for line in fh:
                            pass
                    # second pass to load efficiently if desired in future; keep minimal for now
                except Exception:
                    pass
            self._rooms[room] = RoomMemory(name=room, maxlen=self.maxlen, buffer=buf, file=f)
        return self._rooms[room]

    # recording
    def record(self, msg: Message) -> None:
        rm = self._get_room(msg.room)
        rm.buffer.append(msg)
        line = _json.dumps(
            {
                "room": msg.room,
                "sender": msg.sender,
                "content": msg.content,
                "role": msg.role,
                "ts": msg.ts.isoformat(),
                "meta": msg.meta,
            },
            ensure_ascii=False,
        )
        with rm.file.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def iter(self, room: str) -> Iterator[Message]:
        rm = self._get_room(room)
        yield from list(rm.buffer)

    # lightweight summary heuristic (portable; placeholder for smarter summarizers later)
    def summarize(self, room: str, *, limit: int = 20) -> str:
        rm = self._get_room(room)
        items = list(rm.buffer)[-limit:]
        parts = [f"{m.sender}: {m.content.strip().replace('\n', ' ')[:160]}" for m in items]
        return " \n".join(parts)

    # core memory (long‑term topics)
    def _load_core(self) -> dict[str, list[dict[str, str]]]:
        if not self.core_path.exists():
            return {}
        try:
            with self.core_path.open("r", encoding="utf-8") as fh:
                return _json.load(fh)
        except Exception:
            return {}

    def _atomic_write_core(self, data: dict[str, list[dict[str, str]]]) -> None:
        tmp = self.core_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            _json.dump(data, fh, ensure_ascii=False, indent=2)
        _os.replace(tmp, self.core_path)

    def core_set(self, topic: str, text: str) -> None:
        topic = topic.strip()
        if not topic:
            return
        bucket = self._core_cache.setdefault(topic, [])
        bucket.append({"ts": _now_iso(), "text": text.strip()})
        self._atomic_write_core(self._core_cache)

    def core_get(self, topic: str) -> list[dict[str, str]]:
        return list(self._core_cache.get(topic, []))

    def core_list(self) -> list[str]:
        return sorted(self._core_cache.keys())

    def core_del(self, topic: str) -> bool:
        if topic in self._core_cache:
            del self._core_cache[topic]
            self._atomic_write_core(self._core_cache)
            return True
        return False

    def flush(self) -> None:
        # JSONL is already flushed on write; core is persisted on mutation.
        pass
