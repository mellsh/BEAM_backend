from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_current_user, get_db

router = APIRouter(prefix="/records", tags=["records"])


def _get_owned_record_or_404(
    record_id: int, db: Session, current_user: models.User
) -> models.Record:
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
    if record.user_id != current_user.id:
        # 남의 글은 아예 존재 여부도 알려주지 않기 위해 404로 통일
        raise HTTPException(status_code=404, detail="존재하지 않는 게시글입니다.")
    return record


@router.post("/{record_id}", response_model=schemas.RecordResponse)
def create_record(
    payload: schemas.RecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 로그인한 유저의 id를 그대로 user_id에 사용 (프론트에서 안 보내도 됨)
    record = models.Record(
        user_id=current_user.id,
        content=payload.content,
        category=payload.category,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=List[schemas.RecordResponse])
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


@router.get("/{record_id}", response_model=schemas.RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_record_or_404(record_id, db, current_user)


@router.patch("/{record_id}", response_model=schemas.RecordResponse)
def update_record(
    record_id: int,
    payload: schemas.RecordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = _get_owned_record_or_404(record_id, db, current_user)

    # 보낸 필드만 수정
    if payload.content is not None:
        record.content = payload.content
    if payload.category is not None:
        record.category = payload.category

    db.commit()
    db.refresh(record)
    return record


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
