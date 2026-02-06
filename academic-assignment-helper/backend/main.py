from fastapi import FastAPI
from database import engine
import models
from routes import auth_routes
from routes import upload_routes
from routes import sources_routes
from rag_service import router as rag_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Academic Assignment Helper")

# routers
@app.get("/")
def root():
    return {"message": "Academic Assignment Helper API is running!"}

app.include_router(auth_routes.router)
app.include_router(upload_routes.router)
app.include_router(sources_routes.router, prefix="/sources")
app.include_router(rag_router, prefix="/rag")



