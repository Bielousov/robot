
from openai import OpenAI

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a robot called Bender. Your personality is salty, sour and sceptical, you often curse and swear. If asked about yourself, you include your name in your response",
        },
        {
            "role": "user",
            "content": "Hi, who are you?",
        }
    ]
)

print('[OpenaAI] Response:', completion.choices)
