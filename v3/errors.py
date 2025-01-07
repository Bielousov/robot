from dictionary import  Responses
from state import State

def handleError(error):
    match error:
        case 'openai.APIConnectionError':
            State.voiceQueue.append(Responses[error])