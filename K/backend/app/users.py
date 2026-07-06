from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_current_user, get_db
from app.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/user", response_model=schemas.UserResponse)
def get_my_info(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.patch("/user", response_model=schemas.UserResponse)
def update_my_info(
    payload: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 보낸 필드만 수정 (지금은 name만 지원)
    if payload.name is not None:
        current_user.name = payload.name

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/user/change-password", response_model=schemas.MessageResponse)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 구글 로그인 전용 계정(pword가 없는 유저)은 현재 비밀번호 검증이 불가능
    if not current_user.pword:
        raise HTTPException(
            status_code=400,
            detail="구글 로그인 전용 계정은 비밀번호 변경이 불가능합니다.",
        )

    if not verify_password(payload.current_pword, current_user.pword):
        raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다.")

    current_user.pword = hash_password(payload.new_pword)
    db.commit()
    return schemas.MessageResponse(message="비밀번호가 변경되었습니다.")


@router.delete("/user", response_model=schemas.MessageResponse)
def withdraw(
    payload: schemas.WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 일반(이메일/비번) 가입 유저는 탈퇴 시 비밀번호 재확인
    if current_user.pword:
        if not payload.pword or not verify_password(payload.pword, current_user.pword):
            raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    # 유저 삭제 -> models.py에서 cascade 설정해둬서 해당 유저의 records도 같이 삭제됨
    db.delete(current_user)
    db.commit()
    return schemas.MessageResponse(message="탈퇴가 완료되었습니다.")
