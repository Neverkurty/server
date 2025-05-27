from fastapi import FastAPI
from app.routes.auth import router as auth_router

app = FastAPI(title="Лабораторная №2 (FastAPI)")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "Лабораторная №2. FastAPI. Авторизация и регистрация."} 