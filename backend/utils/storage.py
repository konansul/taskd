"""
Storage system for managing presentations.
Uses JSON files to store presentation data.
"""
import json
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

STORAGE_DIR = Path("presentations_storage")
STORAGE_DIR.mkdir(exist_ok=True)


def generate_presentation_id() -> str:
    """Generate a unique presentation ID."""
    return str(uuid.uuid4())


_SAFE_ID_REGEX = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LENGTH = 120


def _sanitize_identifier(identifier: str) -> str:
    """
    Sanitize identifier for filesystem usage.
    Falls back to a UUID if input is empty or becomes empty after sanitisation.
    """
    if not identifier:
        return generate_presentation_id()

    candidate = _SAFE_ID_REGEX.sub("_", identifier.strip())
    candidate = candidate.strip("._")

    if len(candidate) > _MAX_FILENAME_LENGTH:
        candidate = candidate[:_MAX_FILENAME_LENGTH]

    if not candidate:
        return generate_presentation_id()

    return candidate


def save_presentation(presentation_id: str, slides: List[Dict], metadata: Optional[Dict] = None) -> Dict:
    """Save presentation data to storage."""
    if metadata is None:
        metadata = {}
    safe_id = _sanitize_identifier(presentation_id)
    
    presentation_data = {
        "id": safe_id,
        "slides": slides,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **metadata
        }
    }
    
    file_path = STORAGE_DIR / f"{safe_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(presentation_data, f, ensure_ascii=False, indent=2)
    
    return presentation_data


def load_presentation(presentation_id: str) -> Optional[Dict]:
    """Load presentation data from storage."""
    safe_id = _sanitize_identifier(presentation_id)
    file_path = STORAGE_DIR / f"{safe_id}.json"
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_presentation(presentation_id: str, slides: List[Dict], metadata: Optional[Dict] = None) -> Optional[Dict]:
    """Update existing presentation."""
    safe_id = _sanitize_identifier(presentation_id)
    existing = load_presentation(safe_id)
    if existing is None:
        return None
    
    if metadata is None:
        metadata = {}
    
    existing["slides"] = slides
    existing["metadata"]["updated_at"] = datetime.now().isoformat()
    existing["metadata"].update(metadata)
    
    file_path = STORAGE_DIR / f"{safe_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return existing


def delete_presentation(presentation_id: str) -> bool:
    """Delete presentation from storage."""
    safe_id = _sanitize_identifier(presentation_id)
    file_path = STORAGE_DIR / f"{safe_id}.json"
    
    if file_path.exists():
        file_path.unlink()
        return True
    return False


def list_presentations() -> List[Dict]:
    """List all presentations."""
    presentations = []
    
    for file_path in STORAGE_DIR.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                presentations.append({
                    "id": data["id"],
                    "metadata": data.get("metadata", {}),
                    "slide_count": len(data.get("slides", []))
                })
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return sorted(presentations, key=lambda x: x["metadata"].get("created_at", ""), reverse=True)

