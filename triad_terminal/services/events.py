"""Events and SSE system for real-time updates."""

import asyncio
import json
from collections import defaultdict, deque
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any


class EventManager:
    """Generic publish/subscribe event manager with SSE support."""

    def __init__(self, max_history: int = 100):
        self.subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self.event_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = asyncio.Lock()

    def publish(self, channel: str, event: dict[str, Any]) -> None:
        """Publish event to channel."""
        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat()

        # Store in history
        self.event_history[channel].append(event)

        # Notify all subscribers (non-async version for background threads)
        if self.subscribers[channel]:
            # Create a new event loop if we're not in one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create new loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Schedule the async publish
            if loop.is_running():
                asyncio.create_task(self._async_publish(channel, event))
            else:
                loop.run_until_complete(self._async_publish(channel, event))

    async def _async_publish(self, channel: str, event: dict[str, Any]) -> None:
        """Async publish to subscribers."""
        async with self._lock:
            # Send to all subscribers
            for queue in self.subscribers[channel][:]:  # Copy list to avoid modification during iteration
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Remove full queues
                    self.subscribers[channel].remove(queue)
                except Exception:
                    # Remove broken queues
                    self.subscribers[channel].remove(queue)

    async def subscribe(self, channel: str) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to channel events (async generator for SSE)."""
        queue = asyncio.Queue(maxsize=50)

        async with self._lock:
            self.subscribers[channel].append(queue)

        try:
            # Send recent history
            for event in list(self.event_history[channel]):
                yield event

            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except TimeoutError:
                    # Send keepalive
                    yield {"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}

        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            async with self._lock:
                if queue in self.subscribers[channel]:
                    self.subscribers[channel].remove(queue)

    def get_recent_events(self, channel: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Get recent events from channel history."""
        events = list(self.event_history[channel])
        if limit:
            events = events[-limit:]
        return events

    def clear_history(self, channel: str) -> None:
        """Clear event history for channel."""
        self.event_history[channel].clear()

    def get_subscriber_count(self, channel: str) -> int:
        """Get number of active subscribers for channel."""
        return len(self.subscribers[channel])


# Global event manager instance
_event_manager: EventManager | None = None


def get_event_manager() -> EventManager:
    """Get global event manager instance."""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager


def format_sse_event(event: dict[str, Any]) -> str:
    """Format event for Server-Sent Events."""
    data = json.dumps(event, ensure_ascii=False)
    return f"data: {data}\n\n"
