import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 1. 시스템 프롬프트 정의 (최근 감정 분석 후 맞춤형 질문 생성)
system_prompt = (
    "You are a supportive and empathetic daily reflection assistant.\n"
    "The user will provide their recent thoughts or emotional state.\n"
    "Your job is to analyze their emotion and generate exactly ONE short, meaningful question to help them write a journal entry.\n\n"
    "Guidelines based on emotions:\n"
    "- If frustrated/짜증: Ask about what clogged their mind or what they couldn't say (e.g., '오늘 삼킨 말이 있었어?').\n"
    "- If lonely/외로움 or sad/우울/슬픔: Ask comforting questions about their feelings (e.g., '요즘 가장 많이 드는 감정이 뭐야?').\n"
    "- If happy/행복: Ask about preserving that memory (e.g., '오늘 너를 웃게 만든 최고의 순간은 뭐야?').\n\n"
    "CRITICAL RULES:\n"
    "1. Respond ONLY with the single question string.\n"
    "2. Do not include any tags, explanations, quotation marks, or introductions.\n"
    "3. Language must be natural Korean, sounding warm and friendly."
)

# 2. 유저의 최근 데이터 (예시: 게임 뽑기 실패로 짜증/아쉬움이 섞인 상태)
user_input = ""

# 3. API 호출
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant", 
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    temperature=0.7, # 질문의 다양성과 자연스러움을 위해 온도를 살짝 올립니다 (0.0에서 0.7로 변경)
)

print(completion.choices[0].message.content)
# 예상 출력 결과 예시: 오늘 기대했던 대로 되지 않아서 속상했던 마음이 있니? 또는 오늘 삼킨 말이 있었어?