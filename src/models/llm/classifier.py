from config import Name

def build_conversation_classifier_prompt() -> str:
    return (
        f"You identify the intended listener of spoken speech for a robot named {Name}.\n\n"

        "Output exactly one class:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        "This is NOT a task classification problem.\n"
        "Do not decide whether the speaker wants information, is making a "
        "request, or is saying something meaningful.\n"
        "Decide only whether the speaker is addressing the robot.\n\n"

        "CLASS DEFINITIONS:\n\n"

        "ADDRESSED:\n"
        f"The speech contains evidence that {Name} is the intended listener.\n"
        f"The strongest evidence is an explicit direct address using '{Name}'.\n"
        f"When '{Name}' is used as a vocative or attention-getting name, "
        f"classify as ADDRESSED.\n"
        f"'{Name}' remains the intended listener even if the rest of the "
        "utterance is short, unusual, incomplete, or contains STT errors.\n\n"

        "AMBIGUOUS:\n"
        "The speech is meaningful and could reasonably be addressed to the "
        "robot, but there is no evidence identifying the robot as the listener.\n"
        "The speaker may be talking to the robot, a human, or nobody in "
        "particular.\n"
        "Do NOT infer the listener from the subject of the question or request.\n"
        "A question, command, request, or statement by itself is NOT evidence "
        "that the robot is being addressed.\n\n"

        "NOT_ADDRESSED:\n"
        "There is evidence that the speech is not directed to the robot, "
        "or the utterance is clearly an incidental statement rather than "
        "communication directed toward the robot.\n"
        "Meaningless, nonsensical, or severely corrupted speech should also "
        "be classified as NOT_ADDRESSED.\n\n"

        "IMPORTANT DECISION ORDER:\n\n"

        f"1. Is '{Name}' clearly being used to address the robot?\n"
        "   YES -> ADDRESSED.\n\n"

        "2. Is there positive evidence that the speaker is addressing "
        "someone else, or that this is merely an incidental statement?\n"
        "   YES -> NOT_ADDRESSED.\n\n"

        "3. Otherwise, is the speech meaningful but the intended listener "
        "cannot be determined?\n"
        "   YES -> AMBIGUOUS.\n\n"

        "Do not infer ADDRESSED merely because:\n"
        "- the utterance is a question\n"
        "- the utterance is a command\n"
        "- the utterance asks for help\n"
        "- the utterance concerns information the robot could provide\n"
        "- the utterance concerns the robot's capabilities\n"
        "- the utterance sounds conversational\n\n"

        f"Do not infer ADDRESSED merely because the subject could be relevant "
        f"to {Name}.\n\n"

        "ATTENTION WORDS:\n"
        "'hey' indicates an attempt to get someone's attention.\n"
        f"If 'hey' is followed by '{Name}', classify ADDRESSED.\n"
        "If 'hey' is followed by meaningful speech without a named listener, "
        "treat the utterance as ambiguous unless other evidence identifies "
        "the robot as the listener.\n\n"

        "STT ERRORS:\n"
        f"If '{Name}' is recognizable as a direct address despite minor "
        "transcription errors, classify ADDRESSED.\n"
        "Do not allow minor errors elsewhere in the utterance to override "
        "an explicit address.\n\n"

        "GIBBERISH:\n"
        "Do not invent meaning or a listener.\n"
        "Clearly nonsensical or corrupted speech is NOT_ADDRESSED.\n\n"

        "Output ONLY one of:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED"
    )