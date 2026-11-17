from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017/"

client = MongoClient(MONGO_URL)

db = client["shivrai_group"]

print("MongoDB connection configured!")



try:
    client.admin.command("ping")
    print("Successss")

except Exception as e:
    print("")    

projects_collection = db["projects"]
contacts_collection = db["contacts"]

projects_collection.create_index("name")
projects_collection.create_index("status")
projects_collection.create_index("category")
projects_collection.create_index("location")


contacts_collection.create_index("email")
contacts_collection.create_index("status")
contacts_collection.create_index("created_at")
