from io import BytesIO
from os import getenv
from openai import OpenAI
from .Audio import Audio

# openai.api_key = getenv('OPENAI_API_KEY')

class OpenAiClient:
    def __init__(self, model, personality):

        self.audio = Audio()
        self.client = OpenAI()

        self.chatLog = []
        self.model = model
        self.personality = personality
        self.prompt = ""

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

        response = self.generateText();

        print(">> OpenAI: ", response)

        voiceResponse = self.generateSpeech(response)
        self.audio.stream(voiceResponse)

        return
    
    def generateText(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chatLog
        )

        return response.choices[0].message.content;


    def generateSpeech(self, text):
        if not text:
            return
        
        # Request text-to-speech from OpenAI API
        with self.client.audio.speech.with_streaming_response.create(
            input=text,
            model="tts-1",
            response_format="pcm",
            voice="alloy"
        ) as response:
            for chunk in response.iter_bytes(1024):
                self.audio.stream.write(chunk)

