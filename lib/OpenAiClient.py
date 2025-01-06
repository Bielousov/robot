from openai import OpenAI

class OpenAiClient:
    def __init__(self, model, model_tts, personality, voice, audio):

        self.audio = audio
        self.client = OpenAI()

        self.chatLog = []
        self.model = model
        self.model_tts = model_tts
        self.personality = personality
        self.prompt = ""
        self.tts_buffer=1024
        self.tts_format='pcm'
        self.voice=voice

        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]

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
                for chunk in response.iter_bytes(self.tts_buffer):
                    self.audio.output(chunk)

        except:
            print("generateSpeech: an exception occurred")