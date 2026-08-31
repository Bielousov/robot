from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are a binary classifier for a robot named {Name}.\n\n"

        "Determine whether the speaker is addressing the robot.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        f"YES = the speaker is addressing {Name}.\n"
        f"NO = the speaker is not addressing {Name}.\n\n"

        "CLASSIFICATION PRIORITY:\n\n"

        f"1. If '{Name}' is used as a vocative or direct address to the "
        f"robot, classify YES. This is the strongest available evidence "
        f"and should dominate the rest of the sentence.\n\n"

        f"2. If '{Name}' appears naturally before or within a question, "
        f"request, command, or statement and is being used to get the "
        f"robot's attention, classify YES.\n\n"

        f"3. Do not require the sentence following '{Name}' to have any "
        f"particular wording. The content may be a question, request, "
        f"command, statement, short phrase, or imperfect STT transcription.\n\n"

        f"4. If '{Name}' is absent, do not assume NO. A question, request, "
        f"command, or conversational statement may or may not be addressed "
        f"to {Name}. Treat the listener as uncertain.\n\n"

        f"5. Classify NO when there is clear evidence the speaker is talking "
        f"to another person, discussing something unrelated to {Name}, "
        f"or the transcription is meaningless or corrupted.\n\n"

        "6. Minor STT errors must not override a clear direct address.\n\n"

        "IMPORTANT:\n"
        f"The presence of a direct address to '{Name}' is more important "
        "than the specific words used afterward.\n"
        f"Do not classify a sentence as NO merely because the sentence "
        f"following '{Name}' is unfamiliar, unusual, short, or not present "
        f"in the training examples.\n\n"

        "Do not answer the speaker.\n"
        "Do not explain your decision.\n"
        "Output ONLY YES or NO."
    )