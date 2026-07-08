from fastapi import FastAPI, HTTPException, Query

from app.database import Base, engine
from app import auth, records, users

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    # 안전장치: API 키가 없을 때 안내
    print("⚠️ WARNING: GROQ_API_KEY가 .env 파일에 설정되지 않았습니다.")

groq_client = Groq(api_key=groq_api_key)

# 테이블이 없으면 생성 (이미 있으면 아무 일도 안 함)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JWT Auth API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)


SLOGAN_SYSTEM_PROMPT = (
    "You are an supportive and empathetic daily reflection assistant.\n"
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


@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/slogan")
def get_ai_slogan():
    """
    유저의 최근 생각이나 감정 상태(user_input)를 받아 
    Groq LLM AI가 감정을 분석한 후, 오늘의 일기 작성을 도와줄 따뜻한 질문 문구를 생성합니다.
    """

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SLOGAN_SYSTEM_PROMPT},
                {"role": "user", "content": ""},
            ],
            temperature=0.7,  # 질문의 다양성과 자연스러움을 위해 0.7 설정
        )
        # 결과 텍스트의 앞뒤 공백 제거 후 반환
        ai_question = completion.choices[0].message.content.strip()
        
        return {"slogan": ai_question}

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI 문구 생성 중 오류가 발생했습니다: {str(e)}"
        )
