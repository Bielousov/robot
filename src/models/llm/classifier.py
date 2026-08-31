ConversationClassification = {
    "ADDRESSED": 1.0,
    "AMBIGUOUS": 0.5,
    "NOT_ADDRESSED": 0.0,
}

def build_conversation_classifier_prompt() -> str:
    return (
        "Classify whether the following speech is addressed to a robot named Pip.\n\n"

        "Return ONLY one of these classifications:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        "ADDRESSED means the speaker is clearly talking to Pip.\n"
        "AMBIGUOUS means the speech could naturally be addressed to Pip, "
        "but there is no evidence identifying the intended listener.\n"
        "NOT_ADDRESSED means the speech is clearly not directed at Pip, "
        "or is gibberish/unintelligible.\n\n"

        "Examples:\n"
        "\"Pip, what is your name?\" -> ADDRESSED\n"
        "\"Pip what is your name\" -> ADDRESSED\n"
        "\"Pip tell me a fun fact\" -> ADDRESSED\n"
        "\"Hey Pip\" -> ADDRESSED\n"
        "\"What is your name?\" -> AMBIGUOUS\n"
        "\"What time is it?\" -> AMBIGUOUS\n"
        "\"Can you read me a book?\" -> AMBIGUOUS\n"
        "\"Read me a book\" -> AMBIGUOUS\n"
        "\"I was talking to Pip yesterday\" -> NOT_ADDRESSED\n"
        "\"Pip is a robot\" -> NOT_ADDRESSED\n"
        "\"I think we should leave soon\" -> NOT_ADDRESSED\n"
        "\"immortal the table seventy five\" -> NOT_ADDRESSED\n"
    )
