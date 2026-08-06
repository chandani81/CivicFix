"""
ai_services.image_detection
-----------------------------
Per the project plan: "If it looks so serious, AI should detect it and
mark it as emergency." This module analyses an uploaded complaint photo
and returns whether it looks like an emergency, plus a confidence score.

IMPORTANT (be upfront about this in your defense):
Real emergency detection (e.g. spotting a collapsed structure, a large
gas/water main burst, a fire, or a badly flooded street) needs a trained
computer-vision model. This module ships a lightweight heuristic
(image statistics: red-channel dominance, edge density, low-light
detection) so the feature works end-to-end with zero external
dependencies/API keys. It is deliberately isolated behind
`detect_emergency()` so you can swap it for a real model later
(e.g. a fine-tuned CNN, or a call to a hosted vision API) without
touching any other code.
"""

from dataclasses import dataclass

try:
    from PIL import Image, ImageFilter, ImageStat
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class EmergencyResult:
    is_emergency: bool
    confidence: float
    reason: str


# Keywords a citizen or department might type that strongly imply urgency;
# combined with the image heuristic for a slightly smarter first pass.
_URGENT_TEXT_HINTS = [
    "urgent", "emergency", "danger", "dangerous", "collapsed", "collapse",
    "fire", "burst", "flooding", "flood", "exposed wire", "live wire",
    "gas leak", "accident", "injured", "injury",
]


def _analyze_image(image_path: str) -> tuple[float, str]:
    """Returns (severity_score 0-1, reason) from basic image statistics."""
    if not PIL_AVAILABLE:
        return 0.0, "PIL not available - skipped image analysis"

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception:
        return 0.0, "Could not open image"

    img_small = img.resize((200, 200))
    stat = ImageStat.Stat(img_small)
    r, g, b = stat.mean

    score = 0.0
    reasons = []

    # Heuristic 1: strong red dominance can indicate fire, blood, hazard markings
    if r > g + 25 and r > b + 25 and r > 100:
        score += 0.4
        reasons.append("high red-channel dominance")

    # Heuristic 2: very dark image can indicate a blackout / structural collapse at night
    brightness = (r + g + b) / 3
    if brightness < 40:
        score += 0.2
        reasons.append("very low brightness")

    # Heuristic 3: high edge density can indicate rubble/debris/structural damage
    edges = img_small.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_intensity = edge_stat.mean[0]
    if edge_intensity > 40:
        score += 0.3
        reasons.append("high edge density (possible debris/damage)")

    score = min(score, 1.0)
    reason = "; ".join(reasons) if reasons else "no strong visual emergency signals"
    return score, reason


def detect_emergency(image_path: str = None, title: str = "", description: str = "") -> EmergencyResult:
    """
    Combines a text-hint check with an (optional) image heuristic to decide
    if a complaint should be auto-flagged as an emergency.

    threshold: score >= 0.5 -> flagged as emergency
    """
    text = f"{title or ''} {description or ''}".lower()
    # Explicit danger language must be enough to flag a report even when the
    # citizen cannot safely stop and take a photo.
    text_score = 0.6 if any(hint in text for hint in _URGENT_TEXT_HINTS) else 0.0
    text_reason = "urgent language detected in report" if text_score else ""

    image_score, image_reason = (0.0, "no photo provided")
    if image_path:
        image_score, image_reason = _analyze_image(image_path)

    combined = min(text_score + image_score, 1.0)
    is_emergency = combined >= 0.5

    reason_parts = [p for p in [text_reason, image_reason] if p]
    reason = "; ".join(reason_parts) if reason_parts else "no emergency signals detected"

    return EmergencyResult(is_emergency=is_emergency, confidence=round(combined, 2), reason=reason)
