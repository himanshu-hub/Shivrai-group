
import cloudinary.uploader

# Load Cloudinary credentials and configuration
import app.cloudinary_config


def upload_project_image(file):
    """
    Upload a project image to Cloudinary.
    Returns its secure URL and public ID.
    """

    result = cloudinary.uploader.upload(
        file,
        folder="shivrai-group/projects",
        resource_type="image"
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }
