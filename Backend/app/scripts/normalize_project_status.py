"""One-time migration of legacy project status 'Active' to 'Ongoing'.

Run from the Backend directory:
    python -m app.scripts.normalize_project_status
    python -m app.scripts.normalize_project_status --apply
"""

import argparse
from pymongo.errors import PyMongoError
from app.database import projects_collection


def main():
    parser = argparse.ArgumentParser(description="Normalize legacy project status values")
    parser.add_argument("--apply", action="store_true", help="Apply the migration (default: preview only)")
    args = parser.parse_args()

    try:
        legacy_projects = list(
            projects_collection.find(
                {"status": "Active"},
                {"name": 1, "status": 1},
            )
        )

        if not legacy_projects:
            print("No projects have the legacy status 'Active'. Nothing to change.")
            return

        print(f"Found {len(legacy_projects)} project(s) with status 'Active':")
        for project in legacy_projects:
            print(f"  {project['_id']} | {project.get('name', 'Unnamed project')} | Active -> Ongoing")

        if not args.apply:
            print("\nPreview only. Run with --apply to update these projects.")
            return

        result = projects_collection.update_many(
            {"status": "Active"},
            {"$set": {"status": "Ongoing"}},
        )
        print(f"\nMigration complete: matched={result.matched_count}, modified={result.modified_count}.")
    except PyMongoError as exc:
        raise SystemExit(f"Database error: {exc}") from exc


if __name__ == "__main__":
    main()
