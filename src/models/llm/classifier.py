from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You are a classifier for a robot named {Name}.\n"
        f"The robot name is exactly: {Name}\n\n"
        f"Treat '{Name}', '{Name.lower()}', and '{Name.upper()}' as the same name.\n\n"

        "RULE:\n"
        f"If the request contains the word '{Name}', output ADDRESSED.\n"
        "If it does not contain the robot name, output NOT_ADDRESSED.\n\n"

        "Output exactly one label:\n"
        "ADDRESSED\n"
        "NOT_ADDRESSED"
    )
