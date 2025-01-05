from io import BytesIO
from os import getenv

import openai
from .Audio import Audio

class OpenAiClient:
    def __init__(self, model, personality):

        openai.api_key = getenv('OPENAI_API_KEY')

        self.audio = Audio()
        self.client = openai()

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

        response = self.getText();

        print(">> OpenAI: ", response)

        voiceResponse = self.getVoice()
        self.audio.stream(voiceResponse)

        return
    
    def getText(self):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chatLog
        )

        return response.choices[0].message.content;


    def getVoice(self):
        # Request text-to-speech from OpenAI API
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            messages=self.chatLog
        )

        return response['data']
