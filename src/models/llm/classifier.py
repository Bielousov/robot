from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are classifying speech for a robot named {Name}.\n\n"

        "Output exactly one of:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        f"Respond ADDRESSED when and only when robot name ('{Name}') is present in the request, \n"
        "do not consider other response rules in this case.\n\n"

        "AMBIGUOUS means the utterance is a question, request, command, "
        "or other meaningful speech where the intended listener is unknown. "
        "The robot could be the listener, but there is no evidence "
        "identifying the robot as the listener.\n\n"

        "NOT_ADDRESSED means the utterance is clearly an ordinary statement, "
        "aside, fragment, unrelated speech, or gibberish rather than an "
        "attempt to address the robot.\n\n"

        "CRITICAL:\n"
        "Do not assume that a question or request is addressed to the robot "
        "just because the robot could answer it.\n"
        "Do not infer a listener from the subject matter.\n"
        "Do not explain your decision.\n"
        "Output ONLY ADDRESSED, AMBIGUOUS or NOT_ADDRESSED."
    )