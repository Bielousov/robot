from config import Name


def build_conversation_classifier_prompt(request: str) -> str:
    return (
        "Candidate intents:\n"
        "ADDRESSED: the speaker is directly talking to the robot Pip; "
        "the robot's name is explicitly spoken in the request.\n"
        "AMBIGUOUS: the request could reasonably be directed at Pip, "
        "but the robot's name is not explicitly spoken.\n"
        "NOT_ADDRESSED: the speaker is clearly talking about something "
        "else or is not addressing the robot.\n\n"
        f"User message: {request}\n\n"
        "Answer with exactly one intent name from the list above."
    )
