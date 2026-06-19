#!/usr/bin/env python3
import json
import os
import urllib.request
import urllib.error

LM_STUDIO_URL = os.environ.get("NEON_LOCAL_MODEL_URL", "http://127.0.0.1:1234")
CONFIGURED_MODEL = os.environ.get("NEON_LOCAL_MODEL", "gemma-4-e2b-it")
TIMEOUT_SECONDS = 2.0

def run_health_check() -> dict:
    req = urllib.request.Request(f"{LM_STUDIO_URL}/api/v1/models", method="GET")

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode('utf-8')
    except (urllib.error.URLError, TimeoutError):
        return {
            "status": "blocked",
            "code": "LM_STUDIO_UNAVAILABLE"
        }

    try:
        data = json.loads(body)
        if not isinstance(data, dict) or "models" not in data:
            raise ValueError("Missing 'models' key")
    except (json.JSONDecodeError, ValueError):
        return {
            "status": "blocked",
            "code": "LM_STUDIO_RESPONSE_INVALID"
        }

    models = data.get("models", [])
    loaded_models = [
        model for model in models
        if isinstance(model, dict) and model.get("loaded_instances")
    ]

    if loaded_models:
        active = loaded_models[0]
        return {
            "status": "success",
            "code": "LM_STUDIO_OK",
            "server": LM_STUDIO_URL,
            "configured_model": CONFIGURED_MODEL,
            "active_model": active.get("key"),
            "active_model_display_name": active.get("display_name") or active.get("key"),
            "loaded_model_count": len(loaded_models),
            "model_count": len(models),
        }

    return {
        "status": "needs_review",
        "code": "LM_STUDIO_NO_MODEL_LOADED",
        "configured_model": CONFIGURED_MODEL,
        "active_model": None,
        "active_model_display_name": None,
        "loaded_model_count": 0,
        "model_count": len(models),
    }

if __name__ == "__main__":
    print(json.dumps(run_health_check(), indent=2))
