from datetime import datetime
from lib.LocalDictionary import LocalDictionary
from dictionary import Prompts
from errors import handelVerboseError
from state import State

class IntentHandler:
    def __init__(self, eyes, intentsModel, openai, voice):
        self.eyes = eyes
        self.intentsModel = intentsModel
        self.openai = openai
        self.voice = voice

    def __cache(self):
        return LocalDictionary("prompts.db")

    def handle(self, intentId, confidenceScore):
        """
        Call the intent method if it exists, otherwise fallback to noIntent.
        Both methods receive confidenceScore.
        """
        if intentId != 'noIntent':
            print(datetime.now().strftime('%H:%M:%S.%f')[:-3],
                  'Handling intent', intentId,
                  'with confidence', confidenceScore)

        # Call method or fallback to noIntent
        return getattr(self, intentId, self.noIntent)(confidenceScore)

    # -----------------------------
    # Intent methods
    # -----------------------------
    def ask(self, confidenceScore):
        self.eyes.wonder()
        if State.prompts:
            prompt = State.pop('prompts')
            cache = self.__cache()
            promptCacheSize = cache.count(prompt)
            localResponse = cache.getSome(prompt)

            # Check responses in local dictionary
            if promptCacheSize >= self.openai.cacheLimit:
                State.append('utterances', localResponse)
                return

            # Prompt OpenAI
            else:
                aiResponse = self.openai.ask(
                    prompt,
                    onError=lambda err: State.append('utterances', localResponse)
                    if localResponse else handelVerboseError(err)
                )
                if aiResponse:
                    State.append('utterances', aiResponse)

                    # Save response to local dictionary
                    if not cache.exists(prompt, aiResponse):
                        cache.set(prompt, aiResponse)

    def blink(self, confidenceScore):
        self.eyes.blink(confidenceScore)

    def bored(self, confidenceScore):
        State.append('prompts', Prompts['random fact'])

    def say(self, confidenceScore):
        State.set('speaking', True)
        if State.utterances:
            if self.openai.ttsEnabled:
                self.openai.tts(State.pop('utterances'), onError=handelVerboseError)
                State.set('speaking', False)
            else:
                self.voice.say(
                    State.pop('utterances'),
                    callback=lambda **_: State.set('speaking', False)
                )

    def scared(self, confidenceScore):
        State.append('prompts', Prompts['catchphrase'])

    def sleep(self, confidenceScore):
        State.append('prompts', Prompts['shutdown'])
        State.set('awake', False)


    def train(self, confidenceScore):
        self.eyes.wonder()
        self.intentsModel.trainAsync()

    def wakeup(self, confidenceScore):
        State.set('awake', True)
        State.append('prompts', Prompts['startup'])
        self.eyes.open(confidenceScore)
        print('Waking up!')

    def wonder(self, confidenceScore):
        self.eyes.wonder()

    def noIntent(self, confidenceScore):
        # Fallback when no intent matches
        return
