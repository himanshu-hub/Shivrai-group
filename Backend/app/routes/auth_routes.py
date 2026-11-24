
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.auth import (
    create_access_token,
    verify_password,
    get_current_admin,
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
)

from app.database import (
    projects_collection,
    contacts_collection,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

media_collection = projects_collection.database["media"]


# =============================================
# RESPONSE MODELS
# =============================================

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str


class ProjectDashboardStats(BaseModel):
    total: int
    ongoing: int
    completed: int
    upcoming: int
    total_views: int


class EnquiryDashboardStats(BaseModel):
    total: int
    pending: int
    contacted: int
    resolved: int


class MediaDashboardStats(BaseModel):
    total_images: int


class RecentEnquiry(BaseModel):
    id: str
    name: str
    email: str
    subject: str | None = None
    status: str
    created_at: datetime | None = None


class AdminDashboardResponse(BaseModel):
    projects: ProjectDashboardStats
    enquiries: EnquiryDashboardStats
    media: MediaDashboardStats
    recent_enquiries: list[RecentEnquiry] = Field(
        default_factory=list
    )


# =============================================
# ADMIN LOGIN
# POST /auth/login
# =============================================

@router.post(
    "/login",
    response_model=AdminLoginResponse
)
async def admin_logic(
    credentials: OAuth2PasswordRequestForm = Depends()
):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=500,
            detail="Admin authentication is not configured"
        )

    valid_username = (
        credentials.username == ADMIN_USERNAME
    )

    valid_password = verify_password(
        credentials.password,
        ADMIN_PASSWORD_HASH
    )

    if not valid_username or not valid_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        {"sub": credentials.username}
    )

    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer"
    )


# =============================================
# ADMIN DASHBOARD SUMMARY
# GET /auth/dashboard
# ADMIN ONLY
# =============================================

@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    tags=["Admin Dashboard"]
)
def get_admin_dashboard(
    current_admin: str = Depends(get_current_admin)
):
    try:
        # Project counts
        total_projects = projects_collection.count_documents({})

        ongoing_projects = projects_collection.count_documents(
            {"status": "Ongoing"}
        )

        completed_projects = projects_collection.count_documents(
            {"status": "Completed"}
        )

        upcoming_projects = projects_collection.count_documents(
            {"status": "Upcoming"}
        )

        # Total project views
        views_result = list(
            projects_collection.aggregate([
                {
                    "$group": {
                        "_id": None,
                        "total_views": {
                            "$sum": {
                                "$ifNull": ["$total_views", 0]
                            }
                        }
                    }
                }
            ])
        )

        total_views = (
            views_result[0]["total_views"]
            if views_result
            else 0
        )

        # Enquiry counts
        total_enquiries = contacts_collection.count_documents({})

        pending_enquiries = contacts_collection.count_documents(
            {"status": "Pending"}
        )

        contacted_enquiries = contacts_collection.count_documents(
            {"status": "Contacted"}
        )

        resolved_enquiries = contacts_collection.count_documents(
            {"status": "Resolved"}
        )

        # Media Library image count
        total_images = media_collection.count_documents({
            "deleting": {"$ne": True}
        })

        # Latest five enquiries
        recent_documents = list(
            contacts_collection.find(
                {},
                {
                    "name": 1,
                    "email": 1,
                    "subject": 1,
                    "status": 1,
                    "created_at": 1
                }
            )
            .sort("_id", -1)
            .limit(5)
        )

        recent_enquiries = [
            {
                "id": str(enquiry["_id"]),
                "name": enquiry["name"],
                "email": enquiry["email"],
                "subject": enquiry.get("subject"),
                "status": enquiry.get("status", "Pending"),
                "created_at": enquiry.get("created_at")
            }
            for enquiry in recent_documents
        ]

        return {
            "projects": {
                "total": total_projects,
                "ongoing": ongoing_projects,
                "completed": completed_projects,
                "upcoming": upcoming_projects,
                "total_views": total_views
            },
            "enquiries": {
                "total": total_enquiries,
                "pending": pending_enquiries,
                "contacted": contacted_enquiries,
                "resolved": resolved_enquiries
            },
            "media": {
                "total_images": total_images
            },
            "recent_enquiries": recent_enquiries
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to load admin dashboard"
        ) from exc
