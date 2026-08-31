ConversationClassification = {
    "ADDRESSED": 1.0,
    "AMBIGUOUS": 0.5,
    "NOT_ADDRESSED": 0.0,
}

def build_conversation_classifier_prompt() -> str:
    """Return the classifier instructions for detecting if speech is directed at Pip."""
    return (
    "You classify whether spoken text is addressed to a robot named Pip.\n\n"

    "Return ONLY one label:\n"
    "YES\n"
    "NO\n\n"

    "The probability of YES will be used as the addressing confidence score.\n\n"

    "Classify the speaker's intended listener:\n\n"

    "YES = the speech is clearly directed at Pip.\n"
    "NO = the speech is clearly directed at someone else, is clearly about Pip, "
    "or is clearly unrelated to talking to a listener.\n\n"

    "IMPORTANT:\n"
    "A question or command without a named listener is AMBIGUOUS, not NO.\n"
    "For an ambiguous question or command, choose the label that reflects roughly "
    "equal uncertainty between YES and NO.\n"
    "Do not assume that an unnamed question is directed at Pip.\n"
    "Do not assume that an unnamed question is directed at another person.\n\n"

    "Strong YES examples:\n"
    "Pip, what is your name? -> YES\n"
    "Pip what is your name -> YES\n"
    "Pip, tell me a fun fact -> YES\n"
    "Hey Pip -> YES\n"
    "Pip turn on the lights -> YES\n\n"

    "Ambiguous examples:\n"
    "What is your name? -> ambiguous\n"
    "What time is it? -> ambiguous\n"
    "Can you read me a book? -> ambiguous\n"
    "Read me a book. -> ambiguous\n"
    "Tell me a joke. -> ambiguous\n"
    "Turn on the lights. -> ambiguous\n\n"

    "Strong NO examples:\n"
    "I was talking to Pip yesterday -> NO\n"
    "Pip is a robot -> NO\n"
    "John, what is your name? -> NO\n"
    "I think we should leave soon -> NO\n"
    "I'm going to read a book -> NO\n"
    "immortal the table seventy five -> NO\n"
    "purple seven window banana -> NO\n\n"

    "Minor speech-recognition errors and missing punctuation do not matter.\n"
    "Do not invent meaning that is not present.\n\n"
)
