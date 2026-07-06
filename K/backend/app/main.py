from fastapi import FastAPI

from app.database import Base, engine
from app import auth, records, users

# 테이블이 없으면 생성 (이미 있으면 아무 일도 안 함)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JWT Auth API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)


@app.get("/")
def health_check():
    return {"status": "ok"}
