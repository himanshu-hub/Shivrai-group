
# D:\Codes\shivrai-group\Backend\app\routes\image_routes.py

import io
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import cloudinary.api
import cloudinary.uploader


from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import PyMongoError

from app.auth import get_current_admin
from app.database import projects_collection
from app.utils.cloudinary_upload import upload_project_image


router = APIRouter(
    prefix="/images",
    tags=["Image Management"],
    dependencies=[Depends(get_current_admin)],
)

media_collection = projects_collection.database["media"]

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_GALLERY_IMAGES = 20
MAX_UPLOAD_FILES = 5
CLOUDINARY_FOLDER = "shivrai-group/projects/"


# =============================================
# MEDIA LIBRARY RESPONSE MODELS
# =============================================

class ImageUploadResponse(BaseModel):
    message: str
    media_id: str
    image_url: str
    public_id: str
    saved_in_media_library: bool


class CoverUploadResponse(BaseModel):
    message: str
    project_id: str
    image_url: str
    public_id: str
    saved_in_media_library: bool


class GalleryAssetResponse(BaseModel):
    url: str
    public_id: str


class GalleryUploadResponse(BaseModel):
    message: str
    project_id: str
    uploaded_count: int
    gallery: list[str]
    gallery_assets: list[GalleryAssetResponse]
    saved_in_media_library: bool


class CoverRemovalResponse(BaseModel):
    message: str
    project_id: str
    kept_in_media_library: bool


class GalleryRemovalResponse(CoverRemovalResponse):
    public_id: str


class ImageDeletionResponse(BaseModel):
    message: str
    public_id: str
    deleted_from_cloudinary: bool
    deleted_from_media_library: bool


class CloudinarySyncResponse(BaseModel):
    message: str
    processed: int
    next_cursor: str | None = None
    complete: bool


class CoverSelectionResponse(BaseModel):
    message: str
    project_id: str
    media_id: str
    image_url: str
    uploaded_again: bool


class GallerySelectionResponse(BaseModel):
    message: str
    project_id: str
    selected_count: int
    gallery: list[str]
    uploaded_again: bool


class ImageUsageResponse(BaseModel):
    project_id: str
    project_name: str
    role: str


class MediaImageResponse(BaseModel):
    id: str
    public_id: str
    image_url: str
    filename: str | None = None
    uploaded_at: datetime | None = None
    in_use: bool
    used_in: list[ImageUsageResponse]


class MediaListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    images: list[MediaImageResponse]


class MediaDetailsResponse(MediaImageResponse):
    usage_count: int
    can_delete: bool


class BulkDeleteResultResponse(BaseModel):
    media_id: str
    status: str
    public_id: str | None = None
    reason: str | None = None


class BulkDeleteResponse(BaseModel):
    message: str
    deleted_count: int
    skipped_count: int
    deleted: list[BulkDeleteResultResponse]
    skipped: list[BulkDeleteResultResponse]


class ProjectMediaStatsResponse(BaseModel):
    project_id: str
    project_name: str
    cover_count: int
    gallery_count: int
    total_images: int


class MediaStatsResponse(BaseModel):
    total_images: int
    used_images: int
    unused_images: int
    cover_images: int
    gallery_images: int
    total_projects: int
    projects: list[ProjectMediaStatsResponse]


# =============================================
# DATABASE INDEXES
# =============================================

media_collection.create_index(
    [("public_id", ASCENDING)],
    unique=True,
)

media_collection.create_index(
    [("uploaded_at", DESCENDING)]
)


# =============================================
# HELPERS
# =============================================

def validate_project_id(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID",
        )

    return ObjectId(project_id)


def get_project(project_id: str):
    object_id = validate_project_id(project_id)

    try:
        project = projects_collection.find_one(
            {"_id": object_id}
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


async def validate_image(image: UploadFile):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WebP are allowed",
        )

    data = await image.read(MAX_IMAGE_SIZE + 1)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Image is empty",
        )

    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum image size is 10 MB",
        )

    valid_signatures = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(
            b"\x89PNG\r\n\x1a\n"
        ),
        "image/webp": (
            len(data) >= 12
            and data[:4] == b"RIFF"
            and data[8:12] == b"WEBP"
        ),
    }

    if not valid_signatures.get(image.content_type):
        raise HTTPException(
            status_code=400,
            detail="Invalid image content",
        )

    return data


