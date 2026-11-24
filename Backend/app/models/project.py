
from datetime import datetime, timezone


def project_model(
    name,
    status,
    location,
    description,
    category=None,
    image=None,
    gallery=None
):
    return {
        "name": name,
        "status": status,
        "category": category,
        "location": location,
        "description": description,

        # Main cover image URL
        "image": image,

        # Additional project image URLs
        "gallery": gallery if gallery is not None else [],

        "created_at": datetime.now(timezone.utc)
    }
