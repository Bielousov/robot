from openai import OpenAI

class OpenAiClient:
    def __init__(self, config, audio):

        self.client = OpenAI()
        self.audio = audio

        self.model = config.MODEL
        self.personality = config.PERSONALITY
        self.ttsFormat = config.TTS_FORMAT
        self.ttsModel = config.TTS_MODEL
        self.ttsVoice=config.TTS_VOICE
    
        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]
        self.prompt = ''

    def setPrompt(self, prompt):
        self.prompt = prompt
        print(">> Human: ", self.prompt)
    
    def runQuery(self):
        if not self.prompt:
            return
        

        self.chatLog.append({
            "role": "user",
            "content": self.prompt,
        })
        self.prompt = ""

        response = self.query(self.chatLog);

        print(">> OpenAI: ", response)

        self.generateSpeech(response)
    
    def query(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return response.choices[0].message.content;


    def generateSpeech(self, text):
        if not text:
            return

        try:
            # Request text-to-speech from OpenAI API
            with self.client.audio.speech.with_streaming_response.create(
                input=text,
                format=self.ttsFormat,
                model=self.ttsModel,
                voice=self.ttsVoice,
            ) as response:
                for chunk in response.iter_bytes(self.voice.frames_per_buffer):
                    self.voice.append(chunk)

        except:
            print("generateSpeech: an exception occurred")
