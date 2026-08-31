def build_conversation_classifier_prompt() -> str:
    return (
        "You classify spoken sentences for a robot named Pip.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        "YES means the speaker is talking TO Pip.\n"
        "NO means the speaker is not talking to Pip.\n\n"

        "IMPORTANT CLASSIFICATION RULES:\n\n"

        "1. If the speaker directly uses the name 'Pip' to get the robot's "
        "attention or talk to the robot, strongly favor YES.\n"
        "The presence of 'Pip' as a direct form of address is strong evidence "
        "that Pip is the intended listener.\n\n"

        "2. If the speaker asks a question, gives a command, makes a request, "
        "or speaks conversationally without naming the listener, the intended "
        "listener is unknown. This should be substantially less certain than "
        "an otherwise equivalent sentence that explicitly says 'Pip'.\n\n"

        "3. Do not treat an unnamed question as evidence that the speaker is "
        "NOT talking to Pip. It is simply unknown whether Pip is the listener.\n\n"

        "4. Meaningless or obviously corrupted speech should strongly favor NO.\n\n"

        "5. Do not answer the question. Do not explain your decision.\n\n"

        "Examples:\n"
        "Pip what time is it now -> YES\n"
        "Pip what is your name -> YES\n"
        "Pip what are you doing -> YES\n"
        "Pip tell me about your hardware -> YES\n"
        "Pip tell me a joke -> YES\n"
        "Hey Pip -> YES\n\n"

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