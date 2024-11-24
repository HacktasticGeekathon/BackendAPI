import json
import math


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

    @staticmethod
    def from_json(data, timestamps):
        fact_checks_list = []

        for idx, result in enumerate(data["results"]):
            fact_check = FactCheck(
                title=result.get("title"),
                description=result.get("description"),
                verdict=result.get("verdict"),
                timestamp=[math.floor(float(ts)) for ts in timestamps[idx]] if idx < len(timestamps) else None
            )
            fact_checks_list.append(fact_check)

            fact_checks_list = [fact for fact in fact_checks_list if fact.timestamp is not None]

        return fact_checks_list

    @staticmethod
    def to_json(data, timestamps):
        fact_checks_list = FactCheck.from_json(data, timestamps)
        fact_checks_dict_list = [fact_check.to_dict() for fact_check in fact_checks_list]
        return json.dumps({"factChecks": fact_checks_dict_list}, indent=4)
