import requests
from enum import Enum


class Mode(Enum):
    FALLACY_DETECTION = "logical-reasoning"
    FACT_CHECKING = "fact-checking"


class FallacyDetectionClient:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.analyze_endpoint = "/analyze"
        self.model_id = "meta.llama3-1-8b-instruct-v1:0"
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

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
