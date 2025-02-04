# pylint: disable=R0801
import json
import logging
import time
import vertexai
from vertexai.preview import reasoning_engines
from locust import User, between, task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Vertex AI and load agent config
vertexai.init()
with open("deployment_metadata.json") as f:
    remote_agent_engine_id = json.load(f)["remote_agent_engine_id"]
logger.info("Using remote agent engine ID: %s", remote_agent_engine_id)
agent = reasoning_engines.ReasoningEngine(remote_agent_engine_id)


class ChatStreamUser(User):
    """Simulates a user interacting with the chat stream API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task
    def chat_stream(self) -> None:
        """Simulates a chat stream interaction."""
        inputs = {
            "messages": [
                ("user", "What is the exchange rate from US dollars to Swedish currency?")
            ]
        }
        
        start_time = time.time()
        response = agent.query(input=inputs)
        
        # Register stream completed
        self.environment.events.request.fire(
            request_type="STREAM_END",
            name="reasoning_engine_stream_end", 
            response_time=(time.time() - start_time) * 1000,
            response_length=len(str(response)),
            exception=None
        )
