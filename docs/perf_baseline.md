# Performance Baseline (API + In-Process Metrics)

Populate this document with measurements gathered via the FastAPI service and /perf/status endpoint.

## Environment
- Host machine: (placeholder)
- CPU: (placeholder)
- Python version: (placeholder)
- Commit SHA: (placeholder)
- PERF_ENABLED: 1

## Test Commands

```bash
export PERF_ENABLED=1
uvicorn api.app:app --reload
```

Warm up the service with a few requests:

```bash
for i in {1..50}; do curl -s http://127.0.0.1:8000/health > /dev/null; done
for i in {1..50}; do curl -s http://127.0.0.1:8000/perf/health > /dev/null; done
```

Exercise decorated functionality (trigger guess_intent indirectly through application flows if available).

## Metrics Snapshot Example

```json
{
  "metrics": {
    "guess_intent": {
      "count": 42,
      "total": 0.1234,
      "avg": 0.00294,
      "p50": 0.00210,
      "p95": 0.00485
    }
  },
  "metrics_count": 1
}
```

## Placeholders (Fill These In)

| Metric Name    | Count | Avg (ms) | p50 (ms) | p95 (ms) | Notes |
|----------------|-------|----------|----------|----------|-------|
| guess_intent   | TBD   | TBD      | TBD      | TBD      |       |

Convert seconds to milliseconds where helpful.

## Aggregated Latency Summary

- guess_intent p50: (placeholder) ms
- guess_intent p95: (placeholder) ms
- Overall QPS (approx): (placeholder) (total requests / test duration)

## How Values Are Produced

Data originates from the in-process METRICS registry via api.perf_utils.snapshot(), surfaced at:
GET /perf/status

Only recorded when PERF_ENABLED=1 (default enabled if unset).

## Next Steps (Optional)

- Add additional @timed decorators to other hot paths.
- Track cold vs. warm performance by clearing the process and repeating tests.
