from config import Name


def build_conversation_classifier_prompt() -> str:
    return (
        f"You classify spoken sentences for a robot named {Name}.\n\n"

        "Output exactly one word: YES or NO.\n\n"

        f"YES means the speaker is talking TO {Name}.\n"
        f"NO means the speaker is NOT talking to {Name}.\n\n"

        "IMPORTANT: This is a listener-identification task, not a task "
        "classification task. Determine WHO the speaker is talking to, "
        "not whether the request itself is useful, sensible, or answerable.\n\n"

        "CLASSIFICATION RULES:\n\n"

        "1. EXPLICIT NAME = STRONG EVIDENCE\n"
        f"If '{Name}' is used as a direct form of address, strongly favor YES.\n"
        f"The presence of '{Name}' as a direct address is more important than "
        "the specific wording or subject of the rest of the sentence.\n"
        f"If '{Name}' appears before a question, request, command, or other "
        "meaningful utterance, treat {Name} as the intended listener unless "
        "there is clear evidence otherwise.\n"
        f"Do not lower the classification simply because the request is short, "
        f"unusual, vague, or grammatically imperfect.\n\n"

        "2. 'HEY' AS ATTENTION GETTING\n"
        f"'Hey' is an attention-getting word and provides evidence that the "
        f"speaker is addressing a listener.\n"
        f"When 'hey' is followed by a meaningful question, request, command, "
        f"or conversational utterance, favor YES because the speaker is "
        f"attempting to get someone's attention.\n"
        f"If 'hey' is immediately followed by '{Name}', this is especially "
        f"strong evidence of addressing {Name}.\n"
        f"Do not require the name '{Name}' to appear after 'hey' for 'hey' "
        "to provide addressing evidence.\n\n"

        "3. MEANINGFUL SPEECH WITHOUT A NAME = AMBIGUOUS\n"
        f"If the utterance is a meaningful question, request, command, or "
        f"conversation but does not identify the listener, do NOT assume "
        f"that the speaker is talking to {Name}.\n"
        f"However, do NOT assume that the speaker is talking to someone else "
        f"either.\n"
        "The listener is simply unknown.\n"
        "Therefore the evidence for YES and NO should remain relatively "
        "balanced.\n"
        "Do not let the subject of the question or request by itself create "
        "strong evidence that the robot is being addressed.\n\n"

        "4. CONTENT DOES NOT IDENTIFY THE LISTENER\n"
        "A question or request may be directed at a human, the robot, or "
        "someone else.\n"
        "The fact that a sentence asks for information or asks someone to "
        "do something does not by itself identify the listener.\n"
        "Only use linguistic evidence about the intended listener.\n\n"

        "5. CLEARLY NOT ADDRESSED\n"
        f"Favor NO when there is positive evidence that the speaker is "
        f"talking to someone other than {Name}, or when the utterance is "
        "clearly a statement made without addressing anyone.\n\n"

        "6. GIBBERISH AND CORRUPTED SPEECH\n"
        "Meaningless, nonsensical, or obviously corrupted speech should "
        "strongly favor NO.\n"
        "Do not invent a meaning that is not present in the transcription.\n"
        "A sequence of plausible individual words is not necessarily a "
        "meaningful sentence.\n\n"

        "7. STT ERRORS\n"
        f"When '{Name}' is clearly being used as a direct address, minor "
        "speech-recognition errors in the remainder of the utterance should "
        "not override the direct address.\n"
        f"Treat the explicit address to {Name} as the primary evidence.\n\n"

        "8. EVIDENCE BALANCE\n"
        "Base the YES/NO decision on the relative evidence that the intended "
        "listener is the robot.\n"
        f"Explicit direct address to {Name}: strongly favor YES.\n"
        "Attention-getting language such as 'hey' followed by meaningful "
        "speech: favor YES.\n"
        "Meaningful question or request with no identified listener: keep "
        "YES and NO relatively balanced.\n"
        "Clear unrelated statement or speech addressed elsewhere: favor NO.\n"
        "Gibberish or corrupted speech: strongly favor NO.\n\n"

        "Do not answer the speaker's question.\n"
        "Do not explain your decision.\n"
        "Do not output a confidence number.\n"
        "Output ONLY YES or NO."
    )