from openai import OpenAI

class OpenAiClient:
    def __init__(self, config, voiceBuffer):

        self.client = OpenAI()
        self.voiceBuffer = voiceBuffer

        self.model = config.MODEL
        self.model_tts = config.TTS_MODEL
        self.personality = config.PERSONALITY
        self.tts_format = config.TTS_FORMAT
        self.voice = config.TTS_VOICE

        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]
        self.prompt = ''

    def setPrompt(self, prompt):
        self.prompt = prompt
    
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

        return
    
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
                model=self.model_tts,
                response_format=self.tts_format,
                voice=self.voice
            ) as response:
                for chunk in response.iter_bytes(self.audio.frames_per_buffer):
                    self.voiceBuffer.append(chunk)

        except:
            print("generateSpeech: an exception occurred")
