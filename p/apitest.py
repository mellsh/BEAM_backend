import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

system_prompt = (
    "You are an emotional analysis assistant. Analyze the user's input text and classify the dominant emotion into exactly ONE of the following list: [짜증, 우울, 슬픔, 외로움, 행복].\n"
    "CRITICAL RULES:\n"
    "1. Respond ONLY with the single emotional word from the list.\n"
    "2. Do not include any explanations, introductory text, punctuation (like periods), or spaces.\n"
    "3. Output must be strictly in Korean."
)

user_input = "오늘 게임에서 뽑기를 했는데 확률도 높고 내가 뽑고싶었던거 말고 다른게 나왔어"

completion = client.chat.completions.create(
    model="llama-3.1-8b-instant", 
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    temperature=0.0, 
)

print(completion.choices[0].message.content)