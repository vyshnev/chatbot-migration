import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from agent.graph import chat_node

# All tests pass a config dict. Tests that don't need thread-scoped RAG
# pass an empty configurable dict so document_rag is never called.
EMPTY_CONFIG = {"configurable": {}}


# ---------------------------------------------------------------------------
# Existing behaviour — tool routing
# ---------------------------------------------------------------------------

@patch("agent.graph.document_rag")
@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_agent_routes_to_tools(mock_memory, mock_llm, mock_doc_rag):
    """Verify that if the LLM decides to use a tool, it outputs an AIMessage with tool_calls."""
    mock_memory.get_all_memories.return_value = ""
    mock_doc_rag.search_thread_documents.return_value = ""

    fake_tool_call = {
        "name": "search_tool",
        "args": {"query": "test query"},
        "id": "call_123"
    }
    mock_llm.invoke.return_value = AIMessage(
        content="",
        tool_calls=[fake_tool_call]
    )

    state = {"messages": [HumanMessage(content="Search the web for test query")]}
    result = chat_node(state, EMPTY_CONFIG)

    response_msg = result["messages"][0]
    assert isinstance(response_msg, AIMessage)
    assert len(response_msg.tool_calls) == 1
    assert response_msg.tool_calls[0]["name"] == "search_tool"


@patch("agent.graph.document_rag")
@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_agent_responds_directly(mock_memory, mock_llm, mock_doc_rag):
    """Verify that if the LLM just answers, it outputs standard text with no tool_calls."""
    mock_memory.get_all_memories.return_value = ""
    mock_doc_rag.search_thread_documents.return_value = ""

    mock_llm.invoke.return_value = AIMessage(
        content="Hello! How can I help you today?"
    )

    state = {"messages": [HumanMessage(content="Hi")]}
    result = chat_node(state, EMPTY_CONFIG)

    response_msg = result["messages"][0]
    assert isinstance(response_msg, AIMessage)
    assert not getattr(response_msg, "tool_calls", None)
    assert response_msg.content == "Hello! How can I help you today?"


# ---------------------------------------------------------------------------
# New behaviour — PDF document context injection
# ---------------------------------------------------------------------------

@patch("agent.graph.document_rag")
@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_chat_node_injects_doc_context_when_thread_has_uploads(
    mock_memory, mock_llm, mock_doc_rag
):
    """
    When search_thread_documents returns a non-empty string,
    the SystemMessage content passed to the LLM must contain the PDF context.
    """
    mock_memory.get_all_memories.return_value = ""
    mock_doc_rag.search_thread_documents.return_value = (
        "[From: report.pdf]\nRevenue was $5M in Q4 2024."
    )
    mock_llm.invoke.return_value = AIMessage(content="Based on report.pdf, revenue was $5M.")

    state = {"messages": [HumanMessage(content="What was the Q4 revenue?")]}
    config = {"configurable": {"thread_id": "thread-xyz"}}

    result = chat_node(state, config)

    # doc_rag was called with the correct thread + query
    mock_doc_rag.search_thread_documents.assert_called_once_with(
        "thread-xyz", "What was the Q4 revenue?"
    )

    # The SystemMessage sent to the LLM includes the doc context
    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = call_args[0]
    assert isinstance(system_msg, SystemMessage)
    assert "report.pdf" in system_msg.content
    assert "Revenue was $5M" in system_msg.content


@patch("agent.graph.document_rag")
@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_chat_node_no_doc_context_when_thread_has_no_uploads(
    mock_memory, mock_llm, mock_doc_rag
):
    """
    When search_thread_documents returns an empty string (no uploads),
    the system prompt must NOT contain the 'Uploaded Documents' section.
    """
    mock_memory.get_all_memories.return_value = ""
    mock_doc_rag.search_thread_documents.return_value = ""
    mock_llm.invoke.return_value = AIMessage(content="Paris is the capital of France.")

    state = {"messages": [HumanMessage(content="Capital of France?")]}
    config = {"configurable": {"thread_id": "thread-empty"}}

    result = chat_node(state, config)

    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = call_args[0]
    assert isinstance(system_msg, SystemMessage)
    assert "Uploaded Documents" not in system_msg.content


@patch("agent.graph.document_rag")
@patch("agent.graph.llm_with_tools")
@patch("agent.graph.memory_service")
def test_chat_node_does_not_call_doc_rag_without_thread_id(
    mock_memory, mock_llm, mock_doc_rag
):
    """
    When config has no thread_id, search_thread_documents must NOT be called.
    """
    mock_memory.get_all_memories.return_value = ""
    mock_llm.invoke.return_value = AIMessage(content="Answer.")

    state = {"messages": [HumanMessage(content="Hello")]}

    result = chat_node(state, EMPTY_CONFIG)

    mock_doc_rag.search_thread_documents.assert_not_called()
