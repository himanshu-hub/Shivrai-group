from app.database import projects_collection


sample_project = {
    "name":"test project",
    "status":"ongoing",
    "location":"Nagpur",
    "description":"This is test project"
}

result = projects_collection.insert_one(sample_project)

print("Project Insert Successfully!")
print("Insert Id:", result.inserted_id)