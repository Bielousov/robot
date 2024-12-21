import os
import openai

class OpenAiClient:
    def __init__(self, model, personality):

        openai.api_key = os.getenv('OPENAI_API_KEY')

        self.chatLog = []
        self.client = openai()
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

        self.response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chatLog
        )

        answer = self.response.choices[0].message.content

        print(">> OpenAI: ", answer)

        return answer
