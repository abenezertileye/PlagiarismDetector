from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import auth, models
import os

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
    # 1. Check file type
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported for now.")

    # 2. Save file locally
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # 3. Read text from file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            extracted_text = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read text: {e}")

    # 4. Save assignment metadata + text in DB
    assignment = models.Assignment(
        student_id=current_user['id'],
        filename=file.filename,
        original_text=extracted_text
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "message": "TXT file uploaded successfully and text stored",
        "assignment_id": assignment.id,
        "text_preview": extracted_text[:200]  # first 200 characters
    }
