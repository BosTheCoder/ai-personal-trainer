#!/usr/bin/env python3
"""
Validation script for exercise_videos.json

This script verifies that all exercise template IDs in the JSON file
match those available from the get_exercise_templates function.
"""

import json
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.db import get_exercise_templates
except ImportError as e:
    print(f"Error importing database functions: {e}")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)


def load_exercise_videos():
    """Load exercise videos mapping from JSON file."""
    json_path = Path(__file__).parent.parent / "database" / "exercise_videos.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Exercise videos JSON file not found: {json_path}")

    with open(json_path, "r") as f:
        return json.load(f)


def validate_videos():
    """Validate that JSON template IDs match database template IDs."""
    print("Loading exercise videos from JSON...")
    video_mapping = load_exercise_videos()
    json_template_ids = set(video_mapping.keys())

    print("Fetching exercise templates from database...")
    db_templates = get_exercise_templates()
    db_template_ids = {template.template_id for template in db_templates}

    print("\nValidation Results:")
    print(f"JSON file contains {len(json_template_ids)} exercise video mappings")
    print(f"Database contains {len(db_template_ids)} exercise templates")

    json_only = json_template_ids - db_template_ids
    if json_only:
        print(f"\n❌ Template IDs in JSON but not in database ({len(json_only)}):")
        for template_id in sorted(json_only):
            print(f"  - {template_id}")

    db_only = db_template_ids - json_template_ids
    if db_only:
        print(f"\n⚠️  Template IDs in database but not in JSON ({len(db_only)}):")
        for template_id in sorted(db_only):
            print(f"  - {template_id}")

    matching = json_template_ids & db_template_ids
    if matching:
        print(f"\n✅ Matching template IDs ({len(matching)}):")
        for template_id in sorted(matching):
            print(f"  - {template_id}")

    if json_only:
        print(
            f"\n❌ VALIDATION FAILED: {len(json_only)} template IDs in JSON "
            "are not found in database"
        )
        return False
    else:
        print("\n✅ VALIDATION PASSED: All JSON template IDs exist in database")
        return True


if __name__ == "__main__":
    try:
        success = validate_videos()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        sys.exit(1)
