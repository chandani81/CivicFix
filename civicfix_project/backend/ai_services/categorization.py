"""
ai_services.categorization
---------------------------
Auto-suggests a complaint category from the title + description text,
so a citizen who leaves the category blank (or picks "Others") still
gets routed to the right department.

This first tries a trusted, locally supplied SVM pipeline artifact and
falls back to a fast, dependency-free keyword classifier when the artifact
or its Python dependencies are unavailable. Both paths share `categorize()`
so complaint submission and department routing keep one stable interface.
"""

import logging
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from departments.models import Department


logger = logging.getLogger(__name__)

# Keyword -> category signal. Longer/more specific phrases are checked first.
_KEYWORD_MAP = {
    Department.Category.ROAD_DAMAGE: [
        "pothole", "road damage", "broken road", "cracked road", "road crack",
        "highway", "footpath", "sidewalk broken", "speed breaker", "asphalt",
    ],
    Department.Category.WATER_LEAKAGE: [
        "water leak", "leakage", "pipe burst", "pipe leak", "water supply",
        "no water", "contaminated water", "water pressure", "burst pipe",
    ],
    Department.Category.GARBAGE: [
        "garbage", "trash", "waste", "litter", "dump", "dustbin",
        "rubbish", "not collected", "overflowing bin",
    ],
    Department.Category.STREET_LIGHT: [
        "electricity", "electrical", "power outage", "power cut", "transformer",
        "electric pole", "electrical pole", "power line", "exposed wire", "live wire",
        "sparking wire", "street light", "streetlight", "lamp post",
        "light not working", "dark street", "pole light", "no light",
    ],
    Department.Category.DRAINAGE: [
        "drain", "drainage", "sewer", "sewage", "manhole", "clogged",
        "flooding", "waterlogged", "blocked drain",
    ],
}


_CATEGORY_ALIASES = {
    "road damage": Department.Category.ROAD_DAMAGE,
    "road_damage": Department.Category.ROAD_DAMAGE,
    "water leakage": Department.Category.WATER_LEAKAGE,
    "water_leakage": Department.Category.WATER_LEAKAGE,
    "garbage": Department.Category.GARBAGE,
    "street light": Department.Category.STREET_LIGHT,
    "street_light": Department.Category.STREET_LIGHT,
    "electricity": Department.Category.STREET_LIGHT,
    "electrical": Department.Category.STREET_LIGHT,
    "drainage": Department.Category.DRAINAGE,
    "others": Department.Category.OTHERS,
    "other": Department.Category.OTHERS,
}


@lru_cache(maxsize=1)
def _load_svm_model():
    """Load a trusted local SVM artifact once; return None when unavailable."""
    model_path = Path(settings.SVM_MODEL_PATH) if settings.SVM_MODEL_PATH else None
    if not model_path or not model_path.is_file():
        return None
    try:
        import joblib

        return joblib.load(model_path)
    except Exception as exc:
        logger.warning("Could not load CivicFix SVM categorizer from %s: %s", model_path, exc)
        return None


def _svm_category(text: str):
    model = _load_svm_model()
    if model is None:
        return None
    try:
        prediction = model.predict([text])[0]
    except Exception as exc:
        logger.warning("CivicFix SVM categorization failed; using fallback: %s", exc)
        return None
    return _CATEGORY_ALIASES.get(str(prediction).strip().lower())


def categorizer_status() -> dict:
    """Expose which implementation is active for diagnostics and defense checks."""
    return {
        "engine": "svm" if _load_svm_model() is not None else "keyword_fallback",
        "model_path": str(settings.SVM_MODEL_PATH or ""),
    }


def categorize(title: str, description: str = "") -> str:
    """
    Returns a Department.Category value guessed from the text.
    Falls back to OTHERS if nothing matches confidently.
    """
    text = f"{title or ''} {description or ''}".strip().lower()

    predicted = _svm_category(text)
    if predicted:
        return predicted

    best_category = Department.Category.OTHERS
    best_score = 0

    for category, keywords in _KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def suggest_department(title: str, description: str = ""):
    """Returns the Department instance that matches the guessed category, if one exists."""
    category = categorize(title, description)
    return Department.objects.filter(category=category, is_active=True).first()
