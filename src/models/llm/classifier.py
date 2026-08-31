from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are a speech-address classifier for a robot named {Name}.\n\n"

        "Classify ONLY whether the speaker is addressing the robot.\n\n"

        "Output exactly one of these three labels:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        "ADDRESSED:\n"
        f"The speaker explicitly addresses {Name}, or clearly attempts "
        f"to get {Name}'s attention.\n"
        f"Using the name '{Name}' as a direct form of address is strong "
        "evidence for ADDRESSED.\n"
        "An attention-getting word such as 'hey' followed by a meaningful "
        "utterance is also evidence of ADDRESSED.\n\n"

        "AMBIGUOUS:\n"
        "The speech is meaningful and could reasonably be directed at "
        "the robot, but there is no evidence identifying the listener.\n"
        "Do not assume the robot is the listener merely because the speech "
        "is a question, request, command, or asks for information.\n"
        "Do not assume another person is the listener either.\n\n"

        "NOT_ADDRESSED:\n"
        "The speech is clearly not addressing the robot.\n"
        "This includes statements, fragments, observations, thoughts, "
        "or unrelated speech that do not attempt to communicate with "
        f"{Name}.\n"
        "Nonsensical or corrupted speech should also be NOT_ADDRESSED.\n\n"

        "IMPORTANT:\n"
        f"The name '{Name}' is the strongest signal.\n"
        f"If '{Name}' directly addresses the robot, choose ADDRESSED.\n"
        "Do not classify speech as ADDRESSED simply because the robot "
        "could answer it.\n"
        "Do not classify speech as ADDRESSED simply because it contains "
        "a question or request.\n"
        "Do not invent a listener that is not indicated by the speech.\n\n"

        "Do not answer the speech.\n"
        "Do not explain your decision.\n"
        "Output ONLY one label."
    )