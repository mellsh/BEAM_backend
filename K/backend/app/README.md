# FastAPI + MySQL + JWT + 구글 로그인

README에 있던 테이블 구조(`user`, `records`) 기준으로 구현했어요.

## 1. 설치

```bash
pip install -r requirements.txt
```

MySQL에 `dbname` 데이터베이스만 미리 만들어두면, 테이블(`user`, `records`)은 서버 처음 실행할 때 자동으로 생성돼요 (`Base.metadata.create_all`).

```sql
CREATE DATABASE dbname CHARACTER SET utf8mb4;
```

## 2. 환경변수 설정

`.env.example`을 복사해서 `.env`로 만들고 값 채우기:

```bash
cp .env.example .env
```

- `DATABASE_URL` : MySQL 접속 정보
- `JWT_SECRET_KEY` : 아무 랜덤 문자열 (예: `openssl rand -hex 32` 로 생성)
- `GOOGLE_CLIENT_ID` : 친구한테 받은 **웹 클라이언트 ID**

⚠️ **친구한테 받은 client secret은 이번 구현에서는 안 씁니다.** 아래 "왜 secret을 안 쓰나요?" 참고.

## 3. 실행

```bash
uvicorn app.main:app --reload
```

`http://localhost:8000/docs` 에서 Swagger로 바로 테스트 가능.

## 4. API 목록

| Method | URL | 설명 | 로그인 필요 |
|---|---|---|---|
| POST | `/auth/signup` | 이메일/비번 회원가입 | ❌ |
| POST | `/auth/login` | 이메일/비번 로그인 → JWT 발급 | ❌ |
| POST | `/auth/google-login` | 구글 id_token → JWT 발급 (자동 회원가입 포함) | ❌ |
| GET | `/auth/me` | 내 정보 조회 | ✅ |
| POST | `/auth/forgot-password` | 비밀번호 찾기 (재설정 토큰 발급) | ❌ |
| POST | `/auth/reset-password` | 토큰으로 비밀번호 재설정 | ❌ |
| GET | `/users/me` | 내 정보 조회 (`/auth/me`와 동일) | ✅ |
| PATCH | `/users/me` | 회원정보 수정 (이름 등) | ✅ |
| POST | `/users/me/change-password` | 로그인 상태에서 비밀번호 변경 | ✅ |
| DELETE | `/users/me` | 회원 탈퇴 | ✅ |
| POST | `/records` | 게시글 생성 (user_id 자동 첨부) | ✅ |
| GET | `/records` | 내 게시글 목록 조회 | ✅ |
| GET | `/records/{id}` | 게시글 단건 조회 (내 글만) | ✅ |
| PATCH | `/records/{id}` | 게시글 수정 (내 글만) | ✅ |
| DELETE | `/records/{id}` | 게시글 삭제 (내 글만) | ✅ |

로그인 필요한 API는 헤더에 `Authorization: Bearer <access_token>` 붙이면 됨.

## 5. 구글 로그인 흐름 (중요)

이 구현은 **프론트엔드에서 구글 로그인 → id_token을 백엔드로 전달 → 백엔드가 검증** 하는 방식이에요 (Google Identity Services / One Tap 방식). 이 방식은 **client secret이 필요 없고 client ID만** 있으면 됩니다.

프론트 쪽 흐름 (예: 웹):
1. 구글 로그인 버튼 클릭 → Google Identity Services SDK로 로그인
2. 로그인 성공하면 구글이 `id_token` (JWT)을 프론트에 내려줌
3. 프론트가 그 `id_token`을 그대로 `POST /auth/google-login` 에 보냄
4. 백엔드가 구글 공개키로 그 토큰이 진짜 구글이 발급한 게 맞는지, 우리 client id 대상으로 발급된 게 맞는지 검증
5. 검증 통과하면 이메일로 유저 조회 → 없으면 자동 회원가입 → 우리 서비스 자체 JWT 발급해서 응답

### 왜 secret을 안 쓰나요?
client secret은 서버가 구글에 **authorization code를 교환해서** 토큰을 받아오는 방식(server-side OAuth flow)에서 필요해요. 지금 구현한 id_token 검증 방식은 그 과정이 없어서 secret이 필요 없습니다.

만약 프론트에서 "인가 코드(authorization code)"만 받아서 백엔드로 넘기는 방식으로 하고 싶으면 (secret을 실제로 써야 하는 방식), 그건 별도로 코드 더 필요하니 말씀해주세요.

## 6. 폴더 구조

```
app/
  config.py       환경변수 로드
  database.py     SQLAlchemy 엔진/세션
  models.py       User, Record 테이블 정의
  schemas.py      요청/응답 pydantic 모델
  security.py     비밀번호 해싱, JWT 생성/검증
  deps.py         DB 세션, 로그인 유저 확인(get_current_user)
  routers/
    auth.py       회원가입/로그인/구글로그인
    records.py    게시글 생성/조회
  main.py         앱 실행 진입점
requirements.txt
.env.example
```

## 7. 주의할 점
- `pword` 컬럼은 구글로만 가입한 유저는 `NULL`이라, 그런 유저는 `/auth/login`(이메일/비번)으로 로그인 못 하게 막아뒀어요. 나중에 "구글 유저가 비번도 설정해서 두 방식 다 쓰게" 하고 싶으면 알려주세요.
- access token 유효기간은 1일로 해놨고 (`ACCESS_TOKEN_EXPIRE_MINUTES`), refresh token은 안 넣었어요. 필요하면 추가해드릴게요.
- 게시글 수정/삭제는 **본인 글만** 가능하게 막아뒀어요. 남의 글 id로 조회/수정/삭제 시도하면 404로 응답해요 (존재 여부도 안 알려주기 위해 403 대신 404 사용).
- 회원 탈퇴하면 그 유저의 `records`도 같이 삭제돼요 (`models.py`의 `cascade` 설정).

### `user` 테이블에 컬럼 2개 추가 필요 (비밀번호 찾기 기능용)
비밀번호 찾기 기능을 위해 `user` 테이블에 아래 두 컬럼이 필요해요. 친구가 만든 DB라면 이 컬럼들이 없을 수 있으니, 친구한테 부탁하거나 직접 실행해서 추가해야 해요:

```sql
ALTER TABLE user ADD COLUMN reset_token VARCHAR(255) NULL;
ALTER TABLE user ADD COLUMN reset_token_expires DATETIME NULL;
```

### 비밀번호 찾기 - 이메일 발송은 아직 연결 안 함
`/auth/forgot-password`를 호출하면 재설정 토큰이 만들어지긴 하는데, **실제 이메일 발송은 구현 안 되어 있어요.** 지금은 테스트용으로 서버 콘솔(터미널)에 토큰이 출력돼요:

```
[비밀번호 재설정 토큰] user@example.com -> Ab12Cd34...
```

실제로 이메일로 보내려면 SMTP(Gmail, 네이버 메일, SendGrid 등) 연동이 필요한데, 이건 별도 작업이라 필요하면 말씀해주세요. 지금은 콘솔에 뜬 토큰을 복사해서 `/auth/reset-password`에 `token`, `new_pword`로 보내면 비밀번호 변경되는 것까지는 테스트 가능해요. 토큰 유효시간은 30분이에요.
