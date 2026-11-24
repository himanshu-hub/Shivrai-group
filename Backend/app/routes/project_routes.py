from fastapi import HTTPException, APIRouter, Query, Depends, Response
from app.database import projects_collection
from app.Schema.project import ProjectSchema, ProjectCategory, ProjectStatus
from bson import ObjectId
from pymongo.errors import PyMongoError
import re
from app.auth import get_current_admin
from datetime import datetime, timezone


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)



@router.get("/")
def get_projects(
    status: str = None,
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100
    ),
    category: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = "newest"
):
    if status and status not in [s.value for s in ProjectStatus]:
        raise HTTPException(
            status_code=400,
            detail="Invalid project status"
        )

    if category and category not in [c.value for c in ProjectCategory]:
        raise HTTPException(
            status_code=400,
            detail="Invalid project category"
        )

    query = {}

    if search:
        search = search.strip()

        if search:
            search = re.escape(search)

            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"category": {"$regex": search, "$options": "i"}}
            ]

    if status:
        query["status"] = status

    if category:
        query["category"] = category

    skip = (page - 1) * limit

    if sort_by == "newest":
        sort_option = [("_id", -1)]

    elif sort_by == "oldest":
        sort_option = [("_id", 1)]

    elif sort_by == "name_asc":
        sort_option = [("name", 1), ("_id", -1)]

    elif sort_by == "name_desc":
        sort_option = [("name", -1), ("_id", -1)]

    elif sort_by == "most_viewed":
        sort_option = [
            ("total_views", -1),
            ("_id", -1)
        ]

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting option"
        )

    try:
        projects = list(
            projects_collection.find(query)
            .sort(sort_option)
            .skip(skip)
            .limit(limit)
        )

        for project in projects:
            project["id"] = str(project.pop("_id"))

            # Older projects may not have views yet.
            project["total_views"] = project.get("total_views", 0)

        total_projects = projects_collection.count_documents(query)

        return {
            "total_projects": total_projects,
            "current_page": page,
            "total_pages": (total_projects + limit - 1) // limit,
            "projects": projects
        }

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try later"
        )


@router.post("/{project_id}/view", status_code=204)
def track_project_view(project_id: str):

    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
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

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to record project view"
        )

@router.post("/")
def create_project(
    project: ProjectSchema,
    current_admin: str = Depends(get_current_admin)
):
    try:
        project_data = project.model_dump()
        result = projects_collection.insert_one(project_data)

        return {
            "message":"Project Created Successfully",
            "id": str(result.inserted_id)
        }
    except PyMongoError:
        raise HTTPException(
                status_code=503,
                detail= "Database temporarily unavailable. Please try again later."
            )

@router.get("/{project_id}")
def get_project(project_id: str):
    
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )

    try:
        project = projects_collection.find_one(
            {"_id": ObjectId(project_id)},
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        project["id"] = str(project.pop("_id"))

        return project

    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail = "Database temporarily unavailable. Please Try Again Later"
        )

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_admin: str = Depends(get_current_admin)
):

    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )
    
    try:    
        result = projects_collection.delete_one(
            {"_id":ObjectId(project_id)}
        )

        if result.deleted_count ==0:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
        
        return{
            "message": "project deleted successfully"
        }

    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

@router.put("/{project_id}")
def update_project(
    project_id:str,
    project: ProjectSchema,
    current_admin: str = Depends(get_current_admin)
):

    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid Project Id"
        )

    try:
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set":project.model_dump()}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project not Found"
            )
        return{
            "message": "Project Updated Successfully"
        }

    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail= "Database temporarily unavailable. Please try later."
        )