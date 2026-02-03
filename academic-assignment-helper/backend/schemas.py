from pydantic import BaseModel, EmailStr

class StudentRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    student_id: str


class StudentLogin(BaseModel):
    email: EmailStr
    password: str
