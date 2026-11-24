from fastapi import FastAPI, HTTPException
from app.database import db, client
from app.routes.project_routes import router as project_router
from app.routes.contact_route import router as contact_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth_routes import router as auth_router
from contextlib import asynccontextmanager
from app.routes.image_routes import router as image_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        client.admin.command("ping")
        print("MongoDB connection active!")
        yield
    finally:
            client.close()
            print("Mongodb Connection closed")

app = FastAPI(
    title="Shivrai Group API",
    description="Backend API For Shivrai Group",
    version="1.0.0",
    lifespan= lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials= False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(project_router)
app.include_router(contact_router)
app.include_router(auth_router)
app.include_router(image_router)

@app.get("/database-status")
async def database_status():

    try:
        db.client.admin.command("ping")
        return{"database":"connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable."
        )

@app.get("/")
async def root():

    return {
        "message": "Welcome to Shivrai Group API",
        "status": "running"
    }