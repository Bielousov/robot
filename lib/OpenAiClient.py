from openai import OpenAI

class OpenAiClient:
    def __init__(self, model, personality):
        self.chatLog = []
        self.client = OpenAI()
        self.model = model
        self.personality= personality

        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]
    
    def query(self, query):
        if not query:
            return
        
        self.chatLog.append({
            "role": "user",
            "content": query,
        })

        self.response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chatLog
        )

        return self.response.choices[0].message.content
