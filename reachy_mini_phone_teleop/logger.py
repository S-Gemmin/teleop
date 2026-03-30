import json
import time


class Logger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = open(filepath, "a")

    def log(self, data: dict):
        data["timestamp"] = time.time()
        self.file.write(json.dumps(data) + "\n")
        self.file.flush()

    def close(self):
        self.file.close()
