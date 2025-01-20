from langchain_core.runnables import RunnableConfig
from typing import Any, Iterable, Mapping, Optional, Union, Literal, Sequence
from langchain.load import dump as langchain_load_dump
from vertexai.preview import reasoning_engines
import tomli
from pydantic import BaseModel
from google.cloud import logging as google_cloud_logging
from traceloop.sdk import Instruments, Traceloop
from app.utils.tracing import CloudTraceLoggingSpanExporter
import logging 
import vertexai
import google.auth
import os
import datetime
from app.utils.gcs import create_bucket_if_not_exists
import json
import logging

logging.basicConfig(
    level=logging.INFO,
)

class AgentEngineApp:
    def __init__(self, project_id: Optional[str] = None) -> None:
        """Initialize the AgentEngineApp variables
        """
        self.project_id = project_id

    def set_up(self) -> None:
        """The set_up method is used to define application initialization logic"""
        # Lazy import agent at setup time to avoid deployment dependencies
        from app.agent import agent

        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        
        # Initialize Telemetry
        try:
            Traceloop.init(
            app_name="Sample Chatbot Application",
            disable_batch=False,
            exporter=CloudTraceLoggingSpanExporter(project_id=self.project_id),
            instruments={Instruments.VERTEXAI, Instruments.LANGCHAIN},
        )
        except Exception as e:
            logging.error("Failed to initialize Traceloop: %s", e)

        self.runnable = agent
    def _set_tracing_properties(
        self,
        input: Mapping[str, Any], 
        config: Optional["RunnableConfig"] = None,
    ) -> None:
        """Sets tracing association properties for the current request.
        
        Args:
            run_id: The run ID for the current request
            input: The input mapping containing user and session info
        """
        run_id = config.get("run_id") if config else "None"

        Traceloop.set_association_properties(
            {
                "log_type": "tracing", 
                "run_id": str(run_id),
                "user_id": input.pop("user_id", "None"),
                "session_id": input.pop("session_id", "None"),
                "commit_sha": os.environ.get("COMMIT_SHA", "None"),
            }
        )

    # The query method will be used to send inputs to the agent
    def stream_query(
        self,
        *,
        input: Union[str, Mapping[str, Any]],
        config: Optional["RunnableConfig"] = None,
        **kwargs,
    ) -> Iterable[Any]:
        self._set_tracing_properties(input=input, config=config)
        for chunk in self.runnable.stream(input=input, config=config, **kwargs):
            dumped_chunk = langchain_load_dump.dumpd(chunk)
            yield dumped_chunk

    def register_feedback(self,feedback: dict):
        """Collect and log feedback."""
        feedback = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback.model_dump(), severity="INFO")

    def query(self,
        *,
        input: Union[str, Mapping[str, Any]],
        config: Optional["RunnableConfig"] = None,
        **kwargs
        ):
        return langchain_load_dump.dumpd(
            self.runnable.invoke(input=input, config=config, **kwargs)
        )    
    def register_operations(self) -> Mapping[str, Sequence[str]]:
        """Registers the operations of the Agent.

        This mapping defines how different operation modes (e.g., "", "stream")
        are implemented by specific methods of the Agent.  The "default" mode,
        represented by the empty string ``, is associated with the `query` API,
        while the "stream" mode is associated with the `stream_query` API.

        Returns:
            Mapping[str, Sequence[str]]: A mapping of operation modes to a list
            of method names that implement those operation modes.
        """
        return {
            "": ["query", "register_feedback"],
            "stream": ["stream_query"],
        }

class Feedback(BaseModel):
    """Represents feedback for a conversation."""
    score: Union[int, float]
    text: Optional[str] = ""
    run_id: str
    log_type: Literal["feedback"] = "feedback"

def deploy_agent_engine_app():
    """Deploy the agent engine app to Vertex AI."""

    project = os.getenv("PROJECT_ID")
    if not project:
        _, project = google.auth.default()
    
    LOCATION = os.getenv("LOCATION", "us-central1")
    
    logging.info(f"Deploying agent engine app to project: {project}")
    logging.info(f"Using location: {LOCATION}")
    staging_bucket = f"gs://{project}-agent-engine"

    create_bucket_if_not_exists(
        bucket_name=staging_bucket,
        project=project,
        location=LOCATION
    )
    vertexai.init(
        project=project,
        location=LOCATION,
        staging_bucket=staging_bucket
    )

    # Load requirements from pyproject.toml
    with open("pyproject.toml", "rb") as f:
        requirements = tomli.load(f)["project"]["dependencies"]

    agent = AgentEngineApp(project_id=project)
    
    # Create and return reasoning engine
    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent,
        requirements=requirements,
        display_name="Reasoning Engine with LangGraph",
        description="This is a sample custom application in Reasoning Engine that uses LangGraph",
        extra_packages=["./app"]
    )

    config = {
        "remote_agent_engine_id": remote_agent.resource_name,
        "deployment_timestamp": datetime.datetime.now().isoformat()
    }
    config_file = ".agent_deployment.json"

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    logging.info(f"Agent Engine ID written to {config_file}")

    return remote_agent


if __name__ == "__main__":
    deploy_agent_engine_app()


