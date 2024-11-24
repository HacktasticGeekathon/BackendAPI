import os

import requests
from enum import Enum
import json

class Mode(Enum):
    FALLACY_DETECTION = "logical-reasoning"
    FACT_CHECKING = "fact-checking"


class FallacyDetectionClient:
    def __init__(self):

        self.base_url = os.getenv("FALLACY_API_URL","http://127.0.0.1:8000")
        self.analyze_endpoint = "/analyze"
        self.model_id = "meta.llama3-1-70b-instruct-v1:0"
        self.headers = {
            "Content-Type": "application/json"
        }

    def analyze(self, texts_list, mode: Mode):
        url = self.base_url + self.analyze_endpoint
        payload = {
            "texts": texts_list,
            "model_id": self.model_id,
            "mode": mode.value
        }
        fallacies = requests.post(url, json=payload, headers=self.headers)
        fallacies.raise_for_status()
        payload["mode"] = Mode.FACT_CHECKING.value
        facts = requests.post(url, json=payload, headers=self.headers)

        return {"fallacies": fallacies.json(), "facts": facts.json(),}
