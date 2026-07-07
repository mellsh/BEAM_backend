# from typing import List

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app import models, schemas
# from app.deps import get_current_user, get_db

# router = APIRouter(prefix="/records", tags=["records"])


# def _get_owned_record_or_404(
#     record_id: int, db: Session, current_user: models.User
# ) -> models.Record:
#     record = db.query(models.Record).filter(models.Record.id == record_id).first()
#     if not record:
#         raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
#     if record.user_id != current_user.id:
#         # 남의 글은 아예 존재 여부도 알려주지 않기 위해 404로 통일
#         raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
#     return record


# @router.post("/{record_id}", response_model=schemas.RecordResponse)
# def create_record(
#     payload: schemas.RecordCreateRequest,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     # 로그인한 유저의 id를 그대로 user_id에 사용 (프론트에서 안 보내도 됨)
#     record = models.Record(
#         user_id=current_user.id,
#         content=payload.content,
#         category=payload.category,
#     )
#     db.add(record)
#     db.commit()
#     db.refresh(record)
#     return record


# @router.get("/{record_id}", response_model=List[schemas.RecordResponse])
# def list_my_records(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     return (
#         db.query(models.Record)
#         .filter(models.Record.user_id == current_user.id)
#         .order_by(models.Record.created_at.desc())
#         .all()
#     )


# @router.get("/{record_id}", response_model=schemas.RecordResponse)
# def get_record(
#     record_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     return _get_owned_record_or_404(record_id, db, current_user)


# @router.patch("/{record_id}", response_model=schemas.RecordResponse)
# def update_record(
#     record_id: int,
#     payload: schemas.RecordUpdateRequest,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     record = _get_owned_record_or_404(record_id, db, current_user)

#     # 보낸 필드만 수정
#     if payload.content is not None:
#         record.content = payload.content
#     if payload.category is not None:
#         record.category = payload.category

#     db.commit()
#     db.refresh(record)
#     return record


# @router.delete("/{record_id}", response_model=schemas.MessageResponse)
# def delete_record(
#     record_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     record = _get_owned_record_or_404(record_id, db, current_user)
#     db.delete(record)
#     db.commit()
#     return schemas.MessageResponse(message="삭제되었습니다.")


import os
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from groq import Groq
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_current_user, get_db

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