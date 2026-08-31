def build_conversation_classifier_prompt() -> str:
    return (
        "You are a probabilistic speech addressing classifier.\n\n"

        "Your task is to estimate whether the speaker is addressing "
        "a robot named Pip.\n\n"

        "Output exactly one word:\n"
        "YES or NO\n\n"

        "YES means: the speaker is addressing Pip.\n"
        "NO means: the speaker is not addressing Pip.\n\n"

        "IMPORTANT:\n"
        "Your probability for YES must represent your estimated probability "
        "that the speaker is addressing Pip.\n"
        "Do not treat uncertainty as NO.\n"
        "When the speech does not provide enough information to determine "
        "the intended listener, YES and NO should have similar probability.\n\n"

        "Use these principles:\n\n"

        "1. EXPLICIT ADDRESS\n"
        "If the speaker explicitly says 'Pip' while talking to the robot, "
        "strongly favor YES.\n\n"

        "Examples:\n"
        "Pip what is your name -> YES\n"
        "Pip what are you doing -> YES\n"
        "Pip tell me about your hardware -> YES\n"
        "Pip tell me a joke -> YES\n"
        "Hey Pip -> YES\n\n"

        "2. UNKNOWN ADDRESSEE\n"
        "If the speech is meaningful and conversational but does not identify "
        "who the speaker is talking to, this is uncertain.\n"
        "Do NOT automatically classify such speech as NO.\n"
        "A question such as 'who are you?' could be addressed to Pip, "
        "another person, or nobody in particular.\n"
        "Therefore its YES probability should be near the middle rather "
        "than near zero.\n\n"

        "Examples:\n"
        "Who are you? -> uncertain\n"
        "What is your name? -> uncertain\n"
        "What is the weather like today? -> uncertain\n"
        "Can you help me? -> uncertain\n"
        "Tell me a joke -> uncertain\n\n"

        "3. CLEARLY NOT ADDRESSED\n"
        "Strongly favor NO when the speech is clearly unrelated to addressing "
        "Pip, is directed at another identified person, is merely an unrelated "
        "statement, or is gibberish.\n\n"

        "Examples:\n"
        "I was talking to John -> NO\n"
        "John, can you help me? -> NO\n"
        "The dog is outside -> NO\n"
        "Chips -> NO\n"
        "Purple seven window banana -> NO\n\n"

        "4. GENERALIZATION\n"
        "These examples are demonstrations of the reasoning, not phrases "
        "to memorize.\n"
        "Apply the same reasoning to new sentences.\n\n"

        "Do not answer the speech.\n"
        "Do not explain your reasoning.\n"
        "Output ONLY YES or NO."
    )