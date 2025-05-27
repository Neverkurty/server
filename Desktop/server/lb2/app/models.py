from typing import Optional
from datetime import date

class User:
    def __init__(self, username: str, email: str, password: str, birthday: date):
        self.username = username
        self.email = email
        self.password = password  # Хэшировать в реальном проекте!
        self.birthday = birthday
        self.tokens = []  # список активных access токенов
        self.refresh_tokens = []  # список refresh токенов 