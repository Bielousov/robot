from config import ENV
from dictionary import Responses
from state import State

def debug(arg, label='Debug'):
    if ENV.DEBUG:
        print(f">> {label}: {arg}")

def handelVerboseError(error):
    try:
        print(f"{error}: {Responses['errors'][error]}")
        State.append('utterances', Responses['errors'][error])
    except:
        print(f"{error}: Unhandled error")
        State.append('utterances', Responses['errors']['generic'])
