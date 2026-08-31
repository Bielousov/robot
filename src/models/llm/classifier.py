def build_conversation_classifier_prompt() -> str:
    """Return the classifier instructions for detecting if speech is directed at Pip."""
    return (
    "Classify whether the following speech is addressed to a robot named Pip.\n\n"

    "Return ONLY one label:\n"
    "YES\n"
    "NO\n\n"

    "YES means the speaker is talking to Pip, asking Pip a question, "
    "giving Pip a command, or asking Pip to do something.\n\n"

    "NO means the speaker is talking to someone else, talking about Pip, "
    "making a general statement, or the transcription is gibberish.\n\n"

    "Rules:\n"
    "- If 'Pip' is followed by a question, request, command, or instruction, return YES.\n"
    "- 'Pip' does not need to be present for a direct request or question.\n"
    "- Missing punctuation and minor transcription errors do not matter.\n"
    "- Do not invent meaning that is not present.\n"
    "- Gibberish or meaningless word sequences are NO.\n\n"

    "Examples:\n"
    "\"Pip, what is your name?\" -> YES\n"
    "\"Pip what is your name\" -> YES\n"
    "\"Pip then tell me some fun fact\" -> YES\n"
    "\"Hey Pip\" -> YES\n"
    "\"Pip turn on the lights\" -> YES\n"
    "\"Can you read me a book?\" -> YES\n"
    "\"Read me a book\" -> YES\n"
    "\"Tell me a joke\" -> YES\n"
    "\"What's the weather tomorrow?\" -> YES\n"
    "\"I think we should leave soon\" -> NO\n"
    "\"I was talking to Pip yesterday\" -> NO\n"
    "\"Pip is a robot\" -> NO\n"
    "\"John, can you read me a book?\" -> NO\n"
    "\"I'm going to read a book\" -> NO\n"
    "\"immortal the table seventy five\" -> NO\n"
    "\"purple seven window banana\" -> NO\n\n"
)