async def upload_cloudinary(data: bytes):
    try:
        return await run_in_threadpool(
            upload_project_image,
            io.BytesIO(data),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Cloudinary upload failed",
        ) from exc


async def delete_cloudinary_asset(public_id: str):
    try:
        result = await run_in_threadpool(
            cloudinary.uploader.destroy,
            public_id,
            resource_type="image",
            invalidate=True,
        )

        return result.get("result") in (
            "ok",
            "not found",
        )

    except Exception:
        return False


def reserve_media_image(media_id: str):
    if not ObjectId.is_valid(media_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid media ID"
        )

    media = media_collection.find_one_and_update(
        {
            "_id": ObjectId(media_id),
            "deleting": {"$ne": True}
        },
        {
            "$inc": {"active_operations": 1}
        },
        return_document=ReturnDocument.AFTER
    )

    if not media:
        raise HTTPException(
            status_code=409,
            detail="Image unavailable or being deleted"
        )

    return media


def release_media_image(media_id: str):
    media_collection.update_one(
        {
            "_id": ObjectId(media_id),
            "active_operations": {"$gt": 0}
        },
        {
            "$inc": {"active_operations": -1}
        }
    )



async def upload_and_reserve_image(
    data: bytes,
    filename: str | None = None
):
    uploaded = await upload_cloudinary(data)

    try:
        # Register and reserve in one atomic
        # MongoDB operation.
        media = media_collection.find_one_and_update(
            {
                "public_id": uploaded["public_id"],
                "deleting": {"$ne": True}
            },
            {
                "$setOnInsert": {
                    "url": uploaded["url"],
                    "filename": filename,
                    "uploaded_at": datetime.now(timezone.utc)
                },
                "$inc": {
                    "active_operations": 1
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        if not media:
            raise HTTPException(
                status_code=409,
                detail="Image unavailable"
            )

        return uploaded, str(media["_id"])

    except PyMongoError as exc:
        # Preserve Cloudinary upload for reconciliation.
        raise HTTPException(
            status_code=503,
            detail=(
                "Image uploaded to Cloudinary, "
                "but Media Library reservation failed"
            )
        ) from exc

# =============================================
# SAFE PERMANENT MEDIA DELETION
# =============================================


async def permanently_delete_media(media_id: str):
    if not ObjectId.is_valid(media_id):
        return {
            "media_id": media_id,
            "status": "skipped",
            "reason": "Invalid media ID"
        }

    object_id = ObjectId(media_id)
    claimed = False
    cloudinary_deleted = False

    try:
        # Claim only images with no active operations.
        media = media_collection.find_one_and_update(
            {
                "_id": object_id,
                "deleting": {"$ne": True},
                "$or": [
                    {"active_operations": 0},
                    {
                        "active_operations": {
                            "$exists": False
                        }
                    }
                ]
            },
            {
                "$set": {
                    "deleting": True
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not media:
            return {
                "media_id": media_id,
                "status": "skipped",
                "reason": (
                    "Image missing, busy or being deleted"
                )
            }

        claimed = True

        public_id = media.get("public_id")
        image_url = media.get("url")

        if not public_id or not image_url:
            return {
                "media_id": media_id,
                "status": "skipped",
                "reason": "Incomplete media record"
            }

        validate_public_id(public_id)

        # Verify image details with Cloudinary.
        cloud_asset = await run_in_threadpool(
            cloudinary.api.resource,
            public_id,
            resource_type="image"
        )

        actual_url = cloud_asset.get("secure_url")

        if not actual_url:
            return {
                "media_id": media_id,
                "status": "skipped",
                "reason": "Cloudinary URL unavailable"
            }

        urls = list({
            image_url,
            actual_url
        })

        # Block deletion if used anywhere in projects.
        references = projects_collection.count_documents({
            "$or": [
                {"image_public_id": public_id},
                {"gallery_assets.public_id": public_id},
                {"image": {"$in": urls}},
                {"gallery": {"$in": urls}}
            ]
        })

        if references > 0:
            return {
                "media_id": media_id,
                "status": "skipped",
                "reason": "Image is used by a project"
            }

        # Permanently delete the Cloudinary asset.
        cloudinary_deleted = await delete_cloudinary_asset(
            public_id
        )

        if not cloudinary_deleted:
            return {
                "media_id": media_id,
                "status": "skipped",
                "reason": "Cloudinary deletion failed"
            }

        # Remove the claimed Media Library record.
        result = media_collection.delete_one({
            "_id": object_id,
            "public_id": public_id,
            "deleting": True
        })

        if result.deleted_count != 1:
            return {
                "media_id": media_id,
                "status": "error",
                "reason": (
                    "Cloudinary image deleted, but "
                    "Media Library cleanup was not confirmed"
                )
            }

        return {
            "media_id": media_id,
            "public_id": public_id,
            "status": "deleted"
        }

    except Exception as exc:
        return {
            "media_id": media_id,
            "status": "error",
            "reason": (
                "Database cleanup failed after Cloudinary deletion"
                if cloudinary_deleted
                else f"Deletion failed: {type(exc).__name__}"
            )
        }

    finally:
        # Release unsuccessful deletion claims.
        # Preserve the claim if Cloudinary deletion
        # succeeded but database cleanup failed.
        if claimed and not cloudinary_deleted:
            try:
                media_collection.update_one(
                    {
                        "_id": object_id,
                        "deleting": True
                    },
                    {
                        "$unset": {
                            "deleting": ""
                        }
                    }
                )
            except PyMongoError:
                pass


def register_media_asset(
    uploaded: dict,
    filename: str | None = None,
):
    media_collection.update_one(
        {
            "public_id": uploaded["public_id"]
        },
        {
            "$setOnInsert": {
                "public_id": uploaded["public_id"],
                "url": uploaded["url"],
                "filename": filename,
                "uploaded_at": datetime.now(
                    timezone.utc
                ),
            }
        },
        upsert=True,
    )


def find_image_references(
    public_id: str,
    image_url: str,
):
    return list(
        projects_collection.find(
            {
                "$or": [
                    {"image_public_id": public_id},
                    {"gallery_assets.public_id": public_id},
                    {"image": image_url},
                    {"gallery": image_url},
                ]
            },
            {
                "name": 1,
                "image": 1,
                "image_public_id": 1,
                "gallery": 1,
                "gallery_assets": 1,
            },
        )
    )


def get_image_usage(
    public_id: str,
    image_url: str,
):
    projects = find_image_references(
        public_id,
        image_url,
    )

    used_in = []

    for project in projects:
        project_id = str(project["_id"])
        project_name = project.get(
            "name",
            "Unnamed Project",
        )

        if (
            project.get("image_public_id") == public_id
            or project.get("image") == image_url
        ):
            used_in.append({
                "project_id": project_id,
                "project_name": project_name,
                "role": "cover",
            })

        gallery_assets = (
            project.get("gallery_assets") or []
        )

        gallery_match = any(
            isinstance(asset, dict)
            and asset.get("public_id") == public_id
            for asset in gallery_assets
        )

        if (
            gallery_match
            or image_url in (
                project.get("gallery") or []
            )
        ):
            used_in.append({
                "project_id": project_id,
                "project_name": project_name,
                "role": "gallery",
            })

    return used_in


def validate_public_id(public_id: str):
    if not public_id.startswith(CLOUDINARY_FOLDER):
        raise HTTPException(
            status_code=400,
            detail="Image is outside the project folder",
        )

    if any(
        part in ("", ".", "..")
        for part in public_id.split("/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid public ID",
        )


# =============================================
# 1. UPLOAD IMAGE TO MEDIA LIBRARY
# POST /images/upload
# =============================================


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    image: UploadFile = File(...)
):
    reserved_media_id = None

    try:
        data = await validate_image(image)

        uploaded, reserved_media_id = (
            await upload_and_reserve_image(
                data,
                filename=image.filename
            )
        )

        return {
            "message": "Image uploaded successfully",
            "media_id": reserved_media_id,
            "image_url": uploaded["url"],
            "public_id": uploaded["public_id"],
            "saved_in_media_library": True
        }

    finally:
        if reserved_media_id:
            try:
                release_media_image(reserved_media_id)
            except PyMongoError:
                pass

        await image.close()


# =============================================
# 2. UPLOAD OR REPLACE PROJECT COVER
# POST /images/projects/{project_id}/cover
# =============================================


@router.post("/projects/{project_id}/cover", response_model=CoverUploadResponse)
async def upload_project_cover(
    project_id: str,
    image: UploadFile = File(...)
):
    reserved_media_id = None

    try:
        project = get_project(project_id)
        data = await validate_image(image)

        uploaded, reserved_media_id = (
            await upload_and_reserve_image(
                data,
                filename=image.filename
            )
        )

        try:
            result = projects_collection.update_one(
                {"_id": project["_id"]},
                {
                    "$set": {
                        "image": uploaded["url"],
                        "image_public_id": uploaded["public_id"]
                    }
                }
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=503,
                detail="Unable to update project cover"
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project no longer exists"
            )

        return {
            "message": "Project cover uploaded successfully",
            "project_id": project_id,
            "image_url": uploaded["url"],
            "public_id": uploaded["public_id"],
            "saved_in_media_library": True
        }

    finally:
        if reserved_media_id:
            try:
                release_media_image(reserved_media_id)
            except PyMongoError:
                pass

        await image.close()

# =============================================
# 3. UPLOAD PROJECT GALLERY IMAGES
# POST /images/projects/{project_id}/gallery
# =============================================


@router.post("/projects/{project_id}/gallery", response_model=GalleryUploadResponse)
async def upload_project_gallery(
    project_id: str,
    images: list[UploadFile] = File(...)
):
    reserved_media_ids = []
    uploaded_assets = []

    try:
        if not 1 <= len(images) <= MAX_UPLOAD_FILES:
            raise HTTPException(
                status_code=400,
                detail="Upload between 1 and 5 images"
            )

        project = get_project(project_id)

        existing_gallery = project.get("gallery") or []

        if (
            len(existing_gallery) + len(images)
            > MAX_GALLERY_IMAGES
        ):
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 gallery images allowed"
            )

        # Validate all images before uploading.
        validated_images = []

        for image in images:
            validated_images.append(
                await validate_image(image)
            )

        # Upload, register and reserve every image.
        for index, data in enumerate(validated_images):
            uploaded, media_id = (
                await upload_and_reserve_image(
                    data,
                    filename=images[index].filename
                )
            )

            reserved_media_ids.append(media_id)
            uploaded_assets.append(uploaded)

        gallery_urls = [
            asset["url"]
            for asset in uploaded_assets
        ]

        gallery_metadata = [
            {
                "url": asset["url"],
                "public_id": asset["public_id"]
            }
            for asset in uploaded_assets
        ]

        # Attach images atomically.
        try:
            result = projects_collection.update_one(
                {
                    "_id": project["_id"],
                    "$expr": {
                        "$lte": [
                            {
                                "$size": {
                                    "$ifNull": [
                                        "$gallery",
                                        []
                                    ]
                                }
                            },
                            MAX_GALLERY_IMAGES
                            - len(gallery_urls)
                        ]
                    }
                },
                {
                    "$push": {
                        "gallery": {
                            "$each": gallery_urls
                        },
                        "gallery_assets": {
                            "$each": gallery_metadata
                        }
                    }
                }
            )

        except PyMongoError as exc:
            raise HTTPException(
                status_code=503,
                detail="Unable to save project gallery"
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Project changed or gallery limit reached. "
                    "Uploaded images remain in Media Library."
                )
            )

        return {
            "message": "Gallery uploaded successfully",
            "project_id": project_id,
            "uploaded_count": len(gallery_urls),
            "gallery": gallery_urls,
            "gallery_assets": gallery_metadata,
            "saved_in_media_library": True
        }

    finally:
        # Release reservations even if attachment fails.
        for media_id in reversed(reserved_media_ids):
            try:
                release_media_image(media_id)
            except PyMongoError:
                pass

        for image in images:
            await image.close()


# =============================================
# 4. REMOVE COVER FROM WEBSITE
# DELETE /images/projects/{project_id}/cover
#
# The Cloudinary asset is NOT deleted.
# =============================================

@router.delete("/projects/{project_id}/cover", response_model=CoverRemovalResponse)
async def remove_project_cover(
    project_id: str,
):
    project = get_project(project_id)

    old_url = project.get("image")
    old_public_id = project.get("image_public_id")

    if not old_url:
        raise HTTPException(
            status_code=404,
            detail="Project has no cover",
        )

    try:
        result = projects_collection.update_one(
            {
                "_id": project["_id"],
                "image": old_url,
                "image_public_id": old_public_id,
            },
            {
                "$set": {"image": None},
                "$unset": {"image_public_id": ""},
            },
        )

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to remove cover",
        ) from exc

    if result.matched_count == 0:
        raise HTTPException(
            status_code=409,
            detail="Cover changed. Refresh and retry.",
        )

    return {
        "message": "Cover removed from project",
        "project_id": project_id,
        "kept_in_media_library": True,
    }


# =============================================
# 5. REMOVE ONE GALLERY IMAGE FROM WEBSITE
# DELETE /images/projects/{project_id}/gallery
#
# The Cloudinary asset is NOT deleted.
# =============================================

@router.delete("/projects/{project_id}/gallery", response_model=GalleryRemovalResponse)
async def remove_gallery_image(
    project_id: str,
    public_id: str = Query(...),
):
    project = get_project(project_id)

    gallery_assets = (
        project.get("gallery_assets") or []
    )

    asset = next(
        (
            item
            for item in gallery_assets
            if isinstance(item, dict)
            and item.get("public_id") == public_id
        ),
        None,
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Gallery image not found",
        )

    image_url = asset["url"]

    try:
        result = projects_collection.update_one(
            {
                "_id": project["_id"],
                "gallery_assets": {
                    "$elemMatch": {
                        "public_id": public_id,
                        "url": image_url,
                    }
                },
            },
            {
                "$pull": {
                    "gallery": image_url,
                    "gallery_assets": {
                        "public_id": public_id
                    },
                }
            },
        )

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to update gallery",
        ) from exc

    if result.matched_count == 0:
        raise HTTPException(
            status_code=409,
            detail="Gallery changed. Refresh and retry.",
        )

    return {
        "message": "Image removed from gallery",
        "project_id": project_id,
        "public_id": public_id,
        "kept_in_media_library": True,
    }


# =============================================
# DELETE SINGLE UNUSED IMAGE
# DELETE /images/unused
# =============================================

@router.delete("/unused", response_model=ImageDeletionResponse)
async def delete_unused_image(
    public_id: str = Query(..., min_length=1),
):
    validate_public_id(public_id)

    try:
        media = media_collection.find_one({
            "public_id": public_id
        })

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Media Library unavailable"
        ) from exc

    if not media:
        raise HTTPException(
            status_code=404,
            detail="Image not found in Media Library"
        )

    # Uses the shared deletion helper to:
    # 1. Block deletion during image selection
    # 2. Check project references
    # 3. Delete the Cloudinary asset
    # 4. Remove the Media Library record
    result = await permanently_delete_media(
        str(media["_id"])
    )

    if result["status"] == "deleted":
        return {
            "message": "Image permanently deleted",
            "public_id": public_id,
            "deleted_from_cloudinary": True,
            "deleted_from_media_library": True
        }

    reason = result.get(
        "reason",
        "Unable to delete image"
    )

    if reason == "Image is used by a project":
        status_code = 409
    elif reason in (
        "Image busy, missing or being deleted",
        "Image missing, busy or being deleted",
    ):
        status_code = 409
    elif result["status"] == "error":
        status_code = 503
    else:
        status_code = 502

    raise HTTPException(
        status_code=status_code,
        detail=reason
    )

# =============================================
# 8. SYNC EXISTING CLOUDINARY IMAGES
# POST /images/sync-cloudinary
#
# Run until complete = true.
# =============================================

@router.post("/sync-cloudinary", response_model=CloudinarySyncResponse)
async def sync_cloudinary_images(
    next_cursor: str | None = None,
):
    try:
        options = {
            "type": "upload",
            "resource_type": "image",
            "prefix": CLOUDINARY_FOLDER,
            "max_results": 100,
        }

        if next_cursor:
            options["next_cursor"] = next_cursor

        response = await run_in_threadpool(
            cloudinary.api.resources,
            **options,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch Cloudinary images",
        ) from exc

    imported = 0

    try:
        for asset in response.get("resources", []):
            public_id = asset.get("public_id")
            image_url = asset.get("secure_url")

            if not public_id or not image_url:
                continue

            register_media_asset(
                {
                    "public_id": public_id,
                    "url": image_url,
                },
                filename=asset.get("display_name"),
            )

            imported += 1

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Cloudinary sync database error",
        ) from exc

    cursor = response.get("next_cursor")

    return {
        "message": "Cloudinary sync completed for this page",
        "processed": imported,
        "next_cursor": cursor,
        "complete": not bool(cursor),
    }

