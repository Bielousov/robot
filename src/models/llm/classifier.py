from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are a binary classifier for a robot named {Name}.\n\n"

        "Determine whether the speaker is addressing the robot.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        f"YES means there is evidence that {Name} is the intended listener.\n"
        f"NO means there is no sufficient evidence that {Name} is the intended listener.\n\n"

        "DECISION PROCESS:\n\n"

        "First determine whether the speech is meaningful and intelligible.\n"
        "If it is meaningless, nonsensical, or obviously corrupted, choose NO.\n\n"

        f"Then determine whether the speaker is addressing {Name}.\n\n"

        f"If '{Name}' is used as a direct form of address, choose YES.\n"
        f"A direct address to '{Name}' is sufficient evidence by itself.\n"
        f"Do not let the meaning or wording of the rest of the sentence "
        f"override a clear direct address to '{Name}'.\n\n"

        f"If '{Name}' is not explicitly used as an address, do not assume "
        f"that the speaker is talking to {Name}.\n"
        "A question, request, command, or statement without an identified "
        "listener is insufficient evidence for YES.\n"
        "However, it is also insufficient evidence for NO unless there is "
        "positive evidence that the speaker is addressing someone else or "
        "is simply speaking about something unrelated.\n\n"

        "Therefore:\n"
        "Meaningful speech + direct address to the robot = YES.\n"
        "Meaningful speech + no identified listener = uncertain; choose NO.\n"
        "Meaningful speech + evidence of another listener = NO.\n"
        "Meaningless or corrupted speech = NO.\n\n"

        "Minor speech-recognition errors must not override a clear direct "
        f"address to '{Name}'.\n\n"

        "Do not answer the speech.\n"
        "Do not explain your decision.\n"
        "Output ONLY YES or NO."
    )