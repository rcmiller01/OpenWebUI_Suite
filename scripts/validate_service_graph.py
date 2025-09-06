"""Validate SERVICE_GRAPH.mmd contains required edge set.

Fails (exit 1) if any mandated edge is missing. Keeps docs honest.
"""
from __future__ import annotations
from pathlib import Path
import sys

REQUIRED_EDGES = {
    ("00-pipelines-gateway", "01-intent-router"),
    ("00-pipelines-gateway", "02-memory-2-0"),
    ("00-pipelines-gateway", "03-feeling-engine"),
    ("00-pipelines-gateway", "04-hidden-multi-expert-merger"),
    ("00-pipelines-gateway", "06-byof-tool-hub"),
    ("00-pipelines-gateway", "13-policy-guardrails"),
    ("10-multimodal-router", "11-stt-tts-gateway"),
    ("10-multimodal-router", "16-fastvlm-sidecar"),
    ("09-proactive-daemon", "00-pipelines-gateway"),
}

GRAPH_FILE = Path("SERVICE_GRAPH.mmd")


def parse_edges(text: str) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for line in text.splitlines():
        line = line.strip()
        if "-->" in line and not line.startswith("%%"):
            try:
                left, right = [part.strip() for part in line.split("-->")[:2]]
                # Strip optional labels if ever added (A --> B)
                edges.add((left, right))
            except ValueError:
                continue
    return edges


def main() -> int:
    if not GRAPH_FILE.exists():
        print("SERVICE_GRAPH.mmd not found")
        return 1
    edges = parse_edges(GRAPH_FILE.read_text())
    missing = sorted(REQUIRED_EDGES - edges)
    if missing:
        print("Missing required service graph edges:")
        for a, b in missing:
            print(f" - {a} --> {b}")
        return 1
    print("Service graph validation passed.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
