from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from app.dto import LoginRequest, RegisterRequest, UserDTO
from app.models import User
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import jwt
import os

router = APIRouter()

# In-memory хранилище пользователей и токенов
users: Dict[str, User] = {}
active_tokens: Dict[str, str] = {}  # access_token: username
refresh_tokens: Dict[str, str] = {}  # refresh_token: username

SECRET = os.getenv("SECRET", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_QUANTITY = int(os.getenv("TOKEN_QUANTITY", 10))
TOKEN_ALIVE_HOURS = int(os.getenv("TOKEN_ALIVE_HOURS", 4))
REFRESH_TOKEN_ALIVE_HOURS = int(os.getenv("REFRESH_TOKEN_ALIVE_HOURS", 168))

# --- Вспомогательные функции ---
def create_token(username: str, expires_delta: timedelta, is_refresh=False):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + expires_delta,
        "type": "refresh" if is_refresh else "access"
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def decode_token(token: str, refresh=False):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        if refresh and payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        if not refresh and payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Not an access token")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(lambda request: request.cookies.get('access_token'))):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    username = decode_token(token)
    user = users.get(username)
    if not user or token not in user.tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

# --- Эндпоинты ---
@router.post("/register", status_code=201, response_model=UserDTO)
def register(data: RegisterRequest):
    if data.username in users:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    for u in users.values():
        if u.email.lower() == data.email.lower():
            raise HTTPException(status_code=400, detail="Email уже используется")
    user = User(data.username, data.email, data.password, data.birthday)
    users[data.username] = user
    return UserDTO(username=user.username, email=user.email, birthday=user.birthday)

@router.post("/login")
def login(data: LoginRequest, response: Response):
    user = users.get(data.username)
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    # Ограничение на количество токенов
    if len(user.tokens) >= TOKEN_QUANTITY:
        raise HTTPException(status_code=400, detail="Слишком много активных сессий")
    access_token = create_token(user.username, timedelta(hours=TOKEN_ALIVE_HOURS))
    refresh_token = create_token(user.username, timedelta(hours=REFRESH_TOKEN_ALIVE_HOURS), is_refresh=True)
    user.tokens.append(access_token)
    user.refresh_tokens.append(refresh_token)
    active_tokens[access_token] = user.username
    refresh_tokens[refresh_token] = user.username
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.get("/me", response_model=UserDTO)
def me(user: User = Depends(get_current_user)):
    return UserDTO(username=user.username, email=user.email, birthday=user.birthday)

@router.post("/out")
def logout(response: Response, user: User = Depends(get_current_user), token: str = Depends(lambda request: request.cookies.get('access_token'))):
    if token in user.tokens:
        user.tokens.remove(token)
        active_tokens.pop(token, None)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Пользователь успешно вышел из системы"}

@router.get("/tokens", response_model=List[str])
def get_tokens(user: User = Depends(get_current_user)):
    return user.tokens

@router.post("/out_all")
def logout_all(response: Response, user: User = Depends(get_current_user)):
    for token in list(user.tokens):
        active_tokens.pop(token, None)
    user.tokens.clear()
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Все пользователи успешно вышли из системы"}

@router.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token or refresh_token not in refresh_tokens:
        raise HTTPException(status_code=401, detail="Refresh token invalid")
    username = decode_token(refresh_token, refresh=True)
    user = users.get(username)
    if not user or refresh_token not in user.refresh_tokens:
        raise HTTPException(status_code=401, detail="Refresh token invalid")
    # Удаляем старый refresh, выдаём новый
    user.refresh_tokens.remove(refresh_token)
    refresh_tokens.pop(refresh_token, None)
    new_access = create_token(username, timedelta(hours=TOKEN_ALIVE_HOURS))
    new_refresh = create_token(username, timedelta(hours=REFRESH_TOKEN_ALIVE_HOURS), is_refresh=True)
    user.tokens.append(new_access)
    user.refresh_tokens.append(new_refresh)
    active_tokens[new_access] = username
    refresh_tokens[new_refresh] = username
    response.set_cookie(key="access_token", value=new_access, httponly=True)
    response.set_cookie(key="refresh_token", value=new_refresh, httponly=True)
    return {"access_token": new_access, "refresh_token": new_refresh}

@router.post("/change_password")
def change_password(old_password: str, new_password: str, user: User = Depends(get_current_user)):
    if user.password != old_password:
        raise HTTPException(status_code=400, detail="Старый пароль неверен")
    user.password = new_password
    return {"message": "Пароль успешно изменён"} 