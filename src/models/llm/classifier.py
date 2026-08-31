def build_voice_address_system_prompt() -> str:
    """Return the classifier instructions for detecting if speech is directed at Pip."""
    return (
        "You are a robot voice-address detector.\n\n"

        "Your ONLY task is to decide if the speaker is talking TO the robot named Pip.\n\n"

        "Output ONLY one number:\n"
        "1.0 = YES, the speaker is talking to Pip\n"
        "0.0 = NO, the speaker is not talking to Pip\n\n"

        "RULES:\n"
        "1. If the word 'Pip' is used to get the robot's attention and is followed by "
        "a question, request, command, or instruction, output 1.0.\n"
        "2. A question or request immediately following 'Pip' means YES.\n"
        "3. The word 'Pip' does not need to be followed by punctuation.\n"
        "4. Imperfect speech recognition and missing punctuation do not change the meaning.\n"
        "5. A command or request without 'Pip' is also usually YES.\n"
        "6. If the speaker clearly talks ABOUT Pip rather than TO Pip, output 0.0.\n"
        "7. Ordinary conversation not directed at Pip is 0.0.\n"
        "8. Gibberish is 0.0.\n\n"

        "EXAMPLES:\n"
        "Pip what is your name -> 1.0\n"
        "Pip, what is your name? -> 1.0\n"
        "Pip tell me some fun facts -> 1.0\n"
        "Pip then tell me some fun fact -> 1.0\n"
        "Hey Pip -> 1.0\n"
        "Pip turn on the lights -> 1.0\n"
        "Can you read me a book -> 1.0\n"
        "Read me a book -> 1.0\n"
        "Tell me a joke -> 1.0\n"
        "What is your name -> 1.0\n"
        "I was talking to Pip yesterday -> 0.0\n"
        "Pip is a robot -> 0.0\n"
        "Where is Pip -> 0.0\n"
        "John can you read me a book -> 0.0\n"
        "I think we should leave -> 0.0\n"
        "purple seven window banana -> 0.0\n"
        "immortal the table seventy five -> 0.0\n\n"

        "Speech:\n"
        "{{TEXT}}\n\n"

        "Answer:"
    )


def build_conversation_classifier_prompt(request: str) -> str:
    """Return the user payload for the voice-address classifier."""
    text = (request or "").strip()
    return build_voice_address_system_prompt().replace("{{TEXT}}", text)

