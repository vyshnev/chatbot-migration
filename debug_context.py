import requests
import uuid
import json

BASE_URL = "http://localhost:8000"

def test_context():
    thread_id = str(uuid.uuid4())
    print(f"Testing with Thread ID: {thread_id}")
    
    # Turn 1
    print("\n--- Turn 1: My name is Alice ---")
    payload1 = {"message": "My name is Alice", "thread_id": thread_id}
    response1 = requests.post(f"{BASE_URL}/chat", json=payload1, stream=True)
    
    full_response1 = ""
    for line in response1.iter_lines():
        if line:
            data = json.loads(line)
            if data['type'] == 'chunk':
                full_response1 += data['content']
    print(f"Bot: {full_response1}")

    # Turn 2
    print("\n--- Turn 2: What is my name? ---")
    payload2 = {"message": "What is my name?", "thread_id": thread_id}
    response2 = requests.post(f"{BASE_URL}/chat", json=payload2, stream=True)
    
    full_response2 = ""
    for line in response2.iter_lines():
        if line:
            data = json.loads(line)
            if data['type'] == 'chunk':
                full_response2 += data['content']
    print(f"Bot: {full_response2}")
    
    if "Alice" in full_response2:
        print("\nSUCCESS: Context retained.")
    else:
        print("\nFAILURE: Context lost.")

if __name__ == "__main__":
    test_context()
