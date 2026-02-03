from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
import models, auth
from database import SessionLocal

router = APIRouter(tags=["Assignments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/upload")
def upload_assignment(
    file: UploadFile = File(...),
    current_user=Depends(auth.get_current_student),
    db: Session = Depends(get_db)
):
    assignment = models.Assignment(
        student_id=current_user["id"],
        filename=file.filename
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "message": "Uploaded",
        "assignment_id": assignment.id
    }
