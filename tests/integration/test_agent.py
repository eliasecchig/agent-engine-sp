# pylint: disable=R0801

import logging
import os

from app.agent_engine_app import AgentEngineApp
import pytest

@pytest.fixture
def agent_app():
    """Fixture to create and set up AgentEngineApp instance"""
    app = AgentEngineApp()
    app.set_up()
    return app

def test_agent_stream_query(agent_app):
    """
    Integration test for the agent stream query functionality.
    Tests that the agent returns valid streaming responses.
    """
    input_dict = {
        "messages": [
            {"type": "human", "content": "Test message"},
        ],
        "user_id": "test-user",
        "session_id": "test-session"
    }

    chunks = list(agent_app.stream_query(input=input_dict))

    assert len(chunks) > 0, "Expected at least one chunk in response"

    for chunk in chunks:
        assert isinstance(chunk, dict), f"Expected dict chunk, got {type(chunk)}"
        # The chunk structure includes nested agent messages
        assert any(key in chunk for key in ["agent", "tools"]), f"Expected agent or tool in chunk, got {chunk}"
        
    logging.info("All assertions passed for agent stream query test")

def test_agent_query(agent_app):
    """
    Integration test for the agent query functionality.
    Tests that the agent returns valid responses.
    """
    input_dict = {
        "messages": [
            {"type": "human", "content": "Test message"},
        ],
        "user_id": "test-user", 
        "session_id": "test-session"
    }

    response = agent_app.query(input=input_dict)
    
    # Basic response validation
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "messages" in response, "Response should contain messages"
    assert len(response["messages"]) > 0, "Response should have at least one message"

    # Validate last message is AI response with content
    message = response["messages"][-1]
    kwargs = message["kwargs"]
    assert kwargs["type"] == "ai", "Last message should be AI response"
    assert len(kwargs["content"]) > 0, "AI message content should not be empty"

    logging.info("All assertions passed for agent query test")

def test_agent_feedback(agent_app):
    """
    Integration test for the agent feedback functionality.
    Tests that feedback can be registered successfully.
    """
    feedback_data = {
        "score": 5,
        "text": "Great response!",
        "run_id": "test-run-123",
    }

    # Should not raise any exceptions
    agent_app.register_feedback(feedback_data)

    # Test invalid feedback
    with pytest.raises(ValueError):
        invalid_feedback = {
            "score": "invalid",  # Score must be numeric
            "text": "Bad feedback",
            "run_id": "test-run-123"
        }
        agent_app.register_feedback(invalid_feedback)

    logging.info("All assertions passed for agent feedback test")