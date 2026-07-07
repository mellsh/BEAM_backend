import os
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from groq import Groq
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_current_user, get_db
from sqlalchemy import func

# 환경 변수 로드 및 Groq 클라이언트 초기화
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter(prefix="/records", tags=["records"])

# AI 감정 분석용 시스템 프롬프트 정의
EMOTION_SYSTEM_PROMPT = (
    "You are an emotional analysis assistant. Analyze the user's input text and classify the dominant emotion into exactly ONE of the following list: [짜증, 우울, 슬픔, 외로움, 행복].\n"
    "CRITICAL RULES:\n"
    "1. Respond ONLY with the single emotional word from the list.\n"
    "2. Do not include any explanations, introductory text, punctuation (like periods), or spaces.\n"
    "3. Output must be strictly in Korean."
)


def _get_owned_record_or_404(
    record_id: int, db: Session, current_user: models.User
) -> models.Record:
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
    return record


# --- 1. 게시글 추가 API (Groq AI 연동) ---
@router.post("", response_model=schemas.RecordResponse)
def create_record(
    payload: schemas.RecordCreateRequest,  # content만 담긴 요청 스키마 사용 권장
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Groq API를 이용한 AI 감정 분석
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": EMOTION_SYSTEM_PROMPT},
                {"role": "user", "content": payload.content},
            ],
            temperature=0.0,
        )
        # 결과에서 공백 및 줄바꿈 제거
        ai_category = completion.choices[0].message.content.strip()
    except Exception as e:
        # AI API 호출 실패 시 서버 에러 반환 (또는 기본값 '미분류' 처리 가능)
        raise HTTPException(
            status_code=500, detail=f"AI 감정 분석 중 오류가 발생했습니다: {str(e)}"
        )

    # 로그인한 유저 정보와 AI가 분석한 category를 조합하여 저장
    record = models.Record(
        user_id=current_user.id,
        content=payload.content,
        category=ai_category,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# --- 2. 내 게시글 목록 조회 API (경로 수정 완료) ---
@router.get("", response_model=List[schemas.RecordResponse])
def list_my_records(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Record)
        .filter(models.Record.user_id == current_user.id)
        .order_by(models.Record.created_at.desc())
        .all()
    )


# --- 3. 특정 게시글 상세 조회 API ---
@router.get("/{record_id}", response_model=schemas.RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_record_or_404(record_id, db, current_user)


# --- 4. 게시글 수정 API ---
@router.patch("/{record_id}", response_model=schemas.RecordResponse)
def update_record(
    record_id: int,
    payload: schemas.RecordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = _get_owned_record_or_404(record_id, db, current_user)

    if payload.content is not None:
        record.content = payload.content
    if payload.category is not None:
        record.category = payload.category

    db.commit()
    db.refresh(record)
    return record


# --- 5. 게시글 삭제 API ---
@router.delete("/{record_id}", response_model=schemas.MessageResponse)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = _get_owned_record_or_404(record_id, db, current_user)
    db.delete(record)
    db.commit()
    return schemas.MessageResponse(message="삭제되었습니다.")

@router.get("/stats/monthly", response_model=List[schemas.MonthlyEmotionResponse])
def get_monthly_emotion_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    현재 로그인한 유저의 게시글들을 월별로 묶어 
    각 월에 어떤 감정이 몇 개씩 발생했는지 통계를 반환합니다.
    """
    # 1. MySQL에서 월별, 감정별로 Group By 하여 개수(COUNT) 집계
    # 결과 형태 예시: [("2026-07", "행복", 5), ("2026-07", "슬픔", 2), ("2026-06", "우울", 4)]
    raw_stats = (
        db.query(
            func.date_format(models.Record.created_at, "%Y-%m").label("month"),
            models.Record.category,
            func.count(models.Record.id).label("count")
        )
        .filter(models.Record.user_id == current_user.id)
        .group_by(func.date_format(models.Record.created_at, "%Y-%m"), models.Record.category)
        .order_by(func.date_format(models.Record.created_at, "%Y-%m").desc(), func.count(models.Record.id).desc())
        .all()
    )

    # 2. 데이터베이스 결과를 프론트엔드가 쓰기 좋은 트리 구조(JSON)로 가공
    # { "2026-07": [{"category": "행복", "count": 5}, {"category": "슬픔", "count": 2}] }
    formatted_dict = {}
    for month, category, count in raw_stats:
        if month not in formatted_dict:
            formatted_dict[month] = []
        formatted_dict[month].append({
            "category": category,
            "count": count
        })

    # 3. Pydantic 응답 스키마 리스트 형태로 변환하여 반환
    result = [
        schemas.MonthlyEmotionResponse(month=month, emotions=emotions)
        for month, emotions in formatted_dict.items()
    ]
    
    return result