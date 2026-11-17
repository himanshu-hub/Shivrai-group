from datetime import datetime


def project_model(
    name,
    status,
    location,
    description
):
    return{
        "name": name,
        "status": status,
        "location": location,
        "description": description,
        "created_at": datetime.utcnow()
    }