import json
import uuid
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urljoin
import importlib

from langchain_core.messages import AIMessage, ToolMessage
import requests
import streamlit as st
from frontend.utils.multimodal_utils import format_content
from vertexai.preview import reasoning_engines

from google.api.httpbody_pb2 import HttpBody

@st.cache_resource
def get_remote_agent(remote_agent_engine_id: str) -> Any:
    """Get cached remote agent instance."""
    return reasoning_engines.ReasoningEngine(remote_agent_engine_id)


class Client:
    """A client for streaming events from a server."""
    def __init__(self, agent_callable_path: str, remote_agent_engine_id: str) -> None:
        """Initialize the Client with a base URL."""

        if remote_agent_engine_id:
            self.agent = get_remote_agent(remote_agent_engine_id)
        else:
            # Force reload all submodules to get latest changes
            module_path, class_name = agent_callable_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            self.agent = getattr(module, class_name)()
            self.agent.set_up()

    def log_feedback(self, feedback_dict: Dict[str, Any], run_id: str) -> None:
        """Log user feedback for a specific run."""
        score = feedback_dict["score"]
        if score == "😞":
            score = 0.0
        elif score == "🙁":
            score = 0.25
        elif score == "😐":
            score = 0.5
        elif score == "🙂":
            score = 0.75
        elif score == "😀":
            score = 1.0
        feedback_dict["score"] = score
        feedback_dict["run_id"] = run_id
        feedback_dict["log_type"] = "feedback"
        feedback_dict.pop("type")
        url = urljoin(self.url, "feedback")
        headers = {
            "Content-Type": "application/json",
        }
        if self.authenticate_request:
            headers["Authorization"] = f"Bearer {self.id_token}"
        requests.post(url, data=json.dumps(feedback_dict), headers=headers)

    def stream_events(
        self, data: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream events from the server, yielding parsed event data."""
        for event in self.agent.stream_query(input=data):
            if isinstance(event, HttpBody):
                    # Handle multiline strings by splitting on newlines
                    if isinstance(event.data, bytes):
                        event_data = event.data.decode('utf-8')
                    else:
                        event_data = event.data
                    if "\n" in event_data:
                        lines = event_data.splitlines()
                        for line in lines:
                            yield json.loads(line)
            else:
                # If already a dict/object, yield as-is
                yield event


class StreamHandler:
    """Handles streaming updates to a Streamlit interface."""

    def __init__(self, st: Any, initial_text: str = "") -> None:
        """Initialize the StreamHandler with Streamlit context and initial text."""
        self.st = st
        self.tool_expander = st.expander("Tool Calls:", expanded=False)
        self.container = st.empty()
        self.text = initial_text
        self.tools_logs = initial_text

    def new_token(self, token: str) -> None:
        """Add a new token to the main text display."""
        self.text += token
        self.container.markdown(format_content(self.text), unsafe_allow_html=True)

    def new_status(self, status_update: str) -> None:
        """Add a new status update to the tool calls expander."""
        self.tools_logs += status_update
        self.tool_expander.markdown(status_update)


class EventProcessor:
    """Processes events from the stream and updates the UI accordingly."""

    def __init__(self, st: Any, client: Client, stream_handler: StreamHandler) -> None:
        """Initialize the EventProcessor with Streamlit context, client, and stream handler."""
        self.st = st
        self.client = client
        self.stream_handler = stream_handler
        self.final_content = ""
        self.tool_calls: List[Dict[str, Any]] = []
        self.current_run_id: Optional[str] = None
        self.additional_kwargs = {}

    def process_events(self) -> None:
        """Process events from the stream, handling each event type appropriately."""
        messages = self.st.session_state.user_chats[
            self.st.session_state["session_id"]
        ]["messages"]
        run_id = str(uuid.uuid4())
        self.current_run_id = run_id
        stream = self.client.stream_events(
            data={
                "messages": messages,
                "config": {"run_id": run_id},
                "user_id": self.st.session_state["user_id"],
                "session_id": self.st.session_state["session_id"],
            }
        )

        for event in stream:
            # Handle agent events
            
            if "agent" in event:
                message = event["agent"]["messages"]
                if message["kwargs"].get("tool_calls"):
                    # Handle tool call
                    tool_calls = message["kwargs"]["tool_calls"]
                    ai_message = AIMessage(content="", tool_calls=tool_calls)
                    self.tool_calls.append(ai_message.model_dump())
                    for tool_call in tool_calls:
                        msg = f"\n\nCalling tool: `{tool_call['name']}` with args: `{tool_call['args']}`"
                    self.stream_handler.new_status(msg)
                elif content := message["kwargs"].get("content"):
                    # Handle AI response
                    self.final_content += content
                    self.stream_handler.new_token(content)
                        
            # Handle tool response events
            elif "tools" in event:
                for tool_message in event["tools"]["messages"]:
                    content = tool_message["kwargs"]["content"]
                    tool_call_id = tool_message["kwargs"]["tool_call_id"]
                    tool_message = ToolMessage(
                        content=content,
                        type="tool",
                        tool_call_id=tool_call_id
                    ).model_dump()
                    self.tool_calls.append(tool_message)
                    msg = f"\n\nTool response: `{content}`"
                    self.stream_handler.new_status(msg)

        # Handle end of stream
        if self.final_content:
            final_message = AIMessage(
                content=self.final_content,
                id=self.current_run_id,
                additional_kwargs=self.additional_kwargs,
            ).model_dump()
            session = self.st.session_state["session_id"]
            self.st.session_state.user_chats[session]["messages"] = (
                self.st.session_state.user_chats[session]["messages"] + self.tool_calls
            )
            self.st.session_state.user_chats[session]["messages"].append(final_message)
            self.st.session_state.run_id = self.current_run_id


def get_chain_response(st: Any, client: Client, stream_handler: StreamHandler) -> None:
    """Process the chain response update the Streamlit UI.

    This function initiates the event processing for a chain of operations,
     involving an AI model's response generation and potential tool calls.
    It creates an EventProcessor instance and starts the event processing loop.

    Args:
        st (Any): The Streamlit app instance, used for accessing session state
                        and updating the UI.
        client (Client): An instance of the Client class used to stream events
                         from the server.
        stream_handler (StreamHandler): An instance of the StreamHandler class
                                        used to update the Streamlit UI with
                                        streaming content.

    Returns:
        None

    Side effects:
        - Updates the Streamlit UI with streaming tokens and tool call information.
        - Modifies the session state to include the final AI message and run ID.
        - Handles various events like chain starts/ends, tool calls, and model outputs.
    """
    processor = EventProcessor(st, client, stream_handler)
    processor.process_events()
