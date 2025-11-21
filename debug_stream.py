from langgraph_tool_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

thread_id = str(uuid.uuid4())
config = {
    'configurable': {'thread_id': thread_id},
    "metadata": {"thread_id": thread_id},
    "run_name": "chat_turn"
}

print(f"Debug Stream for Thread: {thread_id}")
print("-" * 50)

try:
    for message_chunk, metadata in chatbot.stream(
        {'messages': [HumanMessage(content="What is the latest stock price of Google?")]},
        config=config,
        stream_mode='messages'
    ):
        print(f"Type: {type(message_chunk)}")
        if isinstance(message_chunk, AIMessage):
            print(f"Content: {repr(message_chunk.content)}")
            print(f"ID: {message_chunk.id}")
        else:
            print(f"Chunk: {message_chunk}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
