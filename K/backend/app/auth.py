import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.deps import get_current_user, get_db
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

RESET_TOKEN_EXPIRE_MINUTES = 30


@router.post("/signup", response_model=schemas.UserResponse)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    user = models.User(
        email=payload.email,
        pword=hash_password(payload.pword),
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    # user.pword가 없는 경우는 구글로만 가입한 유저 -> 일반 로그인 불가
    if not user or not user.pword or not verify_password(payload.pword, user.pword):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

    access_token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=access_token)


@router.post("/google-login", response_model=schemas.TokenResponse)
def google_login(payload: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    # 프론트에서 넘어온 id_token이 실제로 구글이 발급한 것이 맞는지,
    # 그리고 우리 앱(client id)을 대상으로 발급된 것이 맞는지 검증
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="유효하지 않은 구글 id_token 입니다.")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="구글 계정에서 이메일 정보를 가져올 수 없습니다.")

    name = idinfo.get("name") or email.split("@")[0]

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # 처음 구글로 로그인하는 유저는 자동으로 회원가입 처리 (pword는 없음)
        user = models.User(email=email, pword=None, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=access_token)


@router.get("/user", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=schemas.MessageResponse)
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    # 가입 여부를 알려주지 않기 위해, 유저가 없어도 항상 같은 메시지를 응답
    if user and user.pword:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )
        db.commit()

        # TODO: 실제 서비스에서는 여기서 이메일 발송 로직(SMTP 등) 연결 필요
        # 이메일 발송 연동 전까지는 서버 콘솔에 토큰을 찍어서 테스트용으로 확인
        print(f"[비밀번호 재설정 토큰] {payload.email} -> {token}")

    return schemas.MessageResponse(
        message="해당 이메일로 가입된 계정이 있다면, 비밀번호 재설정 안내를 발송했습니다."
    )


@router.post("/reset-password", response_model=schemas.MessageResponse)
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.reset_token == payload.token).first()

    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="유효하지 않은 토큰입니다.")

    expires_at = user.reset_token_expires
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="만료된 토큰입니다. 다시 요청해주세요.")

    user.pword = hash_password(payload.new_pword)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return schemas.MessageResponse(message="비밀번호가 재설정되었습니다.")
