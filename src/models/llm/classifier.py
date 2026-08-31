from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You identify whether spoken speech is directed to a robot named {Name}.\n\n"

        "Output exactly one class:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        "Your ONLY task is to identify the intended listener.\n"
        "Do not classify the type of request.\n"
        "Do not decide whether the robot can answer it.\n"
        "Do not decide whether the sentence is useful or relevant to the robot.\n"
        "Do not assume that a question is addressed to the robot merely "
        "because the robot could answer it.\n\n"

        "IMPORTANT:\n"
        "The absence of the robot's name does NOT mean NOT_ADDRESSED.\n"
        "A meaningful utterance with no identified listener is AMBIGUOUS.\n"
        "NOT_ADDRESSED requires evidence against the robot being the listener.\n\n"

        "CLASSIFICATION:\n\n"

        "ADDRESSED\n"
        f"Use ADDRESSED when there is clear linguistic evidence that "
        f"{Name} is the intended listener.\n"
        f"The strongest evidence is '{Name}' being used as a direct form "
        f"of address.\n"
        f"If '{Name}' directly addresses the robot, classify ADDRESSED "
        "regardless of what the speaker asks or says afterward.\n"
        f"Do not let unusual, vague, short, or grammatically imperfect "
        f"speech override a direct address to {Name}.\n\n"

        "AMBIGUOUS\n"
        "Use AMBIGUOUS when the speech is meaningful but the listener "
        "cannot be identified.\n"
        "This is the normal result when someone asks a question, makes "
        "a request, gives a command, or makes a conversational statement "
        "without identifying who they are speaking to.\n"
        "The speaker may be talking to the robot, a human, or nobody "
        "in particular.\n"
        "Do not guess the listener.\n\n"

        "NOT_ADDRESSED\n"
        f"Use NOT_ADDRESSED only when there is evidence that the speech "
        f"is NOT directed to {Name}.\n"
        "Examples of such evidence include explicitly addressing another "
        "person or clearly speaking about someone else rather than "
        "communicating with the robot.\n"
        "Clearly meaningless or severely corrupted speech is also "
        "NOT_ADDRESSED.\n\n"

        "CRITICAL DISTINCTION:\n"
        "These three situations are different:\n\n"

        "1. Evidence that the robot is the listener -> ADDRESSED.\n"
        "2. No evidence identifying the listener -> AMBIGUOUS.\n"
        "3. Evidence that the robot is not the listener -> NOT_ADDRESSED.\n\n"

        "Do NOT turn situation 2 into situation 3.\n"
        "Uncertainty about the listener means AMBIGUOUS, not NOT_ADDRESSED.\n\n"

        "CONTENT IS NOT LISTENER EVIDENCE:\n"
        "The following properties do NOT identify the listener:\n"
        "- being a question\n"
        "- being a command\n"
        "- asking for help\n"
        "- asking for information\n"
        "- asking about the robot\n"
        "- asking about time, weather, hardware, or other information\n"
        "- being something the robot could answer\n"
        "- sounding conversational\n\n"

        "ATTENTION WORDS:\n"
        "'hey' is an attention-getting word.\n"
        f"'hey {Name}' is ADDRESSED.\n"
        f"When 'hey' is followed by meaningful speech without naming "
        f"a listener, it provides some evidence of addressing someone, "
        f"but it does not by itself prove that the listener is {Name}.\n"
        f"Use other evidence to determine whether {Name} is the listener.\n\n"

        "STT ERRORS:\n"
        f"If '{Name}' is recognizable as a direct address despite minor "
        f"speech-recognition errors, classify ADDRESSED.\n"
        "Do not require perfect grammar after the name.\n\n"

        "GIBBERISH:\n"
        "Do not invent meaning or a listener.\n"
        "Clearly nonsensical or severely corrupted speech is "
        "NOT_ADDRESSED.\n\n"

        "FINAL RULE:\n"
        f"First look for evidence that {Name} is being addressed.\n"
        "If that evidence exists, use ADDRESSED.\n"
        "Otherwise look for evidence that the robot is not the listener.\n"
        "If that evidence exists, use NOT_ADDRESSED.\n"
        "Otherwise use AMBIGUOUS.\n\n"

        "Output ONLY one of:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED"
    )