# =============================================
# MEDIA LIBRARY IMAGE SELECTION
# =============================================

class CoverSelection(BaseModel):
    media_id: str


class GallerySelection(BaseModel):
    media_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=20
    )


def get_media_by_id(media_id: str):
    if not ObjectId.is_valid(media_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid media ID"
        )

    try:
        media = media_collection.find_one({
            "_id": ObjectId(media_id)
        })

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to access Media Library"
        ) from exc

    if not media:
        raise HTTPException(
            status_code=404,
            detail="Image not found in Media Library"
        )

    return media


# =============================================
# 9. SELECT EXISTING IMAGE AS PROJECT COVER
# POST /images/projects/{project_id}/cover/select
# =============================================


@router.post("/projects/{project_id}/cover/select", response_model=CoverSelectionResponse)
async def select_project_cover(
    project_id: str,
    selection: CoverSelection
):
    project = get_project(project_id)

    try:
        media = reserve_media_image(
            selection.media_id
        )

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Media Library unavailable"
        ) from exc

    try:
        result = projects_collection.update_one(
            {"_id": project["_id"]},
            {
                "$set": {
                    "image": media["url"],
                    "image_public_id": media["public_id"]
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Project no longer exists"
            )

        return {
            "message": "Cover selected successfully",
            "project_id": project_id,
            "media_id": selection.media_id,
            "image_url": media["url"],
            "uploaded_again": False
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to update project cover"
        ) from exc

    finally:
        try:
            release_media_image(selection.media_id)
        except PyMongoError:
            # Reconcile stuck reservations with recovery script.
            pass


# =============================================
# 10. SELECT EXISTING GALLERY IMAGES
# POST /images/projects/{project_id}/gallery/select
# =============================================


@router.post("/projects/{project_id}/gallery/select", response_model=GallerySelectionResponse)
async def select_project_gallery(
    project_id: str,
    selection: GallerySelection
):
    project = get_project(project_id)

    media_ids = selection.media_ids

    if len(media_ids) != len(set(media_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate media IDs are not allowed"
        )

    reserved_ids = []
    selected_media = []

    try:
        # Reserve every selected image before attaching.
        for media_id in sorted(media_ids):
            try:
                media = reserve_media_image(media_id)
            except PyMongoError as exc:
                raise HTTPException(
                    status_code=503,
                    detail="Media Library unavailable"
                ) from exc

            reserved_ids.append(media_id)
            selected_media.append(media)

        selected_urls = [
            media["url"]
            for media in selected_media
        ]

        selected_public_ids = [
            media["public_id"]
            for media in selected_media
        ]

        existing_gallery = project.get("gallery") or []
        existing_assets = project.get("gallery_assets") or []

        existing_public_ids = {
            asset.get("public_id")
            for asset in existing_assets
            if isinstance(asset, dict)
        }

        if (
            any(url in existing_gallery for url in selected_urls)
            or any(
                public_id in existing_public_ids
                for public_id in selected_public_ids
            )
        ):
            raise HTTPException(
                status_code=409,
                detail="Image already exists in project gallery"
            )

        if (
            len(existing_gallery) + len(selected_media)
            > MAX_GALLERY_IMAGES
        ):
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 gallery images allowed"
            )

        gallery_metadata = [
            {
                "url": media["url"],
                "public_id": media["public_id"]
            }
            for media in selected_media
        ]

        try:
            result = projects_collection.update_one(
                {
                    "_id": project["_id"],
                    "gallery": {
                        "$nin": selected_urls
                    },
                    "gallery_assets.public_id": {
                        "$nin": selected_public_ids
                    },
                    "$expr": {
                        "$lte": [
                            {
                                "$size": {
                                    "$ifNull": ["$gallery", []]
                                }
                            },
                            MAX_GALLERY_IMAGES
                            - len(selected_media)
                        ]
                    }
                },
                {
                    "$push": {
                        "gallery": {
                            "$each": selected_urls
                        },
                        "gallery_assets": {
                            "$each": gallery_metadata
                        }
                    }
                }
            )

        except PyMongoError as exc:
            raise HTTPException(
                status_code=503,
                detail="Unable to update project gallery"
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Project changed, gallery limit reached, "
                    "or selected images already exist"
                )
            )

        return {
            "message": "Gallery images selected successfully",
            "project_id": project_id,
            "selected_count": len(selected_media),
            "gallery": selected_urls,
            "uploaded_again": False
        }

    finally:
        # Release all successfully reserved images,
        # even when an error occurs.
        for media_id in reversed(reserved_ids):
            try:
                release_media_image(media_id)
            except PyMongoError:
                # A failed release requires reconciliation.
                # It must not mask the original result.
                pass


# =============================================
# MEDIA LIBRARY LISTING + PROJECT FILTER
# GET /images/
# =============================================


@router.get("/", response_model=MediaListResponse)
async def get_media_library(
    project_id: str | None = None,
    project_name: str | None = None,
    usage: str = Query(
        "all",
        pattern="^(all|used|unused|cover|gallery)$"
    ),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query(
        "newest",
        pattern="^(newest|oldest|filename_asc|filename_desc)$"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    if project_id:
        validate_project_id(project_id)

    try:
        assets = list(
            media_collection.find({
                "deleting": {"$ne": True}
            }).sort("uploaded_at", DESCENDING)
        )

        urls = [asset["url"] for asset in assets]
        public_ids = [
            asset["public_id"] for asset in assets
        ]

        projects = list(
            projects_collection.find(
                {
                    "$or": [
                        {"image": {"$in": urls}},
                        {"gallery": {"$in": urls}},
                        {
                            "image_public_id": {
                                "$in": public_ids
                            }
                        },
                        {
                            "gallery_assets.public_id": {
                                "$in": public_ids
                            }
                        }
                    ]
                },
                {
                    "name": 1,
                    "image": 1,
                    "image_public_id": 1,
                    "gallery": 1,
                    "gallery_assets": 1
                }
            )
        )

        results = []

        for asset in assets:
            public_id = asset["public_id"]
            image_url = asset["url"]
            used_in = []

            for project in projects:
                roles = []

                if (
                    project.get("image") == image_url
                    or project.get("image_public_id") == public_id
                ):
                    roles.append("cover")

                gallery_assets = (
                    project.get("gallery_assets") or []
                )

                gallery_match = any(
                    isinstance(item, dict)
                    and item.get("public_id") == public_id
                    for item in gallery_assets
                )

                if (
                    gallery_match
                    or image_url in (project.get("gallery") or [])
                ):
                    roles.append("gallery")

                for role in roles:
                    used_in.append({
                        "project_id": str(project["_id"]),
                        "project_name": project.get(
                            "name", "Unnamed Project"
                        ),
                        "role": role
                    })

            # Search filename, public ID, project name.
            if search:
                keyword = search.strip().lower()

                searchable = [
                    asset.get("filename") or "",
                    public_id,
                    *[
                        item["project_name"]
                        for item in used_in
                    ]
                ]

                if not any(
                    keyword in value.lower()
                    for value in searchable
                ):
                    continue

            # Filter by project ID.
            if project_id and not any(
                item["project_id"] == project_id
                for item in used_in
            ):
                continue

            # Filter by project name.
            if project_name and not any(
                project_name.lower()
                in item["project_name"].lower()
                for item in used_in
            ):
                continue

            roles = {
                item["role"] for item in used_in
            }

            if usage == "used" and not used_in:
                continue

            if usage == "unused" and used_in:
                continue

            if usage in ("cover", "gallery"):
                if usage not in roles:
                    continue

            results.append({
                "id": str(asset["_id"]),
                "public_id": public_id,
                "image_url": image_url,
                "filename": asset.get("filename"),
                "uploaded_at": asset.get("uploaded_at"),
                "in_use": bool(used_in),
                "used_in": used_in
            })

        # Sort before pagination.
        if sort_by == "oldest":
            results.reverse()

        elif sort_by == "filename_asc":
            results.sort(
                key=lambda item: (
                    (item.get("filename") or "").lower(),
                    item["id"]
                )
            )

        elif sort_by == "filename_desc":
            results.sort(
                key=lambda item: (
                    (item.get("filename") or "").lower(),
                    item["id"]
                ),
                reverse=True
            )

        total = len(results)
        start = (page - 1) * limit

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (
                total + limit - 1
            ) // limit,
            "images": results[start:start + limit]
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to load Media Library"
        ) from exc



# =============================================
# BULK DELETE UNUSED MEDIA
# POST /images/bulk-unused
# =============================================

class BulkDeleteRequest(BaseModel):
    media_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=20
    )



@router.post("/bulk-unused", response_model=BulkDeleteResponse)
async def bulk_delete_unused_images(
    request: BulkDeleteRequest
):
    results = []

    for media_id in dict.fromkeys(request.media_ids):
        result = await permanently_delete_media(media_id)
        results.append(result)

    deleted = [
        item for item in results
        if item["status"] == "deleted"
    ]

    skipped = [
        item for item in results
        if item["status"] != "deleted"
    ]

    return {
        "message": "Bulk deletion processed",
        "deleted_count": len(deleted),
        "skipped_count": len(skipped),
        "deleted": deleted,
        "skipped": skipped
    }


# =============================================
# GET SINGLE MEDIA IMAGE DETAILS
# GET /images/media/{media_id}
# =============================================

@router.get("/media/{media_id}", response_model=MediaDetailsResponse)
async def get_media_details(media_id: str):

    if not ObjectId.is_valid(media_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid media ID"
        )

    try:
        media = media_collection.find_one({
            "_id": ObjectId(media_id),
            "deleting": {"$ne": True}
        })

        if not media:
            raise HTTPException(
                status_code=404,
                detail="Media image not found"
            )

        used_in = get_image_usage(
            media["public_id"],
            media["url"]
        )

        return {
            "id": str(media["_id"]),
            "public_id": media["public_id"],
            "image_url": media["url"],
            "filename": media.get("filename"),
            "uploaded_at": media.get("uploaded_at"),
            "in_use": bool(used_in),
            "usage_count": len(used_in),
            "used_in": used_in,
            "can_delete": (not bool(used_in) and media.get("active_operations", 0) == 0)
        }

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Media Library unavailable"
        ) from exc




