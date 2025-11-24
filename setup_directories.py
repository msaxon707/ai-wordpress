# setup_directories.py
import os
import json

def setup_directories():
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    topic_history = "data/topic_history.json"
    if not os.path.exists(topic_history):
        with open(topic_history, "w") as f:
            json.dump([], f)

if __name__ == "__main__":
    setup_directories()
