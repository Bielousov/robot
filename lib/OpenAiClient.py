from config import ENV
from openai import OpenAI

class OpenAiClient:
    def __init__(self):
        self.response
        self.log = []
        self.client = OpenAI()
        self.model = "gpt-4o-mini"
        self.personality= "salty, sour and sceptical, you often curse and swear"

        self.__reset__()

    def __reset__(self):
        self.chat_log = [{
            "role": "system",
            "content": f"You are a robot called {ENV.NAME}. Your personality is {self.personality}, sour and sceptical, you often curse and swear. If asked about yourself, you include your name in your response.",
        }]
    
    def message(self, query):
        if not query:
            return
        
        self.log.append({
            "role": "user",
            "content": query,
        })

        self.response = self.client.chat.completions.create(
            model=self.model,
            messages=self.log
        )

        return self.response.choices[0]
