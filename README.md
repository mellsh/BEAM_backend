# 🧠 BEAM Backend

> AI 기반 감정 분석 다이어리 서비스 Backend API

BEAM Backend는 사용자가 작성한 일기 또는 감정 기록을 AI가 분석하여 감정을 분류하고 저장하는 REST API 서버입니다.

FastAPI를 기반으로 구축되었으며, JWT 인증, Google OAuth 로그인, MySQL 데이터베이스, Groq LLM을 이용한 감정 분석 기능을 제공합니다.

---

# ✨ Features

- 🔐 JWT 기반 회원 인증
- 🌐 Google OAuth 로그인
- 🤖 Groq LLM(Llama 3.1 8B)을 이용한 감정 분석
- 📝 감정 기록 CRUD
- 📊 월별 감정 통계 제공
- 👤 회원 정보 관리
- 📄 Swagger(OpenAPI) 자동 문서화

---

# 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.10+ |
| Framework | FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Validation | Pydantic v2 |
| Authentication | JWT, Google OAuth 2.0 |
| AI | Groq API (Llama 3.1 8B Instant) |
| Server | Uvicorn |

---

# 📂 Project Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── deps.py
│   ├── security.py
│   │
│   └── routers/
│       ├── auth.py
│       ├── records.py
│       └── users.py
│
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone <repository-url>
cd backend
```

---

## 2. Create Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Packages

```bash
pip install -r requirements.txt
```

---

## 4. Environment Variables

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

GOOGLE_CLIENT_ID=your_google_client_id

GROQ_API_KEY=your_groq_api_key
```

---

## 5. Run Server

```bash
uvicorn app.main:app --reload
```

Server

```
http://localhost:8000
```

Swagger

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# 🔐 Authentication API

Base URL

```
/auth
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/signup` | 회원가입 |
| POST | `/login` | 로그인 |
| POST | `/google-login` | Google 로그인 |
| GET | `/user` | 내 정보 조회 |
| POST | `/forgot-password` | 비밀번호 재설정 요청 |
| POST | `/reset-password` | 비밀번호 재설정 |

---

# 📝 Records API

Base URL

```
/records
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/` | 감정 기록 작성 (AI 분석) |
| GET | `/` | 내 기록 조회 |
| GET | `/reords/stats/monthly` | 월별 감정 통계 |
| GET | `/{record_id}` | 기록 상세 조회 |
| PATCH | `/{record_id}` | 기록 수정 |
| DELETE | `/{record_id}` | 기록 삭제 |

---

# 👤 Users API

Base URL

```
/users
```

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/user` | 마이페이지 조회 |
| PATCH | `/user` | 회원정보 수정 |
| POST | `/user/change-password` | 비밀번호 변경 |
| DELETE | `/user` | 회원 탈퇴 |



---

# Slogan API

Base URL

```
/slogan
```

| Method | Endpoint | Description
|---------|----------|-------------|
| GET |              | 슬로건 가져오기 |

---

# 🤖 AI Emotion Analysis

사용자가 작성한 일기를 Groq LLM이 분석하여 다음 감정 중 하나를 자동으로 분류합니다.

- 😊 행복
- 😢 슬픔
- 😞 우울
- 😠 짜증
- 🥺 외로움

분석된 결과는 게시글과 함께 저장되며, 월별 통계 데이터 생성에도 활용됩니다.

---

# 🔑 Authentication

인증이 필요한 API는 JWT Access Token을 사용합니다.

Request Header

```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

# 📊 Database

주요 테이블

- User
- Record

관계

```
User
 └── Record (1:N)
```

회원 탈퇴 시 `ON DELETE CASCADE`를 통해 사용자의 감정 기록도 함께 삭제됩니다.

---

# 📖 API Documentation

FastAPI에서 자동 생성되는 API 문서를 제공합니다.

| Document | URL |
|----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

# 🚀 Future Plans

- 이메일 인증
- Refresh Token 적용
- 감정 분석 정확도 향상
- AI 감정 리포트 생성
- 감정 변화 그래프
- Docker 배포
- CI/CD 구축

---

# 👨‍💻 Developers

**BEAM Team**

AI Emotion Diary Backend Project