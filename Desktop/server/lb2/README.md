# Лабораторная работа №2 (FastAPI)

## Запуск через Docker

```bash
docker-compose up --build
```

## Запуск локально (venv)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Описание
- Авторизация и регистрация пользователей через API
- JWT-токены, refresh-токены, хранение токенов в памяти
- DTO, валидация, ограничения, смена пароля, logout, список токенов и т.д.
- Все требования из ТЗ реализованы 