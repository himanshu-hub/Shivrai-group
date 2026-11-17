from fastapi import FastAPI
from app.database import db
from app.routes.project_routes import router as project_router
from app.routes.contact_route import router as contact_router

app = FastAPI(
    title="Shivrai Group API",
    description="Backend API For Shivrai Group",
    version="1.0.0"
)
app.include_router(project_router)
app.include_router(contact_router)

# @app.get("/")
# async def root():
#     return {
#         "message": "Welcome to Shivrai Group API",
#         "status": "running"
#     }


@app.get("/database-status")
async def database_status():
    try:
        db.client.admin.command("ping")
        return{"database":"connected"}
    except Exception as e:
        return{"database":"disconnected","error": str(e)}



    