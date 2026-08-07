"""
ai_services.categorization
---------------------------
Auto-suggests a complaint category from the title + description text,
so a citizen who leaves the category blank (or picks "Others") still
gets routed to the right department.

This ships as a fast, dependency-free keyword classifier so the whole
project runs out of the box with zero API keys. It's intentionally
isolated behind `categorize()` so it can be swapped for a real trained
NLP model (e.g. a fine-tuned transformer, or a call to an LLM) later
without touching any other app.
"""

from departments.models import Department

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
        "street light", "streetlight", "lamp post", "light not working",
        "dark street", "pole light", "no light",
    ],
    Department.Category.DRAINAGE: [
        "drain", "drainage", "sewer", "sewage", "manhole", "clogged",
        "flooding", "waterlogged", "blocked drain",
    ],
}


def categorize(title: str, description: str = "") -> str:
    """
    Returns a Department.Category value guessed from the text.
    Falls back to OTHERS if nothing matches confidently.
    """
    text = f"{title or ''} {description or ''}".lower()

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
