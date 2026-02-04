from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, auth
from database import SessionLocal

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/register")
def register(student: schemas.StudentRegister, db: Session = Depends(get_db)):
    existing = db.query(models.Student)\
                 .filter(models.Student.email == student.email)\
                 .first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.hash_password(student.password)

    new_student = models.Student(
        email=student.email,
        password_hash=hashed,
        full_name=student.full_name,
        student_id=student.student_id
    )

    db.add(new_student)
    db.commit()

    return {"message": "Student registered successfully"}

@router.post("/login")
def login(data: schemas.StudentLogin, db: Session = Depends(get_db)):
    student = db.query(models.Student)\
                .filter(models.Student.email == data.email)\
                .first()

    if not student or not auth.verify_password(data.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({
        "sub": student.email,
        "id": student.id,
        "role": "student"
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
