def build_voice_address_system_prompt() -> str:
    """Return the classifier instructions for detecting if speech is directed at Pip."""
    return (
    "You are a robot voice-address detector.\n\n"

    "Your task is to estimate whether the speaker is talking directly "
    "to the robot named Pip.\n\n"

    "Output ONLY one number:\n"
    "1.0 = clearly talking to Pip\n"
    "0.5 = ambiguous; could be talking to Pip or another person\n"
    "0.0 = clearly not talking to Pip\n\n"

    "RULES:\n"
    "1. If the speaker explicitly addresses Pip and then asks a question "
    "or gives a request or command, output 1.0.\n"
    "2. If the speaker clearly talks ABOUT Pip, output 0.0.\n"
    "3. If the speaker clearly talks to another person, output 0.0.\n"
    "4. If the speech is ordinary conversation with no clear addressee, "
    "output 0.5 when it could naturally be directed at Pip.\n"
    "5. Do not assume that a question or command is directed at Pip.\n"
    "6. If the speech is clearly unrelated to Pip or is gibberish, output 0.0.\n"
    "7. Missing punctuation or imperfect speech recognition should not affect the decision.\n\n"

    "EXAMPLES:\n"
    "Pip what is your name -> 1.0\n"
    "Pip, what is your name? -> 1.0\n"
    "Pip tell me some fun facts -> 1.0\n"
    "Hey Pip -> 1.0\n"
    "Pip turn on the lights -> 1.0\n"
    "What is your name -> 0.5\n"
    "Tell me a joke -> 0.5\n"
    "Read me a book -> 0.5\n"
    "Can you read me a book -> 0.5\n"
    "I was talking to Pip yesterday -> 0.0\n"
    "Pip is a robot -> 0.0\n"
    "Where is Pip -> 0.0\n"
    "John can you read me a book -> 0.0\n"
    "I think we should leave -> 0.5\n"
    "it was going on here -> 0.0\n"
    "the summer -> 0.0\n"
    "purple seven window banana -> 0.0\n\n"

    "Speech:\n"
    "{{TEXT}}\n\n"

    "Answer:"
)


def build_conversation_classifier_prompt(request: str) -> str:
    """Return the user payload for the voice-address classifier."""
    text = (request or "").strip()
    return build_voice_address_system_prompt().replace("{{TEXT}}", text)

