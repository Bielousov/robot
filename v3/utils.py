from config import ENV

def debug(arg, label='Debug'):
    if ENV.DEBUG:
        print(f">> {label}: {arg}")
