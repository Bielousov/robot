import openai
from .Audio import Audio

class OpenAiClient:
    def __init__(self, config, onError):

        self.client = openai.OpenAI()
        self.onError = onError

        self.model = config.MODEL
        self.personality = config.PERSONALITY
        self.ttsEnabled = config.TTS_ENABBLED
        
        if self.ttsEnabled:
            self.ttsFormat = config.TTS_FORMAT
            self.ttsFramesPerBuffer = config.TTS_FRAMES_PER_BUFFER
            self.ttsModel = config.TTS_MODEL
            self.ttsSampleRate=config.TTS_SAMPLE_RATE
            self.ttsVoice=config.TTS_VOICE
            
            self.ttsAudio = Audio(
                bufferSize = self.ttsFramesPerBuffer,
                sampleRate= self.ttsSampleRate,
            )
    
        self.__reset__()

    def __reset__(self):
        self.chatLog = [{
            "role": "system",
            "content": self.personality,
        }]

    def ask(self, prompt):
        if not prompt:
            return
        

        try:
            self.chatLog.append({
                "role": "user",
                "content": prompt,
            })

            response = self.query(self.chatLog);
            print(">> OpenAI: ", response)
            return response
        
        except (
            openai.APIConnectionError,
            openai.APIError,
            openai.AuthenticationError,
            openai.RateLimitError,
        ) as e:
            self.onError(f"openai.{e.__name__}");
        
        except:
            self.onError('Unhandled OpenAI error');
    
    def query(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return response.choices[0].message.content;

    def tts(self, text):
        if not self.ttsEnabled or not text:
            return

        try:
            self.ttsAudio.stream.start_stream()
            
            # Request text-to-speech from OpenAI API
            with self.client.audio.speech.with_streaming_response.create(
                input=text,
                model=self.ttsModel,
                response_format=self.ttsFormat,
                voice=self.ttsVoice,
            ) as response:
                for chunk in response.iter_bytes(self.ttsFramesPerBuffer):
                    self.ttsAudio.output(chunk)

        finally:
            self.ttsAudio.stream.stop_stream()
