"""Regenerate the golden CartoonSpec baseline. Run intentionally after review."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from cartoonomics.pipeline import run_demo  # noqa: E402

GOLDEN = Path(__file__).parent / "golden" / "cashflow_demo.json"


def main() -> None:
    payload = json.loads(run_demo().to_json())
    payload["provenance"]["fetched_at"] = "<normalized>"
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote golden -> {GOLDEN}")


if __name__ == "__main__":
    main()
