"""Reusable, importable feature engineering for the CivicFix SVM artifact."""

from sklearn.base import BaseEstimator, TransformerMixin


DOMAIN_SIGNALS = {
    "road_damage": (
        "pothole", "asphalt", "pavement", "footpath", "sidewalk", "highway",
        "blacktop", "speed breaker", "road", "roadway", "intersection", "bridge",
        "ruts", "gravel", "crater",
    ),
    "water_leakage": (
        "drinking water", "water pipe", "water supply", "supply line", "water pressure",
        "public tap", "pipeline", "water main", "reservoir", "distribution pipe",
        "clean water", "muddy water", "water meter",
    ),
    "garbage": (
        "garbage", "rubbish", "waste", "trash", "dustbin", "dumping", "debris",
        "litter", "bin", "rats", "refuse", "collection vehicle",
    ),
    "street_light": (
        "electricity", "electrical", "power outage", "power cut", "transformer",
        "electric pole", "power line", "exposed wire", "live wire", "sparking wire",
        "street lamp", "streetlight", "lamp", "lighting", "pole light", "bulb",
        "solar light", "electrical box", "illumination", "sparks", "dark lane",
    ),
    "drainage": (
        "drain", "drainage", "sewage", "sewer", "gutter", "waterlogged",
        "storm drain", "culvert", "wastewater", "silt", "rainwater channel",
        "manhole", "standing dirty water",
    ),
    "others": (
        "public park", "public toilet", "advertising board", "playground", "park bench",
        "abandoned vehicle", "street vendor", "drinking fountain", "overgrown bushes",
        "dead animal", "public signage", "accessibility ramp", "fallen tree",
    ),
}


class CivicSignalAugmenter(BaseEstimator, TransformerMixin):
    """Append domain markers while retaining the citizen's original text."""

    def fit(self, values, labels=None):
        return self

    def transform(self, values):
        augmented = []
        for value in values:
            text = str(value).lower()
            markers = []
            for category, signals in DOMAIN_SIGNALS.items():
                if any(signal in text for signal in signals):
                    markers.extend([f"civic_signal_{category}"] * 3)
            augmented.append(f"{text} {' '.join(markers)}")
        return augmented
