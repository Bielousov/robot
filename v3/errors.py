from dictionary import  Responses
from state import appendState

def handleError(error):
    match error:
        case 'openai.APIConnectionError':
            appendState('utterances', Responses[error])