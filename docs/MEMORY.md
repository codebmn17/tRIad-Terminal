# Triad Terminal — Memory System

This adds durable, terminal‑friendly memory without external services.

- Per‑room history: JSON Lines files at `.triad/rooms/<room>.jsonl`. These append each message with sender, role, mode, and timestamp.
- Rolling buffer: The last N messages per room are kept in memory (default N=10,000) for fast context.
- Core memory: Long‑term knowledge captured by topic at `.triad/core_memory.json`.

Commands
- `/mode <safe|anon|triad>` — Set the current room's mode (Safe is default). Anon and Triad are on‑demand.
- `/room new <name>` — Create and switch to a new room.
- `/join <name>` — Switch to an existing room.
- `/rooms` — List rooms.
- `/core set <topic> <text>` — Save a long‑term note.
- `/core get <topic>` — Show notes for a topic.
- `/core list` — List topics.
- `/core del <topic>` — Delete a topic and its notes.
- `/save` — Force a flush (JSONL writes are immediate; core memory commits on mutation).

Notes
- Stdlib‑only; safe on multi‑platform terminals.
- Summaries (`MemoryStore.summarize`) use a lightweight heuristic you can swap later for smarter summarization.
- RecorderAgent captures every message without altering behavior.