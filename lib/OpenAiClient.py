from openai import OpenAI


class OpenAiClient:
    def __init__(self, config):

        self.client = OpenAI()

        self.model = config.MODEL
        self.personality = config.PERSONALITY
        # self.ttsFormat = config.TTS_FORMAT
        # self.ttsModel = config.TTS_MODEL
        # self.ttsVoice=config.TTS_VOICE
    
        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]

    def ask(self, prompt):
        if not prompt:
            return
        

        self.chatLog.append({
            "role": "user",
            "content": prompt,
        })

        response = self.query(self.chatLog);

        print(">> OpenAI: ", response)

        return response

        # self.generateSpeech(response)
    
    def query(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return response.choices[0].message.content;


    # def generateSpeech(self, text):
    #     if not text:
    #         return

    #     try:
    #         # Request text-to-speech from OpenAI API
    #         with self.client.audio.speech.with_streaming_response.create(
    #             input=text,
    #             model=self.ttsModel,
    #             response_format=self.ttsFormat,
    #             voice=self.ttsVoice,
    #         ) as response:
    #             for chunk in response.iter_bytes(self.audio.frames_per_buffer):
    #                 self.audio.append(chunk)

    #     except:
    #         print("generateSpeech: an exception occurred")
