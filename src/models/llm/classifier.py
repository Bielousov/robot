from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are classifying speech for a robot named {Name}.\n\n"

        "Output exactly one of:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        f"respond with ADDRESSED only when the '{Name}' was present in the request\n\n"

        "AMBIGUOUS means the utterance is a question, request, command, "
        "or other meaningful speech where the intended listener is unknown. "
        "The robot could be the listener, but there is no evidence "
        "identifying the robot as the listener.\n\n"

        "NOT_ADDRESSED means the utterance is clearly an ordinary statement, "
        "aside, fragment, unrelated speech, or gibberish rather than an "
        "attempt to address the robot.\n\n"

        "Examples:\n"
        "'pip what is your name' -> ADDRESSED\n"
        "'what is your name' -> AMBIGUOUS\n"
        "'what time is it' -> AMBIGUOUS\n"
        "'tell me a joke' -> AMBIGUOUS\n"
        "'can you help me' -> AMBIGUOUS\n"
        "'read me a book' -> AMBIGUOUS\n"
        "'what should we do' -> AMBIGUOUS\n"
        "'who are you' -> AMBIGUOUS\n\n"

        "'pip the dog is outside' -> ADDRESSED\n"
        "'the dog is outside' -> NOT_ADDRESSED\n"
        "'dinner is almost ready' -> NOT_ADDRESSED\n"
        "'i think it will rain' -> NOT_ADDRESSED\n"
        "'that movie was really good' -> NOT_ADDRESSED\n"
        "'the package should arrive today' -> NOT_ADDRESSED\n"
        "'someone is calling' -> NOT_ADDRESSED\n"
        "'i forgot to buy milk' -> NOT_ADDRESSED\n"
        "'chips' -> NOT_ADDRESSED\n"
        "'specialized hardware' -> NOT_ADDRESSED\n"
        "'purple seven window banana' -> NOT_ADDRESSED\n\n"

        "CRITICAL:\n"
        "Do not assume that a question or request is addressed to the robot "
        "just because the robot could answer it.\n"
        "Do not infer a listener from the subject matter.\n"
        "Do not explain your decision.\n"
        "Output ONLY ADDRESSED, AMBIGUOUS or NOT_ADDRESSED."
    )