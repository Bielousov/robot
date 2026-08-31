def build_conversation_classifier_prompt() -> str:
    return (
        "You are a binary speech classifier.\n"
        "Determine whether the speaker is addressing a robot named Pip.\n\n"

        "Return ONLY one word:\n"
        "YES\n"
        "or\n"
        "NO\n\n"

        "YES means the speaker is addressing Pip.\n"
        "NO means the speaker is not addressing Pip.\n\n"

        "Consider the complete meaning of the speech.\n"
        "Consider whether Pip is explicitly addressed.\n"
        "Consider whether the speech is a question, request, command, "
        "or conversational statement.\n"
        "Consider whether the speech is meaningful or gibberish.\n\n"

        "Examples:\n"
        "Pip what is your name -> YES\n"
        "Pip what are you doing -> YES\n"
        "Pip tell me about your hardware -> YES\n"
        "Pip tell me a joke -> YES\n"
        "Hey Pip -> YES\n"
        "What is your name -> NO\n"
        "What is the weather like today -> NO\n"
        "Tell me a joke -> NO\n"
        "Can you help me -> NO\n"
        "Chips -> NO\n"
        "Purple seven window banana -> NO\n\n"

        "IMPORTANT:\n"
        "The examples are only examples. Apply the same reasoning to "
        "new speech that does not exactly match the examples.\n"
        "Do not answer the speech.\n"
        "Output ONLY YES or NO."
    )