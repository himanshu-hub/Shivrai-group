
import argparse

import cloudinary.api
import app.cloudinary_config

from app.database import projects_collection


media_collection = projects_collection.database["media"]


def image_references(public_id, url):
    conditions = [
        {"image_public_id": public_id},
        {"gallery_assets.public_id": public_id},
    ]

    if url:
        conditions.extend([
            {"image": url},
            {"gallery": url},
        ])

    return projects_collection.count_documents({
        "$or": conditions
    })


def cloudinary_image_exists(public_id):
    response = cloudinary.api.resources_by_ids(
        [public_id],
        resource_type="image",
        type="upload"
    )

    return bool(response.get("resources"))


def recover_media(apply=False):
    """
    Run only while all backend instances are stopped.

    Default: inspect without modifying data.
    --apply: reconcile interrupted operations.
    """

    print("Media Library recovery started")
    print("Mode:", "APPLY" if apply else "DRY RUN")

    pending = list(media_collection.find({
        "deleting": True
    }))

    recovered = 0
    orphaned = 0
    manual_review = 0

    for media in pending:
        public_id = media.get("public_id")
        url = media.get("url")

        if not public_id:
            print("Missing public_id:", media["_id"])
            manual_review += 1
            continue

        try:
            exists = cloudinary_image_exists(public_id)
            references = image_references(public_id, url)

        except Exception as exc:
            print(
                "Verification failed:",
                public_id,
                type(exc).__name__
            )
            manual_review += 1
            continue

        if exists:
            # The file still exists. Cancel the
            # interrupted deletion claim.
            print("Recover deletion claim:", public_id)

            if apply:
                media_collection.update_one(
                    {"_id": media["_id"], "deleting": True},
                    {
                        "$unset": {"deleting": ""},
                        "$set": {"active_operations": 0}
                    }
                )

            recovered += 1

        elif references == 0:
            # Cloudinary file is gone and no project
            # references the record.
            print("Remove orphaned media record:", public_id)

            if apply:
                media_collection.delete_one({
                    "_id": media["_id"],
                    "deleting": True
                })

            orphaned += 1

        else:
            # Never remove metadata for a missing
            # image that is still used by a project.
            print(
                "MANUAL REVIEW: Missing image is still used:",
                public_id
            )
            manual_review += 1

    # Reset interrupted selection reservations.
    stuck_filter = {
        "active_operations": {"$gt": 0},
        "deleting": {"$ne": True}
    }

    stuck_count = media_collection.count_documents(
        stuck_filter
    )

    if apply:
        media_collection.update_many(
            stuck_filter,
            {"$set": {"active_operations": 0}}
        )

    print("\nRecovery summary")
    print("Interrupted deletion claims:", len(pending))
    print("Claims to recover:", recovered)
    print("Orphaned records to remove:", orphaned)
    print("Stuck reservations:", stuck_count)
    print("Manual review required:", manual_review)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply verified recovery changes"
    )

    args = parser.parse_args()

    recover_media(apply=args.apply)
