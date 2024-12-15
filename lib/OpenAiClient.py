from openai import OpenAI

class OpenAiClient:
    def __init__(self, model, personality):
        self.chatLog = []
        self.client = OpenAI()
        self.model = model
        self.personality = personality
        self.query = ""

        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]

    def setQuery(self, query):
        self.query = query
    
    def runQuery(self):
        if not self.query:
            return
        
        self.chatLog.append({
            "role": "user",
            "content": self.query,
        })
        self.query = ""

        self.response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chatLog
        )

        print(">> OpenAI: ", self.response.choices[0].message.content)

        return self.response.choices[0].message.content
