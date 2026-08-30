from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


MODEL_PATH = Path(__file__).resolve().parent / "openfga" / "model.json"


def create_store_and_model(*, base_url: str) -> tuple[str, str]:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        store_response = client.post("/stores", json={"name": "gmai-r3-authority"})
        store_response.raise_for_status()
        store_id = store_response.json()["id"]
        model_response = client.post(
            f"/stores/{store_id}/authorization-models", json=model
        )
        model_response.raise_for_status()
        model_id = model_response.json()["authorization_model_id"]
    return store_id, model_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    store_id, model_id = create_store_and_model(base_url=args.base_url)
    print(json.dumps({"store_id": store_id, "authorization_model_id": model_id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
