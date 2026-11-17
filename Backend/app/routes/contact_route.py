from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import contacts_collection
from app.Schema.contact import ContactSchema
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bson import ObjectId
from pymongo.errors import PyMongoError
import re
from app.auth import get_current_admin


router = APIRouter(
    prefix="/contact",
    tags=["Contact"]
)

@router.post("/")
async def submit_contact(contact: ContactSchema):
    try:    
        contact_data = contact.model_dump()
        contact_data["status"] = "Pending"
        contact_data["created_at"] = datetime.now(timezone.utc)


        result = contacts_collection.insert_one(contact_data)

        return{
            "message": "Enquiry submitted successfully",
            "id": str(result.inserted_id),
            "created_at": contact_data["created_at"].astimezone(
                ZoneInfo("Asia/Kolkata")
            ).isoformat()
        }

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

@router.get("/{enquiry_id}")
async def get_enquiry(
    enquiry_id: str,
    current_admin: str = Depends(get_current_admin)
):

    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid Enquiry ID"
        )

    try:
        enquiry = contacts_collection.find_one(
            {"_id": ObjectId(enquiry_id)}
        )

        if not enquiry:
            raise HTTPException(
                status_code=404,
                detail="Enquiry not found"
            )
        
        enquiry["id"] = str(enquiry.pop("_id"))

        return enquiry
    
    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

@router.patch("/{enquiry_id}/status")
async def update_enquiry_status(
    enquiry_id: str, 
    status: str,
    current_admin: str = Depends(get_current_admin)
):

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

    try:
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

    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

@router.delete("/{enquiry_id}")
async def delete_enquiry(
    enquiry_id: str,
    current_admin: str = Depends(get_current_admin)
):

    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry ID"
        )

    try:    
        result = contacts_collection.delete_one(
            {"_id": ObjectId(enquiry_id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail = "Enquiry not found"
            )
        return{
            "message": "Enquiry deleted successfully"
        }

    except HTTPException:
        raise

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )    

@router.get("/")
async def get_enquiries(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    status: str | None = None,
    current_admin: str = Depends(get_current_admin)
):
    if search:
        search = search.strip()
        search = re.escape(search)

    if status and status not in ["Pending","Contacted", "Resolved"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry status"
        )

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

    try:
        enquiries = list(contacts_collection.find(query))

        for enquiry in enquiries:
            enquiry["id"] = str(enquiry.pop("_id"))

        return enquiries

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )