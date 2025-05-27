from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import date
import re

class LoginRequest(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль пользователя")

    @field_validator('username')
    def username_validate(cls, v):
        if not re.fullmatch(r'[A-Z][a-zA-Z]{6,}', v):
            raise ValueError('Имя пользователя должно начинаться с большой буквы, содержать только латинские буквы и быть не короче 7 символов')
        return v

    @field_validator('password')
    def password_validate(cls, v):
        if len(v) < 8:
            raise ValueError('Минимальная длина пароля 8 символов')
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы один спецсимвол')
        return v

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    c_password: str
    birthday: date

    @field_validator('username')
    def username_validate(cls, v):
        if not re.fullmatch(r'[A-Z][a-zA-Z]{6,}', v):
            raise ValueError('Имя пользователя должно начинаться с большой буквы, содержать только латинские буквы и быть не короче 7 символов')
        return v

    @field_validator('password')
    def password_validate(cls, v):
        if len(v) < 8:
            raise ValueError('Минимальная длина пароля 8 символов')
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы один спецсимвол')
        return v

    @field_validator('c_password')
    def c_password_validate(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v

    @field_validator('birthday')
    def birthday_validate(cls, v):
        from datetime import date
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14:
            raise ValueError('Возраст пользователя должен быть не менее 14 лет')
        return v

class UserDTO(BaseModel):
    username: str
    email: EmailStr
    birthday: date 