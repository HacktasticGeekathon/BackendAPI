import json
import math


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
    def from_json(data, timestamps):
        fallacies_list = []

        for idx, result in enumerate(data["results"]):
            fallacy = Fallacy(
                title=result.get("title"),
                description=result.get("description"),
                verdict=result.get("verdict"),
                timestamp=[math.floor(float(ts)) for ts in timestamps[idx]] if idx < len(timestamps) else None
            )
            fallacies_list.append(fallacy)

            fallacies_list = [fallacy for fallacy in fallacies_list if fallacy.timestamp is not None]

        return fallacies_list

    @staticmethod
    def to_json(data, timestamps):
        fallacies_list = Fallacy.from_json(data, timestamps)
        fallacies_dict_list = [fallacy.to_dict() for fallacy in fallacies_list]
        return json.dumps({"fallacies": fallacies_dict_list}, indent=4)