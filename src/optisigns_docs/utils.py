import hashlib
import json
import os

def file_hash(content: str) -> str:
    """Return SHA256 hash of the given string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_state():
    """Load state from data/state.json if exists, else return empty dict."""
    state_file = "data/state.json"
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save state to data/state.json, creating directory if needed."""
    os.makedirs("data", exist_ok=True)
    state_file = "data/state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
