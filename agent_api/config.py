import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAGFLOW_API_KEY")
BASE_URL = os.getenv("RAGFLOW_BASE_URL")
AGENT_ID = os.getenv("RAGFLOW_AGENT_ID")
AGENT_EXPLANATOR_ID = os.getenv("RAGFLOW_AGENT_EXPLANATOR_ID")