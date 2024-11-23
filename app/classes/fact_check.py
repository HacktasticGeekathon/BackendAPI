class FactCheck:
    def __init__(self, title, verdict, description, timestamp):
        self.type = "factCheck"
        self.title = title
        self.verdict = verdict
        self.description = description
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "type": self.type,
            "title": self.title,
            "verdict": self.verdict,
            "description": self.description,
            "timestamp": self.timestamp
        }