import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage, HumanMessage
from agent.graph import chat_node

@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_agent_routes_to_tools(mock_memory, mock_llm):
    """Verify that if the LLM decides to use a tool, it outputs an AIMessage with tool_calls."""
    # Mock memory so it doesn't try to read the real DB
    mock_memory.get_all_memories.return_value = ""
    
    # Mock the LLM deciding it needs to use the web search tool
    fake_tool_call = {
        "name": "search_tool",
        "args": {"query": "test query"},
        "id": "call_123"
    }
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[fake_tool_call]
    )
    
    # Simulate LangGraph passing the user message to the chat_node
    state = {"messages": [HumanMessage(content="Search the web for test query")]}
    result = chat_node(state)
    
    # Verify that the node successfully generated the tool call payload
    response_msg = result["messages"][0]
    assert isinstance(response_msg, AIMessage)
    assert len(response_msg.tool_calls) == 1
    assert response_msg.tool_calls[0]["name"] == "search_tool"

@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_agent_responds_directly(mock_memory, mock_llm):
    """Verify that if the LLM just answers, it outputs standard text with no tool_calls."""
    mock_memory.get_all_memories.return_value = ""
    
    mock_llm.invoke.return_value = AIMessage(
        content="Hello! How can I help you today?"
    )
    
    state = {"messages": [HumanMessage(content="Hi")]}
    result = chat_node(state)
    
    response_msg = result["messages"][0]
    assert isinstance(response_msg, AIMessage)
    assert not getattr(response_msg, "tool_calls", None)
    assert response_msg.content == "Hello! How can I help you today?"
