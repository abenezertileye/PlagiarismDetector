from fastapi import FastAPI
from database import engine
import models
from routes import auth_routes
from routes import upload_routes


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Academic Assignment Helper")

# routers
app.include_router(auth_routes.router)
app.include_router(upload_routes.router)

