import requests
from .config import API_KEY, BASE_URL, AGENT_ID

class RagflowClient:
    def __init__(self, agent_id=AGENT_ID):
        self.agent_id = agent_id
        self.url = f"{BASE_URL}/api/v1/agents/{self.agent_id}/completions"
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

    def start_session(self):
        resp = requests.post(self.url, headers=self.headers, json={"question": "", "stream": False})
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["session_id"]

    def analyze_materia(self, materia: str, session_id: str):
        payload = {
            "question": materia,
            "session_id": session_id,
            "stream": False
        }
        resp = requests.post(self.url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()
