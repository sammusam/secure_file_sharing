from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
