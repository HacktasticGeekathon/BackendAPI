import json


class Fallacy:
    def __init__(self, title, description, verdict, timestamp):
        self.type = "fallacy"
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

    @staticmethod
    def from_json(json_data, timestamps):
        data = json.loads(json_data)
        fallacies_list = []

        for idx, result in enumerate(data["results"]):
            fallacy = Fallacy(
                title=result.get("title", ""),
                description=result.get("description", ""),
                verdict=result.get("verdict", ""),
                timestamp=timestamps[idx] if idx < len(timestamps) else None
            )
            fallacies_list.append(fallacy)

        return fallacies_list