
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.database import contacts_collection
from app.Schema.contact import ContactSchema
from app.auth import get_current_admin


router = APIRouter(
    prefix="/contact",
    tags=["Contact"]
)


# =============================================
# RESPONSE MODELS
# =============================================

class ContactSubmissionResponse(BaseModel):
    message: str
    id: str
    created_at: datetime


class EnquiryResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    subject: str | None = None
    message: str
    status: str = "Pending"
    created_at: datetime | None = None


class EnquiryListResponse(BaseModel):
    total_enquiries: int
    current_page: int
    total_pages: int
    enquiries: list[EnquiryResponse] = Field(
        default_factory=list
    )


class EnquiryStatusResponse(BaseModel):
    message: str
    status: str


class ContactMessageResponse(BaseModel):
    message: str


# =============================================
# SUBMIT CONTACT ENQUIRY
# PUBLIC
# =============================================

@router.post(
    "/",
    response_model=ContactSubmissionResponse
)
def submit_contact(contact: ContactSchema):
    try:
        contact_data = contact.model_dump()

        contact_data["status"] = "Pending"

        contact_data["created_at"] = (
            datetime.now(timezone.utc)
        )

        result = contacts_collection.insert_one(
            contact_data
        )

        return {
            "message": "Enquiry submitted successfully",
            "id": str(result.inserted_id),
            "created_at": (
                contact_data["created_at"].astimezone(
                    ZoneInfo("Asia/Kolkata")
                )
            )
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database temporarily unavailable. "
                "Please try again later."
            )
        ) from exc


# =============================================
# GET ALL ENQUIRIES
# ADMIN ONLY
# =============================================

@router.get(
    "/",
    response_model=EnquiryListResponse
)
def get_enquiries(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100
    ),
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_admin: str = Depends(get_current_admin)
):
    if status and status not in [
        "Pending",
        "Contacted",
        "Resolved"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry status"
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
                    "email": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                },
                {
                    "phone": {
                        "$regex": safe_search,
                        "$options": "i"
                    }
                }
            ]

    if status:
        query["status"] = status

    try:
        skip = (page - 1) * limit

        enquiries = list(
            contacts_collection.find(query)
            .sort("_id", -1)
            .skip(skip)
            .limit(limit)
        )

        total_enquiries = (
            contacts_collection.count_documents(query)
        )

        for enquiry in enquiries:
            enquiry["id"] = str(
                enquiry.pop("_id")
            )

        return {
            "total_enquiries": total_enquiries,
            "current_page": page,
            "total_pages": (
                total_enquiries + limit - 1
            ) // limit,
            "enquiries": enquiries
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database temporarily unavailable. "
                "Please try again later."
            )
        ) from exc


# =============================================
# GET SINGLE ENQUIRY
# ADMIN ONLY
# =============================================

@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse
)
def get_enquiry(
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

        enquiry["id"] = str(
            enquiry.pop("_id")
        )

        return enquiry

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database temporarily unavailable. "
                "Please try again later."
            )
        ) from exc


# =============================================
# UPDATE ENQUIRY STATUS
# ADMIN ONLY
# =============================================

@router.patch(
    "/{enquiry_id}/status",
    response_model=EnquiryStatusResponse
)
def update_enquiry_status(
    enquiry_id: str,
    status: str,
    current_admin: str = Depends(get_current_admin)
):
    if not ObjectId.is_valid(enquiry_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry ID"
        )

    if status not in [
        "Pending",
        "Contacted",
        "Resolved"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid enquiry status"
        )

    try:
        result = contacts_collection.update_one(
            {"_id": ObjectId(enquiry_id)},
            {
                "$set": {
                    "status": status
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Enquiry not found"
            )

        return {
            "message": "Enquiry status updated successfully",
            "status": status
        }

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database temporarily unavailable. "
                "Please try again later."
            )
        ) from exc


# =============================================
# DELETE ENQUIRY
# ADMIN ONLY
# =============================================

@router.delete(
    "/{enquiry_id}",
    response_model=ContactMessageResponse
)
def delete_enquiry(
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
                detail="Enquiry not found"
            )

        return {
            "message": "Enquiry deleted successfully"
        }

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Database temporarily unavailable. "
                "Please try again later."
            )
        ) from exc
