from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You classify spoken sentences for a robot named {Name}.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        f"YES means the speaker is talking TO {Name}.\n"
        f"NO means the speaker is not talking to {Name}.\n\n"

        "IMPORTANT CLASSIFICATION RULES:\n\n"

        "1. EXPLICIT ADDRESS:\n"
        f"If the speaker uses the name '{Name}' as a direct form of address, "
        f"this is strong evidence that {Name} is the intended listener.\n"
        f"When '{Name}' appears naturally at the beginning of a question, request, "
        f"or command, strongly favor YES.\n"
        f"The presence of a direct address such as '{Name}' should substantially "
        f"increase your confidence compared with the same utterance without "
        f"'{Name}'.\n\n"

        "2. If the speaker asks a question, gives a command, makes a request, "
        "or speaks conversationally without naming the listener, the intended "
        "listener is unknown. This should be substantially less certain than "
        f"an otherwise equivalent sentence that explicitly says '{Name}'.\n\n"

        "3. Do not treat an unnamed question as evidence that the speaker is "
        f"NOT talking to {Name}. It is simply unknown whether {Name} is the listener.\n\n"

        "4. Meaningless or obviously corrupted speech should strongly favor NO.\n\n"

        "5. Do not answer the question. Do not explain your decision.\n\n"

        "6. ADDRESSING TAKES PRIORITY OVER MINOR STT ERRORS:\n"
        f"If '{Name}' is clearly being used as a direct address, favor YES even "
        "if the rest of the transcription contains minor grammatical errors, "
        "missing words, or imperfect speech recognition.\n"
        "Do not let a small wording error override an otherwise clear direct "
        f"address to {Name}.\n\n"

        "Examples:\n"
        f"{Name} what time is it now -> YES\n"
        f"{Name} what is your name -> YES\n"
        f"{Name} what are you doing -> YES\n"
        f"{Name} tell me about your hardware -> YES\n"
        f"{Name} tell me a joke -> YES\n"
        f"Hey {Name} -> YES\n\n"

        "What time is it now -> uncertain\n"
        "What is your name -> uncertain\n"
        "Who are you -> uncertain\n"
        "What are you doing -> uncertain\n"
        "Tell me a joke -> uncertain\n"
        "Can you help me -> uncertain\n\n"

        "Chips -> NO\n"
        "The dog is outside -> NO\n"
        "I think it will rain -> NO\n"
        "Purple seven window banana -> NO\n\n"

        "For new sentences, apply the rules rather than matching exact examples.\n"
        "Output ONLY YES or NO."
    )