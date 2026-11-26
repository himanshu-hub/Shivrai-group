
from collections import Counter

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from pymongo.errors import PyMongoError

from app.auth import get_current_admin
from app.database import projects_collection


router = APIRouter(
    prefix="/images",
    tags=["Image Management"],
    dependencies=[Depends(get_current_admin)]
)


class GalleryOrderRequest(BaseModel):
    ordered_urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=20
    )

    @field_validator("ordered_urls")
    @classmethod
    def validate_order(cls, urls: list[str]):
        if any(not url.strip() for url in urls):
            raise ValueError("Image URLs cannot be empty")

        if len(urls) != len(set(urls)):
            raise ValueError("Duplicate images are not allowed")

        return urls


class GalleryOrderResponse(BaseModel):
    message: str
    project_id: str
    gallery: list[str]
    gallery_assets: list[dict]
    total_images: int


@router.put(
    "/projects/{project_id}/gallery/order",
    response_model=GalleryOrderResponse
)
def reorder_project_gallery(
    project_id: str,
    request: GalleryOrderRequest
):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID"
        )

    object_id = ObjectId(project_id)

    try:
        project = projects_collection.find_one(
            {"_id": object_id}
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        current_gallery = project.get("gallery") or []
        new_order = request.ordered_urls

        if not current_gallery:
            raise HTTPException(
                status_code=400,
                detail="Project gallery is empty"
            )

        if (
            len(current_gallery) != len(set(current_gallery))
            or Counter(current_gallery) != Counter(new_order)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Image order must contain exactly "
                    "the current gallery images"
                )
            )

        existing_assets = (
            project.get("gallery_assets") or []
        )

        asset_by_url = {}

        for asset in existing_assets:
            if not isinstance(asset, dict):
                raise HTTPException(
                    status_code=409,
                    detail="Invalid gallery metadata"
                )

            url = asset.get("url")

            if (
                not url
                or url in asset_by_url
                or url not in current_gallery
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Gallery metadata is inconsistent"
                )

            asset_by_url[url] = asset

        ordered_assets = [
            asset_by_url[url]
            for url in new_order
            if url in asset_by_url
        ]

        # Optimistic concurrency:
        # Reject the update if the gallery changed
        # while the admin was arranging images.
        filter_query = {
            "_id": object_id,
            "gallery": current_gallery
        }

        if "gallery_assets" in project:
            filter_query["gallery_assets"] = (
                project["gallery_assets"]
            )
        else:
            filter_query["gallery_assets"] = {
                "$exists": False
            }

        result = projects_collection.update_one(
            filter_query,
            {
                "$set": {
                    "gallery": new_order,
                    "gallery_assets": ordered_assets
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Gallery changed. Refresh "
                    "and try again."
                )
            )

        return {
            "message": "Gallery order saved successfully",
            "project_id": project_id,
            "gallery": new_order,
            "gallery_assets": ordered_assets,
            "total_images": len(new_order)
        }

    except HTTPException:
        raise

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to save gallery order"
        ) from exc
