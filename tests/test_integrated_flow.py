import pytest
from app import basic_maths
from app.api_client import AIClient

class MockAIClient:
    def send_message(self, messages):
        # Verify that we receive a list of messages (history)
        if not isinstance(messages, list):
            return "Error: expected list of messages"
        
        # Simple mock logic: if the user asks about 'after class 10', mention 'Engineering'
        last_msg = messages[-1]["content"].lower()
        if "after class 10" in last_msg:
            return "After Class 10, you can choose Science (PCM) for Engineering or Medical. I recommend looking at JEE."
        return "I am your Academic Advisor. How can I help with your maths or career?"

def test_generate_math_reply_multi_turn():
    profile = {
        "student_name": "Rahul",
        "grade": "Class 10",
        "board": "CBSE",
        "goal": "Exam prep",
        "weak_topics": ["algebra"],
    }
    mock_client = MockAIClient()
    
    # turn 1
    messages = [{"role": "user", "content": "Hi, I am Rahul."}]
    reply1 = basic_maths.generate_math_reply(messages, profile, ai_client=mock_client)
    assert "Advisor" in reply1
    
    # turn 2 (with history)
    messages.append({"role": "assistant", "content": reply1})
    messages.append({"role": "user", "content": "What should I do after Class 10?"})
    
    reply2 = basic_maths.generate_math_reply(messages, profile, ai_client=mock_client)
    assert "Science" in reply2 or "JEE" in reply2

def test_generate_math_reply_system_prompt_structure(mocker):
    # Verify that the system prompt sent to the AI client is structured as expected
    profile = {"student_name": "Rahul", "grade": "Class 10", "board": "CBSE", "goal": "Exam prep"}
    mock_ai = mocker.Mock(spec=AIClient)
    mock_ai.send_message.return_value = "Mocked Response"
    
    messages = [{"role": "user", "content": "Hello"}]
    basic_maths.generate_math_reply(messages, profile, ai_client=mock_ai)
    
    # Check the call arguments
    args, _ = mock_ai.send_message.call_args
    sent_messages = args[0]
    
    assert sent_messages[0]["role"] == "system"
    assert "SHAPERS Academic Advisor" in sent_messages[0]["content"]
    assert "Student Profile:" in sent_messages[0]["content"]
    assert sent_messages[1] == messages[0]