# =============================================
# MEDIA LIBRARY STATISTICS + PROJECT-WISE SUMMARY
# GET /images/stats
# =============================================

@router.get("/stats", response_model=MediaStatsResponse)
async def get_media_library_stats():
    try:
        assets = list(
            media_collection.find(
                {"deleting": {"$ne": True}},
                {"public_id": 1, "url": 1}
            )
        )

        projects = list(
            projects_collection.find(
                {},
                {
                    "name": 1,
                    "image": 1,
                    "image_public_id": 1,
                    "gallery": 1,
                    "gallery_assets": 1
                }
            ).sort("name", 1)
        )

        total_images = len(assets)
        used_images = 0
        cover_images = 0
        gallery_images = 0

        project_stats = {
            str(project["_id"]): {
                "project_id": str(project["_id"]),
                "project_name": project.get(
                    "name", "Unnamed Project"
                ),
                "cover_count": 0,
                "gallery_count": 0,
                "total_images": 0
            }
            for project in projects
        }

        for asset in assets:
            image_url = asset["url"]
            public_id = asset["public_id"]

            used_as_cover = False
            used_as_gallery = False

            for project in projects:
                project_id = str(project["_id"])
                stats = project_stats[project_id]

                is_cover = (
                    project.get("image") == image_url
                    or project.get("image_public_id")
                    == public_id
                )

                gallery_assets = (
                    project.get("gallery_assets") or []
                )

                is_gallery = (
                    image_url in (
                        project.get("gallery") or []
                    )
                    or any(
                        isinstance(item, dict)
                        and item.get("public_id")
                        == public_id
                        for item in gallery_assets
                    )
                )

                if is_cover:
                    used_as_cover = True
                    stats["cover_count"] += 1

                if is_gallery:
                    used_as_gallery = True
                    stats["gallery_count"] += 1

                if is_cover or is_gallery:
                    stats["total_images"] += 1

            if used_as_cover or used_as_gallery:
                used_images += 1

            if used_as_cover:
                cover_images += 1

            if used_as_gallery:
                gallery_images += 1

        return {
            "total_images": total_images,
            "used_images": used_images,
            "unused_images": total_images - used_images,
            "cover_images": cover_images,
            "gallery_images": gallery_images,
            "total_projects": len(projects),
            "projects": list(project_stats.values())
        }

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to load Media Library statistics"
        ) from exc
