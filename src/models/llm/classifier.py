from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You classify spoken sentences for a robot named {Name}.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        f"YES means the speaker is talking TO {Name}.\n"
        f"NO means the speaker is NOT talking to {Name}.\n\n"

        "IMPORTANT CLASSIFICATION RULES:\n\n"

        "1. EXPLICIT ADDRESS:\n"
        f"When '{Name}' is used as a direct form of address, this is strong "
        f"evidence that {Name} is the intended listener.\n"
        f"When '{Name}' is clearly being used to address the robot, strongly "
        "favor YES regardless of whether the following speech is a question, "
        "request, command, or statement.\n"
        f"Do not reduce confidence merely because the content following "
        f"'{Name}' is generic, short, unusual, or grammatically imperfect.\n\n"

        "2. NO EXPLICIT ADDRESS:\n"
        "A meaningful question, request, command, or conversational statement "
        "without an identified listener does not provide evidence that the "
        "speaker is NOT talking to the robot.\n"
        "Do not treat the absence of the robot's name as evidence for NO.\n"
        "When the listener cannot be determined from the speech, the YES and "
        "NO probabilities should be relatively close.\n\n"

        "3. CLEARLY NOT ADDRESSED:\n"
        f"Favor NO when there is positive evidence that the speaker is "
        f"addressing someone other than {Name}, or when the speech is clearly "
        "unrelated to communicating with the robot.\n\n"

        "4. GIBBERISH:\n"
        "Meaningless, nonsensical, or obviously corrupted speech should "
        "strongly favor NO.\n\n"

        "5. STT ERRORS:\n"
        f"If '{Name}' is clearly being used as a direct address, favor YES "
        "even when the rest of the transcription contains minor grammatical "
        "errors, missing words, or imperfect speech recognition.\n"
        f"Do not let minor transcription errors override a clear address to "
        f"{Name}.\n\n"

        "6. CONFIDENCE:\n"
        "The probability of YES should reflect the strength of the evidence "
        f"that {Name} is the intended listener.\n"
        f"A clear direct address to {Name} should produce a high YES "
        "probability.\n"
        "A meaningful utterance with no identified listener should produce "
        "a probability closer to the middle.\n"
        "Clear evidence that the robot is not being addressed should produce "
        "a low YES probability.\n\n"

        "Do not answer the speech.\n"
        "Do not explain your decision.\n"
        "Do not output a confidence number.\n"
        "Output ONLY YES or NO."
    )