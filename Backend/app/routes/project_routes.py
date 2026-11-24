
import re
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response
)
from pymongo.errors import PyMongoError
from pydantic import BaseModel, Field

from app.auth import get_current_admin
from app.database import projects_collection

from app.Schema.project import (
    ProjectSchema,
    ProjectUpdateSchema,
    ProjectCategory,
    ProjectStatus,
    ProjectResponse,
    ProjectListResponse
)


# =============================================
# PROJECT WRITE RESPONSE MODELS
# =============================================

class ProjectCreateResponse(BaseModel):
    message: str
    id: str


class ProjectUpdateResponse(BaseModel):
    message: str
    project_id: str
    updated_fields: list[str] = Field(default_factory=list)


class ProjectDeleteResponse(BaseModel):
    message: str
    project_id: str
    media_preserved: bool


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


# =============================================
# VALIDATE PROJECT ID
# =============================================

def validate_project_id(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )

    return ObjectId(project_id)


# =============================================
# GET ALL PROJECTS
# =============================================


@router.get("/", response_model=ProjectListResponse)
def get_projects(
    status: str | None = None,
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100
    ),
    category: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = "newest"
):
    if status and status not in [
        s.value for s in ProjectStatus
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid project status"
        )

    if category and category not in [
        c.value for c in ProjectCategory
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid project category"
        )

    query = {}

    if search:
        search = search.strip()

        if search:
            safe_search = re.escape(search)

            query["$or"] = [
                {
                    "name": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                },
                {
                    "location": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                },
                {
                    "description": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                },
                {
                    "category": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                }
            ]

    if status:
        query["status"] = status

    if category:
        query["category"] = category

    sort_options = {
        "newest": [("_id", -1)],
        "oldest": [("_id", 1)],
        "name_asc": [
            ("name", 1),
            ("_id", -1)
        ],
        "name_desc": [
            ("name", -1),
            ("_id", -1)
        ],
        "most_viewed": [
            ("total_views", -1),
            ("_id", -1)
        ]
    }

    if sort_by not in sort_options:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting option"
        )

    skip = (page - 1) * limit

    try:
        projects = list(
            projects_collection.find(query)
            .sort(sort_options[sort_by])
            .skip(skip)
            .limit(limit)
        )

        for project in projects:
            project["id"] = str(
                project.pop("_id")
            )

            project["total_views"] = (
                project.get("total_views") or 0
            )

            project["gallery"] = (
                project.get("gallery") or []
            )

            project["gallery_assets"] = (
                project.get("gallery_assets") or []
            )

            project["daily_views"] = (
                project.get("daily_views") or {}
            )

        total_projects = (
            projects_collection.count_documents(query)
        )

        return {
            "total_projects": total_projects,
            "current_page": page,
            "total_pages": (
                total_projects + limit - 1
            ) // limit,
            "projects": projects
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        ) from exc


# =============================================
# CREATE PROJECT
# ADMIN ONLY
# IMAGES MANAGED THROUGH MEDIA LIBRARY
# =============================================

@router.post("/", response_model=ProjectCreateResponse)
def create_project(
    project: ProjectSchema,
    current_admin: str = Depends(get_current_admin)
):
    # ProjectSchema forbids image/gallery inputs.
    # All media is attached through Image Management endpoints.
    project_data = project.model_dump(mode="json")

    # Initialize media fields.
    project_data["image"] = None
    project_data["gallery"] = []
    project_data["gallery_assets"] = []

    # Project metadata.
    project_data["created_at"] = (
        datetime.now(timezone.utc)
    )

    # Project analytics.
    project_data["total_views"] = 0
    project_data["daily_views"] = {}

    try:
        result = projects_collection.insert_one(
            project_data
        )

        return {
            "message": "Project Created Successfully",
            "id": str(result.inserted_id)
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        ) from exc


# =============================================
# TRACK PROJECT PAGE VIEWS
# PUBLIC ENDPOINT
# =============================================

@router.post("/{project_id}/view", status_code=204)
def track_project_view(project_id: str):
    object_id = validate_project_id(project_id)

    today = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d"
    )

    try:
        result = projects_collection.update_one(
            {"_id": object_id},
            {
                "$inc": {
                    "total_views": 1,
                    f"daily_views.{today}": 1
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        return Response(status_code=204)

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to record project view"
        ) from exc


# =============================================
# GET SINGLE PROJECT
# =============================================


@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project(project_id: str):
    object_id = validate_project_id(project_id)

    try:
        project = projects_collection.find_one(
            {"_id": object_id}
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        project["id"] = str(
            project.pop("_id")
        )

        project["total_views"] = (
            project.get("total_views") or 0
        )

        project["gallery"] = (
            project.get("gallery") or []
        )

        project["gallery_assets"] = (
            project.get("gallery_assets") or []
        )

        project["daily_views"] = (
            project.get("daily_views") or {}
        )

        return project

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        ) from exc


# =============================================
# UPDATE PROJECT
# ADMIN ONLY
# PARTIAL UPDATES SUPPORTED
# =============================================

@router.put("/{project_id}", response_model=ProjectUpdateResponse)
def update_project(
    project_id: str,
    project: ProjectUpdateSchema,
    current_admin: str = Depends(get_current_admin)
):
    object_id = validate_project_id(project_id)

    # Only update provided metadata fields.
    # Image fields are excluded from this schema.
    project_data = project.model_dump(
        exclude_unset=True,
        mode="json"
    )

    if not project_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    null_fields = [
        field
        for field, value in project_data.items()
        if value is None
    ]

    if null_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Project fields cannot be null",
                "fields": null_fields
            }
        )

    try:
        result = projects_collection.update_one(
            {"_id": object_id},
            {
                "$set": project_data
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        return {
            "message": "Project Updated Successfully",
            "project_id": project_id,
            "updated_fields": list(
                project_data.keys()
            )
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        ) from exc


# =============================================
# DELETE PROJECT
# ADMIN ONLY
# PRESERVE MEDIA LIBRARY IMAGES
# =============================================

@router.delete("/{project_id}", response_model=ProjectDeleteResponse)
def delete_project(
    project_id: str,
    current_admin: str = Depends(get_current_admin)
):
    object_id = validate_project_id(project_id)

    try:
        result = projects_collection.delete_one(
            {"_id": object_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        # Only the project document is deleted.
        # Cloudinary assets and media records
        # remain available for future reuse.
        return {
            "message": "Project deleted successfully",
            "project_id": project_id,
            "media_preserved": True
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable"
        ) from exc
