import difflib
import time
from typing import Any, Dict, List, Optional

from .clients.hevy_client import HevyClient

_template_cache: Optional[List[Dict[str, Any]]] = None
_cache_timestamp: Optional[float] = None
CACHE_DURATION = 3600

OTHER_NOTES_TEMPLATE = {"template_id": "other_notes", "name": "Other – Notes"}


async def get_hevy_templates(hevy_client: HevyClient) -> List[Dict[str, Any]]:
    """Fetch all Hevy exercise templates with caching."""
    global _template_cache, _cache_timestamp

    current_time = time.time()
    if (
        _template_cache is not None
        and _cache_timestamp is not None
        and current_time - _cache_timestamp < CACHE_DURATION
    ):
        return _template_cache

    all_templates = []
    page = 1
    page_size = 100

    while True:
        response = await hevy_client.get_exercise_templates(
            page=page, page_size=page_size
        )
        templates = response.get("exercise_templates", [])

        if not templates:
            break

        all_templates.extend(templates)

        if len(templates) < page_size:
            break

        page += 1

    _template_cache = all_templates
    _cache_timestamp = current_time
    return all_templates


async def match_exercise_template(
    name: str,
    hevy_client: Optional[HevyClient] = None,
    similarity_threshold: float = 0.6,
) -> Dict[str, Any]:
    """
    Match an exercise name to a Hevy template using string similarity.

    Args:
        name: Exercise name to match
        hevy_client: HevyClient instance (will create one if not provided)
        similarity_threshold: Minimum similarity score for a match (0.0-1.0)

    Returns:
        Dictionary with template_id and name, either matched or fallback
    """
    if not name or not name.strip():
        return {
            "template_id": OTHER_NOTES_TEMPLATE["template_id"],
            "name": f"{OTHER_NOTES_TEMPLATE['name']} - {name}",
        }

    if hevy_client is None:
        hevy_client = HevyClient()

    try:
        templates = await get_hevy_templates(hevy_client)

        best_match = None
        best_score = 0.0

        name_lower = name.lower().strip()

        for template in templates:
            template_name = template.get("name", "").lower().strip()
            if not template_name:
                continue

            similarity = difflib.SequenceMatcher(
                None, name_lower, template_name
            ).ratio()

            if similarity > best_score:
                best_score = similarity
                best_match = template

        if best_match and best_score >= similarity_threshold:
            return {
                "template_id": best_match.get("id", best_match.get("template_id")),
                "name": best_match.get("name"),
            }
        else:
            return {
                "template_id": OTHER_NOTES_TEMPLATE["template_id"],
                "name": f"{OTHER_NOTES_TEMPLATE['name']} - {name}",
            }

    except Exception:
        return {
            "template_id": OTHER_NOTES_TEMPLATE["template_id"],
            "name": f"{OTHER_NOTES_TEMPLATE['name']} - {name}",
        }
