from fastapi import APIRouter
from app.database import contacts_collection
from app.Schema.contact import ContactSchema
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bson import ObjectId
from fastapi import HTTPException
from fastapi import Query


router = APIRouter(
    prefix="/contact",
    tags=["Contact"]
)


@router.post("/")
async def submit_contact(contact: ContactSchema):
    contact_data = contact.dict()
    contact_data["status"] = "Pending"
    contact_data["created_at"] = datetime.now(timezone.utc)


    result = contacts_collection.insert_one(contact_data)

    return{
        "message": "Enquiry submitted successfully",
        "ID": str(result.inserted_id),
        "created_at": contact_data["created_at"].astimezone(
            ZoneInfo("Asia/Kolkata")
        ).isoformat()
    }

# @router.get("/")
# async def get_enquiries():
#     enquiries = list(
#         contacts_collection.find({},{"_id": 0})
#     )
#     return enquiries

@router.get("/{enquiry_id}")
async def get_enquiry(enquiry_id: str):
    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid Enquiry ID"
        )
    enquiry = contacts_collection.find_one(
        {"_id": ObjectId(enquiry_id)}
    )

    if not enquiry:
        raise HTTPException(
            status_code=404,
            detail="Enquiry not found"
        )
    enquiry["_id"] = str(enquiry["_id"])

    return enquiry

@router.patch("/{enquiry_id}/status")
async def update_enquiry_status(enquiry_id: str, status: str):
    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry ID"
        )

    if status not in ["Pending","Contacted","Resolved"]:
        raise HTTPException(
        status_code=400,
        detail="Invalid enquiry Status"
      )

    result = contacts_collection.update_one(
        {"_id": ObjectId(enquiry_id)},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        raise HTTPException(
        status_code=404,
        detail= "Enquiry Not Found"
        )

    return{
        "message":"Enquiry status updated successfully",
        "status": status
    }

@router.delete("/{enquiry_id}")
async def delete_enquiry(enquiry_id: str):
    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry ID"
        )
    result = contacts_collection.delete_one(
        {"_id": ObjectId(enquiry_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail = "Enquiry not found"
        )

@router.get("/")
async def get_enquiries(search: str = None, status: str = None):

    if search and status:
        query = {
            "$and": [
                {"status": status},
                {
                    "$or": [
                        {"name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}},
                        {"phone": {"$regex": search, "$options": "i"}}
                    ]
                }
            ]
        }

    elif search:
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        }

    elif status:
        query = {"status": status}

    else:
        query = {}

    enquiries = list(contacts_collection.find(query))

    for enquiry in enquiries:
        enquiry["_id"] = str(enquiry["_id"])

    return enquiries