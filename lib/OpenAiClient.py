from io import BytesIO
import os, openai

from .Audio import Audio

openai.api_key = os.getenv('OPENAI_API_KEY')

class OpenAiClient:
    def __init__(self, model, personality):

        self.audio = Audio()
        self.client = openai

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
        if not input:
            return
        
        # Request text-to-speech from OpenAI API
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        # The response contains the audio data (in binary format)
        return BytesIO(response['data'])
