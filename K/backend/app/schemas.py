from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- 회원가입 / 로그인 ----------

class SignupRequest(BaseModel):
    email: EmailStr
    pword: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    pword: str


class GoogleLoginRequest(BaseModel):
    # 프론트에서 구글 로그인 성공 후 받는 id_token (JWT)을 그대로 전달받음
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 회원정보 수정 / 탈퇴 / 비밀번호 ----------

class UserUpdateRequest(BaseModel):
    # 둘 다 선택값. 보낸 필드만 수정됨
    name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_pword: str
    new_pword: str


class WithdrawRequest(BaseModel):
    # 탈퇴 확인용으로 비밀번호 한 번 더 받음 (구글 전용 계정은 pword가 없어서 생략 가능하게 optional)
    pword: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_pword: str


class MessageResponse(BaseModel):
    message: str


# ---------- records ----------

class RecordCreateRequest(BaseModel):
    content: str
    category: Optional[str] = None


class RecordUpdateRequest(BaseModel):
    # 둘 다 선택값. 보낸 필드만 수정됨
    content: Optional[str] = None
    category: Optional[str] = None


class RecordResponse(BaseModel):
    id: int
    user_id: int
    content: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
