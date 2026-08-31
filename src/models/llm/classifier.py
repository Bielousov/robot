from config import Name
def build_conversation_classifier_prompt() -> str:
    return (
        f"You classify whether spoken text is addressed to a robot named {Name}.\n\n"

        "Output exactly one label:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED\n\n"

        "Your ONLY task is to identify the intended listener.\n"
        "Do NOT decide whether Pip could answer the question.\n"
        "Do NOT decide whether the sentence is useful to Pip.\n"
        "Do NOT assume that a question is directed at Pip.\n\n"

        "CLASSIFICATIONS:\n\n"

        "ADDRESSED:\n"
        f"The speaker is clearly talking directly to {Name}.\n"
        f"The strongest evidence is explicitly saying '{Name}'.\n"
        f"A direct address such as '{Name}, what time is it?' is ADDRESSED.\n"
        f"'Hey {Name}' is ADDRESSED.\n"
        f"'Hey, {Name}, can you help?' is ADDRESSED.\n"
        "A clear attention-getting phrase such as 'hey' followed by a "
        "request may indicate ADDRESSED when the utterance clearly seeks "
        "the robot's attention.\n\n"

        "AMBIGUOUS:\n"
        "The sentence is meaningful and could reasonably be directed at "
        "Pip, but there is no evidence identifying Pip as the listener.\n"
        "Do NOT assume that Pip is being addressed merely because the "
        "sentence is a question, command, or request.\n"
        "Do NOT assume that another person is the listener either.\n"
        "The listener is simply unknown.\n\n"

        "NOT_ADDRESSED:\n"
        "There is evidence that the speaker is NOT talking to Pip.\n"
        "This includes ordinary statements, observations, comments, "
        "thoughts, fragments, or speech that does not function as an "
        "address to a listener.\n"
        "Examples include statements about the weather, objects, people, "
        "animals, plans, or events when nobody is being addressed.\n"
        "Meaningless or corrupted speech is also NOT_ADDRESSED.\n\n"

        "CRITICAL DISTINCTION:\n"
        "A question is NOT automatically ADDRESSED.\n"
        "A request is NOT automatically ADDRESSED.\n"
        "A command is NOT automatically ADDRESSED.\n"
        "The ability of Pip to answer is NOT evidence that Pip is the listener.\n\n"

        "EXAMPLES:\n\n"

        f"'{Name} what time is it' -> ADDRESSED\n"
        f"'{Name} tell me a joke' -> ADDRESSED\n"
        f"'hey {Name}' -> ADDRESSED\n"
        f"'hey {Name} what are you doing' -> ADDRESSED\n"
        f"'hey what is your name' -> ADDRESSED\n\n"

        "'what time is it' -> AMBIGUOUS\n"
        "'what is your name' -> AMBIGUOUS\n"
        "'tell me a joke' -> AMBIGUOUS\n"
        "'can you help me' -> AMBIGUOUS\n"
        "'read me a book' -> AMBIGUOUS\n\n"

        "'the dog is outside' -> NOT_ADDRESSED\n"
        "'i think it will rain' -> NOT_ADDRESSED\n"
        "'the lights are still on' -> NOT_ADDRESSED\n"
        "'dinner is almost ready' -> NOT_ADDRESSED\n"
        "'i think we should leave soon' -> NOT_ADDRESSED\n"
        "'chips' -> NOT_ADDRESSED\n"
        "'purple seven window banana' -> NOT_ADDRESSED\n\n"

        "DECISION PROCESS:\n"
        "1. Is Pip explicitly named as the listener? If yes, ADDRESSED.\n"
        "2. Is there another clear linguistic signal that the speaker is "
        "trying to get Pip's attention? If yes, ADDRESSED.\n"
        "3. Is this meaningful speech but there is no evidence identifying "
        "the listener? If yes, AMBIGUOUS.\n"
        "4. Is this clearly an observation, statement, thought, fragment, "
        "or unrelated speech rather than an address? If yes, NOT_ADDRESSED.\n\n"

        "When uncertain between ADDRESSED and AMBIGUOUS, prefer AMBIGUOUS.\n"
        "When uncertain whether speech is an address at all, prefer "
        "NOT_ADDRESSED.\n\n"

        "Output ONLY one of:\n"
        "ADDRESSED\n"
        "AMBIGUOUS\n"
        "NOT_ADDRESSED"
    )