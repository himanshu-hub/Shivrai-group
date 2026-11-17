from fastapi import APIRouter
from app.database import projects_collection
from app.Schema.project import ProjectSchema
from bson import ObjectId
from fastapi import HTTPException, APIRouter, Query

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.get("/")
async def get_projects(
    status: str = None,
    search: str = None,
    category: str= None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = "newest"
):
    query = {}

    if search:
        query["$or"]= [
            {"name":{"$regex": search, "$options":"i"}},
            {"location":{"$regex": search, "$options":"i"}},
            {"description":{"$regex": search, "$options":"i"}},
            {"category":{"$regex": search, "$options":"i"}}
        ]

    if status:
        query["status"] = status

    if category:
        query["category"] = category

    skip = (page - 1) *limit    

    if sort_by == "newest":
        sort_option =[("_id", -1)]

    elif sort_by == "oldest":
        sort_option = [("_id", 1)]

    elif sort_by == "name_asc":
        sort_option = [("name", 1)]

    elif sort_by == "name_desc":
        sort_option = [("name", -1)]    

    else:
        raise HTTPException(
            status_code=400,
            detail="invalid sorting option"
        )

    projects = list(
        projects_collection.find(query)
        .sort(sort_option)
        .skip(skip)
        .limit(limit)
    )

    for project in projects:
        project["id"] = str(project.pop("_id"))

    total_projects = projects_collection.count_documents(query)

    return {
        "total_projects": total_projects,
        "current_page" : page,
        "total_pages" : (total_projects + limit - 1) // limit,
        "projects": projects
    }        
    # projects = list(projects_collection.find({},{"_id": 0}))
    # return projects


@router.post("/")
async def create_project(project: ProjectSchema):
    try:
            project_data = project.model_dump()
            result = projects_collection.insert_one(project_data)

        #project_data = project.dict()
        #result = projects_collection.insert_one(project_data)

            return {
            "message":"Project Created Successfully",
            "ID": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail= "Failed to create project"
            )


@router.get("/{project_id}")
async def get_project(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )


    project = projects_collection.find_one(
        {"_id": ObjectId(project_id)},
        {"_id": 0}
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )
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
@router.put("/{project_id}")
async def update_project(project_id:str, project: ProjectSchema):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid Project Id"
        )
    result = projects_collection.update_one(
        {"_id": ObjectId(project_id)},
        {"$set":project.dict()}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Project not Found"
        )
    return{
        "message": "Project Updated Successfully"
    